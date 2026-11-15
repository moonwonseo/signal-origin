import numpy as np
import lib
ID, PARENT = "c83", "c73"
HYP = "Ablation of c73: the two yearly climate states alone (ENSO winter state and Brazil grain-fill heat). The difference to c73 is the value of the market-trend vote."
CHANGE = "Agreement of two signals: January Nino 3.4 (sign) and Brazil Jan-Mar mean-temperature anomaly (sign). Both positive: buy early. Both negative: buy late. Else steady."
EXPECT = "RATIO below c73; about +0.5."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean"))


fit_predict = lib.agree_fp(["enso_jan", "fill_tmean"])
