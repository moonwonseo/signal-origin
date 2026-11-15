import numpy as np
import lib
ID, PARENT = "c26", "c22"
HYP = ("Arabica has a two-year cycle: the branches that grow in one season carry the fruit of the next. Heat "
       "in the previous season lowers the coming crop too, so the state must remember it.")
CHANGE = "c22 with the season heat replaced by the mean of this season's and the previous season's maximum-temperature anomaly. Nothing else changes."
EXPECT = "RATIO equal to or above c22, with fewer position changes."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_season_raw(D, "temperature_max_c", name="season_tmax", memory=True).join(lib.bra_stress(D, 90))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    a, b = Xte.season_tmax.to_numpy(float), Xte.stress_bra90.to_numpy(float)
    return np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), 0.0, 0.5))
