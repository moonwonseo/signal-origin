import numpy as np
import lib
ID, PARENT = "c67", "c55"
HYP = "Colombia is the second arabica origin. Its main crop flowers in January-March; heat in that window reduces the harvest of October-December, and the market learns the loss slowly."
CHANGE = "Unfitted rule on one alt-data feature: mean maximum temperature of Jan-Mar to date over the 6 Colombian nodes, held to the next January, minus the last 5 years. Buy early if above normal, else buy late."
EXPECT = "RATIO above zero with similar halves, like the Vietnam rule (+0.24)."
ALT, D_BAND, SMOOTH, SEEDS = ["co_heat"], 0.0, 1, 1


def features(D):
    return lib.origin_heat(D, ["Colombia"], (1, 2, 3), 1, "co_heat")


fit_predict = lib.rule_fp("co_heat")
