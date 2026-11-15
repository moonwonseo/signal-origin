# Multi-origin weather + XGBoost: risk gauge and alpha test. Plan fixed BEFORE results are seen (14 Nov 2026).

Questions:
(a) Risk: does XGBoost on multi-origin weather improve the "touch +k% within h sessions" forecast?
(b) Alpha: does it forecast the DIRECTION of Coffee C returns well enough to trade?
Same data, folds, lag and bootstrap as the multi-origin PCA study, so results are comparable.

Inputs: KC=F archived closes (2000 - 9 Oct 2026); NASA POWER daily, 37 nodes, 8 countries; per-node 30-day
rain and temperature z-scores vs prior years (existing method). Weather used at t-4 calendar days.
Returns for the alpha test: daily log returns with suspected roll days set to zero (the series is an
unadjusted front-month chain; roll jumps cannot be traded). Spike labels: unchanged V5 rule.

Feature sets (all known at t):
- P   (price only): log RV 5/21/63, day-of-year sin/cos, trailing returns 21/63/126. Spike models also get
      the logit of the volatility gauge for the cell.
- PC  = P + 6 weather PCs (3 rain, 3 temperature; PCA refit inside each fold on pre-test weather). PRIMARY.
- RAW = P + 74 node z-scores (37 rain, 37 temperature).
- CTY = P + 34 features: per country, mean rain z and mean temperature z (30-day), their trailing 90-day
      means; Brazil lowest minimum temperature over the last 30 and 90 days (frost).
Rows with any missing feature are dropped (no imputation).

Models (annual expanding refits, test years 2012-2026, training from 2008-01-02, purged):
- XGB: n_estimators 300, max_depth 3, learning_rate 0.03, subsample 0.8, colsample_bytree 0.5,
  min_child_weight 20, reg_lambda 1; mean of 5 seeds (590..594). NO tuning: about 50 independent windows.
- LIN: logistic (C=1) / ridge (alpha=1), train-only scaling. Diagnostic comparator.
- References: B0 (training frequency), V0 (unfitted volatility gauge), zero-return forecast, always-long.

Targets and metrics:
(a) Spike, 9 cells (5/10/15% x 21/63/126). Brier; paired gains vs same-family P model, V0 and B0.
(b) Forward log return over h = 21 and 63 sessions. Reported: MSE gain vs zero forecast and vs P model;
    Spearman rank IC; trading rule: position(t) = mean of sign(forecast) over the last h forecast dates,
    P&L(t+1) = position(t) x return(t+1), no costs. Annualised mean, Sharpe, turnover.
Block bootstrap (block = h, 2000 draws, seed 590) on paired differences. Scopes 2012-26, 2012-18, 2019+.

Bars (primary = XGB with PC):
RISK "works":  +10%/63, 2012-26: (1) beats XGB-P, range above zero; (2) beats V0, range above zero;
               (3) not worse than XGB-P in 2012-18 and in 2019+.
ALPHA "found": h = 63, 2012-26: (1) strategy mean P&L, range above zero; (2) P&L minus XGB-P strategy P&L,
               range above zero; (3) that difference is positive in 2012-18 and in 2019+.
Everything else (RAW, CTY, LIN, other cells, h = 21) is secondary: 54 spike and 12 alpha comparisons in
total, so about 3 "ranges above zero" are expected from noise alone. A secondary win is a lead, not a result.
Run once. Feature importance is descriptive only.
