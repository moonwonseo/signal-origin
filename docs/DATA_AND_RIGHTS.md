# Data and rights policy

This publication draft includes project-authored source code, adapted tests, schema-only templates, documentation and newly generated artificial demo records. It grants no additional rights to underlying third-party sources. The project owners have not selected an open-source license; no license has been inferred or added during preparation.

## Excluded material

Keep the original bundle and every nested archive local. Excluded categories include:

- Yahoo KC=F responses, closes, cleaned price tables, exchange calendars and roll diagnostics containing observations.
- NASA POWER responses, daily weather, joined inputs and reconstructed historical features.
- FRED/BLS table transcriptions and monthly index values.
- Historical predictions, design matrices, split memberships, fitted parameters, per-date losses and other derived row-level research outputs.
- Original historical demo/report HTML, charts and screenshots, including embedded datasets.
- Course materials, internal handoffs, starter prompts, ownership/deadline plans and unreviewed source-use notes.
- Credentials, environment files, local configuration, environments, caches and generated local results.

Original aggregate output files are also withheld in this conservative draft. Documentation summarizes the team's qualitative findings without redistributing original tables. Source accessibility alone was not treated as evidence of redistribution permission.

## Public synthetic material

`signal_origin.synthetic` and `signal_origin.synthetic_v4` generate artificial prices, weather and freight mathematically from fixed seeds. They do not resample or transform the excluded observations. `scripts/build_demo.py` only accepts this synthetic generation path. `demo/index.html` embeds the resulting artificial records and is clearly labeled throughout.

## Future changes

Obtain local data independently under its provider's terms. Record source, units, retrieval/vintage information and availability limitations. Keep observations and outputs under ignored `data/`, `results/`, `runs/`, `private/` or `_local_import/`. Do not mark unverified inputs as verified simply to pass a modeling gate.

`.gitignore` is a convenience, not an enforcement boundary: already tracked files can bypass it. The publication checker compares all tracked and nonignored untracked files with an explicit SHA-256 allowlist and scans the allowed content for common credential formats. Review changes to that allowlist manually. Its passing result is a targeted check, not proof that every possible sensitive string or rights issue has been detected.
