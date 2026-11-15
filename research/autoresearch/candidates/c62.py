import numpy as np
import lib
ID, PARENT = "c62", "c55"
HYP = "Roasters substitute between robusta and arabica. When the robusta price rises, blends move to arabica and the arabica price follows with a delay."
CHANGE = "Unfitted rule on one market feature: 3-month log change of the World Bank monthly robusta price (used from the 15th of the next month). Buy early if above zero, else buy late."
EXPECT = "RATIO above zero with similar halves, like the Vietnam heat rule."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.monthly_chg(D, "wb_robusta", 3)


fit_predict = lib.rule_fp("wb_robusta_chg3")
