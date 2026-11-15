# Autoresearch journal (reflection after each iteration, and the plan for the next one)

Plan: `05_studies/Autoresearch_PLAN.md`, sha256 a145c605e762...eff9. Agent: Claude. All runs on the Mac mini.

## Before iteration 1: baselines (N = 10, RATIO necessary 0.43)
| Id | Model | RATIO | Halves | Years + | AUROC |
|---|---|---|---|---|---|
| B0 | Steady buying | 0.000 | | | |
| B1 | Always early | +0.098 | +0.09 / +0.11 | 6/14 | |
| B2 | Always late | -0.098 | | 8/14 | |
| B3 | Momentum, 63 sessions | -0.026 | +0.26 / -0.32 | 5/14 | |
| B4 | Market-only logistic (13 features) | -0.021 | +0.06 / -0.10 | 7/14 | 0.538 |
| B5 | B4 + Nino 3.4 | -0.221 | -0.36 / -0.08 | 5/14 | 0.506 |

Harness checks: features equal the Direction study (1e-14). Perfect foresight of the label gives RATIO 2.51.
200 random monthly strategies give a standard deviation of 0.26 (plan value 0.28).

Reflection:
- Nothing on hand has skill at 63 sessions. B5 (ENSO) is the worst: the ENSO lead at 21 sessions does not
  carry to this horizon and this score.
- B4 uses 13 features and can train only from 2006 (USD/BRL gap). About 550 training rows for 2009. With about
  56 independent windows, 13 fitted weights is too many. Simple rules with an economic reason are the better start.
- Current best: B1 (always early, +0.098). A new best needs about +0.3 RATIO above it (step rule).

Idea queue (in order). Priors come from published commodity factors, not from knowledge of coffee history:
1. Trend: sign of the 12-month return (time-series momentum).
2. Carry: term structure from the roll-day price gaps (data on hand; roll days are calendar dates).
3. Value: price against its 5-year mean (supply answers slowly to price).
4. Combination of 1-3 (vote or small logistic model, training from 2001).
5. Alt data, one block at a time on the best market model: Brazil rain deficit in flowering/grain-fill;
   frost; positioning extremes; ENSO-type indices (SOI, IOD); USDA stocks-to-use.
6. Other markets: dollar index, sugar, Colombian peso.
7. Model type (forest) and position rule (dead band, smoothing) only on a base that already has skill.

## Iteration 1 - c01: 12-month trend rule -> RATIO -0.022, rejected
- Result: halves +0.34 / -0.40, 8 of 14 years positive, AUROC 0.555, hit 55%.
- Reading: trend had value in 2009-2015 and the opposite in 2016-2022. The label hit rate is above 50%, but the
  money is not there: the rule is correct in quiet periods and incorrect at turns, where the moves are large.
- Worked: nothing. Did not work: a pure trend rule at this horizon.
- Plan for iteration 2: carry from the roll-day gaps (queue item 2). It is a different mechanism (cost of
  holding stock, scarcity), so it is a real second probe and not a variant of trend.

## Iteration 2 - c02: "carry" from the marked roll days -> RATIO +0.425 (first series), then VOID
- The share of "buy early" was 55%. I expected mostly "buy late", because coffee is usually in contango.
  This did not agree with the hypothesis, so I checked the feature (not the score).
- Finding 1 (defect in the eval data): the raw return on the 134 marked roll days is an ordinary return. The
  gap between contracts is in the next session (+1.1% mean; +2.3% in 2017-20; -0.7% in 2021-26). The plan's roll
  adjustment removed the wrong day and left the gaps in the returns. Repair: eval revision 1 sets both days to
  zero. See `05_studies/Autoresearch_PLAN_ADDENDUM_1.md`. All runs were scored again; N did not change.
- After the repair: always-early -0.062 (it was +0.098; the profit came from contract gaps, which a buyer does
  not earn), always-late +0.062, 63-session momentum +0.028, market-only logistic -0.153, with ENSO -0.007,
  c01 (12-month trend) +0.093 with halves +0.50 / -0.34.
- Finding 2: the c02 feature is not carry. It is the mean of four ordinary daily returns. Score after the
  repair +0.434, 6 of 14 years positive. No mechanism -> void (addendum 1). Current best goes back to B2.
- Worked: the habit to check a result that does not fit its hypothesis. Did not work: the first carry measure.
- Plan for iteration 3: the real carry test. Gap = raw return of the session after the marked roll day (known
  at that close). Mean of the last 4 gaps (about 10 months). Buy early in backwardation, late in contango.

## Iteration 3 - c03: carry from the correct gap day -> RATIO -0.340, rejected
- Result: negative in both halves (-0.43 / -0.24). AUROC 0.442: the relation has the opposite sign.
- Reading: in this market, backwardation comes with price spikes that later fall back, and contango comes with
  low prices that later recover. The term structure acts as a price-level signal, not as a carry signal.
- Worked: the gap measure itself (79% "late" before 2021, as expected for contango). Did not work: the carry rule.
- I do not flip the sign of c03. That would be a fit to the result. The opposite-sign idea is the value
  hypothesis, which was already item 3 of the queue, so I test it directly with its own measure.
- Plan for iteration 4: value rule. Raw front-month price against its own 5-year mean: cheap -> buy early.

## Iteration 4 - c04: value rule (price against 5-year mean) -> RATIO -0.129, rejected
- Result: -0.13 in each half. AUROC 0.44, the opposite sign again (a high price was followed by a higher mean price).
- Reading of iterations 1, 3, 4 together: the three standard futures factors give +0.09 (trend), -0.34 (carry),
  -0.13 (value). The label shows a weak trend relation (AUROC about 0.55), but it gives no saving: the rule is
  correct in quiet periods and incorrect at the large turns. Price history alone does not time purchases.
  This agrees with a liquid futures market. I stop single probes of price features.
- Worked: nothing. Current best stays B2 (always late, +0.062).
- Curated queue (alt data, one mechanism for each iteration, sign fixed by economics before the run):
  5. Brazil rain deficit, last 90 days (dry -> smaller crop -> buy early).
  6. Brazil heat-and-dry stress (temperature z minus rain z).
  7. Frost event in Brazil (Jun-Aug), three-state rule: early after a frost, else steady.
  8. Speculator positioning at extremes (crowded long -> buy late), three-state rule.
  9. ENSO state (La Nina -> dry south Brazil -> buy early).
  10. New source: root-zone soil moisture, Brazil (a direct drought measure for trees).
  11. New source: dollar index trend. 12. New source: USDA stocks-to-use. 13. Other origins' weather.
  Then: small fitted models and combinations of the blocks that show a positive RATIO; position rule last.

## Iteration 5 - c05: Brazil rain deficit rule -> RATIO -0.110, rejected
- Result: halves -0.24 / +0.02. The rule said "early" on 75% of days (beta +0.52).
- Reading: the rain z-score is measured against all earlier years from 1981. Brazil became drier, so the
  z-score is below zero most of the time. The rule was mostly "always early", not a drought signal.
- Worked: nothing. Lesson: a weather level needs the removal of its slow drift before a sign rule.
- Plan for iteration 6: heat-and-dry stress (temperature z minus rain z, 90 days), minus its own 5-year mean.
  Both changes follow from the lesson and from queue item 6; it is one new feature, not a tuning of c05.

## Iteration 6 - c06: Brazil heat-and-dry stress, drift removed -> RATIO +0.510, ACCEPTED (new best)
- Result: halves +0.26 / +0.77, 9 of 14 years positive, AUROC 0.578, hit 58%, early on 53% of days, 5.5 position
  changes a year, saving 2.0% of yearly cost. C2-C5 and C7 are satisfied. SCORE +0.016 at N = 16.
- Reading: the first candidate with a mechanism and a positive score. The lesson of c05 (remove the drift)
  made the difference. Caution: it is 1 success in 6 tries, the range is +0.03 to +0.93, and at N = 40 the
  necessary RATIO is 0.61. c06 alone will not pass at the end. The placebo test (C6) will show if the time
  link is real; the plan runs it one time at the end.
- Worked: weather stress as "news against the recent climate". Did not work before: weather as a raw level.
- Strategy from here: (a) find a second signal that is independent of weather, because two independent
  signals of 0.4-0.5 combine to about 0.6-0.7; (b) then improve the weather measure along its mechanism
  (soil moisture, frost, other origins); (c) position rule last.
- Plan for iteration 7: speculator positioning at extremes (queue item 8). Three states: crowded long -> buy
  late, crowded short -> buy early, else steady.

## Iteration 7 - c07: speculator positioning at extremes -> RATIO -0.149, rejected
- Result: halves -0.48 / +0.24. Hit rate 36% against the label: extreme positions were followed by MORE of
  the same price direction, not less.
- Reading: positioning follows the trend. It adds nothing that the price does not show, and the trend rule
  itself failed (c01). Third failure of CFTC data in this project. I drop this block.
- Worked: nothing. Current best: c06 (+0.510).
- Plan for iteration 8: ENSO state (queue item 9). La Nina brings dry weather to south Brazil, so it can lead
  the stress signal by months. Three states by the usual +-0.5 limit. If it has skill, it is a second signal
  that is partly independent of the observed weather.

## Iteration 8 - c08: ENSO state rule -> RATIO -0.001, rejected
- Result: halves +0.20 / -0.20. No skill.
- Reading: ENSO does not lead the purchase timing at this horizon. With B5 (-0.007) this is the second ENSO
  failure at 63 sessions. The ENSO lead of the earlier study (21 sessions) does not transfer. I drop ENSO-type
  indices; SOI, IOD, PDO and MJO stay unused, which saves source budget.
- Worked: nothing. Score so far: 1 mechanism with skill (weather stress), 6 without.
- Decision: use new source 1 (NASA POWER root-zone soil moisture, humidity, radiation). Soil moisture is the
  direct drought measure for trees. Download started on the Mac mini.
- Plan for iteration 9: the same stress measure for the other origins (Colombia, Central America, Mexico,
  Ethiopia, about half of world arabica). If the mechanism is real, their stress must also help, and the two
  can form a world signal. Weaker prior: in the wet tropics, too much rain can be the damage.

## Iteration 9 - c09: stress of the other origins -> RATIO +0.133, rejected
- Result: halves -0.26 / +0.54, 9 of 14 years positive, AUROC 0.49.
- Reading: positive but weak and not stable. The other origins do not confirm the Brazil signal strongly.
  This is plausible: Brazil is the marginal supplier and the only origin with a large single harvest; in the
  wet tropics heat-and-dry is not the main damage. It also means that c06 has no confirmation from a second
  region yet. I keep "world stress" out of the queue.
