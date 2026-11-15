import lib
ID, PARENT = "c31", "c27"
HYP = ("Farm commodities share macro demand, the dollar and fund flows. Coffee follows this common factor with "
       "a delay. The share of farm markets in an up-trend measures the factor better than sugar alone.")
CHANGE = "Vote of 5 market features: 126-session log return > 0 for sugar, cocoa, cotton, corn, soybeans (through t-1). Three or more rising: buy early, else buy late."
EXPECT = "RATIO above the sugar rule (c27, +0.336), equal in the two halves."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_rets(D, ["sugar", "cocoa", "cotton", "corn", "soybeans"], 126)


fit_predict = lib.vote_fp()
