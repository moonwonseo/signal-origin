# Direction of Coffee C returns (up or down): results (14 Nov 2026)

Plan fixed before results (Direction_PLAN.md, sha256 c0c54933...). Run once on the Mac mini (21 s), then the
17 planned placebo runs (6 min). Code and aggregate results: `research/exploratory/direction_study/`.
Sample: 3,702 forecast dates for h = 5 (740 independent windows), 3,686 for h = 21 (176 windows).

## Verdict: direction does not work. All four bars fail for the primary model.

### Primary horizon: 5 sessions, 2012-2026 (share of "up" weeks: 48.1%)
| Model | Hit rate (range) | vs market-only model | P&L per year after cost | Sharpe |
|---|---|---|---|---|
| Always up | 48.1% (45.4 to 50.8) | | +1.4% | 0.04 |
| Momentum sign (63 sessions) | 50.2% (47.7 to 52.8) | | +3.3% | 0.10 |
| XGB market only (A) | 49.9% (47.5 to 52.3) | | -7.7% (-22.5 to +7.2) | -0.25 |
| **XGB + Brazil weather news (B1, primary)** | **49.8% (47.4 to 52.2)** | -0.1 pp (-1.8 to +1.6) | -9.8% (-25.4 to +6.0) | -0.32 |
| XGB + all-origin weather news (B2) | 49.8% (47.3 to 52.3) | 0.0 pp (-2.2 to +2.0) | -5.5% (-20.0 to +11.0) | -0.18 |
| Linear market only (A) | 50.1% (47.8 to 52.5) | | -7.9% | -0.26 |
| Linear + Brazil weather news (B1) | 50.1% (47.5 to 52.6) | -0.1 pp (-2.3 to +2.2) | -3.0% | -0.10 |
| Linear + all-origin weather news (B2) | 52.2% (49.7 to 54.6) | +2.1 pp (-0.6 to +4.8) | +11.0% (-4.2 to +26.5) | 0.36 |

Bars for XGB + B1, h = 5:
1. Hit-rate range above 50%: NOT met (47.4 to 52.2).
2. Better than XGB market-only, range above zero: NOT met (-0.1 pp).
3. Gain larger than all 17 placebo gains: NOT met (9 of 17 placebos are equal or better).
4. Above 50% in both periods: NOT met (49.8% in each).
Separate question, market-only model: no. Hit rate 49.9%, P&L negative. Momentum and USD/BRL give no edge here.

### Secondary horizon: 21 sessions, 2012-2026 (176 windows; ranges are about +/- 4.5 pp wide)
| Model | Hit rate (range) | vs market-only | P&L per year | Placebos >= real (hit gain) |
|---|---|---|---|---|
| XGB A | 51.9% (48.0 to 56.1) | | -2.6% | |
| XGB + B1 | 51.5% (47.9 to 55.8) | -0.4 pp | -2.5% | 6 of 17 |
| XGB + B2 | 52.4% (48.5 to 57.2) | +0.5 pp | +2.2% | 0 of 17 |
| Linear A | 52.8% (49.0 to 57.4) | | +1.0% | |
| Linear + B1 | 54.3% (50.2 to 58.9) | +1.5 pp (-2.1 to +4.9) | +5.1% (-9.8 to +18.9) | 2 of 17 |
| Linear + B2 | 53.6% (49.2 to 58.0) | +0.8 pp | +1.8% | 3 of 17 |
No model has a P&L range above zero. No weather model beats its market-only model with a range above zero.

## Reading
1. Brazil weather news (level, changes, frost, flowering, grain fill) adds nothing at 5 or 21 sessions. Real
   Brazil weather is no better than rotated Brazil weather.
2. The all-origin set (B2) is better than all 17 placebos in 2 of its 4 secondary cells (linear at h = 5 on
   P&L; XGB at h = 21 on hit rate, AUC and P&L). It is not consistent: the other model family shows nothing at
   the same horizon, and every hit-rate range includes 50%. This agrees with the earlier placebo lead: the
   information is in weather that is shared between origins, not in Brazilian crop events. A global climate
   mode (ENSO) is the most probable source. That is a hypothesis, not a result.
3. Secondary cells: 12 weather comparisons. One or two "better than all placebos" results can occur by chance.
4. The linear models have a worse log loss than the base rate in all cells: their probabilities are not usable.

## Deviations from the plan
- USD/BRL history from Yahoo has a gap from Aug 2004 to Mar 2006 and a 26-day gap in Aug 2008. The effective
  training start is mid-2006, not March 2004 (1,443 training rows for the 2012 fold).
- The daily forward log was NOT started. No model passed the bar, and the log needs daily price and weather
  downloads plus a scheduled job on the Mac mini, which need separate approval.

## Erratum (15 Nov 2026): roll adjustment repaired, study run again
The price file marks the last day of the old contract as the roll day; the gap between contracts is in the next
session. The study set only the marked day to zero, so the gaps stayed in the returns and in the labels. The
repair sets both days to zero (`ROLL_FIX=1`; 268 sessions). Real run and 17 placebo runs were repeated on the Mac
mini. Aggregate results: `research/exploratory/direction_study/results_rollfix/`. Details: `research/autoresearch/Autoresearch_PLAN_ADDENDUM_1.md`.

| Quantity (2012-2026) | First run | With the repair |
|---|---|---|
| Up-rate, h = 5 / h = 21 | 48.1% / 48.0% | 47.5% / 45.9% |
| Always-long P&L per year | +1.4% | -1.0% |
| PRIMARY: XGB + Brazil weather, h = 5, hit rate | 49.8% | 50.5% |
| PRIMARY: gain against XGB market-only | -0.1 pp; 9 of 17 placebos at or above | -0.3 pp; 7 of 17 |
| Linear + all-origin weather, h = 5: hit rate | 52.2% | 50.5% |
| Linear + all-origin weather, h = 5: P&L per year | +11.0%; 0 of 17 placebos at or above | +2.3%; 3 of 17 |
| XGB + all-origin weather, h = 21: hit rate | 52.4% | 47.9% |
| XGB + all-origin weather, h = 21: P&L per year | +2.2%; 0 of 17 | -11.2%; 11 of 17 |

Verdict: the primary result does not change (all four bars fail). The two secondary leads of the first run
(all-origin weather in the linear model at h = 5 and in XGBoost at h = 21) do not survive the repair.
