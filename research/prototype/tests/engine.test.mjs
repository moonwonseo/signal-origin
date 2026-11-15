// Tests of the rule engine. Run: node --test tests/*.test.mjs
// The parity tests compare the JavaScript rule with the saved output of the Python harness (core.py final c86).
// They need data/ (local only, from research/autoresearch/export_dashboard.py). Without it they are skipped,
// and the tests on made-up inputs run.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const E = require(path.join(here, "../src/engine.js"));
const file = f => path.join(here, "../data", f);
const haveData = existsSync(file("dashboard_data.json")) && existsSync(file("parity_fixture.json"));
const data = haveData ? JSON.parse(readFileSync(file("dashboard_data.json"), "utf8")) : null;
const fx = haveData ? JSON.parse(readFileSync(file("parity_fixture.json"), "utf8")) : null;
const eng = haveData ? E.create(data) : null;
const real = { skip: haveData ? false : "data/ is not here (local only): run export_dashboard.py and copy its output" };

/* Made-up inputs: each year has one constant temperature, so each result can be found by hand. */
function madeUp() {
  const temp = y => (y === 2010 ? 23 : y === 2011 ? 21 : 22), heat = {};
  for (let y = 2003; y <= 2012; y++) heat[y] = new Array(y % 4 === 0 ? 91 : 90).fill(temp(y));
  return { rule: { lag_days: 10, ref_years: 5, min_days: 30, enso_avail: "02-15", first_year: 2009 },
    heat_daily: heat, enso_jan: { 2010: 1.0, 2011: -1.0, 2012: 0.5 } };
}

test("made-up inputs: the settled readings and calls of three years", () => {
  const e = E.create(madeUp());
  const a = e.yearSummary(2010), b = e.yearSummary(2011), c = e.yearSummary(2012);
  assert.ok(Math.abs(a.heat - 1.0) < 1e-9);                 // 23 against five years of 22
  assert.equal(a.name, "early");
  assert.ok(Math.abs(b.heat - (21 - 22.2)) < 1e-9);         // 21 against (22, 22, 22, 22, 23)
  assert.equal(b.name, "late");
  assert.ok(Math.abs(c.heat) < 1e-9);                       // 22 against (22, 22, 22, 23, 21)
  assert.equal(c.name, "steady");                           // a reading of zero is not a "yes"
  assert.equal(e.yearSummary(2013).state, null);            // no data for 2013
});

test("made-up inputs: the call by session, the dates of use, and the weekly hold", () => {
  const e = E.create(madeUp());
  assert.equal(e.q("2008-06-13"), 0);                       // before the first scored year
  assert.equal(e.q("2010-02-12"), 0);                       // no January value in use yet (2009 is not in the data)
  assert.equal(e.q("2010-06-11"), 1);
  assert.equal(e.q("2011-02-14"), 0);                       // Pacific of January 2010 (+1), heat of 2011 (-1.2): they disagree
  assert.equal(e.q("2011-02-15"), -1);                      // January 2011 value comes into use
  assert.equal(e.q("2011-06-10"), -1);
  assert.equal(e.heatInput("2011-02-08"), e.heatAnomalyOn(E.toMs("2011-01-29")));   // 10 days late: still the 2010 season
  assert.ok(Math.abs(e.heatInput("2011-02-08") - 1.0) < 1e-9);
  assert.ok(Math.abs(e.heatInput("2011-02-09") - (21 - 22.2)) < 1e-9);              // first reading of the 2011 season
  assert.deepEqual(e.weeklyPositions(["2010-06-10", "2010-06-11", "2010-06-14"]), [0, 1, 1]);
  assert.deepEqual(e.weeklyPositions(["2010-06-10", "2010-06-11", "2010-06-14"], ["2010-06-11"]), [0, 0, 1]);
  const c = e.callOn("2011-06-15");
  assert.deepEqual([c.decision, c.name, c.weekOf, c.calendar.nextReview], ["2011-06-10", "late", "2011-06-13", "2012-02-09"]);
});

test("fixture covers the scored years and the test period", real, () => {
  assert.ok(fx.dates.length > 4400);
  assert.equal(fx.dates.length, fx.pos.length);
  assert.ok(fx.dates[0] < "2009-01-01" && fx.dates.at(-1) === "2026-10-09");
});

test("input 1 (January Nino 3.4) is equal to the harness feature on each session", real, () => {
  let n = 0;
  fx.dates.forEach((d, i) => {
    if (fx.enso_jan[i] == null) return;
    assert.ok(Math.abs(eng.ensoInput(d).value - fx.enso_jan[i]) < 1e-3, `${d}: ${eng.ensoInput(d).value} vs ${fx.enso_jan[i]}`);
    n++;
  });
  assert.ok(n > 4400);
});

