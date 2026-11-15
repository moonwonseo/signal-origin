import numpy as np
import lib
ID, PARENT = "c91", "c86"
HYP = "Check of c86: the Brazil heat anomaly contains the common ENSO warmth. With the Brazil-specific part only (Brazil minus the other regions), the rule shows what Brazil adds to the ENSO state."
CHANGE = "c86 with the Brazil heat anomaly replaced by the Brazil-specific anomaly (Brazil Jan-Mar maximum-temperature anomaly minus that of the 31 other nodes, lag 10 days)."
EXPECT = "RATIO between the ENSO rule alone (+0.39) and c86 (+0.79)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "bra_minus_others"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.jfm_specific(D, lag=10)[["bra_minus_others"]])


fit_predict = lib.agree_fp(["enso_jan", "bra_minus_others"])
