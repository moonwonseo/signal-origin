# Buyer dashboard (prototype)

One page for the green-coffee buyer of a roastery: the weekly call (buy early / steady / buy late), an order
planner, the rule explained, its history, and its limits. The call comes from rule c86 of the autoresearch loop
(`research/autoresearch/`). The test period did not confirm that rule, and the page says so.

| Path | Content |
|---|---|
| `src/engine.js` | The buy rule c86 in JavaScript (two inputs, no fitted weights) and the order planner. No DOM |
| `src/template.html` | Page layout, charts and text. The build puts the engine and the data into it |
| `build.py` | Builds `signal_origin_dashboard.html` (one file) from `src/` and `data/` |
| `tests/engine.test.mjs` | Rule tests on made-up inputs; parity tests against the Python harness |
| `tests/page.test.mjs` | Tests of the built page in a DOM (jsdom) |
| `template.html`, `fetch_demo_data.py` | The dashboard of 14 Nov (volatility gauge, weather forecast, frost replay) and its data fetcher |

## Not in the repository
`data/`, `demo_data/` and the built page contain rows from third parties (prices, weather, ocean index), so they
stay local (`AGENTS.md`, rule 1). Without them, the build stops with a message, the parity and page tests are
skipped, and the tests on made-up inputs run.

| File | Source |
|---|---|
| `data/dashboard_data.json`, `data/parity_fixture.json` | `research/autoresearch/export_dashboard.py`, on the compute machine. It reads the saved run of `core.py final c86`. It does not score the test period again |
| `data/gauge_v0.json` | The `gauge` and `track` objects of the dashboard of 14 Nov. Calculated on 12 Nov, before the repair of the price series, and not calculated again |
| `demo_data/kc_recent.csv` | Optional, from `fetch_demo_data.py`: closes after the end of the price archive |

## Commands
```bash
# in the autoresearch folder on the compute machine; then copy out/dashboard/*.json to research/prototype/data/
./run.sh export_dashboard.py
# in research/prototype
python3 build.py                     # writes signal_origin_dashboard.html
python3 build.py --check             # exit 1 if the built page is not up to date
npm install --no-save jsdom          # one time, for the page tests (or set JSDOM_DIR to a folder that has jsdom)
node --test tests/*.test.mjs
```
Open the built page in a browser. Add `?date=2024-06-14` to the address to see the call of another week.

## Checks of 15 Nov 2026
- The JavaScript rule gives the same weekly position as the Python harness on each of 4,495 sessions
  (Dec 2008 to 9 Oct 2026), and both inputs agree on each session.
- One week differs from the pure rule in the harness: 11 Nov 2016 has no usable close, so the harness holds
  "steady" for that week. A test includes this case.
- 22 tests pass with the local data (14 engine, 8 page).

## Limits
- The call is a research signal: development RATIO +0.79 (passed), placebo 0 of 17 (passed), test +0.37 against a
  bar of 0.50 (not confirmed).
- The amounts of the planner are for the futures part of the price only.
- For future dates the page takes Friday as the last session of the week.
- The page gives no call when the data in the file end before the date. It does not hold an old call.
