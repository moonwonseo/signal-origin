/* Signal-Origin rule engine: the buy rule c86 of the autoresearch loop, in plain JavaScript.
 *
 * The rule (candidates/c86.py + lib.py + core.py of research/autoresearch):
 *   input 1  enso_jan    Nino 3.4 anomaly of the latest January. A January value is used from 15 February.
 *   input 2  fill_tmean  Brazil mean temperature (six Arabica regions, weighted by output), mean from 1 January
 *                        to the day (Jan-Mar only, 30 days minimum, held after March), minus the same quantity
 *                        365, 730, ... 1825 days before. Weather is used 10 days late.
 *   call     both inputs > 0 -> +1 (buy early); both < 0 -> -1 (buy late); other cases -> 0 (steady).
 *   The call is read on the last session of each week and held for one week.
 *
 * No DOM here. The page and the tests use the same file.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.SignalEngine = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  const DAY = 86400000;
  const LB_PER_BAG = 132.277;                       // one 60 kg bag in pounds
  const COVER_MONTHS = { early: 3, steady: 1.5, late: 0 };   // plan section 2: cover moves between 0 and 3 months
  const NAMES = { "1": "early", "0": "steady", "-1": "late" };

  const toMs = s => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  const toIso = ms => new Date(ms).toISOString().slice(0, 10);

  /** The agreement rule on two numbers. */
  function agree(enso, heat) {
    if (enso == null || heat == null || !isFinite(enso) || !isFinite(heat)) return 0;
    return enso > 0 && heat > 0 ? 1 : enso < 0 && heat < 0 ? -1 : 0;
  }

  /** ISO week key (year * 100 + week), the same key as pandas isocalendar(). */
  function isoWeekKey(ms) {
    const dow = (new Date(ms).getUTCDay() + 6) % 7;                   // Monday = 0
    const thu = ms - dow * DAY + 3 * DAY, y = new Date(thu).getUTCFullYear();   // the Thursday gives the ISO year
    return y * 100 + Math.floor((thu - Date.UTC(y, 0, 1)) / (7 * DAY)) + 1;
  }

  function create(data) {
    const R = data.rule, heat = data.heat_daily, enso = data.enso_jan;
    const prefix = {};                                  // year -> running sums of the daily temperatures

    function sums(y) {
      if (!(y in prefix)) {
        const a = heat[y];
        if (!a) return (prefix[y] = null);
        const p = new Array(a.length);
        let s = 0;
        for (let i = 0; i < a.length; i++) { s += a[i]; p[i] = s; }
        prefix[y] = p;
      }
      return prefix[y];
    }
    const daysJanMar = y => (Date.UTC(y, 3, 1) - Date.UTC(y, 0, 1)) / DAY;

    /** Mean of 1 Jan .. day index i (0 = 1 Jan) of year y. null if that day is not in the data. */
    function runMean(y, i) {
      const p = sums(y);
      return p && i < p.length ? p[i] / (i + 1) : null;
    }
    /** Mean of the full Jan-Mar window of year y. null if the window is not complete in the data. */
    function finalMean(y) {
      const p = sums(y), n = daysJanMar(y);
      return p && p.length >= n ? p[n - 1] / n : null;
    }
    /** Season value on a calendar day: running mean in Jan-Mar (30 days minimum), held value in other months. */
    function seasonValue(ms) {
      const d = new Date(ms), y = d.getUTCFullYear();
      if (d.getUTCMonth() > 2) return finalMean(y);
      const i = Math.round((ms - Date.UTC(y, 0, 1)) / DAY);
      return i + 1 >= R.min_days ? runMean(y, i) : finalMean(y - 1);
    }
    /** Input 2 on a calendar day (no lag): season value minus the mean of the values 365*k days before. */
    function heatAnomalyOn(ms) {
      const s = seasonValue(ms);
      if (s == null) return null;
      let ref = 0;
      for (let k = 1; k <= R.ref_years; k++) {
        const v = seasonValue(ms - 365 * k * DAY);
        if (v == null) return null;
        ref += v;
      }
      return s - ref / R.ref_years;
    }
    /** Input 2 as the rule sees it on a session: the weather is `lag_days` old. */
    function heatInput(dateStr) { return heatAnomalyOn(toMs(dateStr) - R.lag_days * DAY); }

    /** Input 1 on a session: the January value of the year, from 15 February. */
    function ensoInput(dateStr) {
      const ms = toMs(dateStr), y = +dateStr.slice(0, 4);
      const year = ms >= Date.UTC(y, +R.enso_avail.slice(0, 2) - 1, +R.enso_avail.slice(3, 5)) ? y : y - 1;
      const value = enso[year];
      return value == null ? null : { year, value };
    }

    /** q(t): the call of the rule for one session, as +1, 0 or -1. Before the first scored year it is 0. */
    function q(dateStr) {
      if (+dateStr.slice(0, 4) < R.first_year) return 0;
      const e = ensoInput(dateStr);
      return agree(e && e.value, heatInput(dateStr));
    }

    /** The harness position: q on the last session of each ISO week, held to the next decision day.
     *  `noClose` = sessions with no usable close: the harness makes no forecast there, thus q = 0 (plan section 1). */
    function weeklyPositions(dates, noClose) {
      const keys = dates.map(d => isoWeekKey(toMs(d))), out = new Array(dates.length), skip = new Set(noClose || []);
      let p = 0;
      for (let i = 0; i < dates.length; i++) {
        if (i === dates.length - 1 || keys[i] !== keys[i + 1]) p = skip.has(dates[i]) ? 0 : q(dates[i]);
        out[i] = p;
      }
      return out;
    }

    /** The call for a calendar day, with its inputs. The decision day is the latest Friday on or before the
     *  day (the page has no exchange calendar for future dates; Friday is the usual last session of a week). */
    function callOn(dateStr) {
      const ms = toMs(dateStr), dow = new Date(ms).getUTCDay();
      const decision = toIso(ms - ((dow + 2) % 7) * DAY);
      const e = ensoInput(decision), h = heatInput(decision);
      const missing = [];
      if (!e) missing.push("enso");
      if (h == null) missing.push("heat");
      const wms = toMs(decision) - R.lag_days * DAY, wd = new Date(wms);
      const inWindow = wd.getUTCMonth() <= 2 && Math.round((wms - Date.UTC(wd.getUTCFullYear(), 0, 1)) / DAY) + 1 >= R.min_days;
      const state = missing.length ? null : agree(e.value, h);
      return {
        date: dateStr, decision, state, name: state == null ? null : NAMES[state], missing,
        enso: e, heat: h == null ? null : { value: h, year: inWindow || wd.getUTCMonth() > 2 ? wd.getUTCFullYear() : wd.getUTCFullYear() - 1, final: !inWindow },
        weekOf: toIso(toMs(decision) + 3 * DAY), calendar: calendar(dateStr),
      };
    }

    /** Dates on which the inputs can change, for the cycle that contains or follows the day. */
    function calendar(dateStr) {
      const ms = toMs(dateStr), y0 = +dateStr.slice(0, 4);
      const cyc = y => ({
        year: y,
        windowOpen: toIso(Date.UTC(y, 0, 1)),
        firstHeat: toIso(Date.UTC(y, 0, R.min_days) + R.lag_days * DAY),
        ensoDay: toIso(Date.UTC(y, +R.enso_avail.slice(0, 2) - 1, +R.enso_avail.slice(3, 5))),
        heatFinal: toIso(Date.UTC(y, 2, 31) + R.lag_days * DAY),
      });
      let c = cyc(y0);
      if (ms > toMs(c.heatFinal)) c = cyc(y0 + 1);
      c.phase = ms < toMs(c.firstHeat) ? "held" : "updating";
      c.nextReview = c.phase === "held" ? c.firstHeat : c.heatFinal;
      return c;
    }

    /** The settled inputs of one year (the values that hold from mid April to the next February). */
    function yearSummary(y) {
      const f = finalMean(y);
      let ref = 0, ok = f != null;
      for (let k = 1; ok && k <= R.ref_years; k++) { const v = finalMean(y - k); if (v == null) ok = false; else ref += v; }
      const h = ok ? f - ref / R.ref_years : null, e = enso[y] == null ? null : enso[y];
      const state = h == null || e == null ? null : agree(e, h);
      return { year: y, enso: e, heat: h, meanTemp: f, state, name: state == null ? null : NAMES[state] };
    }

    /** Running Jan-Mar mean of year y and its five-year reference, day by day (for the season chart). */
    function seasonTrack(y) {
      const out = [], n = daysJanMar(y);
      for (let i = R.min_days - 1; i < n; i++) {
        const ms = Date.UTC(y, 0, 1) + i * DAY, s = runMean(y, i);
        let ref = 0, ok = true;
        for (let k = 1; k <= R.ref_years; k++) { const v = seasonValue(ms - 365 * k * DAY); if (v == null) { ok = false; break; } ref += v; }
        out.push({ date: toIso(ms), value: s, ref: ok ? ref / R.ref_years : null });
      }
      return out;
    }

    return { q, weeklyPositions, callOn, calendar, yearSummary, seasonTrack, ensoInput, heatInput, heatAnomalyOn };
  }

  /** What a call means for cover. All amounts are for the futures part of the price only. */
  function plan(o) {
    const target = COVER_MONTHS[o.call];
    if (target == null) throw new Error("unknown call: " + o.call);
    const need = Math.max(0, +o.monthlyBags || 0), now = Math.min(3, Math.max(0, +o.coverNow || 0));
    const price = Math.max(0, +o.priceCents || 0);
    const deltaMonths = target - now, bags = Math.abs(deltaMonths) * need;
    const usd = b => b * LB_PER_BAG * price / 100;
    return {
      targetMonths: target, coverNow: now, deltaMonths, bagsToMove: bags,
      action: deltaMonths > 1e-9 ? "buy" : deltaMonths < -1e-9 ? "wait" : "keep",
      valueUsd: usd(bags), tenPctUsd: usd(bags) * 0.10,
      weeksToTarget: deltaMonths < 0 ? -deltaMonths * 52 / 12 : 0,
      monthValueUsd: usd(need), swingBags: 1.5 * need, swingTenPctUsd: usd(1.5 * need) * 0.10,
    };
  }

  return { create, agree, plan, isoWeekKey, toMs, toIso, NAMES, COVER_MONTHS, LB_PER_BAG };
});
