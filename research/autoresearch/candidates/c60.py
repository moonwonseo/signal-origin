import numpy as np
import lib
ID, PARENT = "c60", "c42"
HYP = "Only two signals were stable in the two halves: the five-market trend composite and the Vietnam dry-season heat. They have different mechanisms (demand and funds; robusta supply). A rule from stable signals is more likely to hold outside the development years."
CHANGE = "Agreement of two signals: five-market trend vote (c42) and Vietnam dry-season heat (c55). Both positive: buy early. Both negative: buy late. Else steady."
EXPECT = "RATIO about +0.4 with equal halves."
ALT, D_BAND, SMOOTH, SEEDS = ["vn_dry_tmax"], 0.0, 1, 1


def features(D):
    return lib.trend5(D).join(lib.vn_heat(D))


fit_predict = lib.sum_fp([lib.trend_sign, lambda X: np.sign(X.vn_dry_tmax.to_numpy(float))])
