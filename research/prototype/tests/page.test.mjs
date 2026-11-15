// Tests of the built page in a DOM (jsdom). Run: JSDOM_DIR=/path/with/node_modules node --test tests/*.test.mjs
// The built page and data/ are local only (they contain prices). Without them, or without jsdom, these tests are skipped.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..");
const page = path.join(root, "signal_origin_dashboard.html");
const built = existsSync(page) && existsSync(path.join(root, "data/dashboard_data.json"));
const html = built ? readFileSync(page, "utf8") : "";
const close = built ? JSON.parse(readFileSync(path.join(root, "data/gauge_v0.json"), "utf8")).gauge.last_close : 0;   // start price of the planner
const usd = v => "$" + Math.round(v).toLocaleString("en-US");
const local = { skip: built ? false : "the built page and data/ are not here (local only): run build.py" };

let JSDOM = null, VirtualConsole = null;
for (const base of [process.env.JSDOM_DIR, root].filter(Boolean)) {
  try { ({ JSDOM, VirtualConsole } = createRequire(path.join(base, "noop.js"))("jsdom")); break; } catch { /* next */ }
}
const dom = { skip: !built ? local.skip : JSDOM ? false : "jsdom is not installed (set JSDOM_DIR)" };

function open(date) {
  const errors = [], vc = new VirtualConsole();
  vc.on("jsdomError", e => { if (!/Could not parse CSS/.test(e.message)) errors.push(e.message); });
  vc.on("error", e => errors.push(String(e)));
  const d = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc,
    url: "http://localhost/signal_origin_dashboard.html?date=" + date });
  const doc = d.window.document;
  return { win: d.window, doc, errors, text: id => doc.getElementById(id).textContent, $: id => doc.getElementById(id) };
}
function set(p, id, value, type = "input") {
  const el = p.$(id); el.value = String(value);
  el.dispatchEvent(new p.win.Event(type, { bubbles: true }));
}
function pick(p, value) {
  const el = p.doc.querySelector(`#callpick input[value="${value}"]`); el.checked = true;
  el.dispatchEvent(new p.win.Event("change", { bubbles: true }));
}

test("the built page is up to date with src/ and data/", local, () => {
  assert.match(execFileSync("python3", [path.join(root, "build.py"), "--check"], { encoding: "utf8" }), /up to date/);
});

test("the built page contains the tested engine file, with no change", local, () => {
  const engine = readFileSync(path.join(root, "src/engine.js"), "utf8").trimEnd();
  assert.ok(html.includes(engine));
  assert.ok(!html.includes("/*__ENGINE__*/") && !html.includes("/*__DATA__*/"));
});

test("demo week (18 Nov 2026): the page loads with no script error and shows 'Buy late'", dom, () => {
  const p = open("2026-11-18");
  assert.deepEqual(p.errors, []);
  assert.equal(p.text("big"), "Buy late");
  assert.match(p.text("asof"), /week of 16 Nov 2026 · set on 13 Nov 2026/);
  assert.match(p.text("inputs"), /−0\.54 °C.*−0\.38 °C.*9 Feb/s);
  assert.match(p.text("why"), /cooler than normal.*cooler than their five-year mean.*buy late/s);
  assert.equal(p.doc.querySelectorAll("#dial .seg.on").length, 1);
  assert.ok(p.doc.querySelector("#dial .seg.late.on"));
  assert.match(p.text("stepnote"), /call holds until 9 Feb 2027/);
});

