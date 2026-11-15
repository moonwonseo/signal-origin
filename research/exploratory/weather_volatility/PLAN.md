# Weather -> price volatility study (local, exploratory) — plan written BEFORE any result

Question: does weather data help forecast how turbulent Coffee C prices will be over the next
h sessions, beyond what recent price turbulence already says? And does a weather-sharpened
volatility forecast make a better price-risk gauge?

## Target
Future realized volatility RV_h(t) = std of daily log returns over sessions t+1..t+h
(h = 63 primary, 21 secondary), log-transformed. Only complete windows count.

## Models (all forecast log RV_h; same rows for every model)
- V0  persistence: log RV over the last 63 sessions (no fitting). This is the volatility gauge's assumption.
- V1  price-only: ridge regression (alpha=1, train-only scaling) on log RV over the last 5, 21, 63
      sessions + day-of-year sine/cosine. Standard conventional benchmark (HAR-style).
- W1  V1 + single-point weather (rain and temperature anomalies, Sul de Minas) at t-4 days.
- W3  V1 + six-region crop-stage weather (frost nights, flowering rain anomaly, grain-fill dry spell) at t-4 days.
No tuning; settings fixed here.

## Evaluation
Annual expanding refits, test years 2012-2026, training from 2008, training windows must end
before each test year (purged). Out-of-sample MSE of log RV; gain = MSE(reference) - MSE(model).
Block-bootstrap ranges (block = h, 2000 draws, seed 590). Scopes: all years, 2012-2018, 2019+.
Breakdown by calendar quarter of the forecast date (reported, not used to choose anything).

## Product test
Gauge probability of a close >= +k% within h sessions: P = 2*(1 - Phi(ln(1+k) / (sigma*sqrt(h)))),
sigma = forecast daily vol (regression forecasts bias-corrected with exp(training residual variance / 2)).
Compare Brier of V0/V1/W1/W3 gauges and B0 on V5's labels, all 9 threshold/horizon cells.

## What counts as "weather works" (decided now)
1. Primary: W3 beats V1 at h=63 over 2012-2026, range above zero.
2. Holds over time: W3 not worse than V1 in both 2012-2018 and 2019+.
3. Product: the W3 gauge beats the V0 gauge on Brier for +10% within 63 sessions, range above zero.
All three -> weather-sharpened gauge is a credible alternative-data product.
1 only -> weather predicts turbulence but not enough to change the gauge: promising, not a product.
None -> report as a clean negative.
