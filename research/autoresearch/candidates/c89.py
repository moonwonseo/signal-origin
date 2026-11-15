import numpy as np
import lib
ID, PARENT = "c89", "c86"
HYP = "Check of c86: the three Minas Gerais regions only (74% of the weight)."
CHANGE = "c86 with the Brazil heat anomaly from Sul de Minas, Matas de Minas and Cerrado Mineiro only."
EXPECT = "RATIO within 0.15 of c86 (+0.787)."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state(D, ids=["sul_de_minas", "matas_de_minas", "cerrado_mineiro"])


fit_predict = lib.agree_fp(["enso_jan", "fill_heat"])
