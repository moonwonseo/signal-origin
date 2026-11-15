import lib
ID, PARENT = "c05", "B2"
HYP = ("A rain deficit in the Brazilian coffee regions reduces the next crop. The market learns the size of the "
       "loss slowly (crop surveys come months later), so the price continues to rise after a dry period.")
CHANGE = "Unfitted rule on one alt-data feature: Brazil output-weighted rain z-score, mean of the last 90 days (at t-4 days). Buy early if below zero, else buy late."
EXPECT = "RATIO above zero in both halves."
ALT, D_BAND, SMOOTH, SEEDS = ["rain_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_wx(D, 90)[["rain_bra90"]]


fit_predict = lib.rule_fp("rain_bra90", sign=-1.0)
