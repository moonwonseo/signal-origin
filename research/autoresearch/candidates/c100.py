import numpy as np
import lib
ID, PARENT = "c100", "c99"
HYP = "The careful design with a third, independent view: the slow market trend. A majority of three is always active."
CHANGE = "Majority of three signs: December-February Nino 3.4 mean, two-product Brazil Jan-Mar heat anomaly, five-market trend vote. Two or three positive: buy early, else buy late."
EXPECT = "RATIO about +0.55 to +0.65 (the c73 design with the careful inputs)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_djf", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.final_inputs(D).join(lib.trend5(D))


fit_predict = lib.sum_fp([lambda X: np.sign(X.enso_djf.to_numpy(float)), lambda X: np.sign(X.fill_heat.to_numpy(float)), lib.trend_sign])
