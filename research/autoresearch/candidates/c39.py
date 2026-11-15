import lib
ID, PARENT = "c39", "B2"
HYP = ("World growth and risk appetite move all commodities: strong demand and fund inflows lift prices. "
       "Equities, copper and crude oil show this state earlier and with less noise than coffee.")
CHANGE = "Vote of 3 market features: 126-session log return > 0 for the S&P 500, copper and crude oil (through t-1). Two or more rising: buy early, else buy late."
EXPECT = "RATIO near the other market-trend rules (+0.2 to +0.3)."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_rets(D, ["spx", "copper", "crude"], 126)


fit_predict = lib.vote_fp()
