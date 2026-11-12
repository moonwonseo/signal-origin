# V5 on branch `v5-weather`: what changed, why, and how to undo it

**Status: proposal for review, not merged.** Drafted by Celine with Claude on 12 Nov 2026 while
Moonwon was unavailable. Nothing has been fitted on real data. The runner refuses historical
fitting until `configs/v5_spec.json` is signed off by both of us.

## V5 in one paragraph
V5 asks whether *better* weather data adds to price-only forecasts: six Arabica regions instead
of one grid point, features timed to crop stages (frost in Jun-Aug, flowering rain in Sep-Nov,
grain-fill dry spells in Jan-Mar), tested over 2012-2026 instead of 2022-2026, across
thresholds of 5/10/15% and horizons of 21/63/126 sessions. It also adds rough uncertainty
ranges and an "always 50%" reference, and one label check (crossings counted only on liquid,
non-roll days). It responds directly to the midterm feedback on locations, crop seasons, and
thresholds/horizons. Freight is left out on purpose: V4's freight results stand as recorded.

## What did NOT change
- `git diff --name-status main..v5-weather`: **21 files added (including this one), 0 modified, 0 deleted.**
- V4 synthetic run (`python -m signal_origin.experiment synthetic`) gives **byte-identical**
  predictions, metrics, annual and calibration files on `main` and on this branch.
- All 187 original tests pass; 16 new tests added (203 total).
- Same model settings as V4: training-only scaling, L2 logistic, C=1, lbfgs, seed 42.

## The commits: review or revert one at a time
| # | Commit | What it adds | Why |
|---|---|---|---|
| 1 | Data tools | `data_tools/`: NASA POWER six-region pull, daily latency logger, price-history and label checks, liquidity mask; `configs/v5_regions.csv` | Data acquisition had no code in the repo; latency logger answers "validate weather availability" |
| 2 | V5 labels | `signal_origin/v5_labels.py`: threshold as a parameter, optional liquidity mask | Threshold was hard-coded at 10%. At 10% the test reproduces V4 labels exactly |
| 3 | Model A3 | `signal_origin/crop_weather.py`, `configs/v5_crop_windows.json` (DRAFT) | "Multiple weather locations" and "crop-season features"; reuses `weather.py` unchanged |
| 4 | Uncertainty | `signal_origin/uncertainty.py` | Block bootstrap (block = horizon) of paired Brier differences; vs B0 and vs always-50% |
| 5 | V5 runner | `signal_origin/v5.py`, `configs/v5_spec.json` (DRAFT), tests | Grid, longer history, sign-off gate, dry run |

| 6 | Docs | This file | Explains the change for review |
| 7 | Data notes | `docs/V5_DATA_NOTES.md`; draft frost threshold 3.0 C -> 3.5 C | Six-region pull checks: recent-data revisions, 3.0 C missed the 2021 frost |

Commit 5 depends on 2-4; to drop any of 2-4, revert 5 first.

## Decisions for Moonwon before sign-off
1. **Crop windows and frost threshold** (`configs/v5_crop_windows.json`). Months come from Conab's
   2026 crop calendar. Frost threshold now 3.5 C (3.0 C missed 2021; see V5_DATA_NOTES.md). No price outcomes were consulted.
2. **Heat-day feature**: off unless you set a threshold.
3. **Region weights**: Conab 2025+2026 shares. Using recent shares to weight earlier years is a
   mild look-ahead; an older survey's shares would be cleaner.
4. **History from 2008** with the same unverified calendar caveat as 2019+. The runner requires
   `--acknowledge-unverified-inputs` and records the input-gate blockers, mirroring the archived
   V4 exploratory route. Agree, or keep the strict gate?
5. **Models** B0, B1, A1, A3 (no freight), **grid** 5/10/15% x 21/63/126, **primary** 10%/63,
   **scopes** 2012-26, 2012-18, 2019+, 2024+. All fixed before any run; every cell reported.
6. **Uncertainty wording**: V4 ruled out IID intervals. These are dependence-aware, but still
   presented as rough ranges, not significance tests.

## Sample sizes (dry run on real local inputs: no fitting, no scores)
| | V4 (63 sessions) | V5 (63 sessions) |
|---|---|---|
| Test years | 2022-Jul 2026 | 2012-2026 (15 annual folds) |
| Test forecast dates | 1,135 | 3,122 |
| Approx. independent 3-month windows | ~18 | ~50 |

Run `--dry-run` yourself to check per-fold counts (`counts.csv`).

## How to run
```bash
python -m signal_origin.v5 synthetic --out runs/v5-synthetic          # artificial data only
python -m signal_origin.v5 run --spec configs/v5_spec.json \
  --prices data/local/prices.csv --sessions data/local/sessions.csv --metadata data/local/metadata.json \
  --weather-features data/local/weather_features.csv \
  --region-weather data/local/power_daily_all_regions.csv \
  --liquidity data/local/liquidity_mask.csv \
  --acknowledge-exploratory --acknowledge-unverified-inputs --dry-run --out runs/v5-dry
```
Drop `--dry-run` only after sign-off. Before the region pull exists, `--models B0 B1 A1` runs the
grid and longer history without A3.

## How to undo
- Not merged yet: simply don't merge; delete with `git branch -D v5-weather` (and
  `git push origin --delete v5-weather` if it was pushed).
- One change: `git revert <commit>` (revert commit 5 before 2, 3 or 4).
- Already merged: `git revert -m 1 <merge-commit>`.
Because no existing file was edited, removing the new files fully restores V4.

*AI assistance: code drafted with Claude (Anthropic) at Celine's request; prompts retained per the syllabus. Both teammates remain responsible for review and claims.*
