import lib
ID, PARENT = "c49", "c45"
HYP = "Robustness of c45: the result must not depend on the length of the normal."
CHANGE = "c45 with a 10-year normal in place of 5 years."
EXPECT = "RATIO within 0.15 of c45 (+0.596)."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (1, 2, 3), 1, "fill_tmax", years=10)


fit_predict = lib.rule_fp("fill_tmax")
