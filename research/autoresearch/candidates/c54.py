import lib
ID, PARENT = "c54", "B2"
HYP = ("Holding coffee stocks costs interest. Rising US yields make traders and roasters cut stocks and make "
       "financial buyers leave commodities, so prices weaken; falling yields support prices.")
CHANGE = "Unfitted rule on one market feature: 126-session change of the log US 10-year yield (through t-1). Buy late if yields rose, else buy early."
EXPECT = "RATIO above zero. Weak prior; independent of weather."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_ret(D, "us10y", 126).to_frame()


fit_predict = lib.rule_fp("us10y_ret126", sign=-1.0)
