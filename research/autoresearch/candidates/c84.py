import numpy as np
import lib
ID, PARENT = "c84", "c83"
HYP = "Robustness of c83: the December-February ENSO mean (known mid March) in place of the January value."
CHANGE = "c83 with the January Nino 3.4 value replaced by the December-February mean."
EXPECT = "RATIO within 0.1 of c83 (+0.705)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_djf", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_djf(D).join(lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean"))


fit_predict = lib.agree_fp(["enso_djf", "fill_tmean"])
