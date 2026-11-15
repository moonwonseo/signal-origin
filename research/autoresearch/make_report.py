"""Iteration table and hill-climb graph from the trial log (eval revision 1). Aggregates only."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")
import core

LABEL = {  # id: (block, short description of the change)
    "c01": ("Price", "Trend rule: sign of the 12-month return"),
    "c02": ("Price", "'Carry' from the marked roll days (wrong day; VOID)"),
    "c03": ("Price", "Carry rule from the correct contract-gap day"),
    "c04": ("Price", "Value rule: price against its 5-year mean"),
    "c05": ("Weather", "Brazil rain deficit, 90 days (raw level)"),
    "c06": ("Weather", "Brazil heat-and-dry stress, 90 days, drift removed"),
    "c07": ("Positioning", "Speculator positions at extremes (CFTC)"),
    "c08": ("Climate index", "ENSO state rule (La Nina / El Nino)"),
    "c09": ("Weather", "Stress of the other origins"),
    "c10": ("Weather", "c06 + frost days"),
    "c11": ("Weather (new source 1)", "Brazil root-zone soil moisture"),
    "c12": ("Weather", "Stress and soil moisture must agree"),
    "c13": ("Other market (new source 2)", "Dollar index trend"),
    "c14": ("Other market", "USD/BRL trend"),
    "c15": ("Model", "Logistic regression on 4 signals"),
    "c16": ("Model", "Random forest on 16 features"),
    "c17": ("Model", "LightGBM on 15 features"),
    "c18": ("Weather", "Stress of the crop season to date (Oct-Apr)"),
    "c19": ("Weather", "Season rain deficit only"),
    "c20": ("Weather", "Season heat only"),
    "c21": ("Weather", "Season maximum temperature"),
    "c22": ("Weather", "Season heat and 90-day stress must agree"),
    "c23": ("Robustness", "c22 with weather 10 days old"),
    "c24": ("Robustness", "c22 with a 10-year normal"),
    "c25": ("Other market (new source 3)", "Arabica-robusta price spread"),
    "c26": ("Weather", "c22 + memory of the previous season"),
    "c27": ("Other market (new source 4)", "Sugar trend"),
    "c28": ("Combination", "Vote: weather rule (c22) + sugar trend"),
    "c29": ("Supply (new source 5)", "USDA world stocks-to-use"),
    "c30": ("Combination", "Majority of season heat, 90-day stress, sugar"),
    "c31": ("Other markets", "Breadth of 5 farm commodities (new data: Yahoo)"),
    "c32": ("Other markets", "Brazil equity fund trend"),
    "c33": ("Calendar", "Frost-risk calendar rule (no data)"),
    "c34": ("Falsification", "Season heat of the other origins (Oct-Apr)"),
    "c35": ("Supply flow (new source)", "Brazil export volume (incomplete file; VOID)"),
    "c36": ("Supply flow", "Brazil export volume, 2nd try (file still incomplete; VOID)"),
    "c37": ("Supply flow", "Brazil export volume, complete file"),
    "c38": ("Positioning", "Hedging pressure of producers (CFTC)"),
    "c39": ("Other markets", "World growth vote: S&P 500, copper, crude"),
    "c40": ("Weather", "It. 22 with price confirmation"),
    "c41": ("Weather", "Season heat, large anomalies only"),
    "c42": ("Other markets", "Five-market slow trend composite"),
    "c43": ("Combination", "Weather rule (22) + five-market composite"),
    "c44": ("Weather", "Flowering heat only (Sep-Nov)"),
    "c45": ("Weather", "Grain-fill heat only (Jan-Mar)"),
    "c46": ("Weather", "Grain-fill heat and 90-day stress agree"),
    "c47": ("Combination", "Majority: fill heat, stress, market composite"),
    "c48": ("Robustness", "It. 45 with weather 10 days old"),
    "c49": ("Robustness", "It. 45 with a 10-year normal"),
    "c50": ("Robustness", "It. 45 with window Dec-Feb"),
    "c51": ("Robustness", "It. 45 with window Feb-Apr"),
    "c52": ("Robustness", "It. 45 with mean temperature"),
    "c53": ("Robustness", "It. 45 with Minas Gerais only"),
    "c54": ("Other markets", "US 10-year yield change"),
    "c55": ("Weather (new data)", "Vietnam dry-season heat (robusta supply)"),
    "c56": ("Price", "Coffee price in reais against its 1-year mean"),
    "c57": ("Model", "Logistic regression on the 4 best features"),
    "c58": ("Model", "Logistic regression with time-decay weights"),
    "c59": ("Other markets", "Market fear: VIX against its 1-year mean"),
    "c60": ("Combination", "Market composite and Vietnam heat agree"),
    "c61": ("Other markets", "Colombian peso trend"),
    "c62": ("Other markets", "Robusta price trend (World Bank)"),
    "c63": ("Exposure", "It. 22 with a volatility switch"),
    "c64": ("Climate index (new source)", "Indian Ocean Dipole (NOAA)"),
    "c65": ("Robustness", "Market composite, 63-session horizon"),
    "c66": ("Robustness", "Market composite, 252-session horizon"),
    "c67": ("Weather", "Colombia flowering heat (Jan-Mar)"),
    "c68": ("Falsification", "Central America heat in Jan-Mar (no crop meaning)"),
    "c69": ("Weather", "Brazil-specific heat (Brazil minus other regions)"),
    "c70": ("Weather", "Common Jan-Mar warmth outside Brazil"),
    "c71": ("Climate index", "ENSO state of January, held for a year"),
    "c72": ("Combination", "Majority: ENSO, Brazil-specific heat, market composite"),
    "c73": ("Combination", "Majority: ENSO, Brazil fill heat, market composite"),
    "c74": ("Climate index", "ENSO rule for real events only"),
    "c75": ("Combination", "ENSO state and market composite agree"),
    "c76": ("Model", "Depth-2 decision tree on 3 inputs"),
    "c77": ("Robustness (new source)", "Brazil fill heat from ERA5"),
    "c78": ("Weather", "Brazil water balance, rain minus ET0 (ERA5)"),
    "c79": ("Robustness", "It. 73 with weather 10 days old"),
    "c80": ("Robustness", "It. 73 with ERA5 heat"),
    "c81": ("Robustness", "It. 73 with 252-session trends"),
    "c82": ("Robustness", "It. 73 with Dec-Feb ENSO mean"),
    "c83": ("Combination", "ENSO state and Brazil fill heat agree"),
    "c84": ("Robustness", "It. 83 with Dec-Feb ENSO mean"),
    "c85": ("Robustness", "It. 83 with ERA5 heat"),
    "c86": ("Robustness", "It. 83 with weather 10 days old"),
    "c87": ("Robustness", "It. 86 with maximum temperature"),
    "c88": ("Robustness", "It. 86 with a 10-year normal"),
    "c89": ("Robustness", "It. 86 with Minas Gerais only"),
    "c90": ("Robustness", "It. 86 with window Dec-Feb"),
    "c91": ("Combination", "ENSO state and Brazil-specific heat agree"),
    "c92": ("Falsification", "ENSO state with Central America heat"),
    "c93": ("Robustness", "It. 86 with both weather products (POWER + ERA5)"),
    "c94": ("Combination", "ENSO, Brazil heat and market composite all agree"),
    "c95": ("Combination", "ENSO state with Vietnam heat"),
    "c96": ("Combination", "ENSO state with Colombia heat"),
    "c97": ("Robustness", "It. 86 with ENSO events only"),
    "c98": ("Robustness", "It. 86 with ENSO updated in mid year"),
    "c99": ("Combination", "Careful design: Dec-Feb ENSO + two-product Brazil heat"),
    "c100": ("Combination", "Careful design + market composite (majority)"),
}
rows = core.log_rows()
void = {r["id"] for r in rows if r["kind"] == "void"}
base = {r["id"]: r["metrics"]["ratio"] for r in rows if r["kind"] == "baseline"}
its = [r for r in rows if r["kind"] == "iter"]
out = Path("results"); out.mkdir(exist_ok=True)
best, best_line, tab = max(base.values()), [], []
for r in its:
    m, c = r["metrics"], r["constraints"]
    status = "VOID" if r["id"] in void else ("ACCEPTED (new best)" if r["accepted"] else "rejected")
    if r["accepted"] and r["id"] not in void:
        best = m["ratio"]
    best_line.append(best)
    worked = "No (void)" if r["id"] in void else ("Yes" if r["accepted"] else
             ("Partly" if m["ratio"] >= 0.45 and all(c.values()) else "No"))
    tab.append(dict(iteration=r["iter"], id=r["id"], block=LABEL[r["id"]][0], change=LABEL[r["id"]][1],
                    ratio=round(m["ratio"], 3), need=round(core.SE0 * core.emax(r["N"]), 3), score=round(m["score"], 3),
                    half1=round(m["ratio_h1"], 2), half2=round(m["ratio_h2"], 2), years_pos=m["years_pos"],
                    hit=None if m.get("hit") is None else round(m["hit"], 3), saved_pct=round(m["pct_cost_saved"], 2),
                    constraints_ok=all(c.values()), step=status, worked=worked, best_after=round(best, 3)))
import csv
with open(out / "iteration_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tab[0])); w.writeheader(); w.writerows(tab)
md = ["| It. | Block | What changed | RATIO | Halves | Years + | Step rule | Worked? |", "|---|---|---|---|---|---|---|---|"]
for t in tab:
    md.append(f"| {t['iteration']} | {t['block']} | {t['change']} | {t['ratio']:+.3f} | {t['half1']:+.2f} / {t['half2']:+.2f} | "
              f"{t['years_pos']}/14 | {t['step']} | {t['worked']} |")
(out / "iteration_table.md").write_text("\n".join(md) + "\n")
print("\n".join(md))

# ---- hill-climb graph ----------------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURF, INK, INK2, GRID, BLUE, ORANGE, MUTE = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#eb6834", "#9a9992"
x = np.array([t["iteration"] for t in tab]); y = np.array([t["ratio"] for t in tab])
need = np.array([t["need"] for t in tab])
fig, ax = plt.subplots(figsize=(11, 5.6), dpi=200)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
ax.axhline(0, color=GRID, lw=1, zorder=1)
for v in (-0.25, 0.25, 0.5, 0.75):
    pass
for v in (-0.25, 0.25, 0.5, 0.75):
    ax.axhline(v, color=GRID, lw=0.6, zorder=1)
ax.plot(np.r_[0, x], np.r_[core.SE0 * core.emax(10), need], color=ORANGE, lw=2, solid_capstyle="round", zorder=3,
        label="RATIO necessary for SCORE > 0 (rises with each trial)")
ax.step(np.r_[0, x], np.r_[max(base.values()), best_line], where="post", color=BLUE, lw=2, zorder=4,
        label="Best RATIO to date (plan's step rule)")
acc = np.array([t["step"].startswith("ACC") for t in tab]); vd = np.array([t["step"] == "VOID" for t in tab])
rej = ~acc & ~vd
ax.scatter(x[rej], y[rej], s=26, facecolor=SURF, edgecolor=MUTE, linewidth=1.3, zorder=5, label="Iteration, rejected")
ax.scatter(x[vd], y[vd], s=60, marker="x", color=MUTE, linewidth=1.8, zorder=5, label="Iteration, void (feature defect)")
ax.scatter(x[acc], y[acc], s=90, facecolor=BLUE, edgecolor=SURF, linewidth=2, zorder=6, label="Iteration, accepted as new best")
note = {6: ("6: Brazil heat-and-dry\nstress, 90 days", (-5.5, 0.19)), 22: ("22: season heat and\nrecent stress agree", (-8.0, 0.27)),
        86: ("86: ENSO winter state and\nBrazil Jan-Mar heat agree", (-27.0, 0.11)),
        45: ("45: Jan-Mar heat", (-12.0, 0.27)), 73: ("73: ENSO + heat\n+ market trend", (-5.5, -0.42)), 71: ("71: ENSO\nalone", (-1.5, -0.47))}
for t in tab:
    if t["iteration"] in note:
        txt, (dx, dy) = note[t["iteration"]]
        ax.annotate(txt, (t["iteration"], t["ratio"]), xytext=(t["iteration"] + dx, t["ratio"] + dy), fontsize=8.5, color=INK2,
                    arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.7) if abs(dx) > 1.2 else None, va="center")
ax.text(101.2, need[-1] - 0.035, f"{need[-1]:.3f} necessary", color=INK2, fontsize=9, va="center")
ax.text(101.2, best_line[-1] + 0.03, f"{best_line[-1]:.3f} best", color=INK2, fontsize=9, va="center")
ax.set_xlim(-2, 114); ax.set_ylim(-0.45, 0.95)
ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]); ax.set_xticklabels(["base", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])
ax.set_xlabel("Iteration", color=INK2, fontsize=10); ax.set_ylabel("RATIO (cost saving / its variation, per year)", color=INK2, fontsize=10)
ax.tick_params(colors=INK2, length=0, labelsize=9)
for s in ax.spines.values():
    s.set_visible(False)
fig.suptitle("Hill-climb of the buy-timing score over 100 iterations", x=0.065, y=0.975, ha="left", fontsize=14, color=INK, fontweight="bold")
ax.set_title("Development years 2009-2022. Best rule (iteration 86): +0.787 against 0.712 necessary; placebo passed (0 of 17).\n"
             "Test 2023-Oct 2026 (second look): RATIO +0.37, below the pass limit of 0.5.", loc="left", fontsize=9, color=INK2, pad=10)
leg = ax.legend(loc="lower left", fontsize=8.5, frameon=False, ncol=2, labelcolor=INK2, bbox_to_anchor=(0.0, -0.33))
fig.subplots_adjust(left=0.065, right=0.985, top=0.84, bottom=0.25)
fig.savefig(out / "hillclimb.png", facecolor=SURF)
print("graph saved")
