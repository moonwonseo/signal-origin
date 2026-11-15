import lib
ID, PARENT = "c19", "c18"
HYP = ("Water deficit is the main cause of yield loss in Brazilian arabica. If the signal is drought, the rain "
       "part alone carries it and the temperature part adds noise.")
CHANGE = "c18 with the temperature part removed: season-to-date rain deficit (minus rain z), Oct-Apr, minus the same quantity of the last 5 years. Buy early if the deficit is above normal."
EXPECT = "RATIO near c18. Clearly lower means that heat matters too."
ALT, D_BAND, SMOOTH, SEEDS = ["season_rain_bra"], 0.0, 1, 1


def features(D):
    return lib.bra_season_stress(D, which="rain")


fit_predict = lib.rule_fp("season_rain_bra")
