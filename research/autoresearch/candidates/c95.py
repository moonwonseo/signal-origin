import numpy as np
import lib
ID, PARENT = "c95", "c86"
HYP = "Check of c86 with another origin: Vietnam dry-season heat has crop meaning for robusta. If the second input must be Brazilian supply news, Vietnam heat will add little to the ENSO state."
CHANGE = "c86 with the Brazil heat anomaly replaced by the Vietnam Jan-Apr maximum-temperature anomaly (3 robusta regions, lag 10 days)."
EXPECT = "RATIO between the ENSO rule alone (+0.39) and c86 (+0.79)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "vn_dry_tmax"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.vn_heat(D, lag=10))


fit_predict = lib.agree_fp(["enso_jan", "vn_dry_tmax"])
