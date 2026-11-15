# Weather -> price volatility: results (local exploratory study, 12 Nov 2026)

Plan written and fingerprinted before any result (PLAN.md, sha256 5eca7122...). Run once as planned.
Data: Yahoo KC=F closes 2008-Oct 2026 (local), NASA POWER six regions + Sul de Minas features.
Test years 2012-2026, annual refits, purged; 3,122 forecast dates at 63 sessions, 3,332 at 21.

## Verdict against the pre-set bar: none of the three criteria met -> clean negative
1. Six-region crop-stage weather (W3) vs price-only volatility model (V1), 63 sessions:
   gain -0.0021 (range -0.0050 to +0.0001). Slightly worse, not better. At 21 sessions reliably worse.
2. Not better in 2012-2018 or 2019+; not better in any calendar quarter, including Jul-Sep (frost season);
   reliably worse in Jan-Mar.
3. Product: the W3 gauge does not beat the plain volatility gauge (V0) for +10% within 63 sessions
   (Brier 0.2461 vs 0.2399; gain -0.0062, range -0.0197 to +0.0048).
Single-point weather (W1) is likewise neutral.

## What the weather terms learned
Signs mostly make agronomic sense (longer grain-fill dry spells and drier flowering -> more volatility),
but effects are tiny (0.01-0.04 standard deviations of log volatility). The frost term rests on one
event (2021) and turns slightly negative after it.

## What holds up
The plain volatility gauge (V0: trailing 63-session volatility in a fixed formula, nothing fitted)
again beats the historical-frequency baseline B0 for +10% within 63 sessions:
Brier 0.2399 vs 0.2645, gain +0.0246 (range +0.0042 to +0.0436), driven by 2019 onward.
A fitted price-only volatility model (V1) does not improve the gauge further.

## Interpretation
Observed, public, after-the-fact weather (reanalysis, 4-day lag) adds nothing measurable beyond what
prices already show, for direction or for turbulence. The plausible reason: markets trade on weather
*forecasts* and crop reports, so by the time observed weather is available it is already priced.
