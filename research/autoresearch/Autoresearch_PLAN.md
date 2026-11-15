# Autoresearch loop: when to buy coffee. Plan and evals.

Status: APPROVED by Celine on 15 Nov 2026 ("Once done planning, autoresearch on this over 30 iterations").
The defaults of section 13 are in force. The sha256 of this file is in the trial log, recorded before the
baselines were scored. The fixed parts do not change.

## 1. Problem
User: the purchasing team of a coffee trader. The team must buy its volume. It selects only the time.
Question: each week, must the team buy early, buy steadily, or buy late?
One track. Horizon: 63 sessions (about three months).

Target (label for training and for the reported values):
`y(t) = 1` if the mean roll-adjusted log price of sessions t+1 to t+63 is higher than the log price at t.
In words: "buying now is cheaper than steady buying during the next quarter". Regression models can use the
continuous value `g(t) = mean(L(t+1..t+63)) - L(t)`.

Price series: archived KC=F closes, 3 Jan 2000 to 9 Oct 2026. `L` is the cumulative daily log return with the
134 suspected roll days set to zero. Missing closes (26) are carried forward for returns. Dates with a
missing close are not forecast dates.

## 2. Decision output
- A candidate gives `q(t)` for each session: +1 (buy early), 0 (steady), -1 (buy late). No other values.
- The harness reads `q` on the last session of each calendar week and holds it until the next decision day.
  This held value is the position `p(t)`. Thus the position changes one time each week at most.
- Baseline: steady buying, `p = 0`. Assumptions: prices are fixed against futures; cover can move between
  0 and 3 months (plus or minus 1.5 months around the baseline).

## 3. Score (the only value that the loop climbs)
```
saving(t) = p(t-1) * r(t)  -  0.0005 * |p(t-1) - p(t-2)|       r = roll-adjusted daily log return
RATIO     = mean(saving) / std(saving) * sqrt(252)             (RATIO of steady buying = 0)
SCORE     = RATIO - 0.28 * Emax(N)                             N = 10 + iteration number
```
- Scored period: walk-forward test years 2009-2022 (3,526 sessions, 14.0 years).
- 0.28 is the standard error of RATIO for a model with no skill (1/sqrt(14) = 0.267, plus 5% for fat tails).
- `Emax(N)` is the expected maximum of N standard normal values: 1.539 (N = 10), 1.867 (20), 2.043 (30),
  2.161 (40).
- N starts at 10 because earlier studies already tested models on these years.

| Iteration | N | RATIO necessary for SCORE > 0 |
|---|---|---|
| 0 (baselines) | 10 | 0.43 |
| 10 | 20 | 0.52 |
| 20 | 30 | 0.57 |
| 30 | 40 | 0.61 |

## 4. Walk-forward protocol (fixed)
- One refit for each test year Y. Training rows: all rows whose label end date (t+63) is before the first
  session of Y. Expanding window. Training starts at the first row where all features of the candidate exist.
- Everything that is fitted (scalers, PCA, thresholds, models, inner selection) uses training rows only.
- Random models: mean of 5 seeds (590-594).
- Loop mode: the harness deletes all rows of all tables after 31 Dec 2022 before candidate code runs.
  The candidate cannot see the test period.

## 5. Constraints on a candidate
A candidate is a "predictor (development)" only if SCORE > 0 and all of these are true.

| # | Constraint | Threshold |
|---|---|---|
| C1 | Leak test: features at dates <= T are identical when data after T are deleted (T = 29 Jun 2012, 30 Jun 2017, 30 Jun 2021) | Exact match (1e-12) |
| C2 | RATIO minus the best of always-early, always-late, steady | > 0 |
| C3 | RATIO in 2009-2015 and in 2016-2022 | > 0 in each |
| C4 | Years with a positive total saving | >= 8 of 14 |
| C5 | RATIO with a cost of 10 basis points | > 0 |
| C6 | Placebo: alt-data features rotated by k = 2..18 years (17 runs). Only for candidates with alt data. | Real RATIO above all 17 (p about 0.06) |
| C7 | RATIO | < 1.5. A larger value starts a leak audit before a claim. |

