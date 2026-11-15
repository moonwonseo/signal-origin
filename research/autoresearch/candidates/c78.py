import numpy as np
import lib
ID, PARENT = "c78", "c77"
HYP = "The climatic water balance (rain minus reference evapotranspiration) is the physical measure of drought stress: it joins rain and heat. If water stress is the cause of the crop loss, the water balance of the grain-fill months must score at least like heat alone."
CHANGE = "Unfitted rule on one alt-data feature (ERA5, t-7 days): Brazil output-weighted mean of (rain - ET0) over Jan-Mar to date, held to the next January, minus the last 5 years. Buy early if below normal (drier), else buy late."
EXPECT = "RATIO near c77 (+0.447) if water stress is the cause; clearly lower means that the signal is temperature."
ALT, D_BAND, SMOOTH, SEEDS = ["fill_wb_era5"], 0.0, 1, 1


def features(D):
    return lib.era5_water_balance(D)


fit_predict = lib.rule_fp("fill_wb_era5", sign=-1.0)
