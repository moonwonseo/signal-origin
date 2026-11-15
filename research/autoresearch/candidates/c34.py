import lib
ID, PARENT = "c34", "c21"
HYP = ("Falsification test. If Brazil season heat is crop news, the same measure from regions with other crop "
       "calendars must have no skill. If it has the same skill, the signal is a climate clock, not crop news.")
CHANGE = "c21 with the Brazil nodes replaced by the 31 nodes of the other origins (simple mean): season-to-date maximum temperature, Oct-Apr, minus the last 5 years. Same sign rule."
EXPECT = "RATIO near zero if the Brazil signal is specific. A value near +0.5 would speak against the mechanism."
ALT, D_BAND, SMOOTH, SEEDS = ["season_tmax_oth"], 0.0, 1, 1


def features(D):
    n = D.nodes()
    return lib.season_raw_nodes(D, list(n.index[n.country != "Brazil"]), name="season_tmax_oth")


fit_predict = lib.rule_fp("season_tmax_oth")
