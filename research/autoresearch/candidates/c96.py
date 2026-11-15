import numpy as np
import lib
ID, PARENT = "c96", "c86"
HYP = "Colombia flowering heat scored +0.51 alone. If that came from the ENSO state (El Nino heats Colombia in the first quarter), Colombia heat will add nothing to the ENSO state."
CHANGE = "c86 with the Brazil heat anomaly replaced by the Colombia Jan-Mar maximum-temperature anomaly (6 nodes, lag 10 days)."
EXPECT = "RATIO near the ENSO rule alone (+0.39) if Colombia heat is ENSO."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "co_heat"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.origin_heat(D, ["Colombia"], (1, 2, 3), 1, "co_heat", lag=10))


fit_predict = lib.agree_fp(["enso_jan", "co_heat"])
