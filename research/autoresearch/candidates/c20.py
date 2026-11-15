import lib
ID, PARENT = "c20", "c18"
HYP = ("Heat in the growing season damages flowers and speeds up fruit growth with less bean mass. c19 showed "
       "that rain alone is weaker than the combination. Heat alone shows how much of the signal is temperature.")
CHANGE = "c18 with the rain part removed: season-to-date temperature z (Oct-Apr), minus the same quantity of the last 5 years. Buy early if above normal."
EXPECT = "RATIO above zero and below c18 (both parts have value)."
ALT, D_BAND, SMOOTH, SEEDS = ["season_temp_bra"], 0.0, 1, 1


def features(D):
    return lib.bra_season_stress(D, which="temp")


fit_predict = lib.rule_fp("season_temp_bra")
