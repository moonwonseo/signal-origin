import lib
ID, PARENT = "c14", "B2"
HYP = ("Brazilian growers sell coffee in dollars and pay costs in reais. When the real weakens, they sell more "
       "and accept lower dollar prices. Currency trends continue, so a weakening real says: wait.")
CHANGE = "Unfitted rule on one market feature: 63-session log return of USD/BRL (through t-1). Buy late if above zero (real weaker), else buy early."
EXPECT = "RATIO above zero and above the dollar index rule (c13)."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.brl_feats(D)[["brl_ret63"]]


fit_predict = lib.rule_fp("brl_ret63", sign=-1.0)
