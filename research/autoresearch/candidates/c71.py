import numpy as np
import lib
ID, PARENT = "c71", "c70"
HYP = "El Nino in the northern winter brings heat and drought to Colombia, Central America, Vietnam and Indonesia. Supply outside Brazil falls in the following harvests and the price rises in that year; La Nina does the opposite."
CHANGE = "Unfitted rule on one alt-data feature: Nino 3.4 anomaly of January (published mid February), held until the next January value. Above zero: buy early. Below zero: buy late."
EXPECT = "RATIO near the common-warmth rule (c70, +0.42) if that warmth is ENSO."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan"], 0.0, 1, 1


def features(D):
    return lib.enso_jan(D)


fit_predict = lib.rule_fp("enso_jan")
