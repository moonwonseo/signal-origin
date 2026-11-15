import lib
ID, PARENT = "c09", "c06"
HYP = ("If heat-and-dry stress in Brazil enters the price slowly, the same stress in the other arabica origins "
       "(about half of world output) must do the same.")
CHANGE = "Same unfitted rule as c06, but the feature is the mean stress of all origins except Brazil (simple mean of country means, 90 days, drift removed)."
EXPECT = "RATIO above zero, lower than c06. A positive result supports a world stress signal."
ALT, D_BAND, SMOOTH, SEEDS = ["stress_oth90"], 0.0, 1, 1


def features(D):
    return lib.other_stress(D, 90)


fit_predict = lib.rule_fp("stress_oth90")
