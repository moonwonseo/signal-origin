import numpy as np
import lib
ID, PARENT = "c47", "c46"
HYP = ("Grain-fill heat (state of the crop), 90-day stress (recent news) and the market-trend composite are "
       "three views with different mechanisms. A majority of the three is never without a call.")
CHANGE = "Majority of three signs: grain-fill maximum-temperature anomaly > 0, 90-day stress > 0, five-market trend vote positive. Two or three: buy early, else buy late."
EXPECT = "RATIO near +0.6 with equal halves."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax", "stress_bra90"], 0.0, 1, 1
TR = ["sugar_ret126", "ewz_ret126", "copper_ret126", "dxy_down63", "kret252"]


def features(D):
    return lib.bra_window_tmax(D, (1, 2, 3), 1, "fill_tmax").join(lib.bra_stress(D, 90)).join(lib.trend5(D))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    s = (Xte[TR].to_numpy(float) > 0).sum(axis=1) >= 3
    v = (Xte.fill_tmax.to_numpy(float) > 0).astype(int) + (Xte.stress_bra90.to_numpy(float) > 0).astype(int) + s.astype(int)
    return (v >= 2).astype(float)
