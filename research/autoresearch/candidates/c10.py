import numpy as np
import lib
ID, PARENT = "c10", "c06"
HYP = ("Frost in the Brazilian regions destroys part of the next crop. It is a supply shock that the "
       "heat-and-dry measure cannot see, and the size of the loss is known only weeks later.")
CHANGE = "c06 plus one feature: buy early if a frost day (lowest regional minimum below 5 C, Jun-Aug) occurred in the last 90 days; else the c06 stress rule."
EXPECT = "Few days change. RATIO equal to or above c06."
ALT, D_BAND, SMOOTH, SEEDS = ["stress_bra90", "frost_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_stress(D, 90).join(lib.bra_frost(D, 90))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    return np.where(Xte.frost_bra90.to_numpy(float) > 0, 1.0, (Xte.stress_bra90.to_numpy(float) > 0).astype(float))
