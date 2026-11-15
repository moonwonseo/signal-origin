import numpy as np
import lib
ID, PARENT = "c40", "c22"
HYP = ("If crop news enters the price slowly, the price already moves in the direction of the news. When the "
       "weather rule and the recent price move disagree, the market does not accept the news and the call is weak.")
CHANGE = "c22 with a price confirmation: keep the c22 position only when the 63-session coffee return has the same sign; else steady."
EXPECT = "Fewer active days. RATIO above c22 if slow adjustment is the mechanism."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.wx22(D).join(lib.price_feats(D)[["kret63"]])


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    w = lib.w22(Xte)
    return np.where(w * np.sign(Xte.kret63.to_numpy(float)) > 0, (w + 1) / 2, 0.5)
