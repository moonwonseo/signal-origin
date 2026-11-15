import numpy as np
import lib
ID, PARENT = "c30", "c28"
HYP = ("Three signals showed skill with different mechanisms or time scales: season heat (state of the crop), "
       "90-day stress (recent news), sugar trend (common Brazil and fund factor). A majority of three uses all "
       "of them and is never without a call.")
CHANGE = "Majority vote of three sign rules: season maximum-temperature anomaly > 0, 90-day stress > 0, 126-session sugar return > 0. Two or three 'yes' -> buy early, else buy late."
EXPECT = "RATIO near c22 and c28, with more active days."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax", "stress_bra90"], 0.0, 1, 1


def features(D):
    return (lib.bra_season_raw(D, "temperature_max_c", name="season_tmax").join(lib.bra_stress(D, 90))
            .join(lib.mkt_ret(D, "sugar", 126)))


def fit_predict(Xtr, ytr, gtr, Xte, seed):
    return ((Xte.to_numpy(float) > 0).sum(axis=1) >= 2).astype(float)
