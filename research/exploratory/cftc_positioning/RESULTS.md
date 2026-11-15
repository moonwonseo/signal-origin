# CFTC positioning study: results (local exploratory, 12 Nov 2026)

Plan fixed before the data was seen (PLAN.md, sha256 fc3e7447...). Run once as planned.
CFTC disaggregated futures-only, Coffee C, 1,065 weekly reports, 13 Jun 2006 to 3 Nov 2026, no gaps.
Usable from report date + 6 days. Test years 2012-2026, 3,122 forecast dates at 63 sessions.
ICE certified stocks: not tested (no free CSV; MacroMicro download is behind a paywall).

## Verdict against the pre-set bar: none met; positioning makes forecasts reliably worse
+10% within 63 sessions, Brier (lower is better):
| | 2012-2026 | 2012-2018 | 2019+ |
|---|---|---|---|
| B0 historical frequency | 0.260 | 0.246 | 0.270 |
| V0 volatility gauge (nothing fitted) | **0.240** | 0.248 | **0.235** |
| G recalibrated gauge | 0.258 | 0.254 | 0.261 |
| GP gauge + positioning | 0.275 | 0.274 | 0.275 |

- GP vs G: -0.017 (range -0.027 to -0.008): reliably worse. Worse in both periods.
- GP is worse than G in all 9 threshold/horizon cells, with the range below zero in 8.
- Positioning does not improve volatility forecasts either (gains near zero or negative).

## Why
The positioning coefficient changes sign between years (2012: -0.42; 2016: +0.17; 2024: -0.18):
the relationship between crowding and later spikes is not stable. Even the one-parameter
recalibration G is worse than the unfitted gauge V0 (-0.018, range -0.034 to -0.002).

## Pattern across all four studies (V1-V4, V5 weather, weather->volatility, positioning)
Every model that learns relationships from 2008-2026 history loses out of sample, because the
market shifted from a calm regime (2012-2018: 32% spike rate) to a volatile one (2019+: 68%).
The only estimate that holds up learns nothing: today's volatility in a fixed formula.
