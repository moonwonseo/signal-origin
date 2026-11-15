# AGENTS.md — orientation for AI agents working on Signal-Origin

Read this first, then `docs/HANDOFF.md` (state of the work, 15 Nov 2026), then `research/autoresearch/README.md`.
Older record: `docs/HANDOFF_2026-11-14.md` and `docs/V5_CHANGES.md`.

## Communication and compute (rules from Celine, 14 Nov 2026)
1. Always write to Celine in ASD-STE100 Simplified Technical English.
2. Make each report concise. Go straight to the point.
3. After each report, give proposed concrete actions.
4. A Mac mini is available for compute (Celine's machine; ask Celine for the SSH login, it is not in this
   repository). Use it to train models and to do all compute-intensive tasks. The MacBook Air that runs the
   agent has low compute. Work folder on the Mac mini: `~/coffee_project` (repo copy, data, `venv`, `out/`).
   Before you use XGBoost there, run:
   `source venv/bin/activate; export DYLD_LIBRARY_PATH="$PWD/venv/lib/python3.12/site-packages/sklearn/.dylibs"`

## Project in one paragraph
Duke AIPI 590.03 (Alternative Data) term project by Celine Yang and Moonwon Seo. Question: can alternative data
(weather in coffee-growing regions) help coffee buyers judge the risk of a large Coffee C price rise?
Target: does the KC=F daily close touch +k% (5/10/15) above today's close within h sessions (21/63/126)?
Primary cell: +10% within 63 sessions. Final presentation: 10 minutes, PDF, due 1:30 PM Wed 18 Nov 2026.

## Current findings (as of 15 Nov 2026)
- No learned model (price-only or with weather, freight, positioning or multi-origin weather) reliably beats
  the historical-frequency baseline B0 out of sample, 2012-2026.
- An unfitted volatility gauge (trailing 63-session volatility in a barrier formula) does beat B0
  (Brier 0.240 vs 0.260). It was found after V5 failed, so it is exploratory, and it is direction-free.
- XGBoost on multi-origin weather (pre-registered, 14 Nov): no alpha, and no gain over the volatility gauge.
  Exploratory placebo test: real weather is better than time-rotated weather in 17 of 17 runs. Open lead, not a result.
  See `research/exploratory/xgb_multi_origin/` (RESULTS.md).
- Direction study (pre-registered, 14 Nov): sign of the 5- and 21-session return. Fails all bars: hit rate 49.8%
  with Brazil weather news; market-only models give no edge. All-origin weather beats placebos in 2 of 4
  secondary cells (weak lead, ENSO hypothesis). See `research/exploratory/direction_study/RESULTS.md`.
- ENSO + CFTC direction test (pre-registered, 14 Nov; FIRST-RUN numbers, superseded by the erratum, see PRICE
  DEFECT below): ENSO (Nino 3.4 level and 3-month change) meets 3 of 4 bars at
  21 sessions: hit rate 55.9% (XGB) and 56.2% (linear), +3 pp over market-only, better than all 17 placebos, but the
  bootstrap range of the gain includes zero and no P&L range is above zero. Strongest lead so far; needs replication
  on untouched data. CFTC positioning fails again. See `research/exploratory/direction_study/RESULTS2_ENSO_CFTC.md`.
- Celine's direction (14 Nov): the "+10% touch" target is ill posed. Predict direction first, magnitude later.
- Celine's direction (15 Nov): the user is a coffee trader's purchasing team that selects WHEN to buy. Score =
  cost saving against steady buying (not long/short Sharpe). One track, 63-session horizon. Scored years
  2009-2022; final test 2023-Oct 2026 (one look); no forward log. Autoresearch loop of 30 iterations with Claude
  as the agent; new data only from the approved whitelist. Plan and evals: `research/autoresearch/Autoresearch_PLAN.md`.
- Autoresearch loop (15 Nov, 100 iterations, done; plan + addenda 1-2 in `research/autoresearch/`): status NOT CONFIRMED.
  Best rule by the plan (iteration 86): ENSO winter state (January Nino 3.4) and Brazil Jan-Mar temperature
  against the last 5 years must agree; about one call a year. RATIO +0.787 on 2009-2022 (necessary 0.712 at
  N = 110), placebo passed (0 of 17), test 2023-Oct 2026 second look +0.37 (limit 0.5): fail. Honest size with
  careful settings about 0.6; no skill before 2009 (label agreement 51%). ENSO winter state alone is the only
  signal with a stable sign in 2001-2022 (+0.4). Slow five-market trend is stable at +0.34. No skill: price
  factors, value, positioning, export flow, stocks, currencies, calendar, water stress, and all six fitted
  models (logistic, random forest, LightGBM, tree). See `research/autoresearch/` (README.md, Autoresearch_RESULTS.md, code, trial log,
  JOURNAL.md, data cards). The test period 2023-Oct 2026
  has been looked at two times: do not score it again. Do not run more iterations on 2009-2022.
