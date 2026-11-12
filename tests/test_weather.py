import numpy as np
import pandas as pd
import pytest
from signal_origin import weather as e

@pytest.mark.parametrize('values,expected',[
    ([0,0,2,0,0,0],3),([1,1,1],0),([0.99,1,0.2],1),([0]*30,30),([2]*30,0),([0,2,0,2,0],1),([0,0,0,2],3),([2,0,0,0],3)
])
def test_run_lengths(values,expected):
    assert e.longest_dry_run(np.array(values))==expected

def test_missing_is_not_dry():
    assert np.isnan(e.longest_dry_run(np.array([0,np.nan,0])))

@pytest.mark.parametrize('values',[[],[-1,0],[0,-999],[[0,0],[1,2]]])
def test_invalid_window(values):
    with pytest.raises(ValueError):e.longest_dry_run(np.array(values))

def weather(values,dates=None):
    return pd.DataFrame({'weather_date_utc':pd.date_range('2020-01-01',periods=len(values)) if dates is None else dates,'precipitation_mm_per_day':np.asarray(values,dtype=float)})

def test_first_29_undefined():
    d=e.dry_spell_features(weather([0]*40))
    assert d.dry_spell_max_30d.iloc[:29].isna().all()
    assert (d.dry_spell_max_30d.iloc[29:]==30).all()

def test_window_clipped_not_unlimited_run():
    d=e.dry_spell_features(weather([0]*100))
    assert d.dry_spell_max_30d.max()==30

def test_boundary_wet_break():
    d=e.dry_spell_features(weather([0]*29+[1.0]+[0]))
    assert d.dry_spell_max_30d.iloc[29]==29
    assert d.dry_spell_max_30d.iloc[30]==28

def test_calendar_gap_not_compressed():
    w=weather([0]*65).drop(index=30)
    d=e.dry_spell_features(w)
    assert len(d)==65
    assert d.dry_spell_max_30d.iloc[30:60].isna().all()
    assert d.dry_spell_max_30d.iloc[60]==30

def test_missing_value_not_interpolated():
    w=weather([0]*65);w.loc[30,'precipitation_mm_per_day']=np.nan
    d=e.dry_spell_features(w)
    assert d.dry_spell_max_30d.iloc[30:60].isna().all()

def test_future_weather_cannot_change_past_feature():
    w=weather([0]*90);a=e.dry_spell_features(w)
    w.loc[60:,'precipitation_mm_per_day']=100
    b=e.dry_spell_features(w)
    pd.testing.assert_frame_equal(a.iloc[:60],b.iloc[:60])

@pytest.mark.parametrize('kind',['duplicate','unsorted','negative','infinite'])
def test_bad_weather_inputs(kind):
    w=weather([0]*40)
    if kind=='duplicate':w.loc[2,'weather_date_utc']=w.loc[1,'weather_date_utc']
    elif kind=='unsorted':w=w.iloc[::-1]
    elif kind=='negative':w.loc[5,'precipitation_mm_per_day']=-1
    else:w.loc[5,'precipitation_mm_per_day']=np.inf
    with pytest.raises(ValueError):e.dry_spell_features(w)

