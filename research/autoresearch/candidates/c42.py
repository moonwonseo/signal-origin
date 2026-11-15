import lib
ID, PARENT = "c42", "c27"
HYP = ("The market-trend rules are noisy views of one common factor (Brazil and world demand, dollar, funds). "
       "A vote of five different markets removes the noise of each one.")
CHANGE = "Vote of 5 market features: sugar, Brazil equities, copper (126-session return > 0), dollar index (63-session return < 0), coffee (252-session return > 0). Three or more: buy early, else buy late."
EXPECT = "RATIO about +0.3 to +0.4 with similar halves."
ALT, D_BAND, SMOOTH, SEEDS = [], 0.0, 1, 1
features = lib.trend5
fit_predict = lib.vote_fp()
