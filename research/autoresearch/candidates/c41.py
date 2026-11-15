import numpy as np
import lib
ID, PARENT = "c41", "c21"
HYP = ("A season-heat anomaly near zero is noise; a large anomaly is clear crop news. Acting only on large "
       "anomalies must raise the quality of the calls.")
CHANGE = "c21 with a dead zone: buy early if the season maximum-temperature anomaly is in the upper third of its earlier values (training rows of each test year), buy late in the lower third, else steady."
EXPECT = "Active on about two thirds of days. RATIO above c21 (+0.596) if size matters."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_season_raw(D, "temperature_max_c", name="season_tmax")


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    lo, hi = np.percentile(Xtr.season_tmax.to_numpy(float), [100 / 3, 200 / 3])
    x = Xte.season_tmax.to_numpy(float)
    return np.where(x > hi, 1.0, np.where(x < lo, 0.0, 0.5))
