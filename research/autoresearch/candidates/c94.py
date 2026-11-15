import numpy as np
import lib
ID, PARENT = "c94", "c86"
HYP = "A call with three independent reasons (ENSO state, Brazil heat, market trend) is more reliable than a call with two. Acting only on full agreement trades active days for quality."
CHANGE = "c86 plus the five-market trend vote as a third condition: buy early only if all three are positive, buy late only if all three are negative, else steady."
EXPECT = "Fewer active days; RATIO near c86 only if the trend vote removes bad calls."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state(D).join(lib.trend5(D))


fit_predict = lib.sum_fp([lambda X: np.where((np.sign(X.enso_jan.to_numpy(float)) == np.sign(X.fill_heat.to_numpy(float))) & (np.sign(X.enso_jan.to_numpy(float)) == lib.trend_sign(X)), lib.trend_sign(X), 0.0)])
