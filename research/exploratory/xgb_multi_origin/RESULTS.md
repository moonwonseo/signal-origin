# Multi-origin weather + XGBoost: results (14 Nov 2026)

Plan fixed before results (XGB_Multi_Origin_PLAN.md, sha256 2cf5ad6a...). Run once, on the Mac mini (68 s).
Code and aggregate results: `research/exploratory/xgb_multi_origin/`. The 37-node PCA study was reproduced first
on the same machine: all 108 rows equal the archived results to 1e-12.
Sample: 2,870 test dates for +10%/63 (fewer than the PCA study's 3,122, because 126-session returns and
90-day weather means need more history). Price data end 9 Oct 2026. 134 roll days set to zero for returns.

## Verdict: no alpha. No gain for the risk gauge.

### (a) Risk: touch +10% within 63 sessions, Brier (lower is better), 2012-2026
| Model | Brier | vs same model without weather | vs volatility gauge V0 |
|---|---|---|---|
| Always 50% | 0.250 | | |
| B0 historical frequency | 0.259 | | -0.019 (-0.037 to -0.001) |
| **V0 volatility gauge (nothing fitted)** | **0.239** | | |
| XGB price only | 0.348 | | -0.109 (-0.152 to -0.070) |
| **XGB + 6 weather PCs (primary)** | **0.327** | +0.021 (-0.013 to +0.054) | -0.087 (-0.130 to -0.051) |
| XGB + 74 node z-scores | 0.278 | +0.070 (+0.022 to +0.113) | -0.039 (-0.076 to -0.005) |
| XGB + country features and frost | 0.292 | +0.056 (+0.005 to +0.105) | -0.053 (-0.102 to -0.012) |
| Linear + 6 weather PCs | 0.310 | +0.007 (-0.024 to +0.031) | -0.070 (-0.123 to -0.029) |

Bar 1 (beats XGB price-only, range above zero): not met. Bar 2 (beats V0): not met; it is reliably worse.
All 9 cells: no learned model beats V0 in any cell (0 of 72); 66 of 72 are reliably worse than V0.
Every XGBoost and linear model is also worse than "always 50%" at the primary cell.

### (b) Alpha: forward 63-session return, trading rule, 2012-2026, no costs
| Model | P&L per year | Sharpe | P&L vs price-only model | Rank IC |
|---|---|---|---|---|
| Always long | +5.5% (-10.5 to +26.1) | 0.16 | | |
| XGB price only | -9.0% (-18.4 to +0.3) | -0.42 | | -0.20 (-0.33 to -0.04) |
| **XGB + 6 weather PCs (primary)** | **-0.6% (-12.0 to +9.6)** | **-0.03** | +8.4% (-1.9 to +18.7) | -0.10 (-0.26 to +0.05) |
| XGB + 74 node z-scores | +2.8% (-7.5 to +16.0) | 0.11 | +11.8% (-0.5 to +27.7) | +0.06 (-0.11 to +0.21) |
| XGB + country features and frost | +6.4% (-5.8 to +20.2) | 0.24 | +15.4% (+3.1 to +30.3) | +0.09 (-0.12 to +0.29) |

Bar 1 (P&L range above zero): not met. Bar 2 (beats XGB price-only, range above zero): not met.
No model of the 8 has a P&L range above zero at h = 63 or h = 21. No model beats always-long reliably.
Every model has a larger squared error than a forecast of zero return.

## Reading
1. The primary model (XGBoost on the PCA factors) fails all bars for risk and for alpha.
2. Weather makes XGBoost "less bad" in 10 of 54 secondary risk cells and 2 of 12 alpha cells. This is an
   improvement over a price-only XGBoost model that is itself much worse than the baseline (0.348 vs 0.259).
   The weather models stay worse than B0 and V0. The placebo test below examines this lead.
3. Feature importance is spread thinly: weather takes 83-92% of the split gain in the RAW and CTY sets, with no
   feature above 4%. No single origin or crop event carries the effect. Forecasts are also too extreme
   (standard deviation 0.23-0.28 vs 0.085 for the gauge).
4. The price-only models have a reliably NEGATIVE rank IC (-0.20): momentum learned in 2008-11 reversed after.
   Found after the fact; not a tradable result.