C1 runs in each iteration. A candidate that fails C1 gets no score, but the iteration is counted.
C6 runs one time, for the best candidate at the end of the loop. It is not an iteration.
Correction: I said "100 rotated runs" before. Whole-year rotation gives only about 17 valid runs.

Labels for a predictor:
- "alt-data value": C6 is satisfied, and RATIO is above the RATIO of the same candidate without its
  alt-data features (one more run, not an iteration).
- "price signal": all other cases. Features from the "other markets" group are market data, not alt data.

## 6. Final test (not for hill-climbing)
- Period: 2 Jan 2023 to 9 Oct 2026 (947 sessions, 3.8 years). Same protocol, refits for 2023-2026.
- One look, with `eval.py --final`, for the best candidate after iteration 30. Each use goes in the log.
- Pass: RATIO > 0.5. A no-skill model passes in about 18% of cases; a true RATIO of 0.8 passes in about 71%.

| Development | Final test | Statement |
|---|---|---|
| Pass | Pass | "Predictor confirmed" |
| Pass | Fail | "Not confirmed" |
| Fail | (one look permitted, labelled exploratory) | "No predictor found" |

## 7. Reported values (they do not steer the loop)
- Percent of yearly purchase cost saved = mean(saving) * 252 * 12.5%.
- AUROC of the candidate's probability against `y`. Hit rate on days with `p` not 0, and the share of such days.
- Recall of large rises: of the days where the highest close of the next 63 sessions is >= 10% above today,
  the share with `p = +1`. Reported with precision and with the share of all days that have `p = +1`.
- Alpha (annualised) and beta from the regression of `saving` on `r`.
- Block-bootstrap range of RATIO (block 63, 2,000 draws, seed 590).

## 8. Search space (what the agent can change)
| Variable | Permitted range |
|---|---|
| Data | Files on the Mac mini (Coffee C prices, USD/BRL, NASA POWER 37 nodes, Nino 3.4, CFTC) and the whitelist below. Maximum 6 new sources. |
| Features | Maximum 20 for each model. Windows of 5, 21, 63, 126, 252 sessions (1, 3, 6, 12 months for monthly data). Lags, changes, season masks, products of two features, PCA components (fitted on training rows). |
| Model | Rule on one feature; logistic or ridge regression; tree-based methods: decision tree, random forest, ExtraTrees, XGBoost, LightGBM, CatBoost, HistGradientBoosting. Boosted trees: depth <= 3, <= 500 trees. Forests: depth <= 6, <= 500 trees, >= 20 rows in a leaf. Mean of up to 3 logged candidates. |
| Inner selection | Permitted on training rows only (time-ordered folds, maximum 20 settings). It is part of one iteration. |
| Position rule | `q = +1` if probability > 0.5 + d; `q = -1` if probability < 0.5 - d; else 0. d = 0, 0.05 or 0.10. Probability smoothed over 1, 5 or 21 sessions. |

Not permitted: neural networks; monotone constraints; a horizon other than 63 sessions; positions other than
-1, 0, +1; a change to sections 1-7.

### Whitelist of new sources (approved by Celine, 15 Nov; access from the Mac mini tested, all HTTP 200)
| Group | Source (each line item is one source) | Type | Minimum delay before use |
|---|---|---|---|
| Climate indices | NOAA: SOI; ONI; Indian Ocean Dipole (DMI); PDO; MJO | Alt data | Monthly: 15th of the next month. MJO: 5 days. |
| Weather | NASA POWER, 37 current nodes: humidity, root-zone soil moisture, solar radiation (one source) | Alt data | 4 calendar days |
| Supply and stocks | USDA PSD coffee tables | Alt data | Only values for marketing years that ended >= 12 months before t (the file holds revised values) |
| Other markets | Yahoo: sugar, cocoa, crude oil, dollar index, Colombian peso (one source each); World Bank monthly prices | Market data | Yahoo: through t-1. World Bank: 15th of the next month. |

Removed: NOAA AMO (the file ends in 2023).
Rules for a new source:
- Data card before first use: publisher, URL, first date, publication delay, revision policy. The card can
  make the delay longer, not shorter.
- History must start in 2004 or before.
- Free public files only. No accounts, forms, or paid data. No personal details in a request.
- Raw files stay on the Mac mini with a sha256. No third-party rows go into the repository.
- A source outside the whitelist stops the loop. The agent asks Celine.

