import numpy as np
import lib
ID, PARENT = "c99", "c86"
HYP = "The design for a buyer, with the two choices that do not depend on luck: ENSO as the standard December-February mean (known mid March) and the Brazil January-March heat as the mean of two independent weather products."
CHANGE = "Agreement of two signals: December-February Nino 3.4 mean (sign) and the two-product Brazil Jan-Mar heat anomaly (sign). Both positive: buy early. Both negative: buy late. Else steady."
EXPECT = "RATIO about +0.6 (c93 gave +0.599 with the January ENSO value)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_djf", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.final_inputs(D)


fit_predict = lib.agree_fp(["enso_djf", "fill_heat"])
