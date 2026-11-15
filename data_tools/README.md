# Data tools (Celine)

Scripts that fetch or check data locally. None of them contain or redistribute third-party
observations; outputs stay on your machine (see docs/DATA_AND_RIGHTS.md). Run from the repo root.

| Script | What it does | Feeds |
|---|---|---|
| `pull_power_regions.py` | NASA POWER daily weather for the six Arabica points in `configs/v5_regions.csv`, 1981 to yesterday; raw responses kept byte-for-byte | V5 model A3 (`--region-weather`) |
| `power_latency_logger.py` | Run once a day: measures how late POWER data arrive and whether recent values are revised | Tests the t-4 day weather assumption |
| `price_history_check.py` | Year-by-year gaps, roll days, thin-volume moves, usable origins, event rates (2000-2026) | Choice of V5 history start (2008) |
| `label_liquidity_check.py` | How many V4 spike labels first cross on thin-volume or roll days | Motivates the V5 label sensitivity |
| `make_liquidity_mask.py` | Dates where a crossing may count (volume >= 1,000, not a roll day) | V5 `--liquidity` sensitivity |

Region weights: Conab, *Acompanhamento da Safra Brasileira de Cafe*, 3rd survey 2026 (Sept 2026),
Table 2, arabica production 2025+2026 averaged to smooth the on/off-year cycle.
