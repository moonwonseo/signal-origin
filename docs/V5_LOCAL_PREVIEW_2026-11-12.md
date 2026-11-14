# V5 local preview — 12 Nov 2026 (before co-sign-off)

**What this is.** Celine asked for an early look at whether the models work. V5 was run locally,
outside the repo, by calling the analysis code directly. The sign-off lock was not altered and nothing
was committed. Plan used: the DRAFT `configs/v5_spec.json` (sha256 starts `c3d3705f96033f45`) and
`configs/v5_crop_windows.json` (sha256 starts `2bb17a71ebfa5ae5`), exactly as pushed on `v5-weather`
(commit 1b8bb64). Any change to those files after this date was made after seeing these results.

## V5 as specified: no model beats B0
- Over 2012-2026, no model beats B0 (historical frequency) in any of the 9 threshold/horizon cells.
- Primary target (+10% within 63 sessions): Brier B0 0.260, B1 0.289, A1 0.284, A3 0.293.
  A3 vs B0: -0.033 (block-bootstrap range -0.062 to -0.011), i.e. reliably worse.
- Within-year ranking (AUC) averages close to 0.5 and swings by year (e.g. 2013 almost fully inverted).
- The six-region crop-stage weather (A3) did not improve on single-point weather (A1).
- Label sensitivity (liquid, non-roll days only) gives the same picture.

## One exploratory check, added after seeing the above
A parameter-free volatility estimate (VOL): probability that a driftless random walk with the trailing
63-session volatility touches +k% within h sessions, P = 2 * (1 - Phi(ln(1+k) / (sigma * sqrt(h)))).
Nothing is fitted; prices through day t only. Same test dates and outcomes as V5.

| Target | Brier B0 | Brier VOL | Gain (range) all years | 2012-2018 | 2019+ |
|---|---|---|---|---|---|
| +10% / 63 | 0.260 | 0.240 | +0.020 (+0.001 to +0.039) | about tied | +0.035 (+0.012 to +0.058) |
| +10% / 126 | 0.251 | 0.219 | +0.032 (+0.003 to +0.061) | about tied | +0.053 |
| +15% / 126 | 0.270 | 0.238 | +0.032 (+0.001 to +0.064) | about tied | +0.055 |

At 21 sessions it is level with B0. It never loses meaningfully. Middle probability levels are roughly
reliable (said 0.54 -> happened 0.57; said 0.64 -> happened 0.59); it over-forecasts in calm periods.

**Caveats.** Chosen after V5 failed, so exploratory, not a pre-registered test. It uses price data
only, not alternative data. It measures how turbulent prices are, not their direction: the same
formula gives the same probability for a 10% fall.

Reading on the last data date (9 Oct 2026, annualised volatility about 40%): about a 63% chance of a
close 10% or more above that day's within 63 sessions.
