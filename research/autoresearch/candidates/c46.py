import numpy as np
import lib
ID, PARENT = "c46", "c22"
HYP = ("c45 showed that the grain-fill months carry the heat signal. The c22 form (state of the crop and recent "
       "news must agree) with the grain-fill state must be equal or better and more equal over time.")
CHANGE = "c22 with the season heat (Oct-Apr) replaced by the grain-fill heat (Jan-Mar, held to the next January). Agreement with the 90-day stress as before."
EXPECT = "RATIO equal to or above c22 with more equal halves."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (1, 2, 3), 1, "fill_tmax").join(lib.bra_stress(D, 90))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    a, b = Xte.fill_tmax.to_numpy(float), Xte.stress_bra90.to_numpy(float)
    return np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), 0.0, 0.5))
