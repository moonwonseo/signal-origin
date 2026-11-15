import lib
ID, PARENT = "c11", "B2"
HYP = ("Root-zone soil moisture is what the tree feels: it sums rain, heat and evaporation over weeks. A dry "
       "root zone against the recent seasonal normal means a smaller crop, and the price learns it slowly.")
CHANGE = "Unfitted rule on one alt-data feature from new source 1: Brazil output-weighted root-zone soil wetness, mean of 90 days minus the seasonal normal of the last 5 years, at t-4 days. Buy early if below zero, else buy late."
EXPECT = "RATIO above zero in both halves, similar to c06."
ALT, D_BAND, SMOOTH, SEEDS = ["gwetroot_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_extra(D, "gwetroot", 90)


fit_predict = lib.rule_fp("gwetroot_bra90", sign=-1.0)
