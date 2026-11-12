# Code and artifact provenance

Source: the user-supplied `Signal_Origin_Project_Bundle_Fresh_Download_2026-11-12.zip`.

- Outer bundle SHA-256: `21757909050747ff59619de5711b16a45eeaca14fb85355d588a4e2f2d69aab0`.
- Nested V4 model ZIP SHA-256: `3a66d295606e59426b7ab4f4c1d26ea9836bc47b4885ba8a88e40c7e142b10e8`.
- Recursive inventory: four ZIP archives and 486 entries in total, counting nested archive containers and their entries. No absolute or parent-traversal archive paths were found.

Neither archive is part of the proposed public contents. The source archive remains unchanged locally. Imported project code is attributed to the supplied team project; no third-party repository code or font assets were imported.

In the table below, paths are relative to `Signal_Origin_V4_Freight_Weather_2026-11-03/` inside the nested model ZIP. `V1` abbreviates `upstream_v3/upstream_v2/upstream_v1/`; `BASE` abbreviates `V1/sources/baseline_v1/experiment/modeling_v1/`.

| Public location | Source and preparation |
| --- | --- |
| `signal_origin/` baseline modules | `BASE/signal_origin/`; numerical feature, label, split, model and metric routines preserved. Metadata schema loading and code hashing now work with the packaged schema location. |
| `run_baselines.py`, `config/`, `schema/` | Baseline entry point and header-only/null templates from `BASE`. The metadata JSON schema moved into package data for installed-wheel use. |
| `signal_origin/weather.py` | `rebuild_features` from `V1/scripts/audit_weather.py`; `longest_dry_run` and `dry_spell_features` from `upstream_v3/scripts/temporal_experiment.py`. Archive I/O and frozen-file imports removed. |
| `signal_origin/parameters.py` | JSON parameter export and probability reconstruction from `V1/scripts/run_a1.py`. |
| `signal_origin/freight.py` | Label, monthly feature, as-of alignment, design, model fitting and scoring functions from `scripts/freight_experiment.py`. Explicit feature constants replace upstream module lookups. Boolean horizons are rejected as invalid integers. |
| `signal_origin/experiment.py` | New portable orchestration of the preserved V4 methods over explicit local inputs. It replaces archive-specific freeze/verification and earlier-version control dependencies; it never claims original-archive reproduction. |
| `signal_origin/synthetic_v4.py` | New seeded artificial daily weather and monthly freight generation; uses the existing artificial price generator and preserved weather calculations. |
| Baseline tests | `BASE/tests/`; preserved synthetic/input-contract tests. |
| Freight/weather tests | Pure synthetic tests adapted from V4 `tests/test_freight.py` and V3 `tests/test_temporal.py`. Historical data-presence and publisher spot-value tests excluded. |
| Pipeline/demo tests | New public end-to-end checks of artificial outputs, matched metrics, timing, outcome paths and synthetic provenance. |
| `demo/template.html` | Layout and UI logic adapted from the outer handoff's `scripts/demo_template.html`; historical payload and hard-coded historical conclusions removed. Wording now identifies artificial data throughout. |
| `scripts/build_demo.py`, `demo/index.html` | New generator and its synthetic-only HTML output. Original historical viewer and archive-reading builder excluded. |
| Documentation and release tooling | New publication documentation, explicit file allowlist, credential-pattern checks, browser checks, package configuration and CI definition. |

The portable runner's from-2024 scope follows the supplied data's complete windows instead of hard-coding the archive's original final forecast date. Other scope/reporting differences are documented in `METHODOLOGY.md`. No original frozen hash manifest was copied, rewritten or presented as validating the modified public package.

The original bundle's archived execution receipts remain excluded. Newly executed checks are described separately in `VALIDATION.md`; they do not establish new forecasting performance.
