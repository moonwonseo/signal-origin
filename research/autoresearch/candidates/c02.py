import lib
ID, PARENT = "c02", "B1"
HYP = ("The term structure shows scarcity. In backwardation (near contract above the next one) stocks are tight "
       "and a futures buyer earns the roll yield; in contango the price of a contract falls toward spot. "
       "The roll-day price gap of the front-month chain measures this slope.")
CHANGE = "Unfitted rule on one feature: carry = minus the mean raw log return of the last 4 roll days. Buy early if carry > 0, else buy late."
EXPECT = "Mostly 'buy late' (coffee is usually in contango). RATIO above zero and above always-late."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.roll_carry(D, 4).to_frame()


fit_predict = lib.rule_fp("carry4")
