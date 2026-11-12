# Modeling methods

The public package preserves the supplied project's B0/B1 calculations and isolates the V3/V4 numerical functions from archive-specific paths. The portable V4 runner uses explicit local inputs; it does not mutate the original frozen archive or recreate its pre-fit timestamp.

## Targets and calendar

The original baseline uses an endpoint event: price at t+63 is at least 1.10 times price at t. V4 uses a within-window event: any close from t+1 through t+h reaches that threshold, with h fixed at 63 or 21 sessions. Decimal source-price strings preserve the inclusive threshold. V4 requires a complete usable future window even when the threshold was crossed early. Missing sessions are preserved, never removed to shorten the horizon. The unfinished tail is unscored.

## Features

Price features are 21- and 63-session simple returns, the nonannualized sample standard deviation of 63 daily simple returns, and sine/cosine day-of-year seasonality. Features use information through the forecast origin.

A1 adds 30-calendar-day rainfall and temperature anomalies. The preserved reference convention uses earlier weather years, a circular ±7 day-of-year window, at least ten prior years, sample standard deviation, and four-decimal feature rounding. The current 30-day statistic may use current-year observations; only its reference distribution excludes the current year. The original min(day-of-year, 365) leap-year convention is retained. Historical source revisions remain unresolved.

A2 replaces the rainfall anomaly with the longest consecutive dry spell wholly inside a complete trailing 30-calendar-day window. Rainfall below 1 mm/day is dry; exactly 1 mm/day breaks the run. Gaps invalidate affected windows. Weather joins exactly to t−4 calendar days, without interpolation or another lag.

Freight features are log(index[m]) minus log(index[m−3]) and log(index[m−12]). All thirteen consecutive monthly values are required. A missing month invalidates the feature window. Observations enter strictly after month-end plus the selected 180- or 45-day assumption, using a backward join with a maximum age of 45 days since assumed availability. The public demo uses a generated index; the original study used a broad US deep-sea freight-cost proxy.

## Fitting and evaluation

B0 estimates one training-event frequency per annual fold. Other models use StandardScaler fitted only on the training rows, then L2 logistic regression with C=1, lbfgs, intercept, no class weights, max_iter=2000, tolerance=1e−8 and seed=42. A fresh model is fitted for each feature set and fold. Nonconvergence stops the fit.

All seven models share eligible origins and labels within each policy/horizon/fold. Training includes only eligible earlier origins whose full label-end date is strictly before the first supplied session of the test year. Earlier test outcomes may enter later annual training after maturity. There is no within-year refit, hyperparameter search, imputation or post-hoc calibration.

Brier loss is primary, on the binary 0–1 scale. Log loss, ROC AUC, mean probability and five fixed calibration bins are descriptive. ROC AUC is undefined for single-class subsets. Pooled B0 AUC may differ from 0.5 because its probability changes between folds. An earliest-disjoint-window diagnostic does not prove statistical independence.

The portable runner exports full, from-2024, annual and disjoint-window comparisons. Unlike the frozen archive's fixed original-date subset, its from-2024 subset extends to the last complete origin in the supplied data. That scope difference must be stated when comparing outputs.

## Limits

The source history was previously inspected. Date-causal calculations do not guarantee point-in-time vintages. Monthly sources and overlapping labels yield dependent daily rows. Original vendor continuous-contract prices had unresolved roll-construction qualifications. One weather point does not describe the whole crop. No independent confirmation, causal identification, operational live test or buyer-savings calculation has been completed. Synthetic output tests software mechanics only.
