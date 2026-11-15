import numpy as np
import lib
ID, PARENT = "c79", "c73"
HYP = "Robustness of c73: its two weather inputs are yearly states, so weather data that are 10 days old must give the same result."
CHANGE = "c73 with the weather lag of the Brazil heat changed from 4 to 10 days."
EXPECT = "RATIO within 0.1 of c73 (+0.646)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean", lag=10)).join(lib.trend5(D))


fit_predict = lib.three_sum()
