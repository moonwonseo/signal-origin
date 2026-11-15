import lib
ID, PARENT = "c37", "B2"
HYP = ("The volume of green coffee that Brazil exports shows how much coffee reaches the world market. A flow "
       "above the seasonal normal means ample supply and lower prices later; a low flow means a tight market.")
CHANGE = "Same as the void c35 and c36, now with the complete export file (358 of 358 months, guarded in code). Unfitted rule on one alt-data feature from new source 19: log of Brazil green-coffee export volume, mean of 3 months, minus the same months of the last 5 years (used from the 15th of the next month). Buy late if above normal, else buy early."
EXPECT = "RATIO above zero. Weak-to-medium prior: exports also react to the price."
ALT, D_BAND, SMOOTH, SEEDS = ["comex_kg_anom"], 0.0, 1, 1


def features(D):
    return lib.monthly_anom(D, "comex_kg")


fit_predict = lib.rule_fp("comex_kg_anom", sign=-1.0)
