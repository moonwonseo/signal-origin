# Signal-Origin: handover of all changes since V4

**For:** Moonwon Seo (owner of V1 to V4) and his agent.
**From:** Celine Yang, written with Claude. **Date:** 15 Nov 2026 (evening).
**Scope:** all work from the V4 package (`main` at commit `4af263f`, 12 Nov) to the state of 15 Nov:
V4 check, data work, V5, seven studies, the new problem definition, the autoresearch loop, the price-series
defect, the buyer dashboard, the slide deck, and the repository.
**Final presentation:** Wed 18 Nov 2026, 10 minutes, PDF on Canvas by 1:30 PM.

## 0. How to read this document
- Sections 1 and 2 are the summary. Section 16 is the list of decisions that only Moonwon can make.
- Each number has a source file. The source files are the authority. If this document and a source file
  disagree, the source file is correct.
- Repository paths are relative to the root of `github.com/moonwonseo/signal-origin`.
- Raw data, row-level outputs and the built dashboard are not in the repository (section 14).
- Words with a fixed meaning are in the glossary (section 17).

Source files, in the order of importance:

| File | Content |
|---|---|
| `docs/HANDOFF.md` | State of 15 Nov: new problem, eval, autoresearch result, defect, errata |
| `research/autoresearch/Autoresearch_RESULTS.md` | Full result of the 100 iterations, table of each iteration |
| `research/autoresearch/Autoresearch_PLAN.md`, `..._ADDENDUM_1.md`, `..._ADDENDUM_2.md` | The fixed plan and its two logged changes |
| `docs/HANDOFF_2026-11-14.md` | Full record to 14 Nov: V4 check, data work, V5 preview, gauge, studies, first dashboard |
| `docs/V5_CHANGES.md`, `docs/V5_DATA_NOTES.md` | V5 design, the decisions for sign-off, the six-region data checks |
| `research/exploratory/*/RESULTS*.md` | Each study, with its erratum where one exists |
| `research/prototype/README.md` | The dashboard of 15 Nov |
| `AGENTS.md` | Rules for agents in this repository |

---

## 1. Summary

### 1.1 Status
1. **There is no confirmed predictor.** No model and no rule that we tested is proven to help a coffee buyer.
2. **V4 was checked and stands as recorded.** No V4 module was edited. V4 synthetic outputs are byte-identical.
3. **V5 (better weather, longer history, more thresholds and horizons) did not beat the baseline B0** in a local
   preview with the draft spec. The official V5 run was not made, because `configs/v5_spec.json` is not signed off.
4. **Seven more studies followed.** Six failed. One unfitted formula (the volatility gauge) beats B0 for the V4/V5
   target. It uses price data only, and it is exploratory.
5. **On 15 Nov Celine defined the problem again:** "each week, buy early, buy steadily, or buy late", scored by
   the money saved against steady buying. Reason: "does the price touch +10%?" is not a decision of a buyer.
6. **An autoresearch loop ran 100 pre-registered iterations on the new problem.** The best rule (two fixed
   questions about ENSO and Brazil summer heat) passed the development score and the placebo test. The held-out
   test period 2023 to Oct 2026 did not confirm it. Verdict by the plan: "Not confirmed".
7. **The loop found a defect in the roll adjustment of the price series.** It is repaired in the new code.
   Three studies of 14 Nov were run again. Two of their results changed. **V4 and V5 labels were not checked for
   this defect** (section 10.4).
8. **The buyer dashboard was built again on the best rule.** It labels the rule "not confirmed".
9. **`v5-weather` was merged into `main` on 15 Nov, with no pull request, at Celine's instruction.**
   CI fails only at `scripts/check_publication.py`, because the allowlist was not edited.

### 1.2 The four numbers to remember
| Item | Value | Source |
|---|---|---|
| Best rule, development years 2009-2022 | RATIO +0.787 (necessary: 0.712) | `Autoresearch_RESULTS.md` |
| Best rule, placebo test | 0 of 17 runs at or above the real score (highest +0.613) | same |
| Best rule, test period 2023-Oct 2026 | RATIO +0.374, range -0.60 to +1.43 (bar: 0.50) | same |
| Volatility gauge, "+10% touch in 63 sessions" | Brier 0.240 against 0.260 for B0 | `docs/HANDOFF_2026-11-14.md` |

### 1.3 What we ask from Moonwon
See section 16. In short: (a) review the merge into `main` and decide on the publication allowlist;
(b) check if the roll defect changes V4 or V5 labels; (c) decide on the V5 sign-off; (d) read the deck and the
dashboard before 18 Nov.

---

## 2. Timeline
| Date | Who | What |
|---|---|---|
| to 3 Nov | Moonwon | V1 to V4: B0, B1, A1, A2, freight models F1, FW1, FW2; annual refits 2022-2026; viewer; publication package on `main` |
| 10 Nov | Moonwon | Handoff bundle to Celine |
| 12 Nov | Celine + Claude | V4 check. Price history check 2000-2018. Thin-trading label check. Six-region NASA POWER pull. Data-revision check. V5 code on branch `v5-weather` (7 commits, 21 files added, 0 modified). V5 local preview. Volatility gauge. Weather-to-volatility study. CFTC positioning study. First dashboard |
| 14 Nov | Celine + Claude | 37-node weather pull (8 countries). Multi-origin PCA study. XGBoost multi-origin study. Direction study. ENSO + CFTC direction test. Agent docs and handoff of 14 Nov |
| 15 Nov | Celine + Claude | New problem definition. Autoresearch plan, eval and harness. Iterations 1-30. Roll defect found and repaired (addendum 1). Extension to 100 iterations (addendum 2). Two looks at the test period. Errata for three studies. Handoff of 15 Nov. Merge into `main`. Slide deck (23 slides). Dashboard built again on the best rule. Prototype source on `main` |

---

## 3. What did NOT change in V4
- Since the V4 commit `4af263f`: **244 files added, 2 files modified, 0 files deleted.**
  The two modified files are `README.md` (a status section was added at the top) and `.gitignore` (new ignore lines).
- No file of the V4 package was edited: `signal_origin/{experiment,freight,features,weather,models,split,...}.py`
  are as on 12 Nov. V5 is in new modules only.
- `python -m signal_origin.experiment synthetic` gives byte-identical predictions, metrics, annual and
  calibration files before and after the merge.
