import lib
ID, PARENT = "c21", "c20"
HYP = ("Heat damage to coffee flowers and fruit comes from hot afternoons. The daily maximum temperature "
       "measures this more directly than the mean temperature z-score.")
CHANGE = "c20 with a different heat measure: season-to-date mean of the daily maximum temperature (Brazil, output-weighted, Oct-Apr, held May-Sep), minus the same quantity of the last 5 years. Buy early if above normal."
EXPECT = "RATIO equal to or above c20."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax"], 0.0, 1, 1


def features(D):
    return lib.bra_season_raw(D, "temperature_max_c", name="season_tmax")


fit_predict = lib.rule_fp("season_tmax")
