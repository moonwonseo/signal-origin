import numpy as np
import lib
ID, PARENT = "c80", "c73"
HYP = "Robustness of c73: with the independent ERA5 temperature in place of NASA POWER, the vote must keep most of its score."
CHANGE = "c73 with the Brazil Jan-Mar mean-temperature anomaly from ERA5 (t-7 days) in place of NASA POWER."
EXPECT = "RATIO above +0.5."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.bra_window_var(D, "tmean", (1, 2, 3), 1, "fill_tmean", lag=7, file="era5_brazil.csv")).join(lib.trend5(D))


fit_predict = lib.three_sum()
