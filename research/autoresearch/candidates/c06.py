import lib
ID, PARENT = "c06", "B2"
HYP = ("Coffee trees lose yield when a period is hot and dry at the same time. Stress against the recent "
       "climate (not against 1981) is the news. The crop loss enters the price slowly.")
CHANGE = "Unfitted rule on one alt-data feature: Brazil (temperature z - rain z), mean of 90 days, minus its trailing 5-year mean, at t-4 days. Buy early if above zero, else buy late."
EXPECT = "Early on about half of the days. RATIO above zero in both halves."
ALT, D_BAND, SMOOTH, SEEDS = ["stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.bra_stress(D, 90)


fit_predict = lib.rule_fp("stress_bra90")
