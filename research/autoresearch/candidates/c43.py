import numpy as np
import lib
ID, PARENT = "c43", "c28"
HYP = ("Weather (supply news) and the market-trend factor are independent. c28 used sugar alone for the trend; "
       "the five-market composite is the more reliable measure of the same factor.")
CHANGE = "c28 with the sugar trend replaced by the five-market vote of c42: position = sign(weather position of c22 + trend vote as +1/-1)."
EXPECT = "RATIO near c28 (+0.576) with balanced halves."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.wx22(D).join(lib.trend5(D))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    s = np.where((Xte[["sugar_ret126", "ewz_ret126", "copper_ret126", "dxy_down63", "kret252"]].to_numpy(float) > 0).sum(axis=1) >= 3, 1.0, -1.0)
    t = lib.w22(Xte) + s
    return np.where(t > 0, 1.0, np.where(t < 0, 0.0, 0.5))
