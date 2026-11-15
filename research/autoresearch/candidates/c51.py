import lib
ID, PARENT = "c51", "c45"
HYP = "Robustness of c45: if grain-fill heat is real, the window one month later (Feb-Apr) must also show skill."
CHANGE = "c45 with the window Feb-Apr (held to the next February)."
EXPECT = "RATIO above +0.3."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (2, 3, 4), 2, "fill_tmax")


fit_predict = lib.rule_fp("fill_tmax")
