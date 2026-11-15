import lib
ID, PARENT = "c57", "c52"
HYP = ("The four rules with skill use only signs. A logistic model fitted on earlier years can weight the "
       "signals by their strength and use their size.")
CHANGE = "Model change: logistic regression (C = 1, scaled) on 4 features: grain-fill mean-temperature anomaly, 90-day stress, Vietnam dry-season heat, number of rising markets (0-5). Buy early if probability > 0.5, else late."
EXPECT = "RATIO above the first logistic model (c15, +0.31). Above +0.6 would justify fitted weights."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmean", "stress_bra90", "vn_dry_tmax"], 0.0, 1, 1
features = lib.best4
fit_predict = lib.logit_fp(1.0)
