import numpy as np
import pandas as pd
import pytest
from signal_origin import freight as f

def frame(vals):
 n=len(vals)
 return pd.DataFrame({'price_date':pd.bdate_range('2019-01-01',periods=n),'session_index':np.arange(n),
 'price_usable':[v is not None for v in vals],'raw_price_text':[str(v) if v is not None else '' for v in vals]})
def months(n=36):
 return pd.DataFrame({'observation_month':pd.date_range('2017-01-01',periods=n,freq='MS'),'freight_ppi':np.arange(n,dtype=float)+100})

@pytest.mark.parametrize('h',[1,3,21,63])
def test_exact_threshold(h):
 vals=[100]*(h+2);vals[h]=110
 out=f.labels(frame(vals),h)
 assert out.loc[0,f.Y]==1
 assert out.loc[0,'first_cross_date']==frame(vals).price_date.iloc[h]
 assert out.loc[0,'label_end_date']==frame(vals).price_date.iloc[h]

@pytest.mark.parametrize('end',[109.999,110,110.001])
def test_boundary(end):assert f.labels(frame([100,end]),1).loc[0,f.Y]==int(end>=110)

@pytest.mark.parametrize('h',[21,63])
def test_full_tail_unlabeled(h):
 d=f.labels(frame([100]*150),h)
 assert d[f.Y].tail(h).isna().all()
 assert d[f.Y].iloc[:-h].eq(0).all()

@pytest.mark.parametrize('h',[21,63])
def test_future_missing_even_after_early_crossing(h):
 vals=[100]*(h+2);vals[1]=120;vals[h//2]=None
 assert pd.isna(f.labels(frame(vals),h).loc[0,f.Y])

def test_temporary_spike_positive():
 out=f.labels(frame([100,111,99,101]),3)
 assert out.loc[0,f.Y]==1

def test_no_calendar_compression():
 x=frame([100]*10).drop(index=2)
 with pytest.raises(ValueError):f.labels(x,3)

@pytest.mark.parametrize('h',[0,-1,2.2])
def test_bad_horizon(h):
 with pytest.raises(ValueError):f.labels(frame([100]*10),h)

@pytest.mark.parametrize('v',[0,-1,'NaN','Infinity'])
def test_bad_price(v):
 with pytest.raises(ValueError):f.labels(frame([100,v,100]),1)

def test_longer_window_contains_shorter():
 x=frame([100,101,103,99,110,100,120,90,95,110])
 a,b=f.labels(x,2),f.labels(x,5)
 mask=b[f.Y].notna()
 assert (a.loc[mask,f.Y]<=b.loc[mask,f.Y]).all()

def test_outcome_not_input():
 for features in f.MODEL_FEATURES.values():
  assert not any('target' in c or 'future' in c or 'cross' in c for c in features)

@pytest.mark.parametrize('name,count',[('B0',0),('B1',5),('A1',7),('A2',7),('F1',7),('FW1',9),('FW2',9)])
def test_feature_counts(name,count):assert len(f.MODEL_FEATURES[name])==count

def test_log_features_and_warmup():
 x=f.monthly_features(months())
 assert x[list(f.FREIGHT)].iloc[:12].isna().all().all()
 assert x.loc[12,f.FREIGHT[1]]==pytest.approx(np.log(112)-np.log(100))
 assert x.loc[12,f.FREIGHT[0]]==pytest.approx(np.log(112)-np.log(109))

def test_missing_month_not_compressed():
 x=f.monthly_features(months().drop(index=20))
 assert len(x)==36
 assert pd.isna(x.freight_ppi.iloc[20])
 assert x.loc[20:32,list(f.FREIGHT)].isna().all().all()

@pytest.mark.parametrize('lag',[45,180])
def test_lag_and_asof(lag):
 x=months();cut=pd.Timestamp('2018-01-31')+pd.Timedelta(days=lag)
 d=pd.DataFrame({'price_date':[cut-pd.Timedelta(days=1),cut,cut+pd.Timedelta(days=1)]})
 out=f.align_freight(d,x,lag)
 assert out.freight_observation_month.iloc[0]<pd.Timestamp('2018-01-01')
 assert out.freight_observation_month.iloc[1]<pd.Timestamp('2018-01-01')
 assert out.freight_observation_month.iloc[2]==pd.Timestamp('2018-01-01')
 assert (out.assumed_freight_available_date<out.price_date).all()

def test_stale_freight_missing():
 out=f.align_freight(pd.DataFrame({'price_date':pd.to_datetime(['2025-01-01'])}),months(),180)
 assert out[list(f.FREIGHT)].isna().all().all()

def test_future_freight_cannot_change_past_features():
 x=months(60);d=pd.DataFrame({'price_date':pd.bdate_range('2019-01-01','2019-12-31')})
 before=f.align_freight(d,x,45)
 x.loc[x.observation_month>=pd.Timestamp('2020-01-01'),'freight_ppi']*=10
 after=f.align_freight(d,x,45)
 pd.testing.assert_frame_equal(before,after)

@pytest.mark.parametrize('bad',['duplicate','negative','unsorted','wrong_month_day'])
def test_invalid_monthly_input(bad):
 x=months()
 if bad=='duplicate':x.loc[1,'observation_month']=x.loc[0,'observation_month']
 elif bad=='negative':x.loc[2,'freight_ppi']=-1
 elif bad=='unsorted':x=x.iloc[::-1]
 else:x.loc[0,'observation_month']=pd.Timestamp('2017-01-02')
 with pytest.raises(ValueError):f.monthly_features(x)




def test_synthetic_train_only_scaler_and_saved_predictions():
 rng=np.random.default_rng(4);cols=sorted(set(c for fs in f.MODEL_FEATURES.values() for c in fs))
 train=pd.DataFrame(rng.normal(size=(300,len(cols))),columns=cols);train[f.Y]=np.tile([0,1],150)
 test=pd.DataFrame(rng.normal(size=(40,len(cols))),columns=cols)
 cfg=f.RunConfig(test_start='2022-01-03')
 pred,pars=f.fit_models(train,test,cfg)
 for m in f.MODELS[1:]:
  # Export shape may vary; prediction helper is the archived independent formula.
  actual=f.probabilities_from_json(test,pars[m])
  np.testing.assert_allclose(actual,pred['p_'+m],rtol=0,atol=1e-12)
 test2=test*100
 _,pars2=f.fit_models(train,test2,cfg)
 assert pars==pars2
 assert pred.p_B0.eq(0.5).all()
