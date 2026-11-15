import numpy as np
import lib
ID, PARENT = "c69", "c45"
HYP = "If Brazilian grain-fill heat is crop news, the part of it that is NOT shared with the other tropical regions must carry skill. If only the common warmth matters, the Brazil-specific part has none."
CHANGE = "Unfitted rule on one alt-data feature: Brazil Jan-Mar maximum-temperature anomaly minus the same anomaly of the 31 other nodes (both against the last 5 years, held to the next January). Buy early if Brazil is hotter than the common anomaly, else buy late."
EXPECT = "RATIO above +0.3 if Brazil crop news is real; near zero if the common warmth is the signal."
ALT, D_BAND, SMOOTH, SEEDS = ["bra_minus_others"], 0.0, 1, 1


def features(D):
    return lib.jfm_specific(D)[["bra_minus_others"]]


fit_predict = lib.rule_fp("bra_minus_others")