- Worked: nothing new. Current best: c06 (+0.510).
- Plan for iteration 10 (soil-moisture download still runs): add frost to c06. Frost is the classic Brazil
  supply shock and it is outside the heat-and-dry measure (it happens in the cool, dry season). One change:
  "buy early" for 90 days after a frost day in Jun-Aug, else the c06 rule.

## Iteration 10 - c10: frost added to c06 -> RATIO +0.484, rejected (c06 has +0.510)
- Result: the share of "early" days went from 53% to 59%, and the score went down a little.
- Reading: a minimum below 5 C on a 50-km grid cell happens in most winters. It is not a damaging frost. The
  measure has too many false alarms. A sharper threshold would be tuning on the result, so I stop here.
- Worked: nothing. Did not work: frost at grid scale.

### Summary after 10 iterations
One mechanism has skill: Brazil heat-and-dry stress against the recent climate (c06, +0.510). Price factors,
positioning, ENSO, other origins and frost have none. At N = 40 the necessary RATIO is 0.61.
Curated plan for iterations 11-20:
- 11: root-zone soil moisture, Brazil (new source 1), as its own rule. A second view of the same mechanism.
- 12: if 11 is positive, agreement rule of stress and soil moisture (act only when both agree).
- 13-15: signals that are independent of weather: dollar index trend (new source), arabica-robusta price
  spread (new source), USDA stocks as a condition for the weather signal (new source).
- 16-20: small fitted models on the features that showed skill; then the position rule.

## Iteration 11 - c11: Brazil root-zone soil moisture rule (new source 1) -> RATIO +0.408, rejected
- Result: halves -0.02 / +0.86, 9 of 14 years positive, AUROC 0.52. Below c06 (+0.510), so not a new best.
- Reading: a second, independent measurement of the same mechanism also gives a positive score. This is
  mild support for "Brazil drought stress has skill". But both measures earn most of it in 2016-2022. The
  result may rest on one or two large drought periods. The halves constraint (C3) fails for soil moisture.
- Worked: drought measured against the recent seasonal normal. Did not work: nothing new.
- Plan for iteration 12: agreement rule. Buy early only when stress AND soil moisture say "dry", buy late only
  when both say "wet", else steady. Mechanism: two noisy measures of one state; acting on agreement removes
  the days where the state is unclear. One change from c06 (a second feature as a confirmation).

## Iteration 12 - c12: agreement of stress and soil moisture -> RATIO +0.512, rejected (c06 has +0.510)
- Result: halves +0.14 / +0.91, 8 of 14 years positive. The same score as c06 with fewer active days.
- Reading: the two measures hold the same information. A confirmation by a second measure of the same state
  adds nothing. The weather block gives about 0.5 and more views of the same drought will not lift it.
- Worked: nothing new. Did not work: confirmation inside the weather block.
- Curated plan: the only way to 0.6+ is a signal that is independent of Brazil weather.
  13: dollar index trend (new source 2; a strong dollar lowers commodity prices in dollars).
  14: USD/BRL trend (on hand; a weak real makes Brazilian growers sell).
  15: agreement rule of c06 with the best independent signal, if one has a positive score.

## Iteration 13 - c13: dollar index trend (new source 2) -> RATIO +0.197, rejected
- Result: halves 0.00 / +0.40, 7 of 14 years positive, 15 position changes a year.
- Reading: weakly positive, correct sign, not stable. Too weak alone. It can still be the independent partner
  of the weather signal if nothing better comes.
- Plan for iteration 14: USD/BRL trend (on hand). It is the currency of the marginal producer, so the link to
  coffee is more direct than the dollar index. Same rule form for a clean comparison.

## Iteration 14 - c14: USD/BRL trend -> RATIO +0.073, rejected
- Result: halves +0.25 / -0.11. No stable skill. The dollar index (c13, +0.197) is the better currency signal.
- Reflection on iterations 1-14 (break-down of the saved results by year and by side; no new score):
  - c06 earns on both sides (early days +0.41, late days +0.65) and in 9 years that are spread over the
    period (2010, 2012, 2014, 2016, 2018-2022). It does not rest on one event. This is good.
  - Its losing years are 2009, 2011, 2013, 2015, 2017: the odd years. Brazil has a two-year crop cycle, so
    this may have a cause, but I have no prior for its direction. A rule on odd/even years would be a fit to
    the result. I record it and I do not use it.
  - Savings of c06 and the dollar rule (c13) are not correlated (-0.09). But an equal vote of a 0.51 signal and
    a 0.20 signal gives about 0.50: the weak partner dilutes. A vote needs a partner above about 0.25.
- Curated plan for iterations 15-20:
  15: fitted weights. Logistic regression on the four features that have a mechanism and a positive score
      (Brazil stress, soil moisture, other-origin stress, dollar trend). Training rows only. A model can give
      the weak signals a small weight, which a vote cannot.
  16-17: tree methods (random forest, then boosting) on a wider feature set, as agreed in the model space.
  18: act only when the stress is clearly high or low (thresholds from training terciles).
  19-20: season-to-date stress; stocks or robusta spread (new sources) if budget remains.

## Iteration 15 - c15: logistic regression on 4 signals -> RATIO +0.308, rejected
- Result: halves +0.31 / +0.31, 9 of 14 years positive, but "late" on 77% of days (beta -0.57).
- Reading: the fitted model is stable but weaker than the sign rule. The intercept learned the falling market
  of the training years and pushed the position to "late". Fitted weights did not use the weak signals better.
  The unfitted rule stays the better form for a signal of this strength.
- Worked: stability in both halves. Did not work: fitted weights.
- Plan for iteration 16: random forest on 16 features (6 weather, 7 price, 2 currency, 1 ENSO). Reason: a
  forest can find conditions (stress matters in some seasons or price states) that a linear model cannot.
  Limits from the plan: depth 4, 500 trees, 50 rows in a leaf, mean of 5 seeds.

## Iteration 16 - c16: random forest on 16 features -> RATIO -0.019, rejected
- Result: halves -0.32 / +0.30, AUROC 0.43 (worse than chance on the label).
- Reading: the forest fitted the regimes of the training years and they did not continue. One error of mine:
  the USD/BRL feature has a data gap, so the training started in 2006 and not in 2001 (683 rows for 2009).
  The run showed a score, so it counts.
- Worked: nothing. Did not work: many features with a flexible model. Same lesson as the earlier studies.
- Plan for iteration 17: boosting (LightGBM, depth 3, 300 trees, mean of 5 seeds) on the same set without
  USD/BRL (15 features), so the training starts in 2001. This is the fair test of the tree family with all
  the training data. If it fails, I close the "wide model" branch and go back to the weather mechanism.

## Iteration 17 - c17: LightGBM on 15 features -> RATIO -0.329, rejected
- Result: negative in both halves, 4 of 14 years positive, AUROC 0.42.
- Reading: with all training years the boosted model is worse than the forest. The tree family fits the
  training regimes; about 30 to 80 independent windows cannot support 15 features. I close the "wide model"
  branch (c15, c16, c17). The unfitted weather rule stays the only form with skill.
- Worked: nothing.
- Reflection on the weather mechanism (c06): the measure uses the last 90 days in all seasons. But in the
  Brazilian dry season (May-Aug) normal rain is near zero, so a rain z-score is mostly noise, and heat is not
  a crop risk then. The crop is made from flowering to grain fill (Sep-Apr). From June to October, c06 acts
  on values that have no agronomic meaning.
- Plan for iteration 18: stress of the crop season to date. Mean of (temperature z - rain z) from October to
  the current day, held from May to September at the end-of-season value; minus the same quantity of the
  last 5 years. One conceptual change from c06: the time window follows the crop calendar.

## Iteration 18 - c18: stress of the crop season to date -> RATIO +0.553, rejected by the step rule (c06: +0.510)
- Result: halves +0.21 / +0.92, 11 of 14 years positive (c06: 9), 2.6 position changes a year (c06: 5.5),
  beta +0.03, AUROC 0.595, hit 60%, saving 2.2% of yearly cost. All constraints C2-C5 are satisfied.
- Reading: the crop-calendar window is better on each value, but the paired difference to c06 is +0.04 with a
  20th percentile of -0.08. The step rule says "not shown", so c06 stays the current best. I respect the rule.
  The agronomic reasoning gave the expected direction (fewer changes, more positive years), which supports
  the mechanism more than the score does.
- Worked: crop-calendar window. Not shown: that it is better than c06.
- Open question for the presentation and for the next step: is the signal drought, heat, or both?
- Plan for iteration 19: season rain deficit only (the temperature part removed). If rain alone is equal or
  better, heat adds noise and the measure can be simpler. Parent: c18.

## Iteration 19 - c19: season rain deficit only -> RATIO +0.339, rejected
- Result: halves -0.23 / +0.94, 9 of 14 years positive. Below c18 (+0.553).
- Reading: rain alone is weaker and fails in the first half. The temperature part carries information, most
  of all in 2009-2015. The combined heat-and-dry measure is the correct one.
- Plan for iteration 20: the other half of the question, season heat only. If heat alone is as good as the
  combination, the measure is "heat", not "heat and drought". This closes the question with one more run.

## Iteration 20 - c20: season heat only -> RATIO +0.569, rejected by the step rule (c06: +0.510)
- Result: halves +0.17 / +0.99, 11 of 14 years positive, 2.5 position changes a year, hit 60%, AUROC 0.597.
- Reading: heat alone equals the combination (c18, +0.553) and is far above rain alone (c19, +0.339). The
  signal is growing-season temperature against the recent normal. This was not my expectation (I expected
  drought). Caution 1: a temperature anomaly is a slow series; it can act as a "clock" for market regimes.
  The placebo test (C6) is the check for that. Caution 2: the second half gives most of the score in all
  weather candidates.
- Worked: season heat. Not shown: that it beats c06 (paired 20th percentile -0.04).

