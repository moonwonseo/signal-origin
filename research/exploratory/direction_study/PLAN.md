# Direction of Coffee C returns (up or down). Plan fixed BEFORE results are seen (14 Nov 2026).

Question: can we forecast the SIGN of the Coffee C return over the next h sessions, and does weather help?
This replaces the "+10% touch" target. Magnitude comes later, only if direction passes the bar.

Target: up(t) = 1 if the roll-adjusted log return from close t to close t+h is > 0, else 0.
Roll adjustment: daily log returns of the KC=F chain with the 134 suspected roll days set to zero.
Missing closes (26 sessions): the last close is carried forward for returns; forecast dates and target end
dates that have a missing close are dropped.
Horizons: h = 5 sessions (PRIMARY; about 740 independent windows in 2012-26) and h = 21 (secondary).

Data: KC=F archived closes 2000 - 9 Oct 2026; USD/BRL daily (Yahoo BRL=X, from Dec 2003, London dates);
NASA POWER daily, 37 nodes, 8 countries; per-node 30-day rain and temperature z-scores vs prior years
(existing method), rebuilt from 1991. Training starts at the first complete row (about March 2004).

Feature sets (all known at close t):
- A (market, 13): KC returns 5/21/63/126/252; log RV 21/63; day-of-year sin/cos; USD/BRL returns 5/21/63 and
  log RV 21. USD/BRL is used through t-1 (its daily bar closes after the Coffee C close).
- B1 = A + Brazil weather news (10). PRIMARY. Brazil = production-weighted mean of the 6 regions
  (weights 36/21/17/14/10/2%). For rain z and temperature z: detrended level (minus its own trailing
  5-year mean), 5-day change, 21-day change (6 features). Crop stage: frost depth = max(0, 5 C - lowest
  minimum temperature of the last 5 days over the 6 regions), Jun-Aug only; flowering rain z, Sep-Nov only;
  grain-fill rain z, Jan-Mar only; 21-day change of the frost depth (4 features). Zero outside season.
- B2 = A + B1 weather + the same 6 "news" features for each of the 7 other countries (simple means): 52 weather.
Weather is used at t-4 calendar days. Rows with any missing feature are dropped.

Models (annual expanding refits, test years 2012-2026, purged so training outcomes end before the test year):
- XGB: n_estimators 300, max_depth 3, learning_rate 0.03, subsample 0.8, colsample_bytree 0.5,
  min_child_weight 20, reg_lambda 1; sigmoid calibration on 3 contiguous training blocks; mean of 5 seeds.
- LIN: logistic regression (C = 1), train-only scaling.
- References: always-up; momentum (sign of the 63-session return); B0 (training up-frequency).
No tuning. Forecast "up" when the probability is above 0.5.

Metrics (scopes 2012-26, 2012-18, 2019+; block bootstrap, block = h, 2000 draws, seed 590):
hit rate; AUC; log-loss gain vs B0; trading rule: position(t) = mean of the last h forecast signs,
P&L(t+1) = position(t) x return(t+1) - 5 bp x |change in position|. Annualised P&L and Sharpe.

Placebo (part of this plan): 17 more runs with all weather features rotated by k = 2..18 whole years inside
1996-2026. They give the null distribution for every weather result.

Bar, "direction works with weather" (XGB with B1, h = 5, 2012-26). All four must hold:
1. Hit rate: bootstrap range above 50%.
2. Hit rate minus the hit rate of XGB with A: bootstrap range above zero.
3. That hit-rate gain is larger than all 17 placebo gains.
4. Hit rate above 50% in 2012-18 and in 2019+.
Also reported as a separate question: does the market-only model XGB-A have a hit-rate range above 50%
and a P&L range above zero after costs? (A positive answer is a price/FX result, not an alt-data result.)
Everything else (LIN, B2, h = 21, P&L of weather models) is secondary: 12 weather comparisons in total.
Known limits: the 2012-26 test period was used by six earlier studies; Brazil weights use 2025-26 output;
weather history is revised data; Yahoo prices are an unverified chain. Run once.
