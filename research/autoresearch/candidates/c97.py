import numpy as np
import lib
ID, PARENT = "c97", "c86"
HYP = "Check of c86: the supply effect of ENSO comes from real events. With neutral winters set to steady, the rule acts only when a real El Nino or La Nina agrees with the Brazil heat."
CHANGE = "c86 with the ENSO condition as an event: January Nino 3.4 above +0.5 and Brazil heat above normal: buy early; below -0.5 and Brazil heat below normal: buy late; else steady."
EXPECT = "Fewer active years; RATIO near c86 if the events carry the effect."
ALT, D_BAND, SMOOTH, SEEDS = ["enso_jan", "fill_heat"], 0.0, 1, 1


def features(D):
    return lib.two_state(D)


fit_predict = lib.sum_fp([lambda X: np.where((X.enso_jan.to_numpy(float) > 0.5) & (X.fill_heat.to_numpy(float) > 0), 1.0, np.where((X.enso_jan.to_numpy(float) < -0.5) & (X.fill_heat.to_numpy(float) < 0), -1.0, 0.0))])