- Tests: the 187 V4 tests pass. 16 V5 tests were added (203 in all). CI runs them and they pass.
- `publication_manifest.json` was not edited.
- Known item, not caused by our changes: `build_demo.py --check` reports "Demo differs" on Celine's compute
  machine. It reports the same on the V4 commit, so it is an effect of that machine.

To undo all of it: revert the commits after the merge, newest first (section 13.2), then `git revert -m 1 98770f2` (the merge commit).

---

## 4. Check of V4 (12 Nov; no refit, Moonwon's saved predictions)
Sample: 2022 to Jul 2026, 1,135 forecast dates, about 18 independent 63-session windows.

| Finding | Value |
|---|---|
| FW1 (price + freight + weather), Brier | 0.2514. Not better than "always 50%" (0.25) |
| FW1 against B0, paired gain | +0.031, range -0.063 to +0.108 (block bootstrap). The range includes zero |
| By year | FW1 better than B0 in 2022 and 2024. Worse in 2023, 2025, 2026 |

Reading: with about 18 independent windows, V4 cannot show a gain. This is the reason for the longer history in V5.
Source: `docs/HANDOFF_2026-11-14.md`, section 3.1.

---

## 5. Data work (12-14 Nov)
All raw files are outside the repository. Tools: `data_tools/`.

| Topic | Finding | Why it matters |
|---|---|---|
| Price history | 2008 and later is usable. 2000-2007 has 20 blank sessions. About five contract rolls each year. Usable forecast dates at 63 sessions: 2,099 in 2008-2018 and 1,846 in 2019-2026. The exchange calendar is not verified | V5 starts training in 2008 |
| Thin-trading labels | Yahoo's KC=F quotes expiring contracts on days with almost no volume. Of 669 positive V4 labels, 280 first cross on a day with volume below 1,000, and 24 on a suspected roll day. 100 labels (15%) vanish if closes with volume below 1,000 are ignored | V5 has a label-sensitivity run with a liquidity mask. Conclusions did not change |
| Six Brazil regions | Sul de Minas, Matas de Minas, Cerrado Mineiro, Alta Mogiana, Espírito Santo mountains, Bahia Planalto: 93.6% of Brazilian Arabica. Weights: Conab 3rd survey 2026, mean of 2025 and 2026 (36/21/17/14/10/2%) | Answer to the midterm feedback "more weather locations". The weights use recent shares for earlier years, which is a mild look-ahead |
| Weather availability | New NASA POWER values arrive in about 2 days, inside the 4-day lag. But the newest month is revised later: against the October pull, 2-30 Sep 2026 changed on almost each day (Tmin up to 1.9 °C, rain up to 11 mm a day; September rain 96.9 mm became 118.2 mm) | Backtests use revised values. A buyer in real time sees provisional values. Backtests are thus a little optimistic |
| Latency logger | `data_tools/power_latency_logger.py` was started on Celine's machine. Its log was not reviewed | Open item |
| Frost threshold | 3.0 °C missed the 2021 frost (coldest grid night 3.05 °C). 3.5 °C registers 1981, 1994, 2000, 2021. Since 2008, only 2021 is below 3.5 °C | The frost feature of V5 rests on one event |
| 37 world nodes | `configs/v6_arabica_world_nodes.csv`: Brazil 6, Colombia 6, Ethiopia 6, Mexico 5, Peru 5, Guatemala 4, Honduras 3, Nicaragua 2. No two nodes in one POWER cell. Data 1981 to 13 Nov 2026 | Used by the PCA study, the XGBoost study and the autoresearch loop |

Sources: `docs/V5_DATA_NOTES.md`; `docs/HANDOFF_2026-11-14.md`, section 3.2.

---

## 6. V5 (branch `v5-weather`, 12 Nov)

### 6.1 Question
Does better weather data add to price-only forecasts of the V4 target ("a close at or above +k% within h sessions")?
V5 answers the four points of the midterm feedback: more locations, crop-season features, real data availability,
other thresholds and horizons.

### 6.2 What V5 adds to V4
| Item | V4 | V5 |
|---|---|---|
| Weather | One grid point | Six regions, weighted by output |
| Weather features | 30-day rain and temperature z-scores | Plus crop-stage features: frost nights in the worst region (Jun-Aug), flowering rain anomaly (Sep-Nov), grain-fill dry spell (Jan-Mar); zero outside the season |
| Test years | 2022 to Jul 2026 (1,135 dates, about 18 windows) | 2012 to 2026 (3,122 dates, about 50 windows, 15 annual folds) |
| Training start | Shorter history | 2 Jan 2008 |
| Grid | 10%, 63 sessions | 5/10/15% × 21/63/126 sessions; primary cell 10%/63 |
| Models | B0, B1, A1, A2, F1, FW1, FW2 | B0, B1, A1, A3 (A3 = six-region crop-stage weather). Freight is left out on purpose |
| Uncertainty | Not given (IID intervals ruled out) | Block-bootstrap ranges on paired Brier differences (block = horizon, 2,000 draws, seed 590), against B0 and against "always 50%" |
| Label check | None | Optional liquidity mask: crossings count only on liquid, non-roll days |
| Model settings | Training-only scaling, L2 logistic, C = 1, lbfgs, seed 42 | Same |

