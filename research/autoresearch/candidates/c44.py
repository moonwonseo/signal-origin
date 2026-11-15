import lib
ID, PARENT = "c44", "c21"
HYP = ("Heat at flowering (Sep-Nov) makes flowers abort and fixes the number of fruits. If this is the main "
       "channel, flowering heat alone carries the signal and is known months earlier than the full season.")
CHANGE = "c21 with the window Sep-Nov only: mean maximum temperature of the flowering months to date, held until the next September, minus the last 5 years. Same sign rule."
EXPECT = "RATIO above zero; near c21 (+0.596) if flowering is the main channel."
ALT, D_BAND, SMOOTH, SEEDS = ["flower_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_window_tmax(D, (9, 10, 11), 9, "flower_tmax")


fit_predict = lib.rule_fp("flower_tmax")
