import numpy as np
import lib
ID, PARENT = "c77", "c52"
HYP = "Data check: if Brazil grain-fill heat is a real weather state, an independent reanalysis (ERA5, ECMWF) must give nearly the same signal as NASA POWER (MERRA-2)."
CHANGE = "c52 with ERA5 daily mean temperature (new source 18, at t-7 days) in place of the NASA POWER temperature. Same nodes, weights, window and normal."
EXPECT = "RATIO within 0.15 of c52 (+0.680)."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmean_era5"], 0.0, 1, 1


def features(D):
    return lib.bra_window_var(D, "tmean", (1, 2, 3), 1, "fill_tmean_era5", lag=7, file="era5_brazil.csv")


fit_predict = lib.rule_fp("fill_tmean_era5")
