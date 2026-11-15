import lib
ID, PARENT = "c03", "B2"
HYP = ("The term structure shows scarcity. In backwardation stocks are tight and the price of a contract rises "
       "toward spot; in contango it falls toward spot. The gap between contracts is the raw return of the "
       "session after each marked roll day.")
CHANGE = "Unfitted rule on one feature: carry = minus the mean of the last 4 contract gaps. Buy early if carry > 0, else buy late."
EXPECT = "Mostly 'buy late' before 2021. RATIO above always-late (+0.06)."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.roll_carry(D, 4, offset=1).to_frame()


fit_predict = lib.rule_fp("carry4n")
