import numpy as np
import lib
ID, PARENT = "c74", "c71"
HYP = "The supply effect comes from real El Nino and La Nina events. In neutral winters the small sign of the index has no physical meaning and adds noise."
CHANGE = "c71 as a three-state rule: January Nino 3.4 above +0.5: buy early. Below -0.5: buy late. Between: steady. Held until the next January value."
EXPECT = "RATIO at or above c71 (+0.385) with fewer active years."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D)


fit_predict = lib.tri_fp("enso_jan", lo=-0.5, hi=0.5)
