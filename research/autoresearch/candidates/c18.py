import lib
ID, PARENT = "c18", "c06"
HYP = ("The crop is made from flowering to grain fill (Sep-Apr). Stress adds up over this season, and stress "
       "values of the dry season (May-Aug) are noise. The stress of the season to date is the correct state.")
CHANGE = "c06 with a different time window: mean stress from 1 October to date (growing months Oct-Apr; the last value is held from May to the next October), minus the same quantity of the last 5 years. Same sign rule."
EXPECT = "Fewer position changes than c06. RATIO above c06."
ALT, D_BAND, SMOOTH, SEEDS = ["season_stress_bra"], 0.0, 1, 1


def features(D):
    return lib.bra_season_stress(D)


fit_predict = lib.rule_fp("season_stress_bra")
