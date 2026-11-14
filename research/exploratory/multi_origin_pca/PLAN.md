# Multi-origin Arabica weather (37 nodes, 8 countries) - PCA study. Plan fixed BEFORE data is seen (14 Nov 2026).

Question: does weather across the main Arabica origins, compressed into a few common factors, improve
(a) the volatility forecast and (b) the price-risk gauge, beyond what recent price volatility says?
Same test design, data and bar as the weather->volatility and CFTC studies, so results are comparable.

Inputs: NASA POWER daily (T2M, PRECTOTCORR) for 37 nodes in arabica_world_nodes.csv; KC=F archived closes.
Per node: 30-day rainfall z-score and 30-day mean temperature z-score vs the same calendar window in
prior years only (existing rebuild_features method). Weather used at t-4 calendar days.

Method: PCA, fitted on TRAINING years only inside each annual fold (no leakage), separately for the
37 rain z-scores and the 37 temperature z-scores. Keep the first 3 components of each -> 6 features.
Components are standardised; nodes with missing days make that day missing (no imputation).

Models (annual expanding refits, test years 2012-2026, training from 2008, purged):
- Volatility: V1 (price-only HAR: log RV 5/21/63 + day-of-year sin/cos) vs PC1 = V1 + 6 weather PCs.
- Spike: G (logistic on logit of the volatility gauge) vs GPC = G + 6 weather PCs; also V0 and B0 reported.
Ridge alpha=1 / logistic C=1, train-only scaling. Block bootstrap (block = horizon, 2000, seed 590).
All 9 cells (5/10/15% x 21/63/126) reported; scopes 2012-26, 2012-18, 2019+.

Bar ("multi-origin weather works"): (1) GPC beats G for +10%/63 over 2012-26, range above zero;
(2) not worse in 2012-18 or 2019+; (3) GPC beats V0 and B0 for that target. Also report PC1 vs V1 volatility.
Descriptive (not tested): variance explained, loadings by country, correlation of PCs with ENSO is NOT used.
