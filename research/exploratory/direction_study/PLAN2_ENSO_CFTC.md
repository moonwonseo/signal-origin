# Direction of Coffee C returns: ENSO and CFTC positioning. Plan fixed BEFORE results are seen (14 Nov 2026).

Why: the all-origin weather set beat its placebos in 2 of 4 secondary cells of the direction study. If a
global climate mode is the source, ONE index (ENSO) must show the effect more clearly than 42 features.
CFTC positioning is on disk and was tested only against the "+10% touch" target, never against direction.

Same target, market feature set A, models, folds, cost, bootstrap and code as the direction study
(Direction_PLAN.md). Horizons: h = 21 sessions (PRIMARY for both sources: both are slow), h = 5 and 63 (secondary).

New feature sets:
- E = A + 2 ENSO features: NOAA CPC monthly Nino 3.4 anomaly (level) and its 3-month change.
  The value for month M is used from the 15th day of month M+1.
- C = A + 2 CFTC features (existing method): managed-money net share of open interest and its 4-week change.
  A report is used from report date + 6 days, for at most 14 days.
Rows are matched: every model is scored on the dates where A, E and C are all complete.

Placebo: 17 runs. ENSO rotated by k x 12 months and CFTC rotated by k x 52 weeks, k = 2..18.

Bar for each source S (E or C), h = 21, 2012-26. All four must hold:
1. XGB with S: hit rate minus hit rate of XGB with A, bootstrap range above zero.
2. That gain is larger than all 17 placebo gains.
3. Logistic with S also has a positive gain over logistic with A (same sign in both model families).
4. The XGB gain is positive in 2012-18 and in 2019+.
Also reported: hit rate vs 50%, AUC, P&L after cost, for all cells. Secondary cells: 10 comparisons.
Known limits: the test period 2012-26 was used by seven earlier studies; ENSO history contains about 5 cycles
since 2006; NOAA revises the index; managed-money positions follow price trends. Run once.
