import numpy as np
import lib
ID, PARENT = "c81", "c73"
HYP = "Robustness of c73: the market factor is a slow trend (c66). With 252-session trends for all five markets the vote must keep its score and change position less often."
CHANGE = "c73 with the five-market trend vote computed from 252-session returns (as in c66)."
EXPECT = "RATIO within 0.1 of c73 (+0.646)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean")).join(lib.trend_n(D, 252))


fit_predict = lib.sum_fp([lambda X: np.sign(X.enso_jan.to_numpy(float)), lambda X: np.sign(X.fill_tmean.to_numpy(float)), lambda X: np.where((X[["sugar_ret252", "ewz_ret252", "copper_ret252", "dxy_down252", "kret252"]].to_numpy(float) > 0).sum(axis=1) >= 3, 1.0, -1.0)])
