import numpy as np
import lib
ID, PARENT = "c98", "c86"
HYP = "An ENSO event can start or end in the middle of the year. A January value that is 7 to 12 months old can be wrong for the second half; the July value (published mid August) is a fresher state."
CHANGE = "c86 with the ENSO input updated two times a year: the January value from mid February and the July value from mid August."
EXPECT = "RATIO at or above c86 if the fresher state helps; lower if only the winter state matters."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jj", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.enso_latest(D).join(lib.two_state(D)[["fill_heat"]])


fit_predict = lib.agree_fp(["enso_jj", "fill_heat"])
