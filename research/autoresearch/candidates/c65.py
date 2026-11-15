import numpy as np
import lib
ID, PARENT = "c65", "c42"
HYP = "Robustness of the market-trend factor (c42): a real common trend must also show with a shorter horizon."
CHANGE = "c42 with a 63-session horizon for all five markets (sugar, Brazil equities, copper, dollar reversed, coffee). Three or more positive: buy early, else buy late."
EXPECT = "RATIO above +0.2 with the same sign in the two halves."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.trend_n(D, 63)


fit_predict = lib.vote_fp()
