import numpy as np
import lib
ID, PARENT = "c93", "c86"
HYP = "The rule depends on the weather product (NASA POWER +0.79, ERA5 +0.50). The two products measure the same heat with different errors; their mean has less error than each one."
CHANGE = "c86 with the Brazil heat anomaly replaced by the mean of the NASA POWER and ERA5 anomalies (each scaled by its own earlier standard deviation; lag 10 days)."
EXPECT = "RATIO between the two single-product versions (+0.50 and +0.79); this is the honest size of the rule."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state_both(D)


fit_predict = lib.agree_fp(["enso_jan", "fill_heat"])
