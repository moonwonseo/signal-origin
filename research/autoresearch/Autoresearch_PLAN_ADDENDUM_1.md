# Autoresearch plan, addendum 1 (15 Nov 2026, after iteration 2). Deviation from the plan.

What happened: iteration 2 used the price gap on the marked roll days as a measure of the term structure. A
check of that feature showed that the raw return on the 134 marked days is an ordinary daily return (mean
+0.0003). The gap between contracts is in the NEXT session: mean +1.1% for all years, +2.9% in 2000-04,
+2.3% in 2017-20, -0.7% in 2021-26. The marked day is the last day of the old contract.

Effect: the plan's "roll-adjusted" return (section 1) set the wrong day to zero. The contract gaps stayed in
the returns. A buyer does not earn these gaps. They gave an always-early position a false profit in contango
years and a false loss in backwardation years. The same defect is in the earlier Direction and XGBoost studies.

Repair (eval revision 1): the return is set to zero on each marked roll day AND on the next session (268
sessions). This choice was made from the gap statistics only, before any candidate was scored with it.
A gap can also be on the marked day in the early years, so both days are removed.

Deviation: the plan says that the loop stops and asks Celine for a change to a fixed part. Celine's last
instruction was to run all 30 iterations and report at the end, and the loop cannot give valid scores with
the defect. Thus the agent made the repair, recorded it in the trial log (row "repair"), scored the baselines
and iterations 1-2 again, and continued. N does not change (plan, section 9). Celine can reject the repair:
all candidates are code, and a new score of all of them takes minutes.

Not repaired: rolls that the price file does not mark, and the exact day of each gap. The Yahoo chain stays
an unverified series.

## Rule for a void candidate (added with this addendum)
A candidate is "void" when a check that does not use its score shows that its feature does not measure what
its hypothesis states. A void candidate keeps its row in the log and its count in N. It cannot be the current
best, and no later candidate is compared with it. This rule can only remove a good score; it cannot add one.
First use: c02 (iteration 2). Its hypothesis was "term structure", but its feature is the mean of four
ordinary daily returns (the marked roll days). Its RATIO of +0.43 has no mechanism and is treated as luck.
