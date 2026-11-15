import lib
ID, PARENT = "c13", "B2"
HYP = ("Coffee is priced in dollars. A rising dollar lowers the dollar price of commodities, and currency "
       "trends continue for months. A rising dollar index says: wait.")
CHANGE = "Unfitted rule on one market feature from new source 2: 63-session log return of the US dollar index (through t-1). Buy late if above zero, else buy early."
EXPECT = "RATIO above zero. Independent of the weather signal."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_ret(D, "dxy", 63).to_frame()


fit_predict = lib.rule_fp("dxy_ret63", sign=-1.0)
