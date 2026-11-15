import lib
ID, PARENT = "c48", "c45"
HYP = "Robustness of c45: grain-fill heat is a slow state, so weather data that are 10 days old must give nearly the same result."
CHANGE = "c45 with the weather lag changed from 4 to 10 days."
EXPECT = "RATIO within 0.1 of c45 (+0.596)."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (1, 2, 3), 1, "fill_tmax", lag=10)


fit_predict = lib.rule_fp("fill_tmax")
