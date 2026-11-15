import numpy as np
import lib
ID, PARENT = "c61", "c14"
HYP = "Colombia is the second arabica origin. A weakening peso raises the local price and makes Colombian growers and exporters sell, which presses the dollar price; a strengthening peso does the opposite."
CHANGE = "Unfitted rule on one market feature: 63-session log return of USD/COP (through t-1). Buy late if above zero (peso weaker), else buy early."
EXPECT = "RATIO above zero; low prior after the USD/BRL result (c14, +0.07)."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_ret(D, "usdcop", 63).to_frame()


fit_predict = lib.rule_fp("usdcop_ret63", sign=-1.0)
