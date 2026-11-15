# Positioning (CFTC) and certified stocks (ICE) study — plan written BEFORE any data is seen

Local exploratory study, same discipline as the weather study: question, models and bar fixed here.

## Question
Do speculators' positions (CFTC disaggregated futures-only, managed money) — and, if obtainable,
ICE certified Arabica stocks — improve (a) the price-risk gauge's odds of a large price rise, and
(b) volatility forecasts, beyond what current price volatility already says?
Unlike weather, positioning is directional: crowded shorts can be squeezed upward. So the primary
test is the up-spike probability, not only volatility.

## Data timing (conservative, fixed now)
- CFTC: positions as of Tuesday, published Friday afternoon; treated as usable from the FOLLOWING
  MONDAY (report date + 6 days), which also covers holiday-delayed releases. Most recent eligible
  report via as-of join; older than 14 days at use -> missing.
- ICE stocks (only if a source is found): daily figure usable from the next session.

## Features (fixed now; no search over alternatives)
- mm_net_share = (managed money long - managed money short) / open interest
- mm_net_change_4w = mm_net_share minus its value 4 reports earlier
- stocks (if available): log change of certified stocks over the last 63 sessions

## Models (annual expanding refits, test years 2012-2026, training from 2008, purged; same rows for all)
Spike probability (+k% within h sessions, V5 labels):
- G   = logistic regression on logit(volatility gauge probability)  [recalibrated gauge]
- GP  = G + positioning features
- GS  = G + stocks feature (only if stocks obtained)
- also reported: raw volatility gauge (V0) and B0 (historical frequency)
Volatility (log realized volatility over the next h sessions):
- V1  = price-only (log RV over 5/21/63 sessions + day-of-year sine/cosine)
- P1  = V1 + positioning features;  S1 = V1 + stocks feature (if obtained)
Logistic/ridge settings fixed: train-only scaling, L2, C=1 / alpha=1.

## Evaluation
Brier score (spikes), squared error of log volatility. Gains with block-bootstrap ranges
(block = h, 2000 draws, seed 590). Scopes: 2012-2026, 2012-2018, 2019+. All 9 threshold/horizon
cells reported (5/10/15% x 21/63/126 sessions).

## What counts as "positioning works" (decided now)
1. Primary: GP beats G for +10% within 63 sessions over 2012-2026, range above zero.
2. Holds over time: GP not worse than G in 2012-2018 or in 2019+.
3. Product: GP also beats the raw volatility gauge V0 and B0 for that target.
All three -> positioning-sharpened gauge is a credible product. 1 only -> promising, not a product.
None -> clean negative. The same bar applies to GS for stocks.
