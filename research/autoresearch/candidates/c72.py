import numpy as np
import lib
ID, PARENT = "c72", "c71"
HYP = "Three weak signals with different causes: ENSO winter state (supply outside Brazil), Brazil-specific grain-fill heat (supply in Brazil), slow market trend (demand and funds). If they are independent, a majority of the three is stronger than each one."
CHANGE = "Majority of three signs: Nino 3.4 of January > 0; Brazil Jan-Mar heat anomaly minus the other regions > 0; five-market trend vote positive. Two or three: buy early, else buy late."
EXPECT = "RATIO about +0.5 to +0.65 with equal halves."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "bra_minus_others"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.jfm_specific(D)[["bra_minus_others"]]).join(lib.trend5(D))


fit_predict = lib.sum_fp([lambda X: np.sign(X.enso_jan.to_numpy(float)), lambda X: np.sign(X.bra_minus_others.to_numpy(float)), lib.trend_sign])
