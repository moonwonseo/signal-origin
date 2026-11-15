import numpy as np
import lib
ID, PARENT = "c73", "c72"
HYP = "c72 with the stronger Brazil measure. The full grain-fill heat (c52) scored +0.68 alone; it shares its common part with the ENSO vote, so the vote may gain less than the single scores suggest."
CHANGE = "c72 with the Brazil-specific heat replaced by the full Brazil Jan-Mar mean-temperature anomaly (c52). Majority of that, Nino 3.4 of January, and the five-market trend vote."
EXPECT = "RATIO at or above c72 (+0.572)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean")).join(lib.trend5(D))


fit_predict = lib.sum_fp([lambda X: np.sign(X.enso_jan.to_numpy(float)), lambda X: np.sign(X.fill_tmean.to_numpy(float)), lib.trend_sign])
