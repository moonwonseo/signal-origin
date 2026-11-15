import numpy as np
import lib
ID, PARENT = "c92", "c86"
HYP = "Falsification of c86: if the second input only has to be a warm tropical first quarter, the Jan-Mar heat of Central America and Mexico (no crop meaning in those months) will work as well as the Brazil heat."
CHANGE = "c86 with the Brazil heat anomaly replaced by the Jan-Mar maximum-temperature anomaly of the 14 nodes of Guatemala, Honduras, Nicaragua and Mexico (lag 10 days)."
EXPECT = "RATIO clearly below c86 (+0.787) if Brazil is special; near it if not."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "ca_heat"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.origin_heat(D, ["Guatemala", "Honduras", "Nicaragua", "Mexico"], (1, 2, 3), 1, "ca_heat", lag=10))


fit_predict = lib.agree_fp(["enso_jan", "ca_heat"])
