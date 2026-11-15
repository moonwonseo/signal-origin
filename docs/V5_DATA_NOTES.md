# V5 data notes: six-region NASA POWER pull (12 Nov 2026)

Pulled with `data_tools/pull_power_regions.py`; raw files kept locally (not in the repo).
Descriptive weather checks only. No price outcomes were looked at.

## Coverage
Six regions (`configs/v5_regions.csv`), 1 Jan 1981 to 11 Nov 2026, 16,751 days each, no duplicates.
Only 11 Nov 2026 is missing (not yet published); all range checks pass (no negative rain, Tmin <= Tmean <= Tmax).
At pull time the latest value was 10 Nov, i.e. new data arrived within about 2 days.

## Recent values get revised (answers "validate the weather availability")
Compared with the original Sul de Minas pull from October:
- 1 Jan 1981 to 1 Sep 2026: identical.
- 2-30 Sep 2026 (the newest weeks at the October pull): almost every day changed.
  Tmin moved by 0.59 C on average (up to 1.88 C), Tmax by up to 2.75 C, daily rain by 2.6 mm
  on average (up to 11 mm). September rainfall total went from 96.9 mm to 118.2 mm.

**Implication.** Data *arrive* fast enough for the model's t-4 day lag, but roughly the newest
month is provisional. A buyer forecasting in real time would see provisional values for most of
the 30-day window; our backtests use the later, revised values. This makes backtests somewhat
optimistic about real-time weather quality. The daily latency logger will pin down when values
stop changing.

## Frost threshold check (grid Tmin, Jun-Aug, worst of six regions)
| Winter | Coldest grid night | Region |
|---|---|---|
| 1981 | 0.65 C (21 Jul) | Sul de Minas |
| 1994 | -0.11 C (26 Jun) | Sul de Minas |
| 2000 | 1.45 C (18 Jul) | Sul de Minas |
| 2021 | 3.05 C (20 Jul) | Sul de Minas |

- At 3.0 C, the draft threshold caught 1981, 1994 and 2000 but **missed 2021**.
- At 3.5 C, all four documented damaging frosts register, plus 1985, 1987, 1988 and 1997.
- At 4.0 C, it adds 2009, 2011, 2019 and 2025.

The draft is changed to 3.5 C (`configs/v5_crop_windows.json`). Still a draft for review.

**Limitation to state openly.** Within V5's price history (2008+), only 2021 has frost nights
below 3.5 C. The frost feature therefore rests on essentially one event and cannot be learned
reliably from this sample; treat any A3 frost coefficient as anecdotal.

## Dry run with A3 on real inputs (sample sizes only)
Adding A3 does not shrink the matched sample: 3,122 test forecast dates at 63 sessions
(3,332 at 21, 2,807 at 126) across 2012-2026; smallest training fold 634 rows.
The liquidity mask marks 59.7% of sessions as eligible for crossings.
