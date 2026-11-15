import numpy as np
import lib
ID, PARENT = "c63", "c22"
HYP = "Volatility is predictable and the mean saving of a signal is not higher when volatility is high. Less exposure in high-volatility periods raises the saving for each unit of risk (volatility-managed exposure)."
CHANGE = "c22 with a volatility switch: steady when the 21-session log volatility of coffee returns is above the upper-third limit of the training rows; else the c22 position."
EXPECT = "RATIO above c22 (+0.612) by 0.05 to 0.15; fewer active days."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return lib.wx22(D).join(lib.price_feats(D)[["lrv21"]])


fit_predict = lib.vol_filter_fp(lib.w22)
