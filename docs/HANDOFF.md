# Signal-Origin: handoff (15 Nov 2026)

For Moonwon and for the next agent. Rules: `AGENTS.md`. The handoff of 14 Nov (V4 check, V5, volatility gauge,
dashboard, data work) is in `docs/HANDOFF_2026-11-14.md`. This file covers what changed on 14-15 Nov, with the
focus on the autoresearch loop. One file with all changes since V4 (V4 check, V5, studies, loop, defect, dashboard,
deck, repository): `docs/HANDOVER_SINCE_V4.md`.

Final presentation: Wed 18 Nov 2026, 10 minutes, PDF on Canvas by 1:30 PM. Celine has the slide deck
(Google Slides, "Final Presentation").

## 1. Status in one minute
- **No confirmed predictor.** After 100 pre-registered iterations, one rule passed the development score and
  the placebo test. The test period 2023-Oct 2026 did not confirm it.
- **One lead:** the ENSO winter state (El Nino: buy early). It is weak (+0.4), but it is the only signal with the
  same sign in all periods from 2001.
- **One defect found in the price series** (the roll adjustment). It is repaired. It changes two results of
  14 Nov (section 7).
- For the first target ("+10% touch within 63 sessions") the unfitted volatility gauge is still the only thing
  that beats the baseline (Brier 0.240 against 0.260; exploratory).

## 2. The problem was defined again (Celine, 15 Nov)
The first target ("does the price touch +10%?") did not match a decision. The new definition:

| Item | Choice | Reason |
|---|---|---|
| User | The purchasing team of a coffee trader or roaster | They must buy the volume. They select only the time |
| Decision | Each week: buy early (+1), buy steadily (0), or buy late (-1) | Three states are what a team can act on |
| Horizon | 63 sessions, one track | About 3 months: the planning time of a buyer, and the range in which cover can move (0 to 3 months) |
| Label | 1 if the mean price of the next 63 sessions is above the price of today | "Buying now is cheaper than steady buying in the next quarter" |
| Score | Cost saving against steady buying | The buyer cannot go short. Long/short Sharpe, AUROC and recall do not measure the money |

## 3. The eval (fixed before the first run; `research/autoresearch/Autoresearch_PLAN.md`)
```
saving(t) = p(t-1) * r(t) - 0.0005 * |p(t-1) - p(t-2)|     p = position (-1, 0, +1), r = daily log return
RATIO     = mean(saving) / std(saving) * sqrt(252)         steady buying = 0
SCORE     = RATIO - 0.28 * Emax(N)                         N = 10 + number of iterations
```
- `0.28` is the standard error of RATIO for a rule with no skill on 14 years. `Emax(N)` is the expected best of N
  no-skill trials. Thus the bar rises with each trial: RATIO 0.43 at the start, 0.61 after 30 iterations,
  0.71 after 100.
- Walk-forward: one refit for each year, expanding window, labels purged at the boundary.
- Scored years: 2009-2022 (3,526 sessions). Test: 2 Jan 2023 - 9 Oct 2026 (947 sessions), pass at RATIO > 0.5.

How the eval prevents reward hacking:

| Guard | What it does |
|---|---|
| Plan fingerprint | The plan was hashed (sha256) before the baselines were scored |
| Cutoff | The harness deletes all data after 31 Dec 2022 before candidate code runs |
| C1 leak test | Features at dates before T must be identical when data after T are deleted (3 dates, exact) |
| Trial penalty | Each scored run raises N, and N raises the bar. A crash does not count; a void run does |
| Step rule | A candidate replaces the best only if a paired block bootstrap shows a gain (20th percentile > 0) |
| C2-C5 | Must beat always-early and always-late, both halves positive, 8 of 14 years positive, positive at double cost |
| C6 placebo | Alt data rotated by 2 to 18 years (17 runs). The real data must beat all 17 |
| C7 | RATIO above 1.5 starts a leak audit before a claim |
| Void rule | A candidate whose feature does not measure its hypothesis cannot become the best |
| Trial log | Append-only, each row holds the sha256 of the row before it. Hypothesis is logged before the run |
| Test period | Not used for selection. Each look is logged. Two looks were made (section 4) |

