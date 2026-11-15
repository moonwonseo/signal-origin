import lib
ID, PARENT = "c32", "c27"
HYP = ("Sugar helps and other farm markets do not, so the shared cause is Brazil. Brazilian assets in dollars "
       "(equities and the real) rise when capital flows to Brazil, and Brazilian export prices follow.")
CHANGE = "Unfitted rule on one market feature: 126-session log return of the Brazil equity fund EWZ in dollars (through t-1). Buy early if above zero, else buy late."
EXPECT = "RATIO near the sugar rule (+0.34) if the Brazil factor is the cause."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.mkt_ret(D, "ewz", 126).to_frame()


fit_predict = lib.rule_fp("ewz_ret126")
