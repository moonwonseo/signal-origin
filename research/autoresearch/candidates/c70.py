import numpy as np
import lib
ID, PARENT = "c70", "c68"
HYP = "The common January-March warmth of the tropical coffee regions outside Brazil. If the heat finding is mostly a common climate state, this measure alone must score like the Brazil rule."
CHANGE = "Unfitted rule on one alt-data feature: Jan-Mar maximum-temperature anomaly of the 31 nodes outside Brazil (against the last 5 years, held to the next January). Buy early if above normal, else buy late."
EXPECT = "RATIO between the Central America test (+0.33) and Colombia (+0.51)."
ALT, D_BAND, SMOOTH, SEEDS = ["others_jfm"], 0.0, 1, 1


def features(D):
    return lib.jfm_specific(D)[["others_jfm"]]


fit_predict = lib.rule_fp("others_jfm")
