# Local input contract

No historical observations are supplied. The template CSVs contain headers only and are not runnable datasets. Keep independently obtained inputs under an ignored local folder.

## Prices and sessions

Use the original price loader with these files:

| File | Required fields |
| --- | --- |
| Prices CSV | `price_date`, `close_us_cents_per_lb`, `quality_status` |
| Sessions CSV | `session_date` for every expected session |
| Metadata JSON | Fields in `signal_origin/schema/metadata.schema.json` |

Dates use YYYY-MM-DD. Prices are source-precision decimal text in US cents per pound. Missing/bad observations stay in the explicit session calendar and receive the loader's usability treatment. Calendar gaps must not be silently removed. No holiday inference, roll adjustment, download or forward fill is performed. Read the schema templates in `schema/` and choose the calendar before evaluation.

`calendar_verified`, `roll_adjustment_status` and provenance fields are evidence claims, not switches to enable a run. The preserved baseline gate rejects inputs lacking documented calendar/series construction. Do not change the original historical archive's qualification flags. Its exploratory raw-vendor path was separate from this strict generic loader.

## Weather and freight for V4

| File | Required fields |
| --- | --- |
| Weather features CSV | `weather_date_utc`, `rain_anom_z`, `temp_anom_z`, `dry_spell_max_30d` |
| Monthly freight CSV | `observation_month` (first of month), `freight_ppi` (positive finite index) |

Weather dates must be unique, sorted, naive UTC day labels. Missing values remain missing. The runner joins weather at exactly t−4 calendar days. Dry-spell values must be integers from 0 through 30. Monthly freight dates must be unique, sorted month starts. A missing month is restored to the calendar and invalidates incomplete feature windows.

Use `signal_origin.weather.rebuild_features` to reconstruct the original prior-year anomaly convention from a daily DatetimeIndex and columns `precipitation_mm_per_day`, `temperature_mean_c`, `temperature_min_c`. Reindex daily weather to a complete calendar before calling it. `dry_spell_features` preserves missing calendar days itself. The V4 CLI accepts audited precomputed features: it checks shape, values and alignment but cannot certify how someone computed their anomalies or when their source values were published. Keep that audit and vintage evidence locally.

Run a separate historical experiment only after documenting source rights and research limitations:

```bash
python -m signal_origin.experiment run \
  --prices data/local/prices.csv \
  --sessions data/local/sessions.csv \
  --metadata data/local/metadata.json \
  --weather-features data/local/weather_features.csv \
  --freight data/local/freight_monthly.csv \
  --years 2022 2023 2024 2025 2026 \
  --acknowledge-exploratory \
  --out runs/local-research
```

Each requested year must exist in the supplied session calendar and meet the preserved minimum sample/class counts. The first supplied session of each year defines the fold boundary; supply complete annual calendars. Outputs contain sensitive derived records and remain local. Input hashes are recorded for CLI historical runs. This command creates a new portable research run; it does not recreate the original frozen V4 archive, availability evidence or prior-version reproduction receipts.
