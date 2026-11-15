import lib
ID, PARENT = "c33", "B2"
HYP = ("The market adds a frost-risk premium before the Brazilian winter (frost season Jun-Aug) and removes it "
       "when the winter passes. Prices tend to rise from February to May and to fall from June to September.")
CHANGE = "Unfitted three-state calendar rule, no data: buy early in Feb-May, buy late in Jun-Sep, steady in Oct-Jan."
EXPECT = "RATIO above zero in both halves. Independent of all other signals."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.season_flag(D).to_frame()


fit_predict = lib.tri_fp("season", lo=-0.5, hi=0.5)
