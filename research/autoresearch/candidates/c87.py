import numpy as np
import lib
ID, PARENT = "c87", "c86"
HYP = "Check of c86: the daily maximum temperature in place of the daily mean must give nearly the same rule."
CHANGE = "c86 with the Brazil Jan-Mar maximum-temperature anomaly in place of the mean-temperature anomaly."
EXPECT = "RATIO within 0.15 of c86 (+0.787)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state(D, col="temperature_max_c")


fit_predict = lib.agree_fp(["enso_jan", "fill_heat"])
