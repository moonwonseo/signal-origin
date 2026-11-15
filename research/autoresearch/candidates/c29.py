import lib
ID, PARENT = "c29", "B2"
HYP = ("When world coffee stocks are low against use, there is no buffer and prices tend to rise; with high "
       "stocks they tend to fall. Stocks change slowly, so a value that is 1-2 years old still has meaning.")
CHANGE = "Unfitted rule on one alt-data feature from new source 5: world ending stocks / consumption (USDA PSD), minus the mean of the 5 marketing years before; used 12 months after the marketing year ended. Buy early if below that mean, else buy late."
EXPECT = "RATIO above zero. Weak prior (old data)."
ALT, D_BAND, SMOOTH, SEEDS = ["stu_dev"], 0.0, 1, 1
features = lib.usda_stocks
fit_predict = lib.rule_fp("stu_dev", sign=-1.0)
