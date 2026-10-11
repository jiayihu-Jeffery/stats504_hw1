"""Compact figures for the two-page summary (print, light mode).
Palette: reference categorical slots 1-3 (blue, orange, aqua; validated all-pairs in light mode).
All plotted values are read from output/ files (or computed here and saved to output/summary_fig_*.csv)."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load
from paths import out, fig
OUT = out("report"); FIG = fig("report")

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#ffffff"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.2, "axes.titlesize": 7.8, "axes.titleweight": "bold",
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": .6,
                     "xtick.major.width": .6, "ytick.major.width": .6, "legend.frameon": False, "legend.fontsize": 6.8,
                     "axes.titlelocation": "left", "axes.titlepad": 5, "text.color": INK})

def grid(ax, axis="y"):
    ax.grid(axis=axis, color=GRID, lw=.6); ax.set_axisbelow(True)

def label_bars(ax, bars, fmt, dy=1.0, inside=False):
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v + dy, fmt.format(v), ha="center", va="bottom", fontsize=6.3, color=INK2)

df = load(); N = len(df)

# ======================= Figure 1: spending & shopping styles =======================
fig, ax = plt.subplots(1, 3, figsize=(7.3, 2.15), gridspec_kw={"width_ratios": [1, 1.2, 1.15]})

# A: relative importance (Shapley R2 share)
sh = pd.read_csv(out("q1") / "q1_shapley_r2.csv", index_col=0)["share_of_R2_pct"].sort_values()
names = {"Kidhome": "Young children", "Teenhome": "Teenagers", "Tenure": "Tenure"}
y = np.arange(len(sh)); b = ax[0].barh(y, sh.values, height=.62, color=S1, edgecolor=SURF, lw=1)
ax[0].set_yticks(y); ax[0].set_yticklabels([names.get(i, i) for i in sh.index])
for yi, v in zip(y, sh.values):
    ax[0].text(v + 1.5, yi, f"{v:.0f}%", va="center", fontsize=6.3, color=INK2)
ax[0].set_xlim(0, 72); ax[0].set_xlabel("Share of explained variation in spending (%)")
ax[0].set_title("A  What explains spending"); grid(ax[0], "x")

# B: median spend by income quartile x young children
df["Kids"] = np.where(df.Kidhome > 0, "1+ young children", "No young children")
med = df.groupby(["IncomeQ", "Kids"], observed=True).TotalSpend.median().unstack()[["No young children", "1+ young children"]]
cnt = df.groupby(["IncomeQ", "Kids"], observed=True).size().unstack()[["No young children", "1+ young children"]]
pd.concat({"median_spend": med, "n": cnt}, axis=1).to_csv(OUT / "summary_fig_spend_by_income_kids.csv")
x = np.arange(4); w = .38
for i, (col, c) in enumerate([("No young children", S1), ("1+ young children", S2)]):
    bars = ax[1].bar(x + (i - .5) * w, med[col].values, w, color=c, edgecolor=SURF, lw=1, label=col)
    label_bars(ax[1], bars, "{:.0f}", dy=25)
ax[1].set_xticks(x); ax[1].set_xticklabels(["Q1\nlowest", "Q2", "Q3", "Q4\nhighest"])
ax[1].set_xlabel("Income quartile"); ax[1].set_ylabel("Median 2-year spend")
ax[1].set_ylim(0, med.values.max() * 1.22); ax[1].legend(loc="upper left", handlelength=1, borderaxespad=0)
ax[1].set_title("B  Spend by income & young kids"); grid(ax[1])

# C: shopping styles - share of customers vs share of spending
seg = pd.read_csv(out("q2") / "q2_segment_profiles.csv", index_col=0)
labs = {"S1": "Value-\nseeking", "S2": "Wine-\nfocused", "S3": "Affluent\ncatalog"}
x = np.arange(3)
for i, (row, c, lab) in enumerate([("pct", S1, "Share of customers"), ("share_of_total_spend_pct", S2, "Share of spending")]):
    v = seg.loc[row, ["S1", "S2", "S3"]].astype(float).values
    bars = ax[2].bar(x + (i - .5) * w, v, w, color=c, edgecolor=SURF, lw=1, label=lab)
    label_bars(ax[2], bars, "{:.0f}%", dy=1.2)
ax[2].set_xticks(x); ax[2].set_xticklabels([labs[s] for s in ["S1", "S2", "S3"]])
ax[2].set_ylabel("%"); ax[2].set_ylim(0, 75); ax[2].legend(loc="upper left", handlelength=1, borderaxespad=0)
ax[2].set_title("C  Shopping styles"); grid(ax[2])
plt.tight_layout(w_pad=1.2); plt.savefig(FIG / "summary_fig1.png", dpi=220); plt.close()

# ======================= Figure 2: response & priorities =======================
fig, ax = plt.subplots(1, 3, figsize=(7.3, 2.3), gridspec_kw={"width_ratios": [0.9, 1.45, 1.05]})

# A: acceptance by earlier campaigns accepted (Wilson CI)
r = pd.read_csv(out("q3") / "q3_rates.csv"); r = r[r.variable == "PrevAcc"]
x = np.arange(len(r))
bars = ax[0].bar(x, 100 * r.rate, .6, color=S1, edgecolor=SURF, lw=1)
ax[0].errorbar(x, 100 * r.rate, yerr=[100 * (r.rate - r.lo), 100 * (r.hi - r.rate)], fmt="none", ecolor=INK2, elinewidth=.7, capsize=2)
for xi, v, hi, n_ in zip(x, 100 * r.rate, 100 * r.hi, r.n):
    ax[0].text(xi, hi + 2, f"{v:.0f}%", ha="center", fontsize=6.3, color=INK2)
ax[0].axhline(100 * df.Response.mean(), color=MUTED, lw=.7, ls="--")
ax[0].set_xticks(x); ax[0].set_xticklabels(r.level); ax[0].set_ylim(0, 100)
ax[0].set_xlabel("Earlier campaigns accepted"); ax[0].set_ylabel("Accepted last campaign (%)")
ax[0].set_title("A  Past response"); grid(ax[0])

# B: profiles - customers / acceptors / spending
p = pd.read_csv(out("q4") / "q4_profiles.csv", index_col=0)
order = ["P1 Engaged high-value", "P2 Responsive, lower-spend", "P3 High-value, low-propensity", "P4 Low priority for campaigns"]
plab = ["P1\nEngaged", "P2\nResponsive", "P3\nHigh value", "P4\nLow priority"]
x = np.arange(4); w = .27
for i, (col, c, lab) in enumerate([("pct_customers", S1, "Customers"), ("pct_of_acceptors", S2, "Acceptors"),
                                   ("pct_of_total_spend", S3, "Spending")]):
    v = p.loc[order, col].astype(float).values
    bars = ax[1].bar(x + (i - 1) * w, v, w, color=c, edgecolor=SURF, lw=1, label=lab)
    label_bars(ax[1], bars, "{:.0f}", dy=1.0)
ax[1].set_xticks(x); ax[1].set_xticklabels(plab, fontsize=6.0); ax[1].set_ylabel("Share of total (%)"); ax[1].set_ylim(0, 62)
ax[1].legend(loc="upper center", handlelength=1, borderaxespad=0, ncol=3, fontsize=6.2, columnspacing=.8)
ax[1].set_title("B  Priority profiles"); grid(ax[1])

# C: gains curve (out-of-fold) + scorecard point
o = pd.read_csv(out("q3") / "q3_oof_predictions.csv"); yv = o.Response.values
for col, c, lab in [("p_Q4", S1, "Full model"), ("p_T0_logit_L2", S2, "Demographics only")]:
    s = np.argsort(-o[col].values); cum = 100 * np.cumsum(yv[s]) / yv.sum()
    ax[2].plot(100 * np.arange(1, len(yv) + 1) / len(yv), cum, color=c, lw=1.6, label=lab)
ax[2].plot([0, 100], [0, 100], color=MUTED, lw=.8, ls="--", label="Random")
sc = pd.read_csv(out("q4") / "q4b_scorecard_performance.csv").iloc[0]
ax[2].scatter([20], [sc.cv_top20_capture_pct], s=26, color=S3, edgecolor=SURF, lw=1.2, zorder=5, label="6-question scorecard")
ax[2].axvline(20, color=GRID, lw=.8, zorder=0)
bud = pd.read_csv(out("q4") / "q4_budget_table.csv"); top20 = bud[(bud.score.str.startswith("Scenario A")) & (bud.contact_pct == 20)].iloc[0]
ax[2].annotate(f"Top 20% contacted:\nmodel {top20.pct_acceptors_captured:.0f}%\nscorecard {sc.cv_top20_capture_pct:.0f}%", xy=(20, top20.pct_acceptors_captured), xytext=(46, 52),
               fontsize=6.2, color=INK2, va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=.6),
               bbox=dict(boxstyle="round,pad=0.25", fc=SURF, ec=GRID, lw=.6))
ax[2].set_xlim(0, 100); ax[2].set_ylim(0, 102)
ax[2].set_xlabel("Contacted, ranked by score (%)"); ax[2].set_ylabel("Acceptors reached (%)")
ax[2].legend(loc="lower right", handlelength=1.3, borderaxespad=0.2, fontsize=6.0, labelspacing=.3)
ax[2].set_title("C  Targeting vs random"); grid(ax[2], "both")
plt.tight_layout(w_pad=1.2); plt.savefig(FIG / "summary_fig2.png", dpi=220); plt.close()
print("saved summary_fig1.png, summary_fig2.png")
