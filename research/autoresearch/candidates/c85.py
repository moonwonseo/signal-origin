import numpy as np
import lib
ID, PARENT = "c85", "c83"
HYP = "Robustness of c83: with the independent ERA5 temperature in place of NASA POWER the rule must keep most of its score."
CHANGE = "c83 with the Brazil Jan-Mar mean-temperature anomaly from ERA5 (t-7 days)."
EXPECT = "RATIO above +0.5; the ERA5 heat rule alone gave +0.45 against +0.68."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_tmean"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D).join(lib.bra_window_var(D, "tmean", (1, 2, 3), 1, "fill_tmean", lag=7, file="era5_brazil.csv"))


fit_predict = lib.agree_fp(["enso_jan", "fill_tmean"])
