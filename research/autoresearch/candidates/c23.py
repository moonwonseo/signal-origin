import numpy as np
import lib
ID, PARENT = "c23", "c22"
HYP = ("The signal is a slow state of the crop. If that is true, weather data that are 10 days old must give "
       "nearly the same result as data that are 4 days old. (Robustness check: real-time POWER values can be late.)")
CHANGE = "c22 with the weather lag changed from 4 to 10 calendar days. Nothing else changes."
EXPECT = "RATIO within 0.05 of c22. A large fall would show a fragile result."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_season_raw(D, "temperature_max_c", name="season_tmax", lag=10).join(lib.bra_stress(D, 90, lag=10))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    a, b = Xte.season_tmax.to_numpy(float), Xte.stress_bra90.to_numpy(float)
    return np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), 0.0, 0.5))
