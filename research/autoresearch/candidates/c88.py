import numpy as np
import lib
ID, PARENT = "c88", "c86"
HYP = "Check of c86: a 10-year normal in place of the 5-year normal."
CHANGE = "c86 with the Brazil heat anomaly measured against the last 10 years."
EXPECT = "RATIO within 0.15 of c86 (+0.787)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state(D, years=10)


fit_predict = lib.agree_fp(["enso_jan", "fill_heat"])
