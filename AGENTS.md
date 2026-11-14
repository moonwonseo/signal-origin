# AGENTS.md — orientation for AI agents working on Signal-Origin

Read this first, then `docs/HANDOFF.md` (full state of the work), then `docs/V5_CHANGES.md`.

## Project in one paragraph
Duke AIPI 590.03 (Alternative Data) term project by Celine Yang and Moonwon Seo. Question: can alternative data
(weather in coffee-growing regions) help coffee buyers judge the risk of a large Coffee C price rise?
Target: does the KC=F daily close touch +k% (5/10/15) above today's close within h sessions (21/63/126)?
Primary cell: +10% within 63 sessions. Final presentation: 10 minutes, PDF, due 1:30 PM Wed 18 Nov 2026.

## Current findings (as of 14 Nov 2026)
- No learned model (price-only or with weather, freight, positioning or multi-origin weather) reliably beats
  the historical-frequency baseline B0 out of sample, 2012-2026.
- An unfitted volatility gauge (trailing 63-session volatility in a barrier formula) does beat B0
  (Brier 0.240 vs 0.260). It was found after V5 failed, so it is exploratory, and it is direction-free.
- Details and numbers: `docs/HANDOFF.md`.

## Branches
- `main`: Moonwon's V4 publication package. Do not modify without both teammates' agreement.
- `v5-weather`: Celine's additions (V5 code, data tools, exploratory studies, these docs). Open PR, not merged.

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
| `research/exploratory/` | Weather→volatility, CFTC positioning, multi-origin PCA studies: PLAN, code, tests, aggregate results |
| `research/prototype/` | Buyer dashboard template and data fetcher (built HTML embeds prices, so it stays local) |
| `docs/` | `HANDOFF.md`, `V5_CHANGES.md`, `V5_DATA_NOTES.md`, `V5_LOCAL_PREVIEW_2026-11-12.md`, plus V4 docs |

## Environment
Python 3.11+. `pip install -r requirements-lock.txt && pip install --no-deps --no-build-isolation -e .`;
exploratory studies also need `scipy`. Historical inputs live outside the repo (see `docs/HANDOFF.md` §6).
