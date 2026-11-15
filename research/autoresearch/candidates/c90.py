import numpy as np
import lib
ID, PARENT = "c90", "c86"
HYP = "Check of c86: the Brazil heat window one month earlier (Dec-Feb, held to the next December)."
CHANGE = "c86 with the Brazil heat window Dec-Feb in place of Jan-Mar."
EXPECT = "RATIO above +0.5."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state(D, months=(12, 1, 2), start_month=12)


fit_predict = lib.agree_fp(["enso_jan", "fill_heat"])
