import lib
ID, PARENT = "c58", "c57"
HYP = ("The relations between these signals and the price change over the years. A model that gives old years "
       "less weight can follow the relation that holds now.")
CHANGE = "c57 with time-decay weights in the fit: a training row 3 years older than the newest row has half its weight. Same 4 features, same logistic regression."
EXPECT = "RATIO above c57 (+0.02) if the relations move slowly; near zero if there is no usable relation."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmean", "stress_bra90", "vn_dry_tmax"], 0.0, 1, 1
features = lib.best4
fit_predict = lib.logit_decay_fp(1.0, 3.0)