## 4. Result (`research/autoresearch/Autoresearch_RESULTS.md`)
| Step | Iterations 1-30 (best: c22) | Iterations 31-100 (best: c86) |
|---|---|---|
| RATIO on 2009-2022 | +0.612 (necessary 0.605) | +0.787 (necessary 0.712) |
| Placebo (17 runs) | Failed (1 above) | Passed (0 above; highest +0.613) |
| Test 2023-Oct 2026 | +0.040, fail | +0.374 (range -0.60 to +1.43), fail (limit 0.5) |
| Statement by the plan | No predictor found | Not confirmed |

**The rule of iteration 86 in words.** In mid February, read two values:
1. the Nino 3.4 index of January (above zero = warm);
2. the mean temperature of January-March to date in the Brazilian coffee regions (6 nodes, weighted by
   output), against the same period of the last 5 years. Weather data are used 10 days late.

Both warm: buy early for the next 12 months. Both cool: buy late. They disagree: buy steadily. Value 2 is
updated until the end of March. The rule makes about one call a year. It has no fitted parameters.

On 2009-2022: 11 of 14 years positive, both halves +0.79 / +0.78, hit rate 70%, 2.3% of the yearly purchase
cost saved. In the test period: 2023 "late", wrong; 2024 "early", correct; 2025 "early" until mid February,
correct; 2026 "late", wrong.

**Why it is not a predictor:**
- It is the top of its own design. Other reasonable settings give 0.50 to 0.79. Careful settings (two weather
  products, seasonal ENSO) give about 0.60: below the bar of 0.712 and below the best placebo run.
- About 9 active yearly calls in 14 years, and 4 in the test period.
- No skill before 2009: in 2001-2008 it agreed with the label on 51% of its active days (71% in 2009-2022).
  The Brazil heat sign alone was opposite before 2009.
- The order of the runs decided which setting became "the best" (it passed the step rule by a margin of 0.005).

## 5. What worked and what did not (100 iterations)
| Block | Best RATIO | Verdict |
|---|---|---|
| ENSO winter state + Brazil Jan-Mar temperature (two-state rule) | +0.79 (careful +0.60) | Lead; not confirmed |
| ENSO winter state alone, held for a year | +0.39 to +0.42 | Weak; the only stable sign in 2001-2022 |
| Votes of ENSO, Brazil heat and slow market trend | +0.67 | Most even over time; below the bar |
| Slow trend of five markets (sugar, Brazil equities, copper, dollar, coffee) | +0.34 | Small and stable |
| Brazil weather as "news against the recent climate" (90-day stress, season heat) | +0.61 | Worked on 2009-2022; failed placebo and test |
| Water stress: rain, soil moisture, water balance | +0.41 (water balance +0.09) | No stable skill. The signal is temperature |
| Price trend, carry, value, price in reais | +0.09 | No skill |
| CFTC positioning, export flow, stocks, calendar, currencies, rates, VIX | +0.27 | No stable skill |
| Fitted models | +0.31 | All worse than rules with a fixed sign |

**Fitted models, in detail.** Logistic regression (+0.31, +0.02, +0.06), random forest (-0.02), LightGBM
(-0.33), depth-2 decision tree (+0.03). The final rule is not a fitted model and not XGBoost. Reason: 14 years
hold about 56 independent 63-session windows, and the best signals change one time a year. A tree model has too
few independent examples and learns relations that flip between periods. XGBoost was used in the three studies
of 14 Nov (section 7); it gave no edge there. The plan permitted XGBoost in the loop with no monotone
constraints; after LightGBM and the random forest failed, no iteration was spent on it.

Graph: `research/autoresearch/results/hillclimb.png`. Table of all iterations:
`research/autoresearch/results/iteration_table.md`. Reflection after each iteration: `JOURNAL.md`.

