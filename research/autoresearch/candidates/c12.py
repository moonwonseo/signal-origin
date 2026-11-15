import numpy as np
import lib
ID, PARENT = "c12", "c06"
HYP = ("Heat-and-dry stress and root-zone soil moisture are two noisy measures of one state (drought stress of "
       "the trees). When they agree, the state is clear; when they disagree, there is no information.")
CHANGE = "c06 plus soil moisture as a confirmation (three-state rule): buy early if stress > 0 and soil moisture anomaly < 0; buy late if stress < 0 and soil moisture anomaly > 0; else steady."
EXPECT = "Active on about 70% of days. RATIO above c06."
ALT, D_BAND, SMOOTH, SEEDS = ["stress_bra90", "gwetroot_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_stress(D, 90).join(lib.bra_extra(D, "gwetroot", 90))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    s, g = Xte.stress_bra90.to_numpy(float), Xte.gwetroot_bra90.to_numpy(float)
    return np.where((s > 0) & (g < 0), 1.0, np.where((s < 0) & (g > 0), 0.0, 0.5))
