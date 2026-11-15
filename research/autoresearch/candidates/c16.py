import lib
from sklearn.ensemble import RandomForestClassifier
ID, PARENT = "c16", "c06"
HYP = ("The effect of weather stress can depend on the season and on the state of the market. A random forest "
       "averages many shallow trees and can find such conditions with low variance.")
CHANGE = "Model change: random forest (500 trees, depth 4, 50 rows in a leaf, mean of 5 seeds) on 16 features: 6 weather, 7 price, 2 currency, 1 ENSO."
EXPECT = "RATIO above the logistic model (c15). A value above c06 would show useful conditions."
ALT, D_BAND, SMOOTH, SEEDS = lib.WIDE_ALT, 0.0, 1, 5
features = lib.wide16
fit_predict = lib.sk_fp(lambda s: RandomForestClassifier(n_estimators=500, max_depth=4, min_samples_leaf=50,
                                                         max_features="sqrt", n_jobs=1, random_state=s))