## 6. Deviations and errors (all in the trial log)
1. The roll repair was made after iteration 2 with no stop (the plan said: stop and ask). Celine accepted it later.
2. Three void iterations: 2 (the feature was not carry), 35 and 36 (incomplete Brazil export file; agent error).
3. The test period was scored two times (c22 after iteration 30, c86 after iteration 100). The agent had seen
   the first result before the second look, and it knows coffee history to mid-2026.
4. Choices that the agent made with no run (which ideas to try) are not counted in N.

## 7. Defect in the price series and errata for the 14 Nov studies
The 134 `suspected_roll_flag` days mark the last day of the OLD contract. The gap between contracts is in the
NEXT session (mean +1.1%; +2.9% in 2000-04, -0.7% in 2021-26). The first roll adjustment set only the marked day
to zero, so the gaps stayed in the returns. The repair sets both days to zero (268 sessions). The three studies
of 14 Nov were run again with `ROLL_FIX=1`. Each results file has an erratum.

| Study (14 Nov) | First result | With the repair |
|---|---|---|
| ENSO direction test, 21 sessions | 3 of 4 bars met; hit rate 55.9% | 0 of 4 bars; hit rate 50.4% |
| Direction study | All bars fail; 2 secondary weather leads | All bars fail; the 2 leads are gone |
| XGBoost on multi-origin weather | No alpha | No change |

**Moonwon: V4 and V5 labels use the same price series.** Labels of the type "touch +10%" use price levels, so a
contract gap in the session after a marked day can make or remove a touch. The effect was not checked. See
`docs/V5_DATA_NOTES.md` for the earlier label checks.

## 8. Where things are
| Path | What |
|---|---|
| `research/autoresearch/` | Plan, addenda, results, code, 100 candidates, data cards, trial log, journal, graph. Start with its `README.md` |
| `research/exploratory/direction_study/` | Direction study and ENSO + CFTC test: plans, code, aggregate results, errata |
| `research/exploratory/xgb_multi_origin/` | XGBoost on 37-node weather: plan, code, aggregate results, erratum |
| `research/exploratory/{weather_volatility,cftc_positioning,multi_origin_pca}/` | Studies of 12-14 Nov |
| `research/prototype/` | Buyer dashboard of 15 Nov: weekly call from rule c86, order planner, history, limits. Source and tests are here; the data and the built page are local. Start with its `README.md` |
| `signal_origin/`, `configs/`, `data_tools/` | V4 package (Moonwon) and V5 modules (Celine); not changed on 15 Nov |
| `docs/HANDOFF_2026-11-14.md` | Full record to 14 Nov |

Raw data are not in the repository (prices, weather, CFTC, market files). They are on Celine's compute machine;
the data cards and `fetch_*.py` scripts say how to get each new source. To run the loop code, see
`research/autoresearch/README.md`.

Repository state: `v5-weather` was merged into `main` on 15 Nov at Celine's instruction. The check
`scripts/check_publication.py` fails by design (new files are not in the allowlist); the allowlist was not
edited. Package tests are not affected: no file of `signal_origin/` changed on 14-15 Nov.

## 9. Do not
- Do not score the test period 2023-Oct 2026 again. It has two looks.
- Do not run more iterations on 2009-2022. N is 110 on these years.
- Do not present iteration 86 as a working strategy. The correct words are "passed development and placebo,
  not confirmed in the test period".
- Do not commit third-party rows (`LOCAL_ONLY_*` files are ignored by git).

## 10. Open decisions and next steps
1. Deck: present a negative result with one lead and one data defect (Celine's draft deck has this story).
   Product demo: the dashboard of `research/prototype/` (built page on Celine's machine). It shows the call of
   rule c86 with the label "not confirmed". The volatility gauge on it was not calculated again after the repair
   of the price series.
2. Moonwon: check if the roll gaps change V4 or V5 labels; decide on the publication allowlist.
3. If the work continues: test the ENSO winter rule on years before 2000. This needs older coffee prices and a
   new plan written before the data are seen. It is the only test that can add evidence, because the rule
   makes one call a year.
