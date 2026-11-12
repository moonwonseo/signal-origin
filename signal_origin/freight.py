"""V4 label, alignment, matched-model fitting and scoring calculations.

Numerical functions preserved from the supplied V4 experiment. Archive-bound
imports, settings lookups and freeze commands are replaced by explicit inputs.
"""
import warnings
from decimal import Decimal, InvalidOperation, localcontext
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from .spec import FEATURES, RunConfig, SignalOriginError
from .models import TARGET as FIT_TARGET, fit_pair, check_binary
from .parameters import export_model, probabilities_from_json
from .split import make_split, nonoverlapping_origins
from .evaluation import probability_metrics, calibration_table
Y = 'target_spike'
FREIGHT = ('freight_log_change_3m', 'freight_log_change_12m')
A1_FEATURES = (*FEATURES, 'rain_anom_z', 'temp_anom_z')
A2_FEATURES = (*FEATURES, 'dry_spell_max_30d', 'temp_anom_z')
MODEL_FEATURES = {
    'B0': (), 'B1': tuple(FEATURES), 'A1': A1_FEATURES, 'A2': A2_FEATURES,
    'F1': (*FEATURES, *FREIGHT), 'FW1': (*A1_FEATURES, *FREIGHT),
    'FW2': (*A2_FEATURES, *FREIGHT),
}
MODELS = tuple(MODEL_FEATURES)
POLICIES = {'delayed_180d_primary': 180, 'fast_45d_revised_sensitivity': 45}
STATUS = 'EXPLORATORY_REVISED_FREIGHT_COST_PROXY_NOT_PORT_TRAFFIC_OR_INDEPENDENT_VALIDATION'

def labels(frame,h):
 """Calendar-preserving threshold labels using decimal raw source values."""
 if type(h) is not int or h<1:raise ValueError('horizon must be a positive integer')
 req={'price_date','session_index','price_usable','raw_price_text'}
 if not req.issubset(frame):raise ValueError('Missing label input columns')
 n=len(frame)
 if not np.array_equal(frame.session_index.to_numpy(),np.arange(n)):raise ValueError('Do not compress the session calendar')
 dates=frame.price_date
 if not pd.api.types.is_datetime64_any_dtype(dates) or dates.isna().any() or dates.duplicated().any() or not dates.is_monotonic_increasing:raise ValueError('Invalid session dates')
 if not pd.api.types.is_bool_dtype(frame.price_usable) or frame.price_usable.isna().any():raise ValueError('Use explicit price usability booleans')
 p=[]
 for ok,s in zip(frame.price_usable,frame.raw_price_text):
  if not ok:p.append(None);continue
  try:v=Decimal(str(s))
  except (InvalidOperation,ValueError) as e:raise ValueError('Bad price') from e
  if not v.is_finite() or v<=0:raise ValueError('Price must be finite and positive')
  p.append(v)
 out=[None]*n; first=[pd.NaT]*n; peak=[None]*n
 with localcontext() as ctx:
  ctx.prec=80
  for i in range(max(0,n-h)):
   w=p[i+1:i+h+1]
   if p[i] is None or any(v is None for v in w):continue
   peak[i]=str(max(w))
   cross=next((j for j,v in enumerate(w,1) if 100*v>=110*p[i]),None)
   out[i]=int(cross is not None)
   if cross is not None:first[i]=dates.iloc[i+cross]
 return pd.DataFrame({Y:pd.array(out,dtype='Int64'),'label_end_date':dates.shift(-h),'first_cross_date':pd.to_datetime(first),'future_max_close_audit_only':peak},index=frame.index)

