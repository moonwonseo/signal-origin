import numpy as np
import lib
ID, PARENT = "c24", "c22"
HYP = ("The signal is heat against the recent normal. If that is true, a 10-year normal must give a similar "
       "result to the 5-year normal. (Robustness check of the one free choice in the season measure.)")
CHANGE = "c22 with the normal of the season maximum temperature changed from the last 5 years to the last 10 years. Nothing else changes."
EXPECT = "RATIO within 0.1 of c22."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_season_raw(D, "temperature_max_c", years=10, name="season_tmax").join(lib.bra_stress(D, 90))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    a, b = Xte.season_tmax.to_numpy(float), Xte.stress_bra90.to_numpy(float)
    return np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), 0.0, 0.5))
