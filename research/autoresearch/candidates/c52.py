import lib
ID, PARENT = "c52", "c45"
HYP = "Robustness of c45: if heat is the cause, the daily mean temperature must show nearly the same skill as the daily maximum."
CHANGE = "c45 with the daily mean temperature in place of the daily maximum temperature."
EXPECT = "RATIO within 0.15 of c45 (+0.596)."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean")


fit_predict = lib.rule_fp("fill_tmean")