- PRICE DEFECT (found 15 Nov): the 134 `suspected_roll_flag` days are the last day of the OLD contract; the gap
  between contracts is in the NEXT session (mean +1.1%). Zeroing only the marked day leaves the gaps in the
  returns (false profit for always-long in contango). The Direction and XGBoost studies have this defect in
  their P&L values. The autoresearch eval zeroes both days (`research/autoresearch/core.py`, REV 1; `Autoresearch_PLAN_ADDENDUM_1.md`).
  Celine accepted this repair on 15 Nov 2026. The three studies were run again with it (`ROLL_FIX=1`); see the
  erratum at the end of each RESULTS file. Main change: the ENSO lead at 21 sessions now meets 0 of 4 bars (it was 3),
  and the two secondary weather leads of the Direction study are gone. The XGBoost study verdict does not change.
- Details and numbers: `docs/HANDOFF.md` (15 Nov) and `docs/HANDOFF_2026-11-14.md` (to 14 Nov).

## Branches
- `main`: Moonwon's V4 publication package plus, from 15 Nov 2026, everything of `v5-weather` (merged at Celine's
  instruction, no pull request). Ask before each further change to `main`.
- `v5-weather`: Celine's additions (V5 code, data tools, exploratory studies, autoresearch loop, these docs).

## Rules
1. **Never commit third-party observations.** No Yahoo/ICE prices, NASA POWER rows, CFTC rows, or derived
   row-level outputs. Aggregate metrics, plans, code and configs are fine. See `docs/DATA_AND_RIGHTS.md`.
2. **Do not edit `main`'s V4 modules** (`signal_origin/{experiment,freight,features,weather,models,split,...}.py`).
   Add new modules instead. V4 synthetic outputs must stay byte-identical (`python -m signal_origin.experiment synthetic`).
3. **Pre-register before looking.** Write `PLAN.md` (question, models, bar), fingerprint it (sha256), then run
   once. Report every cell and scope. Label anything chosen after seeing results as exploratory.
4. **V5 sign-off gate.** `python -m signal_origin.v5 run` refuses historical fitting unless
   `configs/v5_spec.json` is `SIGNED_OFF` by both teammates. Do not bypass it or fill in names. `--dry-run` is always allowed.
5. **No leakage.** Features use prices through t and weather at t-4 calendar days; annual folds purge training
   outcomes that reach the test year; anything fitted (scalers, PCA, models) is fit on training data only.
6. **Evaluation conventions.** Brier score; block-bootstrap ranges on paired differences (block = horizon,
   2,000 draws, seed 590); always report B0 and the always-50% reference (Brier 0.25).
7. Keep changes small, one commit per change, with a plain-English message. Run `python -m pytest -q`.
8. The publication allowlist (`scripts/check_publication.py`) is Moonwon's sign-off on public contents.
   It fails on new files by design; do not edit `publication_manifest.json` unless asked.

## Layout
| Path | What |
|---|---|
| `signal_origin/` | Package. V4 modules (Moonwon) + V5 modules: `v5.py`, `v5_labels.py`, `crop_weather.py`, `uncertainty.py`, `synthetic_v5.py` |
| `configs/` | `v5_spec.json` (DRAFT), `v5_crop_windows.json` (DRAFT), `v5_regions.csv` (6 Brazil points), `v6_arabica_world_nodes.csv` (37 nodes, 8 countries) |
| `data_tools/` | Local data acquisition and checks (POWER pull, latency logger, price/label checks, liquidity mask) |
| `research/autoresearch/` | Autoresearch loop "when to buy coffee" (15 Nov): plan, addenda, results, eval and harness, 100 candidates, data cards, trial log, journal |
| `research/exploratory/` | Weather→volatility, CFTC positioning, multi-origin PCA, XGBoost multi-origin, Direction and ENSO + CFTC studies: PLAN, code, aggregate results |
| `research/prototype/` | Buyer dashboard (15 Nov): rule c86 as a JavaScript engine, page template, build script, tests. Its `data/` and the built HTML have third-party rows, so they stay local. Also the template of 14 Nov and its data fetcher |
| `docs/` | `HANDOFF.md` (15 Nov), `HANDOFF_2026-11-14.md`, `V5_CHANGES.md`, `V5_DATA_NOTES.md`, `V5_LOCAL_PREVIEW_2026-11-12.md`, plus V4 docs |

## Environment
Python 3.11+. `pip install -r requirements-lock.txt && pip install --no-deps --no-build-isolation -e .`;
exploratory studies also need `scipy`. Historical inputs live outside the repo (see `docs/HANDOFF_2026-11-14.md` §6 and
`research/autoresearch/README.md`).
