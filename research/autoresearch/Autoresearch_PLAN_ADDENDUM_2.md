# Autoresearch plan, addendum 2 (15 Nov 2026, after iteration 30). Extension to 100 iterations.

Celine's instruction (15 Nov): "do another 70 iterations, totalling 100. You may expand the search space of
data, as long as they are from reliable and safe to download sources." Celine also accepted the roll repair
of addendum 1 on 15 Nov.

What changes
1. Budget: iterations 31-100. N continues: N = 10 + iteration number, so N = 110 at the end.
   RATIO necessary for SCORE > 0: 0.63 at iteration 50, 0.68 at iteration 75, 0.71 at iteration 100.
2. Data: the whitelist of the plan is replaced by a rule. A new source is permitted when ALL of these are true:
   - Publisher: a government or international agency, a central bank, a space or weather agency, a university
     archive, an exchange, or the market-data vendor that the project already uses (Yahoo Finance).
   - Access: a public file or a documented public interface over HTTPS. No account, key, form, or paid data.
     No personal details in a request.
   - Content: data files only (CSV, JSON, XLSX, text). Nothing that is executed. Files are read as data.
   - History starts in 2004 or before (for a 5-year normal: 2000 or before is preferred).
   - A data card is written before first use, with the publication delay. The delay enters the leak test.
   - Raw files stay on the Mac mini with a sha256. No third-party rows go into the repository.
   The limit of 6 new sources is removed. Each new source is still named in the log and in the results.
3. Reports to Celine after iterations 40, 50, 60, 70, 80, 90 and 100.

What does not change
- Sections 1-7 of the plan: target, position, score, walk-forward protocol, constraints C1-C7, eval revision 1.
- The step rule, the void rule, one hypothesis for each iteration, the journal with a reflection after each run.
- The model space (rules, logistic or ridge regression, tree methods; no neural networks).
- The current best at the start of iteration 31 is c22 (RATIO +0.612).

Test period 2023-Oct 2026
- It was used one time (c22, RATIO +0.04). The plan permitted one look. The agent has seen this result.
- New rule: a second and last look is permitted only if the best candidate after iteration 100 is a
  "predictor (development)": SCORE > 0 at N = 110 and C1-C7 satisfied, placebo included. In all other cases
  there is no second look. A second look is weaker evidence than a first look, and the report must say so.

Honest expectation, written before iteration 31: the necessary RATIO rises to 0.71 and the best level found
in 30 iterations is about 0.5-0.6 on the development years, with no confirmation outside them. A pass needs
at least two more signals that are independent of Brazil weather and have real skill.
