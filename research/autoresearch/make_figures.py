"""Figures for the slide deck. Aggregates and made-up illustrations only: no third-party rows are written.

Run from the autoresearch folder on the compute machine:  ./run.sh make_figures.py
Inputs: trial_log.jsonl, out/c86/saving_final.npy and pos_final.npy (saved by the logged final run; this script
does not score anything again). Outputs: results/figures/*.png and results/figures/yearly_c86.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
import core

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = Path("results/figures"); OUT.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, BLUE, ORANGE, MUTE, LIGHT = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#eb6834", "#9a9992", "#d9d8d2"
W, H, DPI = 9.0, 4.2, 200
plt.rcParams.update({"font.size": 10.5, "axes.edgecolor": GRID, "text.color": INK2, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2})


def clean(ax, grid="y"):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(OUT / name, facecolor="white", dpi=DPI)
    plt.close(fig)
    print("saved", name)


# ---- 1. the label (made-up prices) ---------------------------------------------------------------------
rng = np.random.default_rng(7)
n, t0, h = 125, 30, 63
px = 200 * np.exp(np.cumsum(rng.normal(0.0012, 0.013, n)))[: t0 + h + 1]
n = len(px)
win = np.arange(t0 + 1, t0 + h + 1)
m = px[win].mean()
fig, ax = plt.subplots(figsize=(W, H))
ax.axvspan(t0 + 1, t0 + h, color="#f3f2ee", zorder=0)
ax.plot(np.arange(n), px, color=INK2, lw=1.6, zorder=3)
ax.plot([t0, t0 + h], [px[t0], px[t0]], color=BLUE, lw=2, zorder=4)
ax.plot([t0 + 1, t0 + h], [m, m], color=ORANGE, lw=2, zorder=4)
ax.scatter([t0], [px[t0]], s=70, color=BLUE, edgecolor="white", linewidth=2, zorder=5)
ax.annotate("", xy=(t0 + h + 3, m), xytext=(t0 + h + 3, px[t0]), arrowprops=dict(arrowstyle="<->", color=INK2, lw=1))
ax.text(t0 + h + 5, (m + px[t0]) / 2, "cost saved if you buy today", va="center", fontsize=10)
ax.text(t0 + h + 5, px[t0] - 1.6, "price today", color=BLUE, va="center", fontsize=10.5, fontweight="bold")
ax.text(t0 + h + 5, m + 1.6, "mean price of the next 63 sessions", color=ORANGE, va="center", fontsize=10.5, fontweight="bold")
ax.text(t0 + h / 2, ax.get_ylim()[1] - 1.0, "the next 63 trading sessions (about 3 months)", ha="center", va="top", fontsize=10)
ax.set_xlim(-3, t0 + h + 68)
ax.set_xticks([t0, t0 + h]); ax.set_xticklabels(["today", "today + 63 sessions"])
ax.set_ylabel("Price, US cents per pound")
ax.text(0.995, 0.02, "Made-up prices, for illustration", transform=ax.transAxes, ha="right", fontsize=8.5, color=MUTE)
clean(ax)
fig.subplots_adjust(left=0.08, right=0.985, top=0.97, bottom=0.10)
save(fig, "label_illustration.png")

# ---- 2. walk-forward --------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(W, H))
years = list(range(2009, 2027))
for i, y in enumerate(years):
    test = y >= 2023
    ax.add_patch(Rectangle((2000, i - 0.36), y - 0.25 - 2000, 0.72, color=LIGHT, zorder=2))
    ax.add_patch(Rectangle((y, i - 0.36), 0.77 if y == 2026 else 1.0, 0.72, color=ORANGE if test else BLUE, zorder=3))
ax.set_ylim(len(years) - 0.4, -1.9); ax.set_xlim(1999.5, 2027.6)
ax.set_yticks(range(len(years))); ax.set_yticklabels([str(y) for y in years], fontsize=8.5)
ax.set_xticks(range(2000, 2027, 2))
ax.text(2000, -1.0, "Training: all earlier data, expanding", color=INK2, fontsize=10.5, fontweight="bold", va="center")
ax.text(2013.4, 0.9, "Scored year (2009-2022)", color=BLUE, fontsize=10.5, fontweight="bold", va="center")
ax.text(2027.5, 13.6, "Test years\n(2023-Oct 2026)", color=ORANGE, fontsize=10.5, fontweight="bold", va="bottom", ha="right")
ax.annotate("gap of 63 sessions:\nlabels that reach into the\nscored year are removed", xy=(2015.88, 7), xytext=(2018.2, 3.0), fontsize=9,
            arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.8), va="center")
ax.set_ylabel("Year that is predicted")
clean(ax, grid="x")
fig.subplots_adjust(left=0.085, right=0.985, top=0.985, bottom=0.08)
save(fig, "walk_forward.png")

# ---- 3. best score of each idea family (table "What the 100 iterations show" in Autoresearch_RESULTS.md) ---
fam = [("ENSO winter state + Brazil Jan-Mar heat (final rule)", 0.79), ("Brazil Jan-Mar heat alone", 0.69),
       ("Votes of ENSO, Brazil heat and market trend", 0.67), ("Other weather stress (90 days, season, other origins)", 0.61),
       ("ENSO winter state alone", 0.42), ("Water stress (rain, soil moisture, water balance)", 0.41),
       ("Slow trend of five markets", 0.34), ("Fitted models (logistic, forest, LightGBM, tree)", 0.31),
       ("Positioning, exports, stocks, currencies, rates", 0.27), ("Price trend, carry, value", 0.09),
       ("Climate indices as monthly states", 0.00)]
need = core.SE0 * core.emax(110)
fig, ax = plt.subplots(figsize=(W, H))
ys = np.arange(len(fam))
ax.barh(ys, [v for _, v in fam], height=0.62, color=BLUE, zorder=3)
for y, (lab, v) in zip(ys, fam):
    if v >= 0.2 and not (v - 0.09 < need < v):       # inside the bar, unless the label would cross the orange line
        ax.text(v - 0.012, y, f"+{v:.2f}", va="center", ha="right", fontsize=10, color="white", fontweight="bold")
    else:
        ax.text(v + 0.012, y, f"+{v:.2f}" if v else "0.00", va="center", fontsize=10, color=INK)
ax.axvline(need, color=ORANGE, lw=2, zorder=4)
ax.text(need - 0.015, len(fam) - 1.5, f"score necessary after\n110 trials: {need:.2f}", color=ORANGE, fontsize=10, fontweight="bold", va="center", ha="right")
ax.set_yticks(ys); ax.set_yticklabels([lab for lab, _ in fam], fontsize=10)
ax.set_ylim(len(fam) - 0.4, -0.6); ax.set_xlim(0, 0.95)
ax.set_xlabel("Best score (RATIO) of the family on 2009-2022")
clean(ax, grid="x")
fig.subplots_adjust(left=0.46, right=0.985, top=0.985, bottom=0.13)
save(fig, "families.png")

# ---- 4. yearly result of the final rule (c86), from the saved final run ----------------------------------
D = core.Data(core.FINAL_CUTOFF)
sv = np.load("out/c86/saving_final.npy"); pos = np.load("out/c86/pos_final.npy")
d = pd.DataFrame({"year": D.dates.dt.year.to_numpy(), "sv": sv, "p": pos})
d = d[d.year >= 2009]
g = d.groupby("year").agg(saving_pct=("sv", lambda x: 100 * x.sum()), share_early=("p", lambda x: (x > 0).mean()),
                          share_late=("p", lambda x: (x < 0).mean())).reset_index()
g["state"] = np.where(g.share_early >= 0.5, "early", np.where(g.share_late >= 0.5, "late", "steady"))
g.round(3).to_csv(OUT / "yearly_c86.csv", index=False)
fig, ax = plt.subplots(figsize=(W, H))
ax.axvspan(2022.5, 2026.5, color="#f3f2ee", zorder=0)
ax.bar(g.year, g.saving_pct, width=0.62, color=BLUE, zorder=3)
ax.axhline(0, color=INK2, lw=1, zorder=4)
for _, r in g.iterrows():
    off = 2.5 if r.saving_pct >= 0 else -2.5
    ax.text(r.year, r.saving_pct + off, (f"{r.saving_pct:+.0f}" if abs(r.saving_pct) >= 0.5 else "0"), ha="center", va="bottom" if off > 0 else "top", fontsize=9, color=INK)
    ax.text(r.year, -43, r.state, ha="center", va="center", fontsize=8.5 if r.state != "steady" else 7.5, color=INK if r.state != "steady" else MUTE,
            fontweight="bold" if r.state != "steady" else "normal")
ax.text(2024.5, 68, "test period", ha="center", fontsize=10.5, fontweight="bold", color=INK2)
ax.text(2015.5, 68, "development years", ha="center", fontsize=10.5, fontweight="bold", color=INK2)
ax.text(2008.1, -43, "main\nstate", ha="right", va="center", fontsize=8.5, color=INK2)
ax.set_xticks(g.year); ax.set_xticklabels([str(y) for y in g.year], fontsize=9)
ax.set_ylim(-50, 76); ax.set_xlim(2007.2, 2026.6)
ax.set_ylabel("Saving in the year, % of the price")
clean(ax)
fig.subplots_adjust(left=0.085, right=0.985, top=0.985, bottom=0.08)
save(fig, "yearly_c86.png")

# ---- 5. development, placebo and test with their ranges (trial log) ----------------------------------------
rows = [json.loads(l) for l in open("trial_log.jsonl")]
fin = [r for r in rows if r["kind"] == "final" and r["id"] == "c86"][-1]
plc = [r for r in rows if r["kind"] == "placebo" and r["id"] == "c86"][-1]
dm, tm = fin["dev_metrics"], fin["test_metrics"]
fig, ax = plt.subplots(figsize=(W, 3.6))
for y, mm in ((0, dm), (2, tm)):
    ax.plot([mm["boot_lo"], mm["boot_hi"]], [y, y], color=BLUE, lw=2.5, solid_capstyle="round", zorder=3)
    ax.scatter([mm["ratio"]], [y], s=120, color=BLUE, edgecolor="white", linewidth=2, zorder=5)
    ax.text(mm["ratio"], y - 0.3, f"{mm['ratio']:+.2f}", ha="center", fontsize=11, fontweight="bold", color=INK)
    ax.text(mm["boot_lo"] - 0.02, y, f"{mm['boot_lo']:+.2f}", ha="right", va="center", fontsize=9.5)
    ax.text(mm["boot_hi"] + 0.02, y, f"{mm['boot_hi']:+.2f}", ha="left", va="center", fontsize=9.5)
pv = np.array(list(plc["placebo"].values()))
ax.scatter(pv, np.full(len(pv), 1.0), s=46, facecolor="white", edgecolor=MUTE, linewidth=1.5, zorder=4)
ax.text(pv.max(), 0.7, f"highest {pv.max():+.2f}", ha="center", fontsize=9.5)
for y, v, lab in ((0, need, f"necessary {need:.2f}"), (2, 0.5, "pass limit 0.50")):
    ax.plot([v, v], [y - 0.22, y + 0.22], color=ORANGE, lw=2.5, zorder=4)
    ax.text(v, y + 0.42, lab, color=ORANGE, ha="center", fontsize=9.5, fontweight="bold")
ax.axvline(0, color=INK2, lw=1, zorder=1)
ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["Development\n2009-2022", "Placebo: 17 runs\nwith shifted data", "Test\n2023-Oct 2026"], fontsize=10.5)
ax.set_ylim(2.75, -0.6); ax.set_xlim(-0.85, 1.65)
ax.set_xlabel("Score (RATIO). Dot: result. Line: range from the block bootstrap.")
clean(ax, grid="x")
fig.subplots_adjust(left=0.17, right=0.985, top=0.985, bottom=0.16)
save(fig, "ranges.png")

# ---- 6. roll defect (made-up prices) ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(W, 2.3))
x_old, x_new = np.arange(0, 6), np.arange(5, 11)
old = 200 + np.array([0.0, 0.6, -0.3, 0.5, 0.2, 0.7]); new = old[-1] + 4.4 + np.array([-0.2, 0.0, 0.5, 0.1, 0.8, 0.6])
ax.plot(x_old, old, color=MUTE, lw=2, zorder=3); ax.plot(x_new[1:], new[1:], color=BLUE, lw=2, zorder=3)
ax.plot([5, 6], [old[-1], new[1]], color=ORANGE, lw=2, ls=(0, (3, 2)), zorder=3)
ax.scatter([5], [old[-1]], s=70, color=MUTE, edgecolor="white", linewidth=2, zorder=5)
ax.scatter([6], [new[1]], s=70, color=BLUE, edgecolor="white", linewidth=2, zorder=5)
ax.text(2.0, old[2] - 1.0, "old contract", color=INK2, fontsize=10, fontweight="bold", ha="center", va="top")
ax.text(8.6, new[4] + 0.9, "new contract", color=BLUE, fontsize=10, fontweight="bold", ha="center")
ax.annotate("marked day: last close\nof the old contract", xy=(5, old[-1]), xytext=(3.3, 204.3), fontsize=9.5, ha="center",
            arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.8))
ax.text(6.25, (old[-1] + new[1]) / 2 - 0.4, "the gap is in the return of the NEXT day\n(+1.1% on average)", color=ORANGE, fontsize=9.5, fontweight="bold", va="center")
ax.set_xticks([5, 6]); ax.set_xticklabels(["day t\n(marked)", "day t+1"], fontsize=9.5)
ax.set_yticks([]); ax.set_xlim(-0.3, 10.6); ax.set_ylim(197.6, 207.2)
ax.text(0.995, 0.03, "Made-up prices, for illustration", transform=ax.transAxes, ha="right", fontsize=8.5, color=MUTE)
clean(ax, grid=None)
fig.subplots_adjust(left=0.02, right=0.985, top=0.97, bottom=0.2)
save(fig, "roll_gap.png")
