import lib
ID, PARENT = "c38", "B2"
HYP = ("Hedging-pressure theory: when producers and merchants hold a large net short hedge, the market pays a "
       "premium to those who take the other side, so futures prices tend to rise; a small hedge means no premium.")
CHANGE = "Unfitted three-state rule on one alt-data feature (CFTC, on hand): producer/merchant net short share of open interest, z-score against the last 104 reports. z > +1: buy early. z < -1: buy late. Else steady."
EXPECT = "RATIO above zero. It is close to the mirror of iteration 7, so a value near +0.1 is probable."
ALT, D_BAND, SMOOTH, SEEDS = ["hp_z"], 0.0, 1, 1
features = lib.hedge_pressure
fit_predict = lib.tri_fp("hp_z", lo=-1.0, hi=1.0)