## Placebo test (EXPLORATORY: designed after the results above were seen)
Question: is the "less bad with weather" effect an artefact (more features = more shrinkage), or information?
Method: rotate all weather features by k whole years (k = 2..18, 17 runs) inside 2007-2026. Seasons and
autocorrelation stay; the link between weather dates and price dates is broken. Same code, same sample.
(A first batch failed on a rotation bug that moved empty pre-2007 rows into training; fixed, all 17 rerun.)

| Quantity (2012-2026) | Real weather | 17 placebos: mean (min to max) | Placebos >= real |
|---|---|---|---|
| +10%/63 Brier gain vs price-only, XGB + PCs | +0.021 | -0.014 (-0.046 to +0.010) | 0 of 17 |
| same, XGB + 74 node z-scores | +0.070 | -0.003 (-0.048 to +0.024) | 0 of 17 |
| same, XGB + country features | +0.056 | -0.013 (-0.054 to +0.019) | 0 of 17 |
| Mean XGB gain vs price-only, all 27 cells | +0.028 | -0.003 (-0.032 to +0.018) | 0 of 17 |
| Cells (of 54) with range above zero | 10 | 0.5 (0 to 5) | 0 of 17 |
| h=63 P&L per year, XGB + PCs | -0.6% | -8.5% (-16.9 to +0.8) | 1 of 17 |
| h=63 P&L per year, XGB + 74 node z-scores | +2.8% | -8.1% (-13.9 to +0.9) | 0 of 17 |
| h=63 P&L per year, XGB + country features | +6.4% | -4.2% (-14.7 to +4.7) | 0 of 17 |
| h=63 rank IC, XGB + country features | +0.09 | -0.10 (-0.25 to +0.04) | 0 of 17 |
| Learned models that beat V0 (of 72) | 0 | 0 in every run | |
Full table: `research/exploratory/xgb_multi_origin/results/placebo_summary_EXPLORATORY.csv`.

Reading of the placebo test:
- Real weather is consistently better than rotated weather. The "less bad" effect is not a shrinkage artefact.
  The weather features contain some information that is aligned in time with Coffee C prices.
- This is NOT alpha. The models with real weather still lose to the unfitted gauge, to B0 and to always-long.
- Two explanations are open, and this test cannot separate them:
  (1) a real weather effect on price; (2) a shared slow trend. Temperature z-scores drift up with warming,
  and ENSO moves all origins together, while the spike rate rose from 32% (2012-18) to 68% (2019+). A slow
  weather factor can act as a clock that tells the model which price regime it is in. Rotation breaks that clock.
  2008-2026 contains only about 5 ENSO cycles, so explanation (2) rests on very few independent events.
- The 17 rotations are not independent draws. "0 of 17" is at best p of about 0.06 for each row.
- Status: a lead that justifies one focused follow-up (detrended weather + placebo). It is not a result.

## Erratum (15 Nov 2026): roll adjustment repaired, study run again
Same defect and repair as in `Direction_RESULTS.md` (erratum). It affects the return features and part (b);
the "+10% touch" target of part (a) uses the unadjusted price by design and was not changed (a contract gap can
count toward a touch; this is a limit of that target). Real run and 17 placebo runs were repeated.
Aggregate results: `research/exploratory/xgb_multi_origin/results_rollfix/`.

| Quantity (2012-2026) | First run | With the repair |
|---|---|---|
| (a) Brier +10%/63: V0 / XGB price only / XGB + 6 PCs (primary) | 0.239 / 0.348 / 0.327 | 0.239 / 0.347 / 0.330 |
| (a) Brier gain of the primary model against price only; placebos at or above | +0.021; 0 of 17 | +0.017; 0 of 17 |
| (b) h = 63 P&L per year: always long | +5.5% | +4.7% |
| (b) h = 63 P&L per year: XGB price only | -9.0% | -14.6% |
| (b) h = 63 P&L per year: XGB + 6 PCs (primary) | -0.6% | -4.2% (range -15.8 to +5.8) |
| (b) h = 63 P&L per year: XGB + 74 node z-scores / + country features | +2.8% / +6.4% | +6.8% / +6.7% |

Verdict: no change. No alpha and no gain for the risk gauge. The exploratory placebo result also holds: real
weather is better than rotated weather in 0 of 17 comparisons for each of the three weather sets.
