import lib
ID, PARENT = "c55", "B2"
HYP = ("Vietnam grows about 40% of world robusta. Heat in its dry season (Jan-Apr: flowering and fruit set) "
       "lowers the robusta crop; roasters then need more arabica, and the arabica price follows robusta up.")
CHANGE = "Unfitted rule on one alt-data feature (new data: NASA POWER, 3 Vietnamese regions): mean maximum temperature of Jan-Apr to date, held to the next January, minus the last 5 years, at t-4 days. Buy early if above normal, else buy late."
EXPECT = "RATIO above zero. Independent of Brazil weather."
ALT, D_BAND, SMOOTH, SEEDS = ["vn_dry_tmax"], 0.0, 1, 1


def features(D):
    return lib.season_raw_nodes(D, ["vn_dak_lak", "vn_lam_dong", "vn_gia_lai"], months=(1, 2, 3, 4), start_month=1,
                                name="vn_dry_tmax", file="power_vietnam.csv")


fit_predict = lib.rule_fp("vn_dry_tmax")
