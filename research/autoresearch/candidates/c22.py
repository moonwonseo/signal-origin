import numpy as np
import lib
ID, PARENT = "c22", "c21"
HYP = ("Season heat is the state of the crop and the 90-day stress is the recent news. When the news agrees "
       "with the state the signal is clear; when they disagree the state is changing and there is no clear call.")
CHANGE = "Agreement rule of two features: buy early if season maximum-temperature anomaly > 0 and 90-day stress > 0; buy late if both < 0; else steady."
EXPECT = "Active on about 70% of days. RATIO above c21."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_season_raw(D, "temperature_max_c", name="season_tmax").join(lib.bra_stress(D, 90))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    a, b = Xte.season_tmax.to_numpy(float), Xte.stress_bra90.to_numpy(float)
    return np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), 0.0, 0.5))