### 6.3 New files (no existing file was edited)
| File | Content |
|---|---|
| `signal_origin/v5.py` | Runner: grid, longer history, sign-off gate, dry run |
| `signal_origin/v5_labels.py` | Threshold as a parameter, optional liquidity mask. At 10% it reproduces V4 labels exactly (tested) |
| `signal_origin/crop_weather.py` | Model A3 features. Uses `weather.py` with no change |
| `signal_origin/uncertainty.py` | Block bootstrap of paired Brier differences |
| `signal_origin/synthetic_v5.py` | Artificial data for the tests |
| `configs/v5_spec.json` (DRAFT), `configs/v5_crop_windows.json` (DRAFT), `configs/v5_regions.csv` | Spec, crop windows (months from Conab's 2026 calendar, frost threshold 3.5 °C), region points and weights |
| `tests/test_v5_labels.py`, `test_crop_weather.py`, `test_uncertainty.py`, `test_v5_pipeline.py` | 16 tests |
| `data_tools/` | POWER pull, latency logger, price-history check, label-liquidity check, liquidity mask |

### 6.4 Sign-off gate
`python -m signal_origin.v5 run` refuses a historical fit until `configs/v5_spec.json` is `SIGNED_OFF` by both
teammates. `--dry-run` is always permitted. The gate was not bypassed in the repository. The numbers in 6.5 are from
a local preview with the draft spec, and they are labelled exploratory.

### 6.5 Result of the local preview (12 Nov): V5 did not work
Primary cell, 10% / 63 sessions, 2012-2026, Brier (lower is better):

| Model | Brier |
|---|---|
| Always 50% | 0.250 |
| B0 (historical frequency) | 0.260 |
| B1 (price features) | 0.289 |
| A1 (+ single-point weather) | 0.284 |
| A3 (+ six-region crop-stage weather) | 0.293 |

- A3 against B0: -0.033 (range -0.062 to -0.011). A3 is reliably worse.
- No model beats B0 in any of the 9 cells of the grid.
- AUC inside each year is about 0.5 and not stable.
- Cause: the relations flip between the calm years (2012-2018, 32% of dates are "touch") and the volatile years
  (2019 and later, 68%).
- The spec and crop-window files did not change after the preview (sha256 prefixes `c3d3705f96033f45`,
  `2bb17a71ebfa5ae5`). An official run after sign-off must thus give the same numbers.

Source: `docs/HANDOFF_2026-11-14.md`, section 3.3; `docs/V5_LOCAL_PREVIEW_2026-11-12.md`.

### 6.6 Decisions for Moonwon before a sign-off (from `docs/V5_CHANGES.md`)
1. Crop windows and the frost threshold of 3.5 °C.
2. Heat-day feature: off unless a threshold is set.
3. Region weights: recent Conab shares for all years, or the shares of an older survey.
4. History from 2008 with the unverified calendar (`--acknowledge-unverified-inputs`), or the strict gate.
5. Models B0, B1, A1, A3; the grid; the primary cell; the scopes 2012-26, 2012-18, 2019+, 2024+.
6. Wording of the uncertainty: "rough ranges", not significance tests.

After the roll defect (section 10), a seventh point exists: decide if V5 labels need a check before any official run.

---

## 7. Studies after V5 (12-14 Nov)
Shared design unless noted: annual expanding refits, test years 2012-2026, training from 2008, purged at the
boundary, matched sample, block-bootstrap ranges. Each study except the gauge had a `PLAN.md` with a sha256
before the run.

| # | Study (folder in `research/exploratory/`) | Question | Result | State after the roll repair |
|---|---|---|---|---|
| 1 | Volatility gauge (no folder; formula in the handoff of 14 Nov) | Does a formula with nothing fitted estimate "touch +10% in 63 sessions"? | **Works, exploratory.** Brier 0.240 against B0 0.260; gain +0.020 (range +0.001 to +0.039). In 2019+ the gain is +0.035. Tied in 2012-2018 | Not calculated again; effect not checked |
| 2 | `weather_volatility/` | Does weather improve a forecast of realised volatility? | **No.** W3 against V1 at 63 sessions: -0.0021 (range -0.0050 to +0.0001). Worse at 21 sessions | Not run again; effect not checked |
| 3 | `cftc_positioning/` | Does CFTC managed-money positioning improve the gauge? | **No.** Brier: gauge 0.240, recalibrated gauge 0.258, with positioning 0.275. Worse in all 9 cells. The coefficient changes sign between years | Not run again; effect not checked |
| 4 | `multi_origin_pca/` | Do weather factors of 37 nodes in 8 countries help? | **Not significant.** Brier 0.249 against 0.258 for the recalibrated gauge: +0.009 (range -0.008 to +0.030). Does not beat the gauge (0.240) | Not run again; effect not checked |
| 5 | `xgb_multi_origin/` | Does XGBoost on multi-origin weather give risk skill or alpha? | **No.** See 7.2 | Run again: no change of the verdict |
| 6 | `direction_study/` (`RESULTS.md`) | Can a model predict the sign of the 5- and 21-session return? | **No.** All four bars fail for the primary model (hit rate 49.8%) | Run again: all bars fail; two secondary weather leads are gone |
| 7 | `direction_study/` (`RESULTS2_ENSO_CFTC.md`) | Do ENSO or CFTC positioning predict the sign of the return? | First run: ENSO met 3 of 4 bars at 21 sessions (hit rate 55.9%). CFTC failed | Run again: **ENSO meets 0 of 4 bars** (hit rate 50.4%). CFTC fails as before |

### 7.1 Volatility gauge, in detail
`P(touch +k within h) = 2 · (1 − Φ(ln(1 + k) / (σ · √h)))`, with σ = standard deviation of the last 63 daily log returns.
- Nothing is fitted. It uses price data only, so it is not alternative data.
- It has no direction: on 12 Nov it gave 59% for +10% and 55% for −10% in 3 months.
- Calibration (said → happened): 39% → 26%, 51% → 58%, 60% → 57%, 69% → 58%. It separates calm days from
  risky days. It over-forecasts in calm years.
- It was found after V5 failed. It was not pre-registered.

### 7.2 XGBoost, in detail (the only XGBoost runs of the project)
Numbers after the roll repair, 2012-2026, 2,870 test dates.

**Target A: touch +10% in 63 sessions (Brier, lower is better)**

| Model | Brier |
|---|---|
| Volatility gauge (nothing fitted) | 0.239 |
| Always 50% | 0.250 |
| B0 | 0.259 |
| Best XGBoost (price + 74 node z-scores) | 0.283 |
| XGBoost + 6 weather factors (primary model, named before the run) | 0.330 |
| XGBoost, price only | 0.347 |

**Target B: trade the 63-session return, long or short, no costs**

| Model | Profit per year | Sharpe |
|---|---|---|
| Always long | +4.7% (range -12.3 to +25.8) | 0.14 |
| Best XGBoost (price + 74 node z-scores) | +6.8% (range -3.5 to +19.4) | 0.28 |
| XGBoost + 6 weather factors (primary) | -4.2% (range -15.8 to +5.8) | -0.20 |
| XGBoost, price only | -14.6% | -0.74 |

- The gauge reads 0.239 here and 0.240 in section 7: this study has 2,870 dates, the other studies have 3,122.
- Each XGBoost model is worse than a constant 50% for the risk target. Its forecasts are too extreme.
- No profit range is above zero. The best model is a selection after the results.
- Exploratory placebo test: real weather was better than weather shifted by whole years in all 17 runs. Thus the
  weather holds some information that is aligned with prices, but not enough for a result.
- One sentence in the erratum of `xgb_multi_origin/RESULTS.md` is worded backwards ("real weather is better than
  rotated weather in 0 of 17 comparisons"). The table next to it is correct: 0 of 17 placebo runs reached the real gain.

### 7.3 Reading of the seven studies
- For direction, public data seem to be in the price before a buyer can use them. Fitted models fail across the
  change of regime in 2019.
- For risk, the present turbulence of the price is the strongest signal.
- "No reliable edge found" is correct. "Weather does not matter" is too strong: large moves come from few shocks,
  and the sample holds about 50 independent windows.

---

## 8. The problem was defined again (Celine, 15 Nov)
Reason: the target "does the price touch +10%?" does not match a decision. A buyer must buy the volume. The buyer
selects only the time.

| Item | V4 and V5 | New definition |
|---|---|---|
| User | A buyer who judges the risk of a large rise | The purchasing team of a coffee trader or roaster |
| Output | A probability | One of three calls each week: buy early (+1), buy steadily (0), buy late (−1) |
| Horizon | 21, 63, 126 sessions | 63 sessions only (about 3 months: the planning time of a buyer, and the range in which stock cover can move: 0 to 3 months) |
| Label | A close at or above +10% within 63 sessions | 1 if the mean price of the next 63 sessions is above the price of today ("buying now is cheaper than steady buying in the next quarter") |
| Metric | Brier score | Money saved against steady buying, divided by its variation (RATIO). A buyer cannot go short, so long/short Sharpe, AUROC and recall are reported but not used |
| Baseline | B0 historical frequency | Steady buying (RATIO = 0), always-early, always-late |

This is a new track. It does not replace the V4 or V5 results. It does not use the V4 or V5 code.

---

## 9. The autoresearch loop (15 Nov; `research/autoresearch/`)

### 9.1 What it is
An AI agent (Claude) ran 100 experiments against one fixed evaluation. For each experiment it wrote the hypothesis
before the run, ran one candidate, read the score, wrote a reflection, and selected the next idea. The agent could
change data sources (public only), features, the model type and the position rule. It could not change the
evaluation. All runs were on Celine's compute machine.

### 9.2 The evaluation (fixed in `Autoresearch_PLAN.md`, sha256 `a145c605...eff9`, before the baselines were scored)
```
position p(t)  = the call on the last session of each week, held for one week: -1, 0 or +1
saving(t)      = p(t-1) * r(t) - 0.0005 * |p(t-1) - p(t-2)|      r = roll-adjusted daily log return
RATIO          = mean(saving) / std(saving) * sqrt(252)          steady buying = 0
SCORE          = RATIO - 0.28 * Emax(N)                          N = 10 + number of iterations
```
- `0.28` = standard error of RATIO for a rule with no skill on 14 years (1/√14 = 0.267, plus 5% for fat tails).
- `Emax(N)` = expected maximum of N standard normal values. Thus the necessary RATIO rises with each trial:
  0.43 at the start, 0.61 after 30 iterations, 0.71 after 100.
- N starts at 10 because the earlier studies count as trials. Both 0.28 and 10 are judgements.
- Walk-forward: one refit for each year, expanding window, labels purged by 63 sessions at the boundary.
- Scored years: 2009-2022 (3,526 sessions). Test period: 2 Jan 2023 to 9 Oct 2026 (947 sessions). Pass: RATIO > 0.5.
- Percent of the yearly purchase cost saved = mean(saving) × 252 × 12.5% (a position of ±1 moves 1.5 months of cover).
- Model space: rules, logistic or ridge regression, tree methods. No neural networks.

### 9.3 Guards against reward hacking
| Guard | What it does |
|---|---|
| Plan fingerprint | sha256 of the plan before the first score |
| Cutoff | The harness deletes all data after 31 Dec 2022 before candidate code runs |
| C1 leak test | Features at dates before T must be identical when data after T are deleted (3 dates, exact) |
| Trial penalty | Each scored run raises N, and N raises the bar. A void run counts. A crash does not |
| Step rule | A candidate replaces the best only if a paired block bootstrap shows a gain (20th percentile above 0) |
| C2 to C5 | Beat always-early and always-late; both halves positive; 8 of 14 years positive; positive at double cost |
| C6 placebo | Alt data shifted by 2 to 18 whole years (17 runs). The real data must beat all 17 |
| C7 | A RATIO above 1.5 starts a leak audit before a claim |
| Void rule (addendum 1) | A candidate whose feature does not measure its hypothesis cannot be the best. It still counts in N |
| Trial log | Append-only. Each row holds the sha256 of the row before it. The hypothesis is logged before the run |
| Test period | Not used for selection. Each look is logged |

### 9.4 Result
| Step | Iterations 1-30 (best: c22) | Iterations 31-100 (best: c86) |
|---|---|---|
| Best rule | Season heat and 90-day stress in Brazil agree | ENSO state of January and Brazil Jan-Mar heat agree |
| RATIO on 2009-2022 | +0.612 (necessary 0.605) | +0.787, range +0.38 to +1.23 (necessary 0.712) |
| C1 to C5, C7 | Satisfied | Satisfied: 11 of 14 years positive; halves +0.79 / +0.78 |
| C6 placebo | Failed (1 of 17 above) | Passed (0 of 17 above; highest +0.613; p about 0.06) |
| Test 2023-Oct 2026 | First look: +0.040. Fail | Second look: +0.374, range -0.60 to +1.43, 2 of 4 years positive. Fail |
| Statement by the plan | No predictor found | **Not confirmed** |

Baselines on 2009-2022: steady 0.000; always-early −0.062; always-late +0.062; 63-session momentum +0.028;
market-only logistic −0.153; market-only + Niño 3.4 −0.007.

### 9.5 The best rule (c86) in words
Two inputs, no fitted parameter:
1. **Pacific Ocean:** the Niño 3.4 anomaly of January. It is used from 15 February.
2. **Brazil summer heat:** the mean temperature from 1 January to the day (January to March only, 30 days minimum,
   then held) in six Arabica regions, weighted by output, minus the same quantity of the five years before.
   Weather data are used 10 days late.

Both above zero: buy early. Both below zero: buy late. Other cases: buy steadily. The call is read one time each
week. It changes about one time each year. Hypothesis: heat in the grain-fill months reduces the next harvest, and
the market takes time to price it.
Code: `research/autoresearch/candidates/c86.py`, with `lib.py` (`enso_jan`, `bra_window_var`, `agree_fp`).

Result by calendar year (saving in % of the yearly purchase cost; main call of that year):

| Year | Call | Saving | Year | Call | Saving |
|---|---|---|---|---|---|
| 2009 | steady | +0.7 | 2018 | late | +5.5 |
| 2010 | early | +7.7 | 2019 | early | +3.6 |
| 2011 | late | +3.7 | 2020 | steady | −2.2 |
| 2012 | late | +6.5 | 2021 | steady | +0.6 |
| 2013 | steady | +0.6 | 2022 | late | +4.9 |
| 2014 | steady | 0.0 | 2023 (test) | late | −1.6 |
| 2015 | early | −3.2 | 2024 (test) | early | +5.6 |
| 2016 | early | +1.2 | 2025 (test) | steady | +2.8 |
| 2017 | late | +3.1 | 2026 (test, to 9 Oct) | late | −1.3 |

Mean: 2.3% in 2009-2022, 1.5% in the test period. A "steady" year can have a saving that is not zero, because the
call of the year before runs to mid February.

### 9.6 Why c86 is not a predictor
- **It is the top of its own design.** The same rule with other reasonable settings gives 0.50 to 0.79: ERA5
  temperature +0.50, both weather products +0.60, 10-year normal +0.63, window Dec-Feb +0.63, maximum temperature
  +0.68, weather 4 days old +0.71, seasonal ENSO +0.74, Minas Gerais only +0.78. The careful settings give about
  0.60, which is below the bar of 0.712 and below the best placebo run.
- **Few calls.** About 9 active yearly calls in 14 years, and 4 in the test period.
- **No skill before 2009.** In 2001-2008 it agreed with the label on 51% of its active days (71% in 2009-2022).
  The Brazil heat sign alone agreed on 42% of days before 2009. Only the ENSO sign was stable.
- **The order of the runs decided the winner.** c86 passed the step rule by a margin of 0.005.
- **The score fell by half on new data** (0.79 to 0.37). This is what selection from many trials gives.

### 9.7 Best score of each model type (2009-2022)
| Model type | Best version | Fitted to data? | Best RATIO |
|---|---|---|---|
| Rule, two fixed questions | ENSO and Brazil Jan-Mar heat agree (c86) | No | +0.79 |
| Rule, three fixed questions | ENSO, Brazil heat and market trend all agree (c94) | No | +0.72 |
| Rule, one fixed question | Brazil Jan-Mar heat alone (c48) | No | +0.69 |
| Rule, one fixed question | ENSO alone, real events only (c74); January state held for a year (c71) | No | +0.42; +0.39 |
| Trend rule, fixed sign | Slow trend of five markets (c42) | No | +0.34 |
| Logistic regression | 4 signals (c15); two more versions | Yes | +0.31; +0.02; +0.06 |
| Decision tree, depth 2 | 3 inputs (c76) | Yes | +0.03 |
| Random forest | 16 features (c16) | Yes | −0.02 |
| LightGBM | 15 features (c17) | Yes | −0.33 |
| XGBoost | Not run in the loop. Earlier study, other score (section 7.2) | Yes | Sharpe +0.28 at best; −0.20 for the model named before the run |

Why a fixed rule and not a fitted model: 14 years hold about 56 independent quarters, and the signal changes one
time a year, so a fitted model sees about 14 examples. Relations flip between periods, so a fitted model learns
the old sign. The plan permitted XGBoost in the loop; after LightGBM and the random forest failed, no iteration
was spent on it.

### 9.8 What the 100 iterations show, by block
| Block | Best RATIO | Verdict |
|---|---|---|
| ENSO winter state + Brazil Jan-Mar heat | +0.79 (careful settings +0.60) | Lead; not confirmed |
| Brazil Jan-Mar heat alone | +0.69 (ERA5 +0.45) | Skill on 2009-2022 only; opposite sign before 2009 |
| ENSO winter state alone, held for a year | +0.42 | Weak; the only signal with the same sign in 2001-2022 |
| Votes of ENSO, Brazil heat and slow market trend | +0.67 | Most even over time; below the bar |
| Slow trend of five markets (sugar, Brazil equities, copper, dollar, coffee) | +0.34 | Small and stable |
| Other weather: 90-day stress, season heat, soil moisture, other origins | +0.61 | Mostly the same ENSO-linked warmth; failed placebo and test |
| Water stress: rain, soil moisture, water balance | +0.41 (water balance +0.09) | No stable skill. The signal is temperature, not water |
| Price factors: trend, carry, value, price in reais | +0.09 | No skill |
| CFTC positioning, export flow, stocks, calendar, currencies, rates, VIX | +0.27 | No stable skill |
| Climate indices as monthly states (ENSO, Indian Ocean Dipole) | 0.00 | No skill in this form |
| Fitted models | +0.31 | All worse than rules with a fixed sign |

Three falsification tests (iterations 34, 68, 92) support that Brazil adds information to the ENSO state on
2009-2022: the heat of regions with no crop reason gave −0.07 and +0.33 alone, and nothing on top of ENSO.

### 9.9 Deviations and errors (all in the trial log)
1. The roll repair was made after iteration 2 with no stop. The plan said: stop and ask. Celine accepted it later.
2. Three void iterations: 2 (the feature was not carry), 35 and 36 (incomplete Brazil export file; agent error).
3. The test period was scored two times (c22 after iteration 30, c86 after iteration 100). The agent had seen the
   first result before the second look, and it knows coffee history to mid-2026. A second look is weaker evidence.
4. Iteration 16: one feature had a data gap, so training started in 2006. It counted.
5. Choices that the agent made with no run (which ideas to try) are not counted in N.

### 9.10 New data in the loop (24 data cards in `research/autoresearch/data_cards/`)
NASA POWER (soil moisture, humidity, radiation; three Vietnam regions); ERA5 through Open-Meteo (6 Brazil nodes);
NOAA (Niño 3.4, Dipole Mode Index); USDA PSD; Brazil MDIC Comex Stat (monthly coffee exports: volume and unit
value); World Bank monthly prices (robusta, spread); Yahoo (dollar index, sugar, cocoa, cotton, corn, soybeans,
crude oil, gold, copper, Brazil equity fund, S&P 500, VIX, US 10-year yield, USD/COP).
Rule for a new source (addendum 2): public agency or the vendor already in use; no account or key; data files
only; history from 2004 or before; a data card with the publication delay before the first use; raw files stay
local with a sha256.

### 9.11 Files
| File | Content |
|---|---|
| `core.py` | The eval and the harness: data access with a cutoff, labels, walk-forward refits, score, constraints, trial log. One logged repair (revision 1) |
| `lib.py` | Feature and model helpers for the candidates |
| `candidates/c01.py` to `c100.py` | One file for each iteration: hypothesis, change, expected effect, features, model |
| `trial_log.jsonl` | 227 rows, hash chain |
| `JOURNAL.md` | Reflection after each iteration (1,042 lines) |
| `results/iteration_table.md`, `.csv` | One row for each iteration |
| `results/hillclimb.png` | Report graph, with the line "RATIO necessary" (the plan requires it) |
| `results/hillclimb_slide.png` | Slide version. The line "RATIO necessary" was removed on 15 Nov at Celine's instruction |
| `results/figures/` | Slide figures and `yearly_c86.csv` |
| `selftest.py`, `make_report.py`, `make_figures.py`, `export_dashboard.py` | Harness checks, report, figures, dashboard inputs |
| `run.sh`, `it.sh`, `newc.sh` | Shell helpers. `it.sh` needs the variable `MINI` (the SSH login of the compute machine; it is not in the repository) |

---

## 10. Defect in the price series, and errata

### 10.1 The defect
The price file has 134 days with `suspected_roll_flag`. These days are the **last day of the old contract**. The
price gap between the old and the new contract is in the **next session**: +1.1% on average (+2.9% in 2000-2004,
+2.3% in 2017-2020, −0.7% in 2021-2026). The first roll adjustment set only the marked day to zero. Thus the gaps
stayed in the returns.

### 10.2 The repair (eval revision 1, `ROLL_FIX=1`)
The return is set to zero on each marked day and on the next session (268 sessions). The choice was made from the
gap statistics only, before a candidate was scored with it. Not repaired: rolls that the file does not mark, and
the exact day of each gap. The Yahoo chain stays an unverified series.

### 10.3 Effect on the studies of 14 Nov
| Study | First result | With the repair |
|---|---|---|
| ENSO direction test, 21 sessions | 3 of 4 bars met; hit rate 55.9% | **0 of 4 bars; hit rate 50.4%.** The result of 14 Nov is withdrawn |
| Direction study | All bars fail; 2 secondary weather leads | All bars fail; the 2 leads are gone |
| XGBoost on multi-origin weather | No alpha | No change of the verdict |

Each results file has an erratum at its end. The aggregate results of the second runs are in the folders
`results_rollfix/` and `results_enso_cftc_rollfix/`.

### 10.4 Not checked: V4 and V5 labels (action for Moonwon)
V4 and V5 labels use price levels of the same series ("a close at or above +10%"). A contract gap in the session
after a marked day can make a touch or remove a touch. The effect was not measured. The earlier label checks
(thin trading, liquidity mask) are in `docs/V5_DATA_NOTES.md` and section 5. The volatility gauge and its Brier
numbers were also not calculated again.

---

## 11. Buyer dashboard (`research/prototype/`)

### 11.1 Version of 14 Nov (v0)
One offline HTML page: volatility gauge (59% for +10% in 3 months on 12 Nov), 16-day weather forecast for the six
Brazil regions (frost and dryness flags), replay of the 2021 frost forecasts, Brier bars and a calibration table.
Files in the repository: `template.html`, `fetch_demo_data.py`. Its build script was not kept.

### 11.2 Version of 15 Nov (current)
The user asked for the dashboard to use the best algorithm of the autoresearch loop. The page keeps the colors and
the style of v0. The weather forecast panel, the frost replay and the model bars were removed.

| Section of the page | Content |
|---|---|
| This week's call | A dial with three states (buy late / steady / buy early), the two inputs, the date of the next review. First screen has the label "Research signal · not confirmed on new data" |
| Order planner | Inputs: monthly need (60 kg bags), cover now (months), futures price. Output: what to do, bags moved, their value, the effect of a 10% price move. Cover targets: late 0 months, steady 1.5, early 3 |
| How the call is made | The two questions; a chart of each year 2009-2026 on the two inputs; two sliders to try other readings; the dates on which the call can change; the heat reading of the season day by day |
| What the rule did | Weekly price 2009-2026 with the calls as bands; saving by year; table |
| How far to trust the call | Development +0.79 (passed), shifted-data test 0 of 17 (passed), new data +0.37 (not confirmed); five limits |
| Market roughness | The volatility gauge of v0 as a second reading (numbers of 12 Nov, not calculated again) |

Call for the week of 16 Nov 2026: **buy late** (Niño 3.4 of January 2026: −0.54 °C; Brazil Jan-Mar 2026 heat:
−0.38 °C). The call holds until the first heat reading of 2027 (9 Feb 2027). Note: the "late" call of 2026 lost
1.3% of the yearly cost to 9 Oct 2026.

### 11.3 How it is built
| File | Content |
|---|---|
| `src/engine.js` | Rule c86 and the order planner in JavaScript. No DOM. The page and the tests use the same file |
| `src/template.html` | Layout, charts (inline SVG), text |
| `build.py` | Puts the engine and the data into one HTML file. `--check` tells if the built file is up to date |
| `tests/engine.test.mjs` | 14 tests: the rule on made-up inputs; parity with the Python harness |
| `tests/page.test.mjs` | 8 tests of the built page in a DOM (jsdom): five dates, planner, sliders, hover |
| `research/autoresearch/export_dashboard.py` | Writes the inputs from the saved run of `core.py final c86`. It does not score the test period again |

Checks of 15 Nov:
- The JavaScript rule gives the same weekly position as the Python harness on each of 4,495 sessions (Dec 2008 to
  9 Oct 2026). Both inputs agree on each session.
- One week differs between the pure rule and the harness: 11 Nov 2016 has no usable close, so the harness holds
  "steady" for that week. A test includes this case.
- 22 of 22 tests pass with the local data. In the repository with no data, 5 tests run and 17 are skipped.

### 11.4 What is local only
`data/` (rule inputs, weekly closes, parity fixture, gauge numbers), `demo_data/` and the built page contain rows
from third parties. They are in `.gitignore`. **Moonwon cannot build the page from the repository alone.** Celine
must send the built page or the three data files by a private channel.

Limits: amounts are for the futures part of the price only. For future dates the page takes Friday as the last
session of the week. The page gives no call when its data end before the date.

---

## 12. Slide deck
Google Slides, "Final Presentation", Luxe theme, 23 slides. Celine owns the deck and does the final count of slides.
The link is not in this public repository. Ask Celine for the link and for access.

| # | Slide | # | Slide |
|---|---|---|---|
| 1 | Title | 13 | Hill-climb graph of the 100 iterations |
| 2 | Summary with three numbers | 14 | Best score of each idea family (bar chart) |
| 3 | Project path, V1 to the loop (block diagram) | 15 | What worked and what did not |
| 4 | The buyer's choice and the design choices | 16 | The final rule |
| 5 | The label (illustration) | 17 | Saving by year |
| 6 | The score | 18 | Best score of each model type (table) |
| 7 | The eval: periods and the bar that rises | 19 | Why two fixed questions and not a fitted model |
| 8 | Walk-forward (chart) | 20 | Verdict: passed development and placebo, not confirmed |
| 9 | Seven guards against gaming the score | 21 | Ranges of development, placebo and test |
| 10 | The loop | 22 | Price-series defect |
| 11 | The harness (block diagram) | 23 | Conclusion and next steps |
| 12 | The 28 data series in five groups | | |

Facts about the deck:
- It covers the autoresearch track. It has no section "Responsible AI" and no recap of the midterm. The course asks
  for these sections (`docs/HANDOFF_2026-11-14.md`, section 1). Celine builds the remaining parts.
- Slide 13: the line "RATIO necessary" was removed at Celine's instruction. The necessary score (0.71) is in words on
  slides 2, 7, 9, 18 and 20, and as a line on slide 14.
- Slide 3 names the current dashboard: weekly buy call from the final rule, order planner, risk gauge (corrected on 15 Nov).
- Chart images come from `research/autoresearch/results/` on `main`. Two illustrations (label, contract gap) use
  made-up prices and say so.

---

## 13. Repository state

### 13.1 Branches and CI
- `main` = `v5-weather`. The last commit before this document is `ca5670b`. Pull request 1 shows as merged.
- The merge commit is `98770f2` ("Merge v5-weather", `--no-ff`), 15 Nov, with no review. Celine's instruction was:
  no pull request, merge directly.
- CI ("Public repository checks"): install passes, `pytest` passes, `scripts/check_publication.py` fails, the build
  step is skipped. The check fails because the new files are not in the allowlist and because `README.md` and
  `.gitignore` changed after the publication review. The allowlist is Moonwon's decision.
- The repository holds no third-party rows: no prices, no weather rows, no CFTC rows, no row-level outputs. Files with
  the prefix `LOCAL_ONLY_` and the folders `research/autoresearch/{out,data}` are in `.gitignore`.
- Commits by AI assistance have the trailer `Co-Authored-By: Claude ...`.

### 13.2 Commits since V4 (newest first)
| Commit | Content |
|---|---|
| `ca5670b` | Slide graph of the hill-climb without the line "RATIO necessary" |
| `ba15f1b`, `e9c4f4b`, `8333721`, `a99df45` | Dashboard of 15 Nov: docs, page + build + page tests, rule engine + tests, export script |
| `dfb602d`, `f75ba12`, `83ec919` | Slide figures and their script |
| `98770f2` | Merge of `v5-weather` into `main` |
| `f6dcbb3`, `afbd117` | `AGENTS.md`, `CLAUDE.md`, `README.md`; handoff of 15 Nov |
| `4d45b15` | Errata: three studies run again with the roll repair |
| `c996fc7`, `5cb819e`, `a7e7a66`, `b4beae1`, `4788e67`, `44d51c2`, `a2f371c`, `d1423c3` | Autoresearch: results, log and journal, candidates 31-100 + addendum 2, addendum 1, candidates 1-30, data cards, eval and harness, plan |
| `ec6b135`, `d5d831b`, `b423817` | ENSO + CFTC test, direction study, XGBoost study (work of 14 Nov, committed on 15 Nov) |
| `4f8fe8d` | `.gitignore` for row-level outputs |
| `5f80fbf` | Exploratory studies of 12-14 Nov, agent docs, handoff of 14 Nov, README status section |
| `1b8bb64` to `57b8255` | V5: data notes, docs, runner, uncertainty, model A3, labels, data tools (7 commits, 12 Nov) |

The commits of 15 Nov group the file states of that day. They are not snapshots of each hour of work.

### 13.3 Layout
| Path | Content | Owner |
|---|---|---|
| `signal_origin/` | V4 modules (not changed) + V5 modules `v5.py`, `v5_labels.py`, `crop_weather.py`, `uncertainty.py`, `synthetic_v5.py` | Moonwon / Celine |
| `configs/` | `v5_spec.json` (DRAFT), `v5_crop_windows.json` (DRAFT), `v5_regions.csv`, `v6_arabica_world_nodes.csv` | Celine |
| `data_tools/` | Local data pulls and checks | Celine |
| `research/exploratory/` | Six study folders: PLAN, code, aggregate results, errata | Celine |
| `research/autoresearch/` | The loop (section 9.11) | Celine |
| `research/prototype/` | The dashboard (section 11) | Celine |
| `docs/` | `HANDOFF.md`, `HANDOFF_2026-11-14.md`, `V5_CHANGES.md`, `V5_DATA_NOTES.md`, `V5_LOCAL_PREVIEW_2026-11-12.md`, and the V4 docs | both |
| `AGENTS.md`, `CLAUDE.md` | Rules for agents | Celine |

### 13.4 Commands
```bash
# V4 and V5 package
pip install -r requirements-lock.txt && pip install --no-deps --no-build-isolation -e .
python -m pytest -q                                   # 203 tests
python -m signal_origin.experiment synthetic          # V4, byte-identical to 12 Nov
python -m signal_origin.v5 synthetic --out runs/v5-synthetic
python -m signal_origin.v5 run --spec configs/v5_spec.json ... --dry-run      # full line: docs/V5_CHANGES.md

# Autoresearch (in research/autoresearch, with the local data; see its README.md)
./run.sh selftest.py                                  # harness checks
./run.sh core.py iter candidates/c86.py               # do NOT run: N is used (section 15)

# Dashboard (in research/prototype)
python3 build.py                                      # needs the local data/
node --test tests/*.test.mjs                          # page tests need jsdom
```

---

## 14. Data inputs (all outside the repository)
| Input | Where it is | Notes |
|---|---|---|
| KC=F closes 2000 to 9 Oct 2026, session calendar, metadata | Moonwon's handoff bundle (V4 archive); a copy is on Celine's compute machine | Unverified calendar. The roll flag marks the last day of the old contract (section 10) |
| Single-point weather features | Same archive | V1 to V4 model A1 |
| Six-region POWER daily, 1981 to Nov 2026 | Celine's machine | `data_tools/pull_power_regions.py` |
| 37-node POWER daily, 1981 to 13 Nov 2026 | Celine's machine | `configs/v6_arabica_world_nodes.csv` |
| CFTC disaggregated, Coffee C | Celine's machine | publicreporting.cftc.gov, table `72hh-3qpy` |
| Niño 3.4 monthly | Celine's machine | NOAA CPC `sstoi.indices` |
| The 24 sources of the loop | Celine's compute machine | One data card each; `fetch_*.py` scripts in `research/autoresearch/` |
| Recent KC=F, forecast archive, forecast snapshot | Celine's machine | `research/prototype/fetch_demo_data.py` |
| Dashboard inputs and the built page | Celine's machine | Section 11.4 |

---

## 15. Rules that are in force (for each agent)
1. Do not score the test period 2023 to Oct 2026 again. It has two looks.
2. Do not run more iterations on 2009-2022. N is 110 on these years.
3. Do not present rule c86 as a working strategy. The correct words: "passed development and placebo, not confirmed
   in the test period".
4. Do not commit third-party rows. Aggregates, plans, code and configs are permitted.
5. Do not edit the V4 modules. Add new modules. V4 synthetic outputs must stay byte-identical.
6. Do not bypass the V5 sign-off gate, and do not fill in names in `configs/v5_spec.json`.
7. Do not edit `publication_manifest.json` unless Moonwon asks.
8. Write a `PLAN.md` with a sha256 before each new study. Label each choice after the results as exploratory.
9. Do not start a new signal search on the same years. Each more variant mainly raises the risk of a false positive.

---

## 16. Decisions and actions for Moonwon
| # | Item | Detail | Urgency |
|---|---|---|---|
| 1 | Review the merge into `main` | It was made with no review. To undo: section 3 | Before 18 Nov |
| 2 | Publication allowlist | CI is red only for this check. Decide: add the new files, or keep the check red, or move the research folders out of the public package. Also decide if `configs/*.csv` with Conab figures are permitted | Before the repository is shown as final |
| 3 | Roll defect and the V4 / V5 labels | Count the labels that change when the session after each marked roll day is excluded or adjusted. Section 10.4 | Before a new claim on V4 or V5 numbers |
| 4 | V5 sign-off | Sign off and run the official V5, or cite the preview as exploratory. Six points in section 6.6, plus the roll point | Before 18 Nov if V5 numbers go in the deck |
| 5 | The story for the presentation | Negative result with one lead (ENSO), one data defect found, a dashboard with the label "not confirmed". Agree or change | Before the rehearsal |
| 6 | Deck parts that are not there | Recap of the midterm, Data & Model for V1 to V5, Responsible AI. The team builds them together | Before 18 Nov |
| 7 | Dashboard | Ask Celine for the built page. Decide if the gauge section stays (its numbers were not calculated again) | Before the demo |
| 8 | Withdrawn result | If the ENSO result of 14 Nov ("3 of 4 bars") is in any note or draft, remove it. Section 10.3 | Now |

Next steps if the work continues after the course:
1. Test the ENSO winter rule on coffee prices before 2000, with a new plan written before the data are seen. It is
   the only test that can add evidence, because the rule makes one call a year.
2. Verify the price chain (exchange data in place of the Yahoo chain) and mark each roll.
3. Untested and plausible sources: weather-forecast archives, satellite crop health, Conab estimate revisions,
   ICE certified stocks, option-implied volatility.

---

## 17. Glossary
| Term | Meaning |
|---|---|
| B0, B1, A1, A2, F1, FW1, FW2 | V4 models, as in `README.md`: historical frequency; price features; B1 + rain and temperature anomalies; B1 + dry spell and temperature anomaly; B1 + freight changes; A1 + freight; A2 + freight |
| A3 | V5 model: B1 + six-region crop-stage weather |
| V0 or "gauge" | The volatility gauge formula of section 7.1. (In the weather-to-volatility study, V0 is "persistence") |
| Touch target | "A close at or above +k% within h sessions" (V4, V5, gauge) |
| Buy-timing target | "Mean price of the next 63 sessions above the price of today" (autoresearch) |
| Position, call | +1 buy early, 0 buy steadily, −1 buy late |
| RATIO | Yearly mean saving against steady buying ÷ its standard deviation. Steady buying = 0 |
| SCORE | RATIO − 0.28 × Emax(N). Positive = above the best of N trials with no skill |
| N | 10 + number of scored iterations. 110 at the end |
| Development years | 2009-2022, used for selection |
| Test period | 2 Jan 2023 to 9 Oct 2026, not used for selection, two looks |
| Placebo (C6) | The same candidate with alt data shifted by 2 to 18 whole years |
| Void | A scored candidate whose feature does not measure its hypothesis. It counts in N. It cannot be the best |
| c22, c86 | Best candidates after 30 and after 100 iterations |
| ENSO, Niño 3.4 | El Niño / La Niña state; the sea-surface temperature anomaly of the Niño 3.4 region |
| Eval revision 1, `ROLL_FIX=1` | The repaired roll adjustment (section 10.2) |
| Range | 95% block-bootstrap range, not a significance test |

---

## 18. What is not verified
- The Yahoo KC=F chain and the exchange calendar.
- The effect of the roll defect on V4 and V5 labels, on the gauge, and on studies 2, 3 and 4 of section 7.
- The official V5 run (the spec is a draft).
- The log of the weather latency logger.
- Real-time weather: all backtests use final, revised weather values. The two weather products (POWER, ERA5)
  disagree in some years.
- "0 of 17 placebo runs" is at best p of about 0.06, and the 17 shifts are not independent.
- The test period is not fully clean: earlier studies had 2023-2026 in their results, and the agent knows coffee
  history to mid-2026.
- The score of the loop covers the futures part of the price only: no differentials, storage, interest or lot sizes.

*Prepared by Claude (Anthropic) with Celine Yang. AI assistance: code, analysis and this document were drafted with
Claude at Celine's request. Both teammates stay responsible for the review and for the claims.*
