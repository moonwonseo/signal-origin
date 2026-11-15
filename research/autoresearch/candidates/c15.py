import lib
ID, PARENT = "c15", "c06"
HYP = ("The weather signal is strong and the others are weak but independent. Weights fitted on earlier data "
       "can use the size of each signal, which a sign rule ignores.")
CHANGE = "Model change: logistic regression (C = 1, scaled) on 4 features: Brazil stress, Brazil soil moisture anomaly, other-origin stress, dollar index 63-session return. Buy early if probability > 0.5, else late."
EXPECT = "RATIO near or above c06."
ALT, D_BAND, SMOOTH, SEEDS = ["stress_bra90", "gwetroot_bra90", "stress_oth90"], 0.0, 1, 1
features = lib.signals4
fit_predict = lib.logit_fp(1.0)
