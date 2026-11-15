import lib
ID, PARENT = "c08", "B2"
HYP = ("La Nina brings dry conditions to southern Brazil and El Nino brings rain. The ENSO state is known "
       "months before the crop effect, so it can lead the weather stress.")
CHANGE = "Unfitted three-state rule on one alt-data feature: Nino 3.4 anomaly (published value). Below -0.5 (La Nina): buy early. Above +0.5 (El Nino): buy late. Else steady."
EXPECT = "RATIO above zero. Active on about half of the days."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_lvl"], 0.0, 1, 1


def features(D):
    return lib.enso2(D)[["enso_lvl"]]


fit_predict = lib.tri_fp("enso_lvl", lo=-0.5, hi=0.5, sign=-1.0)
