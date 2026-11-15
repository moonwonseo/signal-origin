import lib
ID, PARENT = "c50", "c45"
HYP = "Robustness of c45: if grain-fill heat is real, the window one month earlier (Dec-Feb) must also show skill, a little less."
CHANGE = "c45 with the window Dec-Feb (held to the next December)."
EXPECT = "RATIO above +0.3."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (12, 1, 2), 12, "fill_tmax")


fit_predict = lib.rule_fp("fill_tmax")
