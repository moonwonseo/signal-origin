import lib
ID, PARENT = "c04", "B2"
HYP = ("Coffee supply and demand answer slowly to price: a high price brings more planting and care and a low "
       "price brings neglect, so the price moves back toward its long-run level (commodity 'value').")
CHANGE = "Unfitted rule on one feature: log raw front-month price minus its 5-year mean (1,260 sessions). Buy early if below the mean, else buy late."
EXPECT = "RATIO above zero in both halves."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.value(D, 1260).to_frame()


fit_predict = lib.rule_fp("value1260", sign=-1.0)
