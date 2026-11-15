import lib
ID, PARENT = "c27", "B2"
HYP = ("Sugar and arabica share Brazil: the same currency, the same weather belt and the same investors. "
       "A sugar price trend shows the common Brazil factor before it is complete in coffee.")
CHANGE = "Unfitted rule on one market feature from new source 4: 126-session log return of ICE sugar (through t-1). Buy early if above zero, else buy late."
EXPECT = "RATIO above zero. Weak prior."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_ret(D, "sugar", 126).to_frame()


fit_predict = lib.rule_fp("sugar_ret126")
