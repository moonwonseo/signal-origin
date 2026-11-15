import numpy as np
import lib
ID, PARENT = "c82", "c73"
HYP = "Robustness of c73: an ENSO event is defined by a season, not by one month. The December-February mean (known in mid March) must give nearly the same vote as the January value."
CHANGE = "c73 with the January Nino 3.4 value replaced by the December-February mean (available from mid March, held to the next March)."
EXPECT = "RATIO within 0.1 of c73 (+0.646)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_djf", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_djf(D).join(lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean")).join(lib.trend5(D))


fit_predict = lib.sum_fp([lambda X: np.sign(X.enso_djf.to_numpy(float)), lambda X: np.sign(X.fill_tmean.to_numpy(float)), lib.trend_sign])
