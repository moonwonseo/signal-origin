# Multi-origin Arabica weather (37 nodes, 8 countries), PCA: results (14 Nov 2026)

Plan fixed before data (PLAN.md, sha256 07fa4634...). Run once as planned. PCA refit inside each fold on
pre-test weather only (checked: changing test-period weather leaves pre-test components unchanged).
Data: NASA POWER 1981 - 13 Nov 2026, 37 nodes, clean (no duplicates, at most 1 missing day per node).

## Verdict against the bar: not met (closest weather result so far, but within noise)
+10% within 63 sessions, Brier (lower better), 2012-2026, 3,122 dates:
B0 0.260 | V0 volatility gauge 0.240 | G recalibrated gauge 0.258 | GPC gauge + 6 weather PCs 0.249
1. GPC vs G: +0.009 (range -0.008 to +0.030). Positive, but the range includes zero.          -> not met
2. Not worse in either period: +0.003 (2012-18), +0.013 (2019+).                               -> met
3. GPC vs V0: -0.009 (range -0.027 to +0.010); vs B0: +0.011 (range -0.009 to +0.035).          -> not met
Across all 9 cells GPC vs G is positive in 6, none with a range above zero; it never beats V0 reliably.
Volatility forecasts: no improvement (63 sessions: -0.005, range -0.014 to +0.001).

## What the components show (fit on 2008-2025)
- Temperature PC1 explains 43%: all eight countries move together (a shared warm/cool signal).
- Rainfall is far less shared: PC1 explains only 15%, and it sets Brazil against Colombia and Central America
  (opposite signs). Each origin's rain is largely its own story.

## Reading
Multi-origin weather recovers some of what recalibrating the gauge loses, but still does not beat the plain,
unfitted volatility gauge. This is the fourth weather design tested; a positive point estimate with a range
spanning zero is what noise looks like after several attempts, so it is not evidence of a signal.
