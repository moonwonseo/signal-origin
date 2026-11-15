import numpy as np
import lib
ID, PARENT = "c28", "c22"
HYP = ("The weather rule (supply news) and the sugar trend (common Brazil and fund factor) are independent "
       "views. A vote of two independent signals with skill has less noise than each one.")
CHANGE = "c22 plus the sugar trend as an equal vote: position = sign(weather agreement position + sign of the 126-session sugar return). Disagreement gives steady; when weather is steady, sugar decides."
EXPECT = "RATIO above c22 if the savings are independent."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return (lib.bra_season_raw(D, "temperature_max_c", name="season_tmax").join(lib.bra_stress(D, 90))
            .join(lib.mkt_ret(D, "sugar", 126)))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    a, b, s = (Xte[c].to_numpy(float) for c in ("season_tmax", "stress_bra90", "sugar_ret126"))
    w = np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), -1.0, 0.0))
    t = w + np.where(s > 0, 1.0, -1.0)
    return np.where(t > 0, 1.0, np.where(t < 0, 0.0, 0.5))