test("each section has its content", dom, () => {
  const p = open("2026-11-18"), n = sel => p.doc.querySelectorAll(sel).length;
  assert.equal(n("#quad .dot"), 18);                       // years 2009-2026
  assert.equal(n("#quad .now"), 1);
  assert.equal(n("#ychart .bar"), 18);
  assert.equal(n("#ytable tr"), 19);
  assert.match(p.text("ytable"), /2010Buy early.*2012Buy late.*2014Steady.*2026 \(new data\)Buy late/s);
  assert.ok(n("#pchart .band.early") >= 5 && n("#pchart .band.late") >= 5);
  assert.ok(p.doc.querySelector("#pchart .px").getAttribute("d").length > 5000);
  assert.equal(n("#season path"), 2);
  assert.equal(n("#steps div"), 4);
  assert.equal(n("#tiles .tile"), 3);
  assert.match(p.text("tiles"), /\+0\.79.*0\.71.*Passed.*0 of 17.*Passed.*\+0\.37.*0\.50.*−0\.60 to \+1\.43.*Not confirmed/s);
  assert.match(p.text("pastsum"), /11 of 14 years, 2\.3%.*2 of 4 years and 1\.5%/s);
  assert.equal(p.text("gbig"), "59%");
  assert.match(p.text("gnote"), /0\.240 against 0\.260/);
  assert.match(p.text("method"), /4,47\d sessions/);
  const body = p.doc.body.cloneNode(true);
  body.querySelectorAll("script").forEach(e => e.remove());
  assert.doesNotMatch(body.textContent, /NaN|undefined|null|Infinity/);
  assert.doesNotMatch(body.innerHTML, /="(NaN|undefined|null)"|NaN/);       // no broken SVG attribute
});

test("planner: the default plan, then a change of call, need and cover", dom, () => {
  const p = open("2026-11-18");
  assert.equal(p.text("act"), "Place no forward orders for about 6.5 weeks.");
  const value = 600 * 132.277 * close / 100, stats = p.text("planstats");
  assert.equal(p.$("price").value, close.toFixed(1));
  for (const t of ["600 bags", usd(value), close.toFixed(1) + " ¢/lb", usd(value / 10)]) assert.ok(stats.includes(t), t);
  pick(p, "early");
  assert.equal(p.text("act"), "Buy about 600 bags now.");
  set(p, "need", 1000); set(p, "cover", 0);
  assert.equal(p.text("act"), "Buy about 3,000 bags now.");
  set(p, "price", 300);
  assert.match(p.text("planstats"), /3,000 bags.*\$1,190,493.*\$119,049/s);
  pick(p, "steady"); set(p, "cover", 1.5);
  assert.equal(p.text("act"), "Keep your usual buying pace.");
  assert.match(p.text("gnote"), /10% move on 1\.5 months of need is \$59,525/);
  assert.deepEqual(p.errors, []);
});

test("what-if sliders give the call of the rule", dom, () => {
  const p = open("2026-11-18");
  assert.equal(p.text("whatout"), "Buy late");
  set(p, "s-enso", 1); set(p, "s-heat", 0.5);
  assert.equal(p.text("whatout"), "Buy early");
  set(p, "s-heat", -0.5);
  assert.equal(p.text("whatout"), "Steady");
  set(p, "s-enso", -1);
  assert.equal(p.text("whatout"), "Buy late");
  p.$("reset").dispatchEvent(new p.win.Event("click", { bubbles: true }));
  assert.equal(p.$("s-enso").value, "-0.54");
  assert.equal(p.$("s-heat").value, "-0.38");
  assert.equal(p.text("reset"), "");
});

test("a hover on a year bar shows its numbers", dom, () => {
  const p = open("2026-11-18"), hit = p.doc.querySelectorAll("#ychart .hit")[1];
  hit.dispatchEvent(new p.win.MouseEvent("mousemove", { bubbles: true }));
  assert.equal(p.$("tip").hidden, false);
  assert.match(p.text("tip"), /2010.*\+7\.7% of the yearly purchase cost.*buy early/s);
  hit.dispatchEvent(new p.win.MouseEvent("mouseleave"));
  assert.equal(p.$("tip").hidden, true);
});

test("other weeks: early, steady, a week in the reading window, and a date after the data", dom, () => {
  let p = open("2024-06-14");
  assert.equal(p.text("big"), "Buy early");
  assert.equal(p.text("act"), "Buy about 600 bags now.");
  p = open("2025-06-13");
  assert.equal(p.text("big"), "Steady");
  assert.equal(p.text("act"), "Keep your usual buying pace.");
  p = open("2024-02-23");
  assert.match(p.text("why"), /so far/);
  assert.match(p.text("stepnote"), /can change each week until 10 Apr 2024/);
  p = open("2027-03-12");
  assert.equal(p.text("big"), "No call");
  assert.match(p.text("bigcap"), /data in this file end before this date/);
  assert.equal(p.doc.querySelector('#callpick input[value="steady"]').checked, true);
  assert.deepEqual(p.errors, []);
});
