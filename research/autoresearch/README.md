# Autoresearch loop: when to buy coffee (15 Nov 2026)

An AI agent (Claude) ran 100 pre-registered iterations to find a rule or model that tells a coffee purchasing
team when to buy: early, steadily, or late. Each iteration is one hypothesis, one candidate, one scored run.

**Result: no confirmed predictor.** The best rule (iteration 86) passed the development score and the placebo
test, and failed the test period. Read `Autoresearch_RESULTS.md` first.

## Read in this order
| File | What |
|---|---|
| `Autoresearch_RESULTS.md` | Verdict, the best rule in words, the table of all 100 iterations, limits |
| `Autoresearch_PLAN.md` | Problem, score, constraints, search space, loop protocol. Fixed before the first run (sha256 in the trial log) |
| `Autoresearch_PLAN_ADDENDUM_1.md` | Repair of the roll adjustment (eval revision 1) and the void rule |
| `Autoresearch_PLAN_ADDENDUM_2.md` | Iterations 31-100, the rule for new data sources, the second test look |
| `JOURNAL.md` | The agent's reflection after each iteration and the plan for the next one |
| `results/iteration_table.md`, `.csv` | One row for each iteration: what changed, score, accepted or not |
| `results/hillclimb.png` | Score of each iteration, best score to date, and the score necessary after N trials |
| `trial_log.jsonl` | Append-only log. Each row holds the sha256 of the row before it. Aggregates only |

## Code
| File | What |
|---|---|
| `core.py` | The eval and the harness. Data access with a cutoff date, labels, walk-forward refits, score, constraints C1-C7, trial log. The agent does not change this file during the loop (one logged repair: revision 1) |
| `lib.py` | Feature and model helpers that the candidates use |
| `candidates/c01.py` ... `c100.py` | One file for each iteration: hypothesis, change, expected effect, features, model |
| `data_cards/*.json` | One card for each data source: publisher, URL, first date, publication delay, revision policy |
| `fetch_*.py` | Download scripts for the new sources (public files, no account) |
| `selftest.py` | Checks of the harness (leak test, perfect-foresight score, random strategies) |
| `make_report.py` | Builds the iteration table and the hill-climb graph from the trial log |
| `make_figures.py` | Builds the slide figures in `results/figures/` (label, walk-forward, idea families, yearly result of the final rule, ranges, roll gap). Aggregates and made-up illustrations only |
| `export_dashboard.py` | Writes the inputs of the buyer dashboard (`research/prototype/`) from the saved final run of c86. No score is calculated. Its output has third-party rows and stays local |
| `run.sh`, `it.sh`, `newc.sh` | Shell helpers: run on the compute machine, run one counted iteration, make a candidate file |

## Commands (from the `autoresearch` folder on the compute machine)
```bash
./run.sh selftest.py                       # harness checks
./run.sh core.py base                      # baselines B0-B5
./run.sh core.py iter candidates/c86.py    # one counted iteration (appends to the trial log)
./run.sh core.py placebo c86               # constraint C6: 17 runs with rotated alt data
./run.sh core.py ablate c86                # the same candidate without its alt-data features
./run.sh core.py final c86                 # TEST PERIOD. Each use goes in the log. Do not use it again.
./run.sh make_report.py                    # table and graph
```
`it.sh` copies the candidates to the compute machine and runs one iteration there. Set `MINI` to the SSH login
of that machine.

## Data (not in the repository)
The raw files stay on the compute machine. No third-party rows are committed. `core.py` reads:
- `../data/prices/` (Coffee C closes and session calendar), `../data/fx/`, `../data/enso/`, `../data/cftc/`,
  `../data/z_long/`, `../data/power_daily_arabica_world.csv`, `../data/arabica_world_nodes.csv`
- `data/` inside this folder: the files that the `fetch_*.py` scripts write (see the `file` field of each data card)

## Path names in the plan files
The plan and the addenda are fingerprinted, so their text was not changed. They use the folder names of
Celine's working folder:

| Name in the plan | Path in this repository |
|---|---|
| `04_code_and_branch/autoresearch/` | `research/autoresearch/` |
| `05_studies/Autoresearch_*.md` | `research/autoresearch/Autoresearch_*.md` |
| `eval.py`, `harness.py` | `core.py` (one file holds both) |

## Rules for the next person
- The test period 2023-Oct 2026 has been scored two times. Do not score it again.
- Do not run more iterations on 2009-2022. 110 trials are already counted on these years.
- A new idea needs a new plan and data that this loop has not seen (for example prices before 2000).
