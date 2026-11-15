import lib
ID, PARENT = "c07", "B2"
HYP = ("When speculators hold an extreme net position, few buyers (or sellers) remain, and the position must be "
       "closed later. An extreme net long position is followed by lower prices, an extreme net short by higher prices.")
CHANGE = "Unfitted three-state rule on one alt-data feature: managed-money net share of open interest, z-score against its last 104 weekly reports. z > +1: buy late. z < -1: buy early. Else steady."
EXPECT = "Active on about a third of the days. RATIO above zero."
ALT, D_BAND, SMOOTH, SEEDS = ["mm_z"], 0.0, 1, 1


def features(D):
    return lib.cot_z(D, 104)


fit_predict = lib.tri_fp("mm_z", lo=-1.0, hi=1.0, sign=-1.0)
