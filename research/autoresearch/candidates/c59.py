import numpy as np
import lib
ID, PARENT = "c59", "B2"
HYP = "When equity-market fear (VIX) is high, funds cut risk and sell commodity positions; when fear is low they add risk. Coffee follows these flows."
CHANGE = "Unfitted rule on one market feature: log VIX (through t-1) minus its 252-session mean. Buy late if above the mean, else buy early."
EXPECT = "RATIO above zero; weak prior."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1


def features(D):
    return lib.level_dev(D, "vix").to_frame()


fit_predict = lib.rule_fp("vix_dev252", sign=-1.0)
