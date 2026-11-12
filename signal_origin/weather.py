"""Preserved A1 anomaly reconstruction and V3 dry-spell features.

Source: the supplied project bundle; see docs/PROVENANCE.md.
"""
import numpy as np
import pandas as pd
from .spec import SignalOriginError
WEATHER = ('rain_anom_z', 'temp_anom_z')
def datestr(value):
    return pd.Timestamp(value).strftime('%Y-%m-%d')

def rebuild_features(w,years_to_build=None):
    """Preserve the supplied prior-years-only expanding climatology convention.

    z reference uses rolling statistics whose END DATE is in an earlier year,
    within circular +/-7 DOY units. The raw 30-day statistic of course includes
    current-year observations. Leap convention min(DOY,365) is retained/flagged.
    """
    f=pd.DataFrame(index=w.index)
    f['rain30_mm']=w.precipitation_mm_per_day.rolling(30,min_periods=30).sum()
    f['temp30_mean_c']=w.temperature_mean_c.rolling(30,min_periods=30).mean()
    f['tmin30_lowest_c']=w.temperature_min_c.rolling(30,min_periods=30).min()
    yr=f.index.year.to_numpy();doy=np.minimum(f.index.dayofyear.to_numpy(),365)
    f['rain_anom_z']=np.nan;f['temp_anom_z']=np.nan
    f['reference_latest_date']=pd.NaT;f['reference_first_year']=np.nan;f['reference_last_year']=np.nan;f['reference_years']=np.nan
    norms=[]
    for y in sorted(set(yr)):
        if years_to_build is not None and y not in years_to_build:continue
        before=(yr<y)
        if len(set(yr[before]))<10:continue
        rows=np.flatnonzero(yr==y)
        for day in sorted(set(doy[rows])):
            dist=np.abs(doy-day);dist=np.minimum(dist,365-dist)
            history=before & (dist<=7)
            current=rows[doy[rows]==day]
            usable=history & f.rain30_mm.notna().to_numpy() & f.temp30_mean_c.notna().to_numpy()
            latest=f.index[usable].max()
            if not (latest<f.index[current].min()):raise SignalOriginError('Future reference observations found.')
            f.loc[f.index[current],'reference_latest_date']=latest
            f.loc[f.index[current],'reference_first_year']=int(yr[usable].min())
            f.loc[f.index[current],'reference_last_year']=int(yr[usable].max())
            f.loc[f.index[current],'reference_years']=len(set(yr[usable]))
            for value,z in [('rain30_mm','rain_anom_z'),('temp30_mean_c','temp_anom_z')]:
                vals=f.loc[history,value].dropna().to_numpy()
                mean=float(np.mean(vals));sd=float(np.std(vals,ddof=1))
                if not np.isfinite(sd) or sd<=0:raise SignalOriginError('Invalid climatology variance.')
                f.loc[f.index[current],z]=(f.loc[f.index[current],value].to_numpy()-mean)/sd
                norms.append({'weather_year':int(y),'climatology_doy':int(day),'variable':value,'n_reference_windows':len(vals),'reference_first_year':int(yr[usable].min()),'reference_last_year':int(yr[usable].max()),'reference_latest_date':datestr(latest),'reference_mean':mean,'reference_sd_ddof1':sd})
    # Source handoff rounded all five candidate features to 4 decimals. Retain it.
    f.loc[:,['rain30_mm','temp30_mean_c','tmin30_lowest_c',*WEATHER]]=f.loc[:,['rain30_mm','temp30_mean_c','tmin30_lowest_c',*WEATHER]].round(4)
    return f,pd.DataFrame(norms)

def longest_dry_run(window: np.ndarray, threshold: float = 1.0) -> float:
    """Length of the longest run in a complete window. A wet day at 1 mm breaks a run."""
    arr = np.asarray(window, dtype=float)
    if arr.ndim != 1 or not len(arr):
        raise ValueError('A nonempty one-dimensional rainfall window is required.')
    if not np.isfinite(arr).all():
        return np.nan
    if (arr < 0).any():
        raise ValueError('Negative rainfall is invalid.')
    best = current = 0
    for val in arr:
        current = current + 1 if val < threshold else 0
        best = max(best, current)
    return float(best)

def dry_spell_features(weather: pd.DataFrame) -> pd.DataFrame:
    """Compute past-only 30-calendar-day values. Never compress missing weather dates."""
    columns = {'weather_date_utc','precipitation_mm_per_day'}
    if not columns.issubset(weather):
        raise ValueError('Weather requires date and rainfall columns.')
    w = weather[list(columns)].copy()
    w['weather_date_utc'] = pd.to_datetime(w.weather_date_utc, errors='raise')
    if w.weather_date_utc.isna().any() or w.weather_date_utc.duplicated().any() or not w.weather_date_utc.is_monotonic_increasing:
        raise ValueError('Weather dates must be present, unique and sorted.')
    w['precipitation_mm_per_day'] = pd.to_numeric(w.precipitation_mm_per_day, errors='raise')
    if np.isinf(w.precipitation_mm_per_day).any() or (w.precipitation_mm_per_day.dropna()<0).any():
        raise ValueError('Rainfall must be finite/nonnegative or explicitly missing.')
    expected = pd.date_range(w.weather_date_utc.min(), w.weather_date_utc.max(), freq='D')
    w = w.set_index('weather_date_utc').reindex(expected)
    w.index.name = 'weather_observation_date'
    w['dry_spell_max_30d'] = w.precipitation_mm_per_day.rolling(30, min_periods=30).apply(longest_dry_run, raw=True)
    w['weather_window_start'] = w.index-pd.Timedelta(days=29)
    w['weather_window_end'] = w.index
    return w.reset_index()
