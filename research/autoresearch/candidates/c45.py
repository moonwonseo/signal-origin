import lib
ID, PARENT = "c45", "c21"
HYP = ("Heat at grain fill (Jan-Mar) reduces bean size and weight. c44 showed that flowering heat alone has no "
       "stable skill. If the fill months carry the signal, this window alone must score like the full season.")
CHANGE = "c21 with the window Jan-Mar only: mean maximum temperature of the grain-fill months to date, held until the next January, minus the last 5 years. Same sign rule."
EXPECT = "RATIO near c21 (+0.596) if grain fill is the main channel."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (1, 2, 3), 1, "fill_tmax")


fit_predict = lib.rule_fp("fill_tmax")
