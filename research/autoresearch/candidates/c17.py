import lib
from lightgbm import LGBMClassifier
ID, PARENT = "c17", "c06"
HYP = ("Same idea as c16 (the weather effect depends on season and market state), with boosted trees and with "
       "all the training years from 2001.")
CHANGE = "Model change: LightGBM (300 trees, depth 3, learning rate 0.03, row share 0.8, column share 0.5, 50 rows in a leaf, mean of 5 seeds) on 15 features (the 16 of c16 without USD/BRL)."
EXPECT = "RATIO above c16. A value above c06 would show useful conditions."
ALT, D_BAND, SMOOTH, SEEDS = lib.WIDE_ALT, 0.0, 1, 5


def features(D):
    return lib.wide16(D).drop(columns=["brl_ret63"])


fit_predict = lib.sk_fp(lambda s: LGBMClassifier(n_estimators=300, max_depth=3, num_leaves=8, learning_rate=0.03,
                                                 subsample=0.8, subsample_freq=1, colsample_bytree=0.5,
                                                 min_child_samples=50, reg_lambda=1.0, n_jobs=1, verbose=-1,
                                                 random_state=s))
