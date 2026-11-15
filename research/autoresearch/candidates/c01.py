import lib
ID, PARENT = "c01", "B1"
HYP = ("Coffee is a tree crop: supply answers to price with a delay of years, so price trends continue. "
       "The sign of the 12-month return (time-series momentum) tells the direction of the next quarter.")
CHANGE = "Unfitted rule on one feature: buy early if the 252-session return is above zero, else buy late."
EXPECT = "RATIO above B3 (63-session momentum) and above zero."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.price_feats(D)[["kret252"]]


fit_predict = lib.rule_fp("kret252")
