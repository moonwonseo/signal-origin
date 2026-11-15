#!/usr/bin/env python3
"""Build the buyer dashboard: one HTML file with the rule engine and the data inside.

    python3 build.py            write signal_origin_dashboard.html
    python3 build.py --check    exit 1 if the built file is not up to date

Inputs:
  src/template.html, src/engine.js
  data/dashboard_data.json      from the autoresearch folder: export_dashboard.py (run on the compute machine)
  data/parity_fixture.json      same source; only its session count goes into the page
  data/gauge_v0.json            volatility gauge and its test, as in the dashboard of 14 Nov (not calculated again)
  demo_data/kc_recent.csv       optional (fetch_demo_data.py): closes after the end of the price archive
data/, demo_data/ and the built file contain rows from third parties. Keep them local. Do not commit them.
"""
import csv
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "signal_origin_dashboard.html"
BUILT = "2026-11-15"                      # fixed, so that the same inputs give the same file


def recent_weekly(after):
    """Last close of each ISO week after the end of the archive (the last row can be a part week)."""
    found = [p for p in (HERE / "demo_data" / "kc_recent.csv", HERE.parent / "03_data" / "demo_data" / "kc_recent.csv")
             if p.exists()]
    if not found:
        return []
    rows, weeks = list(csv.DictReader(found[0].open())), {}
    for r in rows:
        if r["date"] > after and r["close"]:
            y, w, _ = dt.date.fromisoformat(r["date"]).isocalendar()
            weeks[(y, w)] = [r["date"], round(float(r["close"]), 2)]
    return [weeks[k] for k in sorted(weeks)]


def build():
    D = json.loads((HERE / "data/dashboard_data.json").read_text())
    fx = json.loads((HERE / "data/parity_fixture.json").read_text())
    g = json.loads((HERE / "data/gauge_v0.json").read_text())
    D["weekly_close"] += recent_weekly(D["weekly_close"][-1][0])
    D["gauge"], D["track"] = g["gauge"], g["track"]
    D["latest_close"] = dict(date=g["gauge"]["asof"], value=g["gauge"]["last_close"])
    D["parity_sessions"] = sum(d >= f"{D['rule']['first_year']}-01-01" for d in fx["dates"])
    D["built"] = BUILT
    html = (HERE / "src/template.html").read_text()
    assert html.count("/*__ENGINE__*/") == 1 and html.count("/*__DATA__*/") == 1
    html = html.replace("/*__ENGINE__*/", (HERE / "src/engine.js").read_text().rstrip())
    return html.replace("/*__DATA__*/", "const D = " + json.dumps(D, separators=(",", ":"), ensure_ascii=False) + ";")


if __name__ == "__main__":
    missing = [f for f in ("dashboard_data.json", "parity_fixture.json", "gauge_v0.json") if not (HERE / "data" / f).exists()]
    if missing:
        sys.exit("data/ has no " + ", ".join(missing) + ". These files are local only: see README.md.")
    html = build()
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text() == html
        print("up to date" if ok else "NOT up to date: run python3 build.py")
        sys.exit(0 if ok else 1)
    OUT.write_text(html)
    print(f"wrote {OUT.name}: {len(html):,} characters")
