import lib
ID, PARENT = "c56", "B2"
HYP = ("Brazilian growers decide in reais. When the coffee price in reais is high against the last year they "
       "sell stocks and hedge the next crop, which presses the dollar price; when it is low they hold back.")
CHANGE = "Unfitted rule on one market feature: log(coffee price x USD/BRL) minus its 252-session mean. Buy late if above the mean, else buy early."
EXPECT = "RATIO above zero. Risk: value rules had the opposite sign in this market (c04, c25)."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.brl_price_dev(D).to_frame()


fit_predict = lib.rule_fp("brl_price_dev", sign=-1.0)