test("input 2 (Brazil Jan-Mar heat) is equal to the harness feature on each session", real, () => {
  let worst = 0, n = 0;
  fx.dates.forEach((d, i) => {
    if (fx.fill_tmean[i] == null) return;
    const v = eng.heatInput(d);
    assert.notEqual(v, null, d);
    worst = Math.max(worst, Math.abs(v - fx.fill_tmean[i]));
    n++;
  });
  assert.ok(n > 4400);
  assert.ok(worst < 2e-4, `largest difference ${worst}`);       // daily inputs are rounded to 4 decimals
});

test("the weekly position is equal to the harness position on each of the sessions, 2009 to Oct 2026", real, () => {
  const p = eng.weeklyPositions(fx.dates, fx.no_close);
  const bad = fx.dates.filter((d, i) => p[i] !== fx.pos[i]);
  assert.deepEqual(bad, []);
  const count = v => p.filter(x => x === v).length;
  assert.ok(count(1) > 500 && count(-1) > 500 && count(0) > 500, "all three calls occur");
});

test("a decision day with no usable close gives a steady week in the harness (one such week: 11 Nov 2016)", real, () => {
  const pure = eng.weeklyPositions(fx.dates), diff = fx.dates.filter((d, i) => pure[i] !== fx.pos[i]);
  assert.deepEqual(diff, ["2016-11-11", "2016-11-14", "2016-11-15", "2016-11-16", "2016-11-17"]);
  assert.ok(fx.no_close.includes("2016-11-11"));
});

test("the settled call of each year agrees with the main state of the saved run", real, () => {
  for (const r of data.yearly) assert.equal(eng.yearSummary(r.year).name, r.state, String(r.year));
});

test("the rule has three states and treats zero and missing inputs as steady", () => {
  assert.equal(E.agree(0.4, 0.2), 1);
  assert.equal(E.agree(-0.4, -0.2), -1);
  assert.equal(E.agree(0.4, -0.2), 0);
  assert.equal(E.agree(-0.4, 0.2), 0);
  assert.equal(E.agree(0, 0.2), 0);
  assert.equal(E.agree(null, 0.2), 0);
  assert.equal(E.agree(0.3, NaN), 0);
});

test("ISO week keys agree with known dates", () => {
  assert.equal(E.isoWeekKey(E.toMs("2021-01-03")), 202053);   // Sunday, last week of ISO year 2020
  assert.equal(E.isoWeekKey(E.toMs("2021-01-04")), 202101);
  assert.equal(E.isoWeekKey(E.toMs("2026-11-13")), 202646);
  assert.equal(E.isoWeekKey(E.toMs("2024-12-30")), 202501);
});

test("the call for the demo week is 'buy late' and names its inputs", real, () => {
  const c = eng.callOn("2026-11-18");
  assert.equal(c.decision, "2026-11-13");
  assert.equal(c.name, "late");
  assert.equal(c.enso.year, 2026);
  assert.ok(c.enso.value < 0 && c.heat.value < 0);
  assert.deepEqual([c.heat.year, c.heat.final], [2026, true]);
  assert.equal(c.calendar.nextReview, "2027-02-09");      // 30 January + 10 days
  assert.equal(c.calendar.ensoDay, "2027-02-15");
});

test("the call uses the January value only from 15 February, and weather that is 10 days old", real, () => {
  assert.equal(eng.ensoInput("2024-02-14").year, 2023);
  assert.equal(eng.ensoInput("2024-02-15").year, 2024);
  assert.equal(eng.heatInput("2024-06-14"), eng.heatAnomalyOn(E.toMs("2024-06-04")));
  const a = eng.callOn("2024-02-06"), b = eng.callOn("2024-02-23");
  assert.deepEqual([a.heat.year, a.heat.final], [2023, true]);
  assert.deepEqual([b.heat.year, b.heat.final], [2024, false]);
});

test("a date after the end of the data gives no call, not an old call", real, () => {
  const c = eng.callOn("2027-03-12");
  assert.equal(c.state, null);
  assert.ok(c.missing.includes("enso") && c.missing.includes("heat"));
});

test("planner: cover targets and amounts", () => {
  const late = E.plan({ call: "late", monthlyBags: 400, coverNow: 1.5, priceCents: 250 });       // made-up price
  assert.equal(late.action, "wait");
  assert.equal(late.targetMonths, 0);
  assert.equal(late.bagsToMove, 600);
  assert.ok(Math.abs(late.weeksToTarget - 6.5) < 1e-9);
  assert.ok(Math.abs(late.valueUsd - 600 * 132.277 * 2.5) < 1e-6);
  assert.ok(Math.abs(late.tenPctUsd - late.valueUsd / 10) < 1e-9);
  const early = E.plan({ call: "early", monthlyBags: 400, coverNow: 1, priceCents: 300 });
  assert.deepEqual([early.action, early.targetMonths, early.bagsToMove], ["buy", 3, 800]);
  const keep = E.plan({ call: "steady", monthlyBags: 400, coverNow: 1.5, priceCents: 300 });
  assert.deepEqual([keep.action, keep.bagsToMove], ["keep", 0]);
  assert.throws(() => E.plan({ call: "sell", monthlyBags: 1, coverNow: 0, priceCents: 1 }));
});