## 9. Loop protocol (30 iterations, agent: Claude)
One iteration = one hypothesis = one candidate = one scored run. No grids. Each run that shows a score counts.
1. Read the trial log.
2. Write in the log, before the run: id, parent candidate, hypothesis (one sentence with an economic reason),
   the exact change, the expected direction of the effect.
3. Run the harness on the Mac mini (maximum 10 minutes).
4. `eval.py` writes the score, C1-C5, C7 and the reported values to the log.
5. Step rule: the candidate becomes the new best if it satisfies C1 and the 20th percentile of the paired
   block-bootstrap difference (RATIO of candidate minus RATIO of current best; block 63, 2,000 draws, seed
   590) is above zero. If not, the current best stays.
6. A crash before a score is shown can be repaired and run again. It is not counted.
7. Reflection (Celine's instruction): after each iteration, the agent writes in `JOURNAL.md` what the result
   shows, what worked and what did not, and the curated plan for the next iteration (the idea queue, in order).

Baselines (scored before iteration 1; they are part of the N start of 10):
B0 steady; B1 always-early; B2 always-late; B3 momentum (sign of the 63-session return);
B4 market-only (logistic regression, C = 1, 13 market features of the Direction study);
B5 market-only + Nino 3.4 level and 3-month change. The first "current best" is the baseline with the highest RATIO.

Stop and report:
- The loop runs all 30 iterations. There is no early stop on success.
- Short report to Celine after iterations 10, 20 and 30. The loop does not wait for an answer.
- The loop stops and asks Celine for: a source outside the whitelist, a change to a fixed part, a C7 leak
  audit, or a defect in `eval.py`. After a repair of `eval.py`, all logged candidates are scored again and N
  does not change.
- After iteration 30: C6 placebo and the alt-data run for the best candidate, then the final test (section 6).
- A poor result is reported as a poor result. No iteration 31.

## 10. Files
- Mac mini, `~/coffee_project/autoresearch/`: `eval.py`, `harness.py`, `candidates/`, `data_cards/`,
  `trial_log.jsonl` (append-only; each row holds the sha256 of the row before it), `out/`.
- Project folder: `04_code_and_branch/autoresearch/` (code, trial log, aggregate results only) and
  `05_studies/Autoresearch_RESULTS.md`.
- All training and scoring run on the Mac mini.
- Final deliverables: (a) a table with one row for each iteration: what changed, the result, and if it worked;
  (b) a graph of the hill-climb: RATIO of each iteration, the best RATIO to date, and the RATIO necessary for
  SCORE > 0.

## 11. Known limits
- Small sample: about 56 independent 63-session windows in 14 years. A true RATIO below about 0.6 cannot be
  shown with this design.
- The test period is not fully clean: earlier studies had 2023-2026 in their results, and the agent knows
  coffee history to mid-2026. The agent can select sources with hindsight. C6 and N are the guards.
- The score measures the futures part of the price. It does not include physical differentials, storage,
  interest, or lot sizes. Steady buying is an assumed baseline.
- A 2% loss and a 2% saving have equal weight. "Recall of large rises" reports the buyer's worst error, but
  it does not change the score.
- N = 10 at the start and the value 0.28 are judgements. Yahoo prices are an unverified chain.
- USDA, PDO and DMI files hold revised values. The delays reduce this problem but do not remove it.

## 12. Schedule
15 Nov: approval, hash, build of `eval.py` and harness, baselines. 15-16 Nov: iterations 1-30.
17 Nov: placebo, final test, results document. 18 Nov: presentation (PDF by 1:30 PM).

## 13. Defaults that Celine did not confirm in words (in force after her start command)
1. Target: mean price of the next 63 sessions (not the price on session t+63).
2. A price-only model counts as a predictor, with the label "price signal".
3. Final test: one look, pass at RATIO > 0.5.
4. Maximum 6 new sources and 20 features; cost check at 10 basis points; N start of 10.
5. Positions of -1, 0, +1 with one change each week; cover range of 0 to 3 months.
6. All 30 iterations run with no early stop; reports after iterations 10, 20 and 30.
