# Direction of Coffee C returns: ENSO and CFTC positioning. Results (14 Nov 2026)

Plan fixed before results (Direction2_ENSO_CFTC_PLAN.md, sha256 77303546...). Mac mini, 14 s per run, 17 placebos.
Code and aggregate results: `research/exploratory/direction_study/` (`direction_study2.py`, `results_enso_cftc/`).
Run note: the first run did not include h = 63 (a parallel-worker bug: the horizon list did not reach the
workers). Fixed and rerun. The h = 5 and h = 21 numbers of the two runs are identical (difference 0.0).

## ENSO: 3 of 4 bars met. Not a result by the fixed rule, but the strongest lead of the project.

Primary: 21 sessions, 2012-2026, 3,686 dates, 176 independent windows, 48.0% "up".
| Model | Hit rate (range) | Gain vs market-only | P&L per year after cost | Sharpe | AUC |
|---|---|---|---|---|---|
| Always up | 48.0% | | +1.4% | 0.04 | |
| Momentum sign | 52.9% (48.6 to 57.8) | | +3.5% | 0.12 | |
| XGB market only (A) | 53.0% (49.5 to 57.1) | | 0.0% | 0.00 | 0.529 |
| **XGB + ENSO (E)** | **55.9% (51.7 to 60.2)** | **+2.9 pp (-0.6 to +6.2)** | +4.1% (-9.4 to +17.5) | 0.15 | 0.558 |
| Linear market only (A) | 53.2% (49.3 to 57.8) | | +1.5% | 0.06 | 0.543 |
| **Linear + ENSO (E)** | **56.2% (52.0 to 60.3)** | **+3.0 pp (-0.2 to +5.9)** | +9.1% (-5.5 to +23.0) | 0.34 | 0.580 |

Bars (XGB + ENSO, h = 21):
1. Gain over market-only, range above zero: NOT met. +2.9 pp, range -0.6 to +6.2 (the range includes zero).
2. Gain larger than all 17 placebo gains: MET. Largest placebo gain +1.7 pp; placebo mean -1.7 pp.
3. Same sign in the linear model: MET (+3.0 pp; also larger than all 17 placebos).
4. Positive in both periods: MET (+4.6 pp in 2012-18, +1.3 pp in 2019+).

Secondary cells:
- h = 5: linear + ENSO 52.3% (49.8 to 54.8), gain +2.2 pp (+0.5 to +4.0), larger than all 17 placebos.
  XGB + ENSO +0.6 pp (-0.9 to +2.1), 4 of 17 placebos are equal or better.
- h = 63: nothing. +0.7 and +0.8 pp, ranges -5 to +6 pp. (58 windows only.)

Limits that prevent the word "alpha":
- No P&L range is above zero. The best is +9.1% per year with a range of -5.5% to +23.0%.
- The gain is concentrated in 2012-18 (+4.6 pp). In 2019+ it is +1.3 pp.
- ENSO has about 5 cycles since 2006. "0 of 17 placebos" is at best p of about 0.06, and rotations are not independent.
- The test period 2012-26 was used by seven earlier studies. ENSO was selected after the all-origin weather lead.
- A physical cause exists (ENSO changes rain in Brazil, Colombia, Central America and Southeast Asia), and the
  effect appears in both model families. These two facts are why this lead is better than the earlier ones.

## CFTC positioning: fails. It makes the forecast worse.
h = 21: XGB + CFTC 49.5%, gain -3.4 pp (-5.7 to -1.3), reliably worse; 16 of 17 placebos are better than the real
data. Linear + CFTC -0.2 pp. h = 63: -9.6 pp. Reading: the relation between positioning and the next return
changes sign between the training years and the test years. This is the second failure of this source.
