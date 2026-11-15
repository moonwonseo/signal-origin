import lib
from sklearn.tree import DecisionTreeClassifier
ID, PARENT = "c76", "c73"
HYP = "A depth-2 decision tree on the three inputs of c73 is a fitted version of the vote: it can find the thresholds and the one interaction that the earlier years support, and it stays readable."
CHANGE = "Model change: decision tree (depth 2, at least 200 rows in a leaf) on 3 features: January Nino 3.4, Brazil Jan-Mar mean-temperature anomaly, number of rising markets (0-5). Buy early if probability > 0.5, else late."
EXPECT = "RATIO below the unfitted vote c73 (+0.646); above +0.3 would be a good result for a fitted model."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1
features = lib.three
fit_predict = lib.sk_fp(lambda s: DecisionTreeClassifier(max_depth=2, min_samples_leaf=200, random_state=s))