def monthly_features(monthly):
 x=monthly.copy()
 x['observation_month']=pd.to_datetime(x.observation_month,errors='raise')
 if x.observation_month.duplicated().any() or not x.observation_month.is_monotonic_increasing or x.observation_month.isna().any():raise ValueError('Monthly dates must be sorted and unique')
 if not x.observation_month.dt.is_month_start.all():raise ValueError('Month must be first-day observation label')
 x['freight_ppi']=pd.to_numeric(x.freight_ppi,errors='raise')
 if not np.isfinite(x.freight_ppi).all() or (x.freight_ppi<=0).any():raise ValueError('Freight index must be finite and positive')
 expected=pd.date_range(x.observation_month.min(),x.observation_month.max(),freq='MS')
 x=x.set_index('observation_month').reindex(expected)
 x.index.name='observation_month'
 logs=np.log(x.freight_ppi)
 for k in (3,12):x[f'freight_log_change_{k}m']=logs-logs.shift(k)
 # Complete previous year required: missing monthly data never compress time.
 complete=x.freight_ppi.rolling(13,min_periods=13).count().eq(13)
 x.loc[~complete,list(FREIGHT)]=np.nan
 return x.reset_index()

def align_freight(design,monthly,lag):
 if lag not in POLICIES.values():raise ValueError('Only predeclared availability assumptions allowed')
 x=monthly_features(monthly)
 x['freight_period_end']=x.observation_month+pd.offsets.MonthEnd(0)
 x['assumed_freight_available_date']=x.freight_period_end+pd.to_timedelta(lag,unit='D')
 x=x.rename(columns={'observation_month':'freight_observation_month'})
 d=pd.merge_asof(design.sort_values('price_date'),x.sort_values('assumed_freight_available_date'),
   left_on='price_date',right_on='assumed_freight_available_date',direction='backward',allow_exact_matches=False,tolerance=pd.Timedelta(days=45))
 if not d.price_date.tolist()==design.price_date.tolist():raise ValueError('As-of join changed price calendar')
 d.index=design.index
 return d

def build_design(base,frame,monthly,h,lag):
 d=base.copy(deep=True)
 lab=labels(frame,h)
 for c in lab:d[c]=lab[c]
 d['label_ready']=d[Y].notna()
 d=align_freight(d,monthly,lag)
 d['upstream_features_ready']=base.features_ready.to_numpy()
 cols=sorted(set(c for fs in MODEL_FEATURES.values() for c in fs))
 d['features_ready']=np.isfinite(d[cols].to_numpy(dtype=float)).all(axis=1)
 d['eligible']=d.features_ready & d.label_ready
 if not (d.weather_observation_date==d.price_date-pd.Timedelta(days=4)).all():raise ValueError('Weather lag changed')
 used=d.loc[d.features_ready]
 if not (used.assumed_freight_available_date<used.price_date).all():raise ValueError('Freight timing violation')
 return d

def fit_models(train,test,cfg):
 adapter=train.copy(deep=True);adapter[FIT_TARGET]=train[Y]
 pair=fit_pair(adapter,cfg)
 pred=pair.predict(test)
 params={'B0_probability':pair.b0.probability_,'B1':export_model(pair.b1,FEATURES),
  'training_rows':len(train),'training_positives':int(train[Y].sum())}
 y=check_binary(train[Y])
 for name in MODELS[2:]:
  cols=list(MODEL_FEATURES[name]);model=clone(pair.b1)
  with warnings.catch_warnings(record=True) as caught:
   warnings.simplefilter('always',ConvergenceWarning)
   model.fit(train[cols],y)
  if any(issubclass(c.category,ConvergenceWarning) for c in caught):raise SignalOriginError('Convergence failure: '+name)
  idx=int(np.flatnonzero(model.classes_==1)[0])
  pred['p_'+name]=model.predict_proba(test[cols])[:,idx]
  params[name]=export_model(model,cols)
 return pred,params

def score(p,scope):
 d=pd.DataFrame([{'scope':scope,'model':m,**probability_metrics(p[Y],p['p_'+m])} for m in MODELS])
 for b in ('B0','B1','A1','A2','F1'):
  d['brier_improvement_vs_'+b]=float(d.loc[d.model.eq(b),'brier_score'].iloc[0])-d.brier_score
 d['evidence_status']=STATUS
 return d
