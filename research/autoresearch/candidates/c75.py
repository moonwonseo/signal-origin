import numpy as np
import lib
ID, PARENT = "c75", "c71"
HYP = "ENSO winter state (supply outside Brazil) and slow market trend (demand and funds) are the two signals with the most stable record and with different causes. A rule from these two does not use Brazil weather, which failed before 2009."
CHANGE = "Agreement of two signals: Nino 3.4 of January (sign) and the five-market trend vote. Both positive: buy early. Both negative: buy late. Else steady."
EXPECT = "RATIO about +0.5 with equal halves."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.trend5(D))


fit_predict = lib.sum_fp([lambda X: np.sign(X.enso_jan.to_numpy(float)), lib.trend_sign])
