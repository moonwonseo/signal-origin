import lib
ID, PARENT = "c25", "B2"
HYP = ("Roasters substitute between arabica and robusta. A wide arabica premium moves demand to robusta and "
       "the arabica price falls back; a narrow premium does the opposite.")
CHANGE = "Unfitted rule on one market feature from new source 3: log(arabica price / robusta price), World Bank monthly, minus its mean of the last 60 months. Buy late if above the mean, else buy early."
EXPECT = "RATIO above zero. Independent of weather."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    t = D.monthly("wb_spread")
    t["spread_dev"] = t.value - t.value.rolling(60, min_periods=60).mean()
    return D.align_avail(t, ["spread_dev"], 45)


fit_predict = lib.rule_fp("spread_dev", sign=-1.0)
