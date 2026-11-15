import lib
ID, PARENT = "c53", "c45"
HYP = "Robustness of c45: Minas Gerais grows most Brazilian arabica. The rule with the three Minas regions only must give nearly the same result."
CHANGE = "c45 with the three Minas Gerais regions only (Sul de Minas, Matas de Minas, Cerrado Mineiro; weights re-scaled)."
EXPECT = "RATIO within 0.15 of c45 (+0.596)."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_tmax_mg"], 0.0, 1, 1


def features(D):
    return lib.bra_window_var(D, "temperature_max_c", (1, 2, 3), 1, "fill_tmax_mg", ids=["sul_de_minas", "matas_de_minas", "cerrado_mineiro"])


fit_predict = lib.rule_fp("fill_tmax_mg")
