# Signal-Origin

Exploratory research into whether weather and freight context improve estimates of a large future coffee-price increase. The latest archived experiment is V4, completed 3 November 2026. Its evidence is mixed and does not establish a dependable procurement signal.

This repository contains the project's modeling methods, tests, documentation, and an offline **synthetic demo**. It excludes third-party observations and historical row-level outputs. The public demo's scores are generated software examples, not the original research results.

## Try the demo

Open [demo/index.html](demo/index.html) in a browser. No installation, account or network connection is needed. Compare seven models, switch between 21- and 63-session horizons and two freight availability assumptions, inspect an artificial forecast, then reveal its artificial outcome.

Every displayed value is generated from seeded mathematical inputs. The dates follow a fictional Monday–Friday calendar, not the ICE exchange calendar. Synthetic scores provide no evidence of real forecasting skill.

## Install and check

Python 3.11 or newer is required; the publication draft was tested with Python 3.12. Create an environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
python scripts/build_demo.py --check
python scripts/check_publication.py
```

The lock records the tested Python dependencies. The numerical versions match those recorded for the archived V4 experiment; the public draft's full dependency environment is separately recorded. Installation needs network access unless the packages are cached. Modeling and demo use are offline.

## Run the models

Generate new V4 software-test outputs for all seven models, both horizons and both policies:

```bash
python -m signal_origin.experiment synthetic --out runs/synthetic-v4
```

Output folders must be new or empty. Predictions, metrics, calibration bins, fold audits and JSON parameters are written under the ignored `runs/` directory. To rebuild the distributable synthetic viewer:

```bash
python scripts/build_demo.py
```

The original B0/B1 endpoint experiment is also preserved:

```bash
python -m signal_origin demo --out runs/synthetic-baselines
```

The baseline command tests a +10% increase **exactly 63 sessions later**. V4 tests a +10% increase **at any daily close within the next 21 or 63 sessions**. Scores across those tasks are not directly comparable.

To work with historical data, independently obtain authorized local inputs and follow [the input contract](docs/DATA_INPUTS.md). No downloader or credential is required by this code. The public package cannot reproduce the original historical experiment without its excluded inputs and provenance checks.

## Models and research boundaries

| Model | Inputs |
| --- | --- |
| B0 | Frequency of the event among matured training labels |
| B1 | Trailing returns, volatility and calendar seasonality |
| A1 | B1 plus rainfall and temperature anomalies |
| A2 | B1 plus longest 30-day dry spell and temperature anomaly |
| F1 | B1 plus three- and twelve-month freight-index log changes |
| FW1 | A1 plus freight changes |
| FW2 | A2 plus freight changes |

V4 uses annual expanding fits, training-only scaling, matched samples, complete future windows and purging of training outcomes that reach the test boundary. Freight enters strictly after assumed month-end +180 days, or +45 days for a revised-data sensitivity. These assumptions do not establish historical publication vintages.

The original full longer-horizon replay favored combined inputs on average; recent-period, shorter-horizon and timing comparisons did not establish a stable advantage. History had already informed development. Overlapping outcomes are dependent. A broad freight-cost proxy is not coffee shipments, port congestion or tariffs. No live forecasting, causal effect, procurement savings or validated buying advice is claimed. See [methodology](docs/METHODOLOGY.md) and [research status](docs/RESEARCH_STATUS.md).

## Publication and attribution

[Publication review](docs/PUBLICATION_REVIEW.md) lists the proposed public contents and exclusions. [Provenance](docs/PROVENANCE.md) explains which calculations were preserved and which packaging changes were made. [Validation](docs/VALIDATION.md) separates newly executed checks from archived receipts. [The demo script](docs/DEMO_SCRIPT.md) provides a short walkthrough.


No project-wide open-source license has been selected. Publication does not grant third-party data redistribution rights. See [data and rights policy](docs/DATA_AND_RIGHTS.md). No commit or push is part of this preparation draft.