### Summary after 20 iterations
| Block | Best RATIO | Verdict |
|---|---|---|
| Price factors (trend, carry, value) | +0.09 | no skill |
| Positioning, ENSO | -0.00 | no skill |
| Currency trends (dollar index, USD/BRL) | +0.20 | weak |
| Fitted models (logistic, forest, LightGBM) | +0.31 | worse than rules |
| Brazil weather stress, 90 days (c06, current best) | +0.51 | skill |
| Brazil crop-season stress / heat (c18, c20) | +0.55 / +0.57 | skill, same mechanism |
The plateau is 0.5-0.57. The necessary RATIO at N = 40 is 0.61.
Curated plan for iterations 21-30 (10 left):
- 21: sharper heat measure: daily MAXIMUM temperature of the season (heat damage comes from hot afternoons).
- 22: memory of the previous season (the tree's growth in one season makes the crop of the next).
- 23: season heat AND recent 90-day stress in one agreement rule (season state + recent news).
- 24: act only on clear signals (thresholds from training terciles).
- 25-27: independent partner again (dollar vote; stocks condition from USDA if the budget allows).
- 28-30: consolidation of what passed; no new blocks.

## Iteration 21 - c21: season maximum temperature -> RATIO +0.596, rejected by the step rule (c06: +0.510)
- Result: halves +0.24 / +0.97, 11 of 14 years positive, hit 60%, AUROC 0.604, saving 2.3% of yearly cost,
  beta +0.02. SCORE +0.021 at N = 31. Paired 20th percentile against c06: -0.03 (very near the limit).
- Reading: three steps along the mechanism each gave a small gain (0.553 -> 0.569 -> 0.596): crop calendar,
  heat only, afternoon heat. Each step alone is inside the noise, but the direction is consistent with the
  agronomy. c21 is the best single rule. It is not "the current best" by the plan's rule.
- Plan for iteration 22: agreement rule of the season heat (c21) with the recent 90-day stress (c06). Reason:
  the season value is the state of the crop; the 90-day value is the recent news. Act when both agree, else
  steady. This is the first combination of two rules that both have skill.

## Iteration 22 - c22: agreement of season heat and 90-day stress -> RATIO +0.612, ACCEPTED (new best)
- Result: halves +0.28 / +0.96, 11 of 14 years positive, hit 62%, AUROC 0.612, active on 78% of days, 4.2
  position changes a year, saving 2.2% of yearly cost. Paired 20th percentile against c06: +0.04. All
  constraints C2-C5 and C7 are satisfied. SCORE +0.032 at N = 32; at N = 40 the same RATIO gives +0.007.
- Reading: the first combination of two rules with skill passes the step rule. The gain is small and the
  final margin is a knife edge. The first half (+0.28) stays much weaker than the second (+0.96).
- Worked: state + news agreement inside the weather block. 
- Reflection on the 8 iterations left: a weaker independent signal cannot help (a vote dilutes, and using it
  only on the "steady" days also lowers the ratio; both follow from the arithmetic). More variants of the
  heat measure will mostly fit noise. The most useful runs now are robustness checks of c22, because they tell
  Celine if the result is fragile. They count as iterations like all scored runs.
- Plan: 23 = c22 with weather 10 days old (is fresh data necessary?). 24 = c22 with a 10-year normal in place
  of 5 years (is the "recent climate" choice critical?). Then 25-28 mechanism ideas with a clear reason
  (previous-season memory, humidity), 29-30 consolidation.

## Iteration 23 - c23: c22 with weather 10 days old -> RATIO +0.495, rejected
- Result: halves +0.24 / +0.77, 11 of 14 years positive. The hit rate and AUROC do not change (62%, 0.612).
- Reading: six more days of delay cost 0.12 of RATIO. The label skill is the same, so the loss comes from
  the days near a change of position: there the fresh data matter. The result still stands (11 of 14 years),
  but it depends on weather data that arrive in 4 days. Real-time POWER values are less exact than the final
  values in our file. This is a real risk for use, and it must be in the report.
- Plan for iteration 24: second robustness check. "Normal" = last 10 years in place of 5, for the season
  heat part. The idea "news against the recent climate" must not depend on one window length.

## Iteration 24 - c24: c22 with a 10-year normal -> RATIO +0.473, rejected
- Result: halves +0.28 / +0.69, 9 of 14 years positive.
- Reading of the two robustness checks: 0.50 (older data) and 0.47 (longer normal) against 0.61 for c22. The
  sign and the stability stay; the size does not. c22 is the top of a group of similar rules, so its 0.61 has
  a selection gain. My honest estimate of the weather skill on these years is about 0.5, and this value is
  itself the best of several blocks.
- Decision for the 6 iterations left: no more tuning of the heat measure. I use the runs for the two
  mechanism ideas that are open (25, 26) and for the untested independent sources of the whitelist (27-29),
  so that the final table shows each block one time. Iteration 30 is the consolidation run.
- Plan for iteration 25: arabica-robusta price spread (new source 3, World Bank monthly). Mechanism:
  substitution. When arabica is expensive against robusta, roasters change their blends and arabica demand
  falls. This is a relative value, different from the price-level value rule that failed (c04).

## Iteration 25 - c25: arabica-robusta spread (new source 3) -> RATIO -0.363, rejected
- Result: negative in both halves, AUROC 0.36: a wide arabica premium was followed by a still higher arabica
  price. Substitution does not act at this horizon; the premium moves with the arabica trend.
- Reading: third value-type rule with the opposite sign (c03, c04, c25). Coffee prices did not revert within a
  quarter in 2009-2022. I do not test more value ideas. (The World Bank file at the whitelist address ends in
  December 2024; it would need a newer file for use after that date.)
- Plan for iteration 26: memory of the previous season. In arabica, the branches that grow in one season
  carry the fruit of the next, so heat in the last season also lowers the coming crop. One change from c22:
  the season heat is the mean of this season's and the last season's anomaly.

## Iteration 26 - c26: memory of the previous season -> RATIO +0.550, rejected
- Result: halves +0.32 / +0.79, 8 of 14 years positive (c22: 11). The two-season mean is slower and worse.
- Reading: the market reacts to the heat of the current season. The two-year cycle gives no extra timing
  value. This closes the mechanism ideas for the season measure.
- Plan for iteration 27: sugar trend (new source 4). Sugar and coffee share the Brazilian real, Brazilian
  weather and the same funds. A 126-session trend is used (not 63) because the sugar chain has contract gaps
  that add noise to short returns.

## Iteration 27 - c27: sugar trend (new source 4) -> RATIO +0.336, rejected (below c22)
- Result: halves +0.34 / +0.33, 10 of 14 years positive, hit 63%, AUROC 0.629 (the highest label skill of
  all runs). The score is equal in the two halves, which no weather rule shows.
- Reading: the first signal outside weather that is stable. It is market data, not alt data. Caution: the
  sugar chain has contract gaps like KC=F had, so a part of the 126-session "return" is the sugar term
  structure. That is still information known at t-1, but its meaning is "sugar trend plus sugar carry".
- By the arithmetic of iteration 14, a partner above about 0.25 with independent savings can lift a vote.
- Plan for iteration 28: equal vote of the weather rule (c22) and the sugar trend. Position = sign of the sum:
  both agree -> act; weather says early and sugar says late (or the reverse) -> steady; weather steady ->
  follow sugar. One change from c22: one more feature in the vote.

## Iteration 28 - c28: vote of the weather rule and the sugar trend -> RATIO +0.576, rejected (c22: +0.612)
- Result: halves +0.47 / +0.67, 12 of 14 years positive (the most of all runs), hit 68%, AUROC 0.661,
  precision for large rises 72%, beta 0.00. The RATIO is a little below c22, so the step rule keeps c22.
- Reading: the vote did not lift the RATIO, but it made the result more even: the first half went from +0.28
  to +0.47 and two more years are positive. For a purchasing team, c28 is the more robust rule; by the plan's
  score, c22 stays the candidate. I report both and I do not change the selection rule.
- Plan for iteration 29: USDA world stocks-to-use (new source 5), the last untested block of the whitelist.
  Low stocks -> any shortfall moves the price more -> buy early. The data are 1 to 2 years old by the plan's
  delay rule, so my prior is weak. I checked the series before the run: it has a break between 2001 and 2002
  (coverage change), so only marketing years from 2002 are used.

## Iteration 29 - c29: USDA world stocks-to-use (new source 5) -> RATIO +0.155, rejected
- Result: halves +0.23 / +0.09, 5 of 14 years positive, less than one position change a year.
- Reading: the sign is as expected but the data are too old and too slow to time purchases in a quarter.
  All blocks of the whitelist that I planned to test now have one run. Unused: SOI, IOD, PDO, MJO (dropped
  after two ENSO failures), cocoa, crude oil, Colombian peso (weak priors). 5 of 6 new sources were used.
- Plan for iteration 30 (consolidation): one vote for each of the three signals with skill: season heat (c21),
  90-day stress (c06), sugar trend (c27). Position = the majority. Difference from c28: when the two weather
  signals agree they decide; sugar decides only when they disagree. The rule is never "steady".

## Iteration 30 - c30: majority vote of three signals -> RATIO +0.579, rejected (c22: +0.612)
- Result: halves +0.30 / +0.88, 11 of 14 years positive, hit 62%. Near c22 and c28, not better.
- Reading: all the rules built from the weather signal, with or without sugar, are in a band of 0.55-0.61.
  The loop reached a plateau at iteration 22. The budget of 30 iterations is used. No iteration 31.

## After the loop
- Best candidate by the plan's rule: c22 (season heat and 90-day stress agree). RATIO +0.612, necessary
  0.605 at N = 40, so SCORE = +0.007. C1-C5 and C7 are satisfied.
- C6 placebo (17 runs with the weather rotated by 2 to 18 years): real +0.612; placebo mean -0.051, range
  -0.597 to +0.723. One rotation (13 years) is above the real value. The plan needs "above all 17". C6 FAILS.
  The real value is second of 18 (p about 0.11).
- Development verdict by the plan: NOT a predictor. The score passed by 0.007 and the placebo test failed.
- The plan permits one look at the test period 2023-Oct 2026 in this case, labelled exploratory. I take it now
  for c22, and for no other candidate.
- Final test, one look (exploratory): c22 on 2023-Oct 2026 -> RATIO +0.040 (range -0.92 to +0.95), 2 of 4
  years positive, saving 0.15% of yearly cost. FAIL (necessary 0.5).

## Final reflection
- Verdict: no predictor found. The plan's three guards did their work: the score correction left a margin of
  only 0.007, the placebo test failed, and the test period did not confirm.
- What I believe after 30 iterations: (1) price history, positioning, ENSO and stocks do not time coffee
  purchases at a quarter horizon; (2) fitted models are worse than fixed-sign rules with this sample size;
  (3) Brazil growing-season heat is the only lead, with a skill of about 0.5 on 2009-2022 that is not
  confirmed outside those years; (4) the price series had a roll-adjustment defect that changes the P&L
  values of the earlier studies.
- What I would not do: an iteration 31, or a second look at the test period.
- What can still be done with data that the loop did not touch: the weather rules are unfitted, so the years
  2001-2008 are an unused period for them. This needs its own plan and Celine's approval.

# Iterations 31-100 (addendum 2; Celine's instruction of 15 Nov)
Start state: current best c22 (+0.612). N = 40. Necessary RATIO at N = 110: 0.71.
The test period was seen one time (c22: +0.04). I know now that the weather rule did not hold in 2023-2026.
Strategy, written before iteration 31:
- Weather gives about 0.5 on the development years and was not confirmed. More weather variants will not
  change this. A pass needs two or more signals that are independent of weather, each with real skill, and a
  vote of them. The search is for independent signals, one mechanism for each run.
- Order of the blocks: (A) other markets as a common factor (sugar gave +0.34 with equal halves);
  (B) an independent weather data set and a real water balance (ERA5), vegetation from satellites (MODIS);
  (C) hedging pressure of producers (CFTC, on hand); (D) macro risk series; (E) Brazil export flow;
  (F) votes of the signals that have skill; no fitted model with many features.
- New market series downloaded for block A (Yahoo; data cards 6-17): cocoa, cotton, corn, soybeans, crude oil,
  gold, copper, Brazil equity fund (EWZ), S&P 500, VIX, US 10-year yield, USD/COP. Robusta and orange juice
  are not available from this vendor.

## Plan for iteration 31
Farm-commodity breadth. Sugar alone gave +0.336. If the cause is a common factor of farm commodities (macro
demand, dollar, fund flows) that coffee follows with a delay, the share of rising farm markets must be a
cleaner measure than one market.

## Iteration 31 - c31: farm-commodity breadth -> RATIO +0.269, rejected
- Result: halves +0.09 / +0.46, 10 of 14 years positive. Below sugar alone (+0.336, equal halves).
- Reading: the common farm-commodity factor is weaker than sugar. So the sugar link is not "all farm
  commodities move together". The link that sugar and coffee share and the others do not is Brazil.
- Plan for iteration 32: test the Brazil factor directly with the Brazil equity fund (EWZ, in dollars). It
  holds the Brazilian real and Brazil risk in one price, without the contract gaps of a futures chain.

## Iteration 32 - c32: Brazil equity fund trend -> RATIO +0.202, rejected
- Result: halves +0.35 / +0.05, 9 of 14 years positive.
- Reading: positive, weak, not stable. The market-trend family now has six runs: sugar +0.34, farm breadth
  +0.27, Brazil equities +0.20, dollar +0.20, coffee's own trend +0.09, USD/BRL +0.07. All are small and
  positive. This looks like one weak common trend factor of about 0.2-0.3, with sugar at its top by chance
  or by the Brazil link. More single markets will not add much; I stop single market-trend probes.
- A different kind of signal is necessary. Started in the background: ERA5 reanalysis for the Brazil nodes
  (an independent weather data set, with reference evapotranspiration for a real water balance).
- Plan for iteration 33: the frost-risk calendar. Before the Brazilian winter the market adds a premium for
  frost risk; when winter passes without a frost the premium goes away. A buyer must buy before the premium
  builds and wait while it decays. This uses no data, only the calendar and one mechanism.

## Iteration 33 - c33: frost-risk calendar rule -> RATIO -0.163, rejected
- Result: negative in both halves. There is no usable frost-premium season in 2009-2022.
- Reading: a pure calendar rule has no value. Seasonality stays out.
- Plan for iteration 34: a falsification test of the weather lead. The same season-heat rule (c21), but with
  the temperature of the OTHER origins (Colombia, Central America, Mexico, Peru, Ethiopia) in the same Oct-Apr
  window. Their crop calendars are different, so this measure has no crop meaning. If it scores like Brazil,
  the "Brazil heat" signal is a tropical climate clock (for example ENSO warmth), not crop news.

## Iteration 34 - c34: falsification test, season heat of the other origins -> RATIO -0.065
- Result: halves +0.10 / -0.24, AUROC 0.51. No skill.
- Reading: this is a "good" failure. The season-heat signal exists only with the Brazil regions. It is not a
  general tropical warmth or ENSO clock. This supports the crop mechanism on the development years (it does
  not repair the failed placebo and test).
- Data access checked: ERA5 (Open-Meteo) works and is downloading; NASA MODIS vegetation (ORNL) and FRED are
  not reachable from the Mac mini; the Brazilian government export statistics (Comex Stat) work.
- Plan for iteration 35: Brazil export flow (new source 19, official). Mechanism: the monthly volume of green
  coffee that leaves Brazil shows how much coffee reaches the market. A flow above the seasonal normal means
  ample supply -> buy late; below normal -> buy early. Independent of weather and of market trends.

## Iteration 36 - c36: export flow, second try -> RATIO -0.055, VOID (data defect again)
- The service applies the month range of the request to each year, so a request that ends in "2026-10" returns
  only January to October of all years. My completeness check found the gap, but the command chain did not
  stop, and the run used a file with 10 missing months in 2017-2021. Void; it counts in N.
- Two iterations lost to one data problem. Repair: one request to "2026-12" gives 358 of 358 months; the
  feature code now stops (assert) when a month is missing, so this cannot give a score again.
- Plan for iteration 37: the export-flow hypothesis, third time, with the complete file.

## Iteration 37 - c37: Brazil export flow, complete data -> RATIO -0.180, rejected
- Result: halves -0.07 / -0.29, AUROC 0.42, "late" on 76% of days.
- Reading: the sign is the opposite of the hypothesis. Exports rise when demand is strong and prices rise;
  the flow follows the market and does not lead it. Also the volume grows over the years, so "above the
  5-year normal" is true most of the time. Export flow gives no timing value. Block E is closed.
- Plan for iteration 38: hedging pressure (block C, data on hand). Classic theory: when producers and
  merchants hold a large net short hedge, the buyers of that risk get a premium, so futures tend to rise.
  This is the commercial side of the report; iteration 7 used the speculator side as a contrarian signal.

## Iteration 38 - c38: hedging pressure (commercial net short) -> RATIO +0.171, rejected
- Result: halves +0.69 / -0.44, 6 of 14 years positive, hit 64% on the active days.
- Reading: strong in 2009-2015 and the opposite in 2016-2022. No stable premium. With iteration 7 this closes
  the CFTC block (four failures in the project).
- Plan for iteration 39: world growth and risk appetite (block D). Equities, copper and crude oil rise when
  world demand and fund flows are strong, and commodities follow. A vote of the three 126-session trends.

## Iteration 39 - c39: world growth and risk composite -> RATIO +0.251, rejected
- Result: halves -0.02 / +0.54, 9 of 14 years positive. The same weak level as the other market trends.
- Reading: block A/D is one weak trend factor (0.2-0.3) seen through different markets. Closed.
- Plan for iteration 40: use the price as a confirmation of the weather rule. If crop news enters the price
  slowly, the price must already move in the direction of the news while the move is not complete. Act on
  c22 only when the 63-session coffee return has the same sign; else steady.

## Iteration 40 - c40: weather rule with price confirmation -> RATIO +0.408, rejected
- Result: halves +0.58 / +0.26, hit 66% and precision for large rises 78% on the active days, but only 49%
  of days are active and the RATIO is below c22 (+0.612).
- Reading: when the price already agrees with the weather, the call is more often correct, but the days
  without price agreement also earned (most of all in 2016-2022). So the weather rule earns before the price
  moves, which fits "news that is not yet in the price". The confirmation removes useful days. Not adopted.
- Plan for iteration 41: size of the anomaly. A small season anomaly may be noise; a large one is clear news.
  Rule on the season heat (c21): act only in the upper or lower third of its own earlier values (limits from
  the training rows of each year); the middle third is steady.

## Iteration 41 - c41: act only on large season-heat anomalies -> RATIO +0.551, rejected
- Result: halves +0.29 / +0.81, 11 of 14 years positive; c21 without the dead zone has +0.596.
- Reading: the size of the anomaly does not improve the calls. The sign carries the information. The weather
  family stays in the band 0.47-0.61 for each reasonable design. I stop design changes of the weather rule.
- Plan for iteration 42: one composite of the market-trend family. Each single trend gave +0.1 to +0.34.
  If they are noisy views of one factor, a vote of five (sugar, Brazil equities, copper, dollar down, coffee's
  own 12-month trend) must be more stable than each one. If it reaches about +0.35 with equal halves, it is
  the independent partner for the weather rule.

## Iteration 42 - c42: composite of five market trends -> RATIO +0.340, rejected
- Result: halves +0.41 / +0.27, 10 of 14 years positive, hit 59%. The same level as sugar alone (+0.336), but
  from five markets, so it rests less on one series.
- Reading: the market-trend factor is real but small, about 0.3. Arithmetic for the end result: weather 0.6
  and trend 0.34, if independent and combined with ideal weights, give at most sqrt(0.6^2 + 0.34^2) = 0.69.
  Positions of -1, 0, +1 cannot reach ideal weights. The necessary RATIO at N = 110 is 0.71. So a pass now
  needs a third independent signal, not a better vote. I will say this to Celine in the next report.
- Plan for iteration 43: the vote of the weather rule with the five-market composite (the stable form of
  c28), as the reference combination. Then back to the search for a third signal (ERA5, robusta regions).

## Iteration 43 - c43: weather rule + five-market composite -> RATIO +0.525, rejected (c22: +0.612)
- Result: halves +0.50 / +0.55 (the most equal of all runs), 11 of 14 years positive, hit 65%, precision for
  large rises 71%, beta -0.04.
- Reading: the combination is the most even rule found, and its RATIO is lower than c22. The plan's score
  prefers c22; a user who fears regime changes would prefer c43. Both are reported. No new best.
- Plan for iterations 44 and 45 (insight for the presentation, one run each): which part of the crop season
  carries the heat signal? 44 = flowering only (Sep-Nov, held to the next September). 45 = grain fill only
  (Jan-Mar, held to the next January). Agronomy says that heat at flowering causes flower loss and heat at
  grain fill reduces bean size. If one window carries all of it, the measure can be earlier or sharper.

## Iteration 44 - c44: flowering heat only (Sep-Nov) -> RATIO +0.082, rejected
- Result: halves -0.58 / +0.78. No stable skill.
- Reading: flowering heat alone does not carry the signal. Either the later months matter, or a value that is
  held for 9 months is too old. Iteration 45 answers which.

## Iteration 45 - c45: grain-fill heat only (Jan-Mar) -> RATIO +0.596, rejected by the step rule (c22: +0.612)
- Result: halves +0.51 / +0.68, 10 of 14 years positive, hit 62%, 2.2 position changes a year, beta +0.07.
- Reading: the grain-fill months carry the heat signal. Flowering alone has none (c44, +0.08). The fill
  window gives the same RATIO as the full season (c21, +0.596) with much more equal halves (c21: +0.24 /
  +0.97). This is the clearest agronomic result of the loop: hot January-March in the Brazil regions, against
  the last 5 years, goes with higher prices in the following months. Caution: the position changes about
  two times a year, so this is about 14 yearly calls; 10 correct of 14 is weak evidence by itself.
- Plan for iteration 46: the c22 form with the better state measure. Agreement of grain-fill heat (state of
  the crop) and 90-day stress (recent news); steady when they disagree. One change from c22: the season
  window Oct-Apr becomes Jan-Mar.

## Iteration 46 - c46: grain-fill heat and 90-day stress agree -> RATIO +0.624, rejected by the step rule
- Result: halves +0.44 / +0.82, 10 of 14 years positive, hit 64%. It is +0.013 above c22; the paired 20th
  percentile is -0.08, so the step rule does not accept it. c22 stays the current best.
- Reading: the best RATIO of the loop to date, by a margin that is noise. The weather family now has a
  clear shape: Brazil heat in January-March against the last 5 years, with or without the 90-day stress,
  gives 0.60-0.62 on 2009-2022.
- Plan for iteration 47: the most complete rule that the findings support: one vote each for grain-fill heat,
  90-day stress and the five-market trend composite (majority, always active). Reason: three views with
  different mechanisms; c43 showed that the market composite makes the halves equal.

## Iteration 47 - c47: majority of grain-fill heat, 90-day stress, market composite -> RATIO +0.509, rejected
- Result: halves +0.32 / +0.71, 11 of 14 years positive. Below c46 (+0.624) and c22 (+0.612).
- Reading: each way to add the market factor to the weather rule lowers the RATIO a little and makes the
  years more even. The arithmetic of iteration 42 holds. Votes are finished.
- Decision for iterations 48-54: a robustness set for the clearest finding, the grain-fill heat rule (c45,
  +0.596, halves +0.51 / +0.68). One setting changes in each run: data age (48), length of the normal (49),
  window one month earlier (50), window one month later (51), mean in place of maximum temperature (52),
  Minas Gerais regions only (53), an independent weather data set, ERA5 (54). These runs cannot lift the
  score. Their purpose is to show Celine if the finding is one lucky setting or a stable effect.

## Iteration 48 - c48: grain-fill heat with weather 10 days old -> RATIO +0.687, rejected by the step rule
- Result: halves +0.52 / +0.86, 10 of 14 years positive. Higher than c45 (+0.596) with OLDER data.
- Reading: older data cannot be better information. The difference of +0.09 comes from a few position
  changes that move by six days. It shows the size of the pure noise in this score: about 0.1. The finding
  does not depend on fresh data (good), and no difference below 0.1 between two rules has meaning (important).
  Note: 48 and 49 ran in one step, as two fixed parts of the robustness set; the reflections were written after both.

## Iteration 49 - c49: grain-fill heat with a 10-year normal -> RATIO +0.601, rejected
- Result: halves +0.57 / +0.63, 9 of 14 years positive.
- Reading: the length of the normal does not matter for this rule (c45: +0.596). For the season rule it
  did matter (c24: -0.14). The grain-fill window is the more stable design.
- Plan for iteration 50: the window one month earlier (Dec-Feb). A real effect must not vanish when the
  window moves by one month.

## Iteration 50 - c50: grain-fill heat, window Dec-Feb -> RATIO +0.533, rejected
- Result: halves +0.32 / +0.76, 9 of 14 years positive.
- Reading: one month earlier keeps most of the skill (+0.53 against +0.60). The effect does not vanish.
- Plan for iteration 51: the window one month later (Feb-Apr).

## Iteration 51 - c51: grain-fill heat, window Feb-Apr -> RATIO +0.225, rejected
- Result: halves +0.07 / +0.39, 9 of 14 years positive.
- Reading: one month later loses most of the skill (+0.23 against +0.60). So the finding is NOT robust to the
  window in this direction. Two readings: (a) January heat is the active part and April adds noise, which
  agrees with agronomy (bean filling is fastest in January-February); (b) the Jan-Mar result is partly luck.
  The data cannot separate them. I report the three windows together: Dec-Feb +0.53, Jan-Mar +0.60, Feb-Apr +0.23.
- Plan for iteration 52: mean temperature in place of maximum temperature (same Jan-Mar window).

## Iteration 52 - c52: grain-fill heat with mean temperature -> RATIO +0.680, rejected by the step rule
- Result: halves +0.62 / +0.74, 11 of 14 years positive, hit 64%, 1.6 position changes a year. SCORE +0.027
  at N = 62. The paired 20th percentile against c22 is -0.07, so c22 stays the current best.
- Reading: mean temperature works as well as maximum temperature (difference inside the noise of 0.1). The
  heat finding does not depend on the temperature measure. Rules of this family now give 0.53-0.69.
- Plan for iteration 53: Minas Gerais regions only (Sul de Minas, Matas de Minas, Cerrado Mineiro: about 74%
  of the weight). If the three other regions carry the result, it is fragile.

## Iteration 53 - c53: grain-fill heat, Minas Gerais only -> RATIO +0.553, rejected
- Result: halves +0.50 / +0.61, 9 of 14 years positive.
- Reading: the main region alone keeps the result. Robustness summary of the grain-fill heat rule (c45,
  +0.596): older data +0.69, 10-year normal +0.60, mean temperature +0.68, Minas only +0.55, window one
  month earlier +0.53, window one month later +0.23. Six of seven settings give 0.53-0.69; the later window
  is the weak point. The ERA5 check (independent data) follows when the download is complete.
- Meanwhile, back to the search for a third independent signal. Plan for iteration 54: interest rates. Stocks
  of coffee cost interest to hold. When US yields rise, traders and roasters reduce stocks and financial
  buyers leave commodities, so prices weaken; falling yields do the opposite. Rule on the 126-session change
  of the 10-year yield.

## Iteration 54 - c54: US 10-year yield change -> RATIO +0.079, rejected
- Result: halves -0.22 / +0.40. No stable skill. Interest rates give no timing signal.
- Plan for iteration 55: robusta supply. Vietnam grows about 40% of world robusta, and roasters substitute
  between robusta and arabica. Heat in the Vietnamese dry season (Jan-Apr, flowering and fruit set, the trees
  depend on irrigation) lowers the robusta crop; the robusta price rises and arabica follows. Same heat
  measure as the Brazil finding, in a different country: a supply signal that is independent of Brazil weather.
  New data: NASA POWER for three Vietnamese regions (same source as the project's weather).

## Iteration 55 - c55: Vietnam dry-season heat (robusta supply) -> RATIO +0.239, rejected
- Result: halves +0.27 / +0.21, 9 of 14 years positive, 1.4 position changes a year.
- Reading: weak, but equal in the two halves and with the expected sign. It is a supply signal from a
  different country, so it can be the third independent view. Alone it is far too weak. I keep it for the
  consolidation runs at the end.
- Plan for iteration 56 (the ERA5 file is not complete yet): the grower's price. Brazilian growers sell
  when the price in reais is high against the last year and hold coffee back when it is low. A high price in
  reais brings selling pressure -> buy late; a low one -> buy early. This differs from the dollar value rule
  (c04), because it uses the currency in which the marginal seller decides.

## Iteration 56 - c56: coffee price in reais against its 1-year mean -> RATIO -0.233, rejected
- Result: halves -0.42 / -0.04, AUROC 0.39: the opposite sign again.
- Reading: fourth value-type rule with the opposite sign (c03, c04, c25, c56). In 2009-2022 a high coffee
  price, in any measure, was followed by a still higher mean price in the next quarter. Grower selling does
  not cap the price at this horizon. Value ideas are closed for good.
- Plan for iteration 57: a second try of fitted weights, now with the four best features (grain-fill heat,
  90-day stress, Vietnam heat, count of rising markets). The first try (c15) had weaker features and gave
  +0.31. If a logistic model cannot beat the sign rules with these features, fitted models have no place here.

## Iteration 57 - c57: logistic regression on the four best features -> RATIO +0.023, rejected
- Result: halves +0.04 / +0.00, "late" on 70% of days. Fitted weights fail completely.
- I looked at the fitted weights by training period (a diagnostic; no new score). The reason is important:
  - Trained on 2001-2008, the weight of grain-fill heat is NEGATIVE (-0.38). In those years the sign of the
    heat anomaly agreed with the label on only 42% of days (about 30 windows). In 2009-2022 it is 62-64%.
  - The 90-day stress and the Vietnam heat agree with the label on 50% of days in 2001-2008: no relation.
- Reading: the heat relation did not exist before 2009 (it had the opposite sign), it exists in 2009-2022,
  and the weather rule failed in the test period 2023-2026. Together with the failed placebo this says: the
  weather lead belongs to one period. It is not a stable law that a purchasing team can rely on. This is the
  check on 2001-2008 that I proposed to Celine, done at the label level, and its result is negative.
- Consequence for the 43 iterations left: more designs of the weather rule have no value. The open question is
  if any signal is stable over all periods. The market-trend composite had the most equal halves.
- Plan for iteration 58: if relations change over time, a model that forgets old data can follow them.
  Logistic regression on the same four features with time-decay weights (half-life 3 years). This tests
  "the relation is real but moves" against "there is no relation".

## Iteration 58 - c58: logistic regression with time-decay weights -> RATIO +0.064, rejected
- Result: halves -0.13 / +0.27. A model that forgets old years does not follow the relation either.
- Reading: with c15, c16, c17, c57 this is the fifth fitted model below the sign rules. Closed.
- Plan for iteration 59: fear in financial markets. When the VIX is above its 1-year mean, funds cut risk
  and sell commodities; when it is below, they add risk. A level rule, different from the trend rules.

## Iteration 59 - c59: market fear (VIX against its 1-year mean) -> RATIO +0.270, rejected
- Result: halves -0.30 / +0.87, 18 position changes a year. Not stable.
- Reading: one more market signal that works in one half only. Since the weather lead belongs to one period
  too, I now sort all signals by stability. Only three had the same sign and similar size in the two halves:
  sugar trend (+0.34 / +0.33), five-market composite (+0.41 / +0.27), Vietnam heat (+0.27 / +0.21).
- Plan for iteration 60: a rule from the stable signals only. The five-market composite and the Vietnam heat
  must agree; else steady. It will not reach the weather rule's RATIO, but it does not rest on one period.

## Iteration 60 - c60: agreement of the two stable signals -> RATIO +0.422, rejected
- Result: halves +0.53 / +0.32, 9 of 14 years positive, hit 66% and precision for large rises 72% on the
  active days; active on 48% of days.
- Reading: the stable signals combine to +0.42, as the arithmetic says ((0.34 + 0.24) / 1.41). It is the rule
  that I would trust most outside the development years, and it is far below the necessary 0.67.
- Curated plan for iterations 61-70: look for more STABLE weak signals (equal halves is the filter, not a
  high RATIO), because only stable parts can add up. Candidates with a mechanism: ERA5 heat (data check),
  robusta price trend, Indian Ocean Dipole (Indonesia and East Africa supply), Colombian peso, gold, volume.
- Plan for iteration 61: Colombian peso. Colombia is the second arabica origin; a weak peso makes Colombian
  growers sell, as for the real. USD/BRL failed (c14), so my prior is low, but it costs one run and it
  completes the currency block.

## Iteration 61 - c61: Colombian peso trend -> RATIO +0.056, rejected
- Result: halves -0.03 / +0.15. No skill. Producer currencies give no timing signal (USD/BRL +0.07, USD/COP +0.06).
- Plan for iteration 62: robusta price trend (World Bank monthly, already downloaded). Roasters substitute, so
  a rising robusta price pulls arabica up with a delay. The Vietnam heat rule (c55) is the weather form of
  this idea and was stable; the robusta price is the direct measure.

## Iteration 62 - c62: robusta price trend -> RATIO +0.317, rejected
- Result: halves +0.60 / +0.02, 9 of 14 years positive. Not stable; it does not pass the stability filter.
- Reflection: single signals are used up. A different lever is the exposure, not the signal. Published work
  on "volatility-managed" portfolios shows that less exposure in high-volatility periods raises the return
  for each unit of risk, because volatility is predictable and the mean return is not higher when it is high.
  The RATIO divides by the standard deviation, which the high-volatility days dominate.
- Plan for iteration 63: c22 with a volatility switch. Steady when the 21-session volatility of coffee is in
  the upper third of its earlier values (limit from the training rows); else the c22 position. One change.

## Iteration 63 - c63: c22 with a volatility switch -> RATIO +0.620, rejected (c22: +0.612)
- Result: halves +0.29 / +0.93, hit 65%, active on 54% of days. The same RATIO with fewer active days.
- Reading: the volatility switch gives no gain here. The savings of the weather rule do not come more from
  calm periods. Exposure management is closed.
- Plan for iteration 64: Indian Ocean Dipole (NOAA, whitelist of the first plan). A positive dipole brings
  drought to Indonesia (robusta and Sumatra arabica) and floods to East Africa; both reduce supply. It is a
  climate driver for origins that the Brazil and Vietnam rules do not cover. ENSO failed two times, so the
  prior is low; it is one run to complete the climate-index block.

## Iteration 64 - c64: Indian Ocean Dipole -> RATIO -0.162, rejected
- Result: no skill; active on 18% of days only. Climate indices are closed (ENSO two times, IOD one time).
- Curated plan for the 36 iterations left. The verdict will not change without a new strong signal, so the
  runs go where they add knowledge: (a) 65-68: how solid is the one stable factor (market trend)? horizon
  and breadth; (b) 69-76: supply-weather signals of other origins in their own crop windows, like the stable
  Vietnam rule; (c) 77-80: ERA5 check and small tree models on the best features; (d) 81-100: consolidation.
- Plan for iteration 65: the five-market composite with a 63-session horizon for all markets (c42 uses 126
  and 252). A real trend factor must not depend on one horizon.

## Iteration 65 - c65: trend composite, 63-session horizon -> RATIO +0.100, rejected
- Result: halves +0.15 / +0.04, 18 position changes a year.
- Reading: with a shorter horizon the composite loses most of its value (+0.34 -> +0.10). The "stable"
  market factor depends on the slow horizons. Iteration 66 tests the slow side.

## Iteration 66 - c66: trend composite, 252-session horizon -> RATIO +0.341, rejected
- Result: halves +0.39 / +0.29, 10 of 14 years positive, 6 position changes a year.
- Reading: the slow composite equals c42 (+0.340). The market factor is a slow trend (6 to 12 months) and
  it is stable at about +0.34; fast trends have no value. Block (a) is done.
- Plan for iteration 67 (block b, supply weather of other origins in their own crop windows): Colombia, the
  second arabica origin. Its main crop flowers in January-March; heat and drought then (often with El Nino)
  cut the harvest of October-December. Same measure as the Vietnam rule.

## Iteration 67 - c67: Colombia flowering heat (Jan-Mar) -> RATIO +0.507, rejected (below c22)
- Result: halves +0.66 / +0.35, 10 of 14 years positive, hit 62%, 2.2 position changes a year.
- Reading: a second origin gives a result near the Brazil rule (c45, +0.596), in the same months. Two
  readings: (a) supply news from two origins, which would be strong support; (b) a common January-March
  warmth of the tropics that moves with something else in the market, a "clock". Brazil, Colombia and Vietnam
  all use January-March(-April). The earlier falsification test (c34) used October-April, not this window.
- This must be separated before anything is built on it. Plan for iteration 68: falsification test in the
  same window. Jan-Mar heat of Central America and Mexico (Guatemala, Honduras, Nicaragua, Mexico). There,
  January-March is harvest time and flowering comes in March-May, so Jan-Mar heat has little crop meaning.
  If it scores like Brazil and Colombia, reading (b) is correct.

## Iteration 68 - c68: falsification, Jan-Mar heat of Central America and Mexico -> RATIO +0.326
- Result: halves +0.48 / +0.17, 7 of 14 years positive.
- Reading: not zero. A region where Jan-Mar heat has little crop meaning gives about half of the Brazil
  score. So a part of the "grain-fill heat" finding is a common January-March warmth of the tropics, not
  Brazilian crop news. All these rules set one position in the first quarter and hold it for a year: about 14
  yearly calls, and the calls of different regions are not independent. The Colombia result (c67) is thus
  not a second confirmation.
- Plan for iteration 69: separate the two parts directly. Brazil-specific heat = Brazil Jan-Mar anomaly minus
  the Jan-Mar anomaly of all 31 other nodes. If Brazilian crop news has value beyond the common warmth, this
  difference must have skill.

## Iteration 69 - c69: Brazil-specific grain-fill heat (Brazil minus other regions) -> RATIO +0.393, rejected
- Result: halves +0.27 / +0.52, 10 of 14 years positive.
- Reading: the Brazil-specific part keeps about two thirds of the score of c45 (+0.596). So there is Brazil
  information beyond the common warmth, about +0.4, and the rest is the common part.
- Plan for iteration 70: the common part alone. Jan-Mar anomaly of the 31 nodes outside Brazil. This completes
  the split: Brazil total +0.60 = Brazil-specific (+0.39) and common (this run), not as a sum of numbers but
  as a picture of where the skill is.

## Iteration 70 - c70: common January-March warmth outside Brazil -> RATIO +0.416, rejected
- Result: halves +0.67 / +0.15, 8 of 14 years positive.
- Reading: the common part alone gives +0.42, strong in 2009-2015 and weak after. The Brazil-specific part
  (c69, +0.39) is stronger in 2016-2022. The Brazil rule (c45, +0.60, equal halves) is the two together.
  Neither part is stable alone. All of them are about 14 yearly calls.
- The common tropical warmth in January-March is mostly the El Nino state of the northern winter. The first
  ENSO rule (c08) used the opposite idea (La Nina dries south Brazil -> buy early) for all months and gave 0.
  The market view is different: El Nino brings heat and drought to Colombia, Central America, Vietnam and
  Indonesia, so supply outside Brazil falls.
- Plan for iteration 71: ENSO as the yearly state. Nino 3.4 of January (known in mid February), held for a
  year. Warm (above zero): buy early; cool: buy late. If this scores like c70, the "common warmth" is ENSO.

## Iteration 71 - c71: ENSO state of January, held for a year -> RATIO +0.385, rejected
- Result: halves +0.41 / +0.36, 9 of 14 years positive, hit 62%, one position change a year.
- Reading: the common tropical warmth is ENSO. With the market sign (El Nino -> buy early) and a yearly hold,
  ENSO gives a stable +0.39. My first ENSO rules (B5, c08) used the wrong idea and a monthly state. This is
  the third stable signal, next to the slow market trend (+0.34) and Vietnam heat (+0.24, which is partly the
  same ENSO effect). It is about 14 yearly calls, so alone it proves little.
- The picture is now simple: three weak views with different causes: ENSO winter state (supply outside
  Brazil), Brazil-specific grain-fill heat (supply in Brazil), slow market trend (demand and funds).
- Plan for iteration 72: one vote for each of the three. Ideal arithmetic gives about 0.65.

## Iteration 72 - c72: majority of ENSO state, Brazil-specific heat, market trend -> RATIO +0.572, rejected
- Result: halves +0.59 / +0.55, 11 of 14 years positive, hit 64%, AUROC 0.634, beta -0.08.
- Reading: the arithmetic held (+0.57 from three signals of 0.34-0.39), and the two halves are equal. This is
  the best rule that is built only from stable parts. It is below c22 (+0.612) by less than the noise, and its
  design does not rest on 2016-2022. It is my choice as the "robust candidate"; c22 stays the plan's "best".
- Plan for iteration 73: the same vote with the full Brazil grain-fill heat (mean temperature, c52, +0.68) in
  place of the Brazil-specific part. The full measure is stronger alone but shares the ENSO part with the
  ENSO vote, so the gain is not certain.

## Iteration 73 - c73: majority of ENSO state, full Brazil grain-fill heat, market trend -> RATIO +0.646, rejected by the step rule
- Result: halves +0.63 / +0.66, 11 of 14 years positive, hit 69%, AUROC 0.687 (the highest of the loop),
  recall of large rises 68%, precision 67%, beta -0.01, 4.8 position changes a year, saving 2.5% of yearly cost.
- Reading: the best rule of the loop by all values except the plan's step rule. Its savings are not close to
  those of c22, so the paired test cannot show a difference (20th percentile -0.20), and c22 stays the plan's
  "current best". SCORE -0.037 at N = 83; the necessary RATIO at N = 110 is 0.711.
- Diagnostic on the training years (label only, no new score): share of days where each sign agrees with the
  label, by period 2001-2008 / 2009-2015 / 2016-2022:
  ENSO January 58% / 64% / 60%; Brazil grain-fill heat 42% / 62% / 67%; Brazil-specific heat 50% / 56% / 62%;
  market trend 52% / 68% / 50%; Vietnam heat 51% / 55% / 56%; 90-day stress 50% / 51% / 65%;
  c73 majority 56% / 70% / 68%; c72 majority 56% / 66% / 62%.
- Reading of the diagnostic: the ENSO winter state is the only single signal with the same sign and a similar
  size in all three periods, the years before 2009 included. The Brazil heat signs did not work before 2009.
  The c73 vote stays above 50% in all three periods because ENSO holds it up.
- Plan for iteration 74: the ENSO rule in its event form. Act only in real events (January Nino 3.4 above
  +0.5 or below -0.5); steady in neutral years. If the effect is a supply effect of real El Nino and La Nina
  events, neutral years add only noise.

## Iteration 74 - c74: ENSO rule for real events only -> RATIO +0.417, rejected
- Result: halves +0.61 / +0.25, 9 of 14 years positive. Near c71 (+0.385): the event form is not better.
- Plan for iteration 75: the two signals that are stable and have different causes, ENSO winter state and
  slow market trend, in one agreement rule (steady when they disagree). No Brazil weather in it, so it does
  not rest on the part that failed before 2009.

## Iteration 75 - c75: ENSO state and market trend agree -> RATIO +0.481, rejected
- Result: halves +0.54 / +0.41, 10 of 14 years positive, hit 69% on the active days (57% of days).
- Reading: two stable signals without Brazil weather give +0.48. The Brazil heat vote adds +0.17 to reach
  c73 (+0.646). So Brazil weather still adds on the development years, and it is the part with the weak past.
- Plan for iteration 76: one small tree model, as agreed for the model space. A decision tree of depth 2 on
  the three inputs of c73 (ENSO value, Brazil heat anomaly, number of rising markets). A depth-2 tree is a
  fitted version of a vote and gives a rule that a person can read. The five larger fitted models failed;
  this is the smallest possible one.

## Iteration 76 - c76: depth-2 decision tree on the three inputs of c73 -> RATIO +0.025, rejected
- Result: halves +0.21 / -0.17, "late" on 70% of days. The smallest fitted model fails like the larger ones.
- Reading: six fitted models, six failures (best +0.31). With this sample, a rule with a sign from economics
  is better than any fitted rule. Model search is closed for good.
- Plan for iteration 77: data check of the Brazil heat with an independent reanalysis. ERA5 (ECMWF) is now
  complete for the 6 Brazil nodes. Same rule as c52 (Jan-Mar mean temperature against the last 5 years) with
  ERA5 values at t-7 days. If the finding is in the weather and not in one data product, the score must be
  near c52 (+0.68).

## Iteration 77 - c77: Brazil grain-fill heat from ERA5 -> RATIO +0.447, rejected
- Result: halves +0.66 / +0.22, 11 of 14 years positive, hit 61%.
- Reading: the independent data set gives the same sign and the same number of positive years, with a
  smaller score (+0.45 against +0.68 for NASA POWER). The heat signal is in the weather, not in one data
  product; its size on the development years is better stated as 0.45-0.68 than as one number.
- Plan for iteration 78: the complete drought measure. ERA5 gives reference evapotranspiration, so the
  climatic water balance (rain minus evapotranspiration) of January-March can be computed. It joins rain and
  heat in the physical way. Rain alone was weak (c19); if the water balance is not better than heat alone,
  the signal is temperature and not water.

## Iteration 78 - c78: Brazil grain-fill water balance (ERA5) -> RATIO +0.091, rejected
- Result: halves +0.17 / +0.00, 7 of 14 years positive. No skill.
- Reading: an important negative. The physical drought measure has no skill; rain alone was weak (c19); soil
  moisture failed its halves test (c11). The signal is temperature only. A crop-loss mechanism through water
  stress is NOT supported. What remains is "warm January-March", of which a large part is ENSO (c70, c71).
  The honest name of the weather finding is "ENSO-linked warmth", not "Brazilian drought stress".
- Plan for iterations 79-84: robustness set for the best stable rule (c73, +0.646), one setting for each run:
  weather 10 days old (79), ERA5 heat (80), slow 252-session trends (81), ENSO as the December-February mean
  (82), without the trend vote (83), with Vietnam heat as a fourth vote (84).

## Iteration 79 - c79: c73 with weather 10 days old -> RATIO +0.666, rejected by the step rule
- Result: halves +0.67 / +0.67, 11 of 14 years positive, hit 69%. The same as c73 (+0.646) inside the noise.
- Reading: the rule does not need fresh weather data. Good for real use: a buyer can compute it by hand.
- Plan for iteration 80: the same vote with the ERA5 heat (independent data).

## Iteration 80 - c80: c73 with ERA5 heat -> RATIO +0.545, rejected
- Result: halves +0.70 / +0.38, 10 of 14 years positive, hit 65%.
- Reading: with independent weather data the vote keeps +0.55. So the honest range for the c73 design on the
  development years is 0.55-0.67, not the single value 0.646.
- Plan for iteration 81: slow trends. c66 showed that the 252-session composite equals the mixed one; in the
  vote it would change position less often.

## Iteration 81 - c81: c73 with 252-session trends -> RATIO +0.618, rejected
- Result: halves +0.35 / +0.90, 11 of 14 years positive, hit 68%. The RATIO is kept; the halves are less equal.
- Reading: the vote does not depend on the trend horizon for its level (0.62-0.65), but the equal halves of
  c73 came partly from the mixed horizons. Equal halves are a weaker property than I thought.
- Plan for iteration 82: ENSO as the December-February mean (the standard season of ENSO events), known in
  mid March, in place of the single January value.

## Iteration 82 - c82: c73 with the December-February ENSO mean -> RATIO +0.669, rejected by the step rule
- Result: halves +0.72 / +0.62, 12 of 14 years positive, hit 69%.
- Reading: the ENSO definition does not matter. Robustness of the c73 design, five settings: 0.67 (older
  weather), 0.55 (ERA5), 0.62 (slow trends), 0.67 (seasonal ENSO), 0.65 (base). All inside 0.55-0.67.
- Plan for iteration 83: what does the trend vote add? ENSO state and Brazil heat only, as an agreement rule.

## Iteration 83 - c83: ENSO winter state and Brazil grain-fill heat agree -> RATIO +0.705, rejected by the step rule
- Result: halves +0.72 / +0.69, 10 of 14 years positive, hit 71% on the active days (63% of days), 1.4
  position changes a year, range +0.30 to +1.17. SCORE +0.010 at N = 93; at N = 110 the same RATIO gives -0.006.
  Paired 20th percentile against c22: -0.075, so c22 stays the plan's current best.
- Reading: the highest RATIO of the loop, from the simplest rule: two yearly climate states, both known by
  mid February, no market data. Without the trend vote the score is higher than with it (c73, +0.646): the
  vote filled the "disagree" days with a weaker signal, as the arithmetic of iteration 28 says.
- Cautions, all strong: (1) it is the top of 83 trials and its margin over the noise bar is zero;
  (2) it makes about one call a year, and it is active in about 9 of 14 years; (3) the Brazil heat sign failed
  before 2009; (4) no test outside 2009-2022 is permitted for it unless it becomes a development predictor.
- Plan for iterations 84-86: the three robustness checks that mattered before, on c83: ENSO as the seasonal
  mean (84), ERA5 heat (85), weather 10 days old (86). No design changes.

## Iteration 84 - c84: c83 with the December-February ENSO mean -> RATIO +0.743, rejected by the step rule
- Result: halves +0.82 / +0.67, 10 of 14 years positive, hit 72%, range +0.35 to +1.21. SCORE +0.047 at N = 94.
  Paired 20th percentile against c22: -0.04.
- Reading: the seasonal ENSO definition gives the same rule within the noise (+0.04 above c83). The design is
  not sensitive to it. This is now above the necessary RATIO of N = 110 (0.711) by 0.03, which is one third
  of the noise of a single setting. I do not treat it as a pass: the next two checks use the settings that
  lowered the earlier rules.

## Iteration 85 - c85: c83 with ERA5 heat -> RATIO +0.495, rejected
- Result: halves +0.69 / +0.32, 9 of 14 years positive, hit 65%.
- Reading: with the independent temperature data the rule falls from +0.705 to +0.495. The two data
  products disagree on the sign of the Brazil anomaly in some years, and with about one call a year each
  such year moves the score a lot. The honest range of the two-state rule is 0.50-0.74. Its value above the
  noise bar depends on which weather product is used. This is not a pass.
- Plan for iteration 86: weather 10 days old (the third check).

## Iteration 86 - c86: c83 with weather 10 days old -> RATIO +0.787, ACCEPTED (new best by the step rule)
- Result: halves +0.79 / +0.78, 11 of 14 years positive, hit 71% on the active days (63% of days), 1.5
  position changes a year. Paired 20th percentile against c22: +0.005. SCORE +0.089 at N = 96; at N = 110
  the same RATIO gives +0.076.
- Reading: by the plan's rule this is the new best, by the smallest margin. I do not believe the number.
  (1) Older weather data cannot be better; c83 (+0.705), c84 (+0.743), c85 (+0.495, ERA5) and c86 (+0.787)
  are one design, and their spread of 0.3 is the noise of a rule with one call a year.
  (2) Yearly positions 2009-2022: steady in 2009, 2013, 2014, 2020, 2021; early in 2010, 2015, 2016, 2019;
  late in 2011, 2012, 2017, 2018, 2022. That is 9 calls. A RATIO from 9 calls has a very wide range.
  (3) Diagnostic on the training years (label only): in 2001-2008 the rule was active on 38% of days and
  agreed with the label on 51% of them. No skill before 2009. With ERA5 heat: 61% before 2009, 71% and 60% after.
- The plan's guards decide, not my opinion: the placebo test (C6) after iteration 100, and only then a
  possible second look at the test period.
- Plan for iterations 87-100: checks of this rule, one change each, fixed now: maximum temperature (87),
  10-year normal (88), Minas Gerais only (89), window Dec-Feb (90), Brazil-specific heat (91), Vietnam heat in
  place of Brazil (92), falsification with Central America heat (93), all three signals must agree (94),
  ENSO events only (95), 90-day stress as a third state (96). The last four runs stay free for what these show.

## Iteration 87 - c87: c86 with maximum temperature -> RATIO +0.677, rejected
- Result: halves +0.59 / +0.77, 10 of 14 years positive, hit 67%. Lower than c86 by 0.11, same sign and shape.
- Plan for iteration 88: 10-year normal.

## Iteration 88 - c88: c86 with a 10-year normal -> RATIO +0.631, rejected
- Result: halves +0.75 / +0.50, 10 of 14 years positive. Lower by 0.16.
- Plan for iteration 89: Minas Gerais regions only.

## Iteration 89 - c89: c86 with Minas Gerais only -> RATIO +0.780, rejected (c86: +0.787)
- Result: halves +0.77 / +0.79, 11 of 14 years positive. The same rule.
- Plan for iteration 90: Brazil window one month earlier (Dec-Feb). The single heat rule kept +0.53 there.

## Iteration 90 - c90: c86 with the Brazil window Dec-Feb -> RATIO +0.626, rejected
- Result: halves +0.53 / +0.72, 9 of 14 years positive. Lower by 0.16; the rule keeps its sign and shape.
- Checks of the two-state design to date: 0.787 (base), 0.780 (Minas only), 0.743 (seasonal ENSO), 0.705
  (fresh weather), 0.677 (maximum temperature), 0.631 (10-year normal), 0.626 (window Dec-Feb), 0.495 (ERA5).
  Median 0.69. The base c86 is the top of its own family; the family is at about 0.7 with POWER data and 0.5
  with ERA5 data.
- Plan for iteration 91: is the Brazil part of the rule Brazil news or the same ENSO warmth twice? ENSO state
  and Brazil-SPECIFIC heat (Brazil anomaly minus the other regions) must agree.

## Iteration 91 - c91: ENSO state and Brazil-specific heat agree -> RATIO +0.612, rejected
- Result: halves +0.52 / +0.73, 9 of 14 years positive, hit 71% on the active days (49% of days).
- Reading: with the common warmth removed from the Brazil measure, the rule keeps +0.61. Brazil adds
  information to the ENSO state (ENSO alone: +0.39).
- Plan for iteration 92: falsification of that reading. ENSO state and the Jan-Mar heat of Central America and
  Mexico (no crop meaning in those months) must agree. If this scores like c86, the second input only needs to
  be "a warm tropical first quarter", and Brazil is not special.

## Iteration 92 - c92: falsification, ENSO state with Central America heat -> RATIO +0.394, rejected
- Result: halves +0.55 / +0.25. The same as the ENSO rule alone (c71, +0.385).
- Reading: a "good" failure. Heat of a region without a crop reason adds nothing to the ENSO state; Brazil
  heat lifts it to 0.6-0.8. On the development years, Brazil grain-fill heat is real extra information.
- Plan for iteration 93: the main weakness of the rule is the weather product (POWER +0.79, ERA5 +0.50). A
  buyer cannot know which product is right. The careful design uses both: the mean of the two Brazil
  anomalies (each in its own units, scaled by its own earlier spread). One change from c86.

## Iteration 93 - c93: the two-state rule with both weather products -> RATIO +0.599, rejected
- Result: halves +0.77 / +0.46, 10 of 14 years positive, hit 66%.
- Reading: with the mean of the two products the rule gives +0.60. This is my best estimate of the size of
  the two-state rule on the development years. It is below the necessary 0.711. c86 (+0.787) is the lucky end
  of the design; the step rule keeps it as the plan's best because it came first.
- Plan for iteration 94: all three stable signals must agree (ENSO state, Brazil heat, market trend); steady
  in all other cases. Fewer calls, each with three reasons. This is the "high conviction" form of c73.

## Iteration 94 - c94: ENSO state, Brazil heat and market trend all agree -> RATIO +0.722, rejected (c86: +0.787)
- Result: halves +0.81 / +0.65, 11 of 14 years positive, hit 72%, active on 39% of days only.
- Reading: the third condition removes days and keeps the quality; the RATIO does not rise. No gain.
- Plan for iteration 95: the same two-state form with a different second origin. ENSO state and Vietnam
  dry-season heat (robusta supply, a window with crop meaning). If Brazil is the origin that matters, this
  must be weaker than c86 and near the ENSO rule alone.

## Iteration 95 - c95: ENSO state with Vietnam heat -> RATIO +0.397, rejected
- Result: halves +0.46 / +0.33. The same as the ENSO rule alone (+0.385): Vietnam heat adds nothing to ENSO.
- Reading: Vietnam heat is the ENSO state seen in Asia. Only Brazil adds to ENSO. The picture is complete:
  the usable climate information is (1) the ENSO winter state and (2) Brazil January-March temperature.
- Plan for iteration 96: Colombia in the same form (ENSO state and Colombia Jan-Mar heat). Colombia scored
  +0.51 alone, the highest outside Brazil; this shows if that was ENSO too.

## Iteration 96 - c96: ENSO state with Colombia heat -> RATIO +0.471, rejected
- Result: halves +0.60 / +0.35. A little above the ENSO rule alone; far below c86. Colombia heat is mostly ENSO.
- Plan for iteration 97: ENSO in its event form inside the two-state rule. Neutral winters (index between
  -0.5 and +0.5) give steady. The event form did not help the ENSO rule alone (c74); this checks it in c86.

## Iteration 97 - c97: c86 with ENSO events only -> RATIO +0.735, rejected (c86: +0.787)
- Result: halves +0.79 / +0.68, 11 of 14 years positive, hit 70%. The same rule within the noise.
- Plan for iteration 98: a fresher ENSO state. c86 holds the January value for 12 months, but an event can
  start or end in the middle of the year. Update the ENSO input in mid August with the July value; the
  Brazil heat input does not change. One change.

## Iteration 98 - c98: c86 with the ENSO state updated in mid year -> RATIO +0.567, rejected
- Result: halves +0.52 / +0.61. Lower by 0.22: the fresher ENSO value is worse.
- Reading: the winter state is what matters (the season when ENSO events peak and when the crops of the next
  year are set). A mid-year value is a different thing. The yearly form stays.
- Plan for iterations 99 and 100 (the last two): the design that I would give to a buyer, with the two
  choices that do not depend on luck: ENSO as the standard December-February mean, and the Brazil heat as
  the mean of the two weather products. 99 = this two-state rule. 100 = the same with the slow market trend
  as a third vote (always active).

## Iteration 99 - c99: the careful two-state design -> RATIO +0.633, rejected
- Result: halves +0.86 / +0.45, 10 of 14 years positive, hit 66%, 1.5 position changes a year.
- Reading: with the choices that do not depend on luck, the two-state rule gives +0.63 (c93: +0.60). This
  confirms about 0.6 as its honest size on 2009-2022. Necessary at N = 110: 0.711.
- Plan for iteration 100: the same inputs with the slow market trend as a third vote.

## Iteration 100 - c100: the careful design with the trend vote -> RATIO +0.561, rejected
- Result: halves +0.74 / +0.37, 11 of 14 years positive, hit 65%. Inside the band of all votes (0.51-0.67).
- The budget of 100 iterations is used. No iteration 101.

## After iteration 100
- Best candidate by the plan's step rule: c86 (ENSO winter state and Brazil Jan-Mar heat agree; weather 10
  days old). RATIO +0.787; necessary 0.712 at N = 110; SCORE +0.075. C1-C5 and C7 are satisfied.
- C6 placebo (ENSO and weather rotated together by 2 to 18 years): real +0.787; placebo mean +0.016, range
  -0.538 to +0.613; 0 of 17 at or above the real value. C6 PASSES (p about 0.06).
- By the plan and addendum 2, c86 is a "predictor (development)", and a second and last look at the test
  period 2023-Oct 2026 is permitted for it. Pass limit: RATIO above 0.5.
- What I think before the look, so that it cannot be changed after: (1) c86 is the lucky end of its design;
  the careful versions give 0.60-0.63, and 0.60 would NOT pass the placebo (highest placebo +0.613). (2) The
  test period holds at most 4 yearly calls of this rule, so its RATIO has a range of about -1 to +1; a pass or
  a fail will both be weak evidence. (3) This is a second look at these years, and I know the price history
  of 2023-2025 in outline. I take the look because the plan permits it, and I report it with these limits.
- Second look at the test period (c86, 2023-Oct 2026): RATIO +0.374 (range -0.60 to +1.43), 2 of 4 years
  positive, saving 1.5% of yearly cost. Below the pass limit of 0.5: FAIL. By the plan: "not confirmed".
  Yearly detail: 2023 "late" all year, saving -12.7% (the price rose 12.7%); 2024 "early", +44.9% (price
  +50.5%); 2025 "early" to mid February and then steady, +22.3%; 2026 "late" from mid February, -10.5%.

## Final reflection after 100 iterations
- Verdict: one rule passed the development score and the placebo test (c86), and it did not reach the pass
  limit in the test period. Status: not confirmed. There is no predictor that I can give to a purchasing team
  as proven.
- What I believe: (1) Two climate states carry information on 2009-2022: the ENSO state of the northern
  winter and the January-March temperature in the Brazil regions. Together they give about 0.6 with careful
  settings and 0.5-0.8 over all settings. (2) The ENSO part is the only signal that had the same sign before
  2009; the Brazil part did not. (3) The slow market trend is real but small (about 0.34). (4) Water stress,
  price value, positioning, export flow, currencies, calendar and all fitted models have no value here.
- The rule makes about one call a year. 14 development years and 4 test years cannot prove or reject a
  yearly rule. More iterations on these years cannot change this; only more years or other markets can.
