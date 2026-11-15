import numpy as np
import lib
ID, PARENT = "c68", "c67"
HYP = "Falsification test. In Central America and Mexico, January-March is harvest time and heat then has little effect on the crop. If Jan-Mar heat there scores like Brazil and Colombia, the signal is a common tropical warmth (a clock), not crop news."
CHANGE = "Same rule as c67 with the 14 nodes of Guatemala, Honduras, Nicaragua and Mexico: mean maximum temperature of Jan-Mar to date, held to the next January, minus the last 5 years."
EXPECT = "RATIO near zero if the Brazil and Colombia signals are crop news; near +0.5 if they are a clock."
ALT, D_BAND, SMOOTH, SEEDS = ["ca_heat"], 0.0, 1, 1


def features(D):
    return lib.origin_heat(D, ["Guatemala", "Honduras", "Nicaragua", "Mexico"], (1, 2, 3), 1, "ca_heat")


fit_predict = lib.rule_fp("ca_heat")
