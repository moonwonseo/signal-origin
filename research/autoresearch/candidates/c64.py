import numpy as np
import lib
ID, PARENT = "c64", "c08"
HYP = "A positive Indian Ocean Dipole brings drought to Indonesia and floods to East Africa. Both reduce coffee supply from origins that the Brazil and Vietnam rules do not cover."
CHANGE = "Unfitted three-state rule on one alt-data feature (NOAA Dipole Mode Index, used from the 15th of month M+2): index above +0.4: buy early. Below -0.4: buy late. Else steady."
EXPECT = "RATIO above zero; low prior after two ENSO failures."
ALT, D_BAND, SMOOTH, SEEDS = ["dmi_lvl"], 0.0, 1, 1


def features(D):
    return lib.monthly_feats(D, "dmi", "dmi", d=(), tol_days=75)


fit_predict = lib.tri_fp("dmi_lvl", lo=-0.4, hi=0.4)
