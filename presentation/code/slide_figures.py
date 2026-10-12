"""Figures for the presentation slides (16:9 Beamer, UM Stats theme).
All values are read from the section outputs or recomputed from the cleaned data; output -> presentation/figures/*.pdf."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load
from paths import out

FIG = ROOT / "presentation" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
S1, S2, S3, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
INK, INK2, GRID, SURF, NAVY = "#0b0b0b", "#52514e", "#e6e5e1", "#ffffff", "#283755"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "bold",
                     "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GREY, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.linewidth": .6, "legend.frameon": False, "legend.fontsize": 7.2, "text.color": INK})

def grid(ax, axis="y"): ax.grid(axis=axis, color=GRID, lw=.6); ax.set_axisbelow(True)
def save(fig, name):
    fig.tight_layout(); fig.savefig(FIG / f"{name}.pdf", metadata={"CreationDate": None}); fig.savefig(FIG / f"{name}.png", dpi=200); plt.close(fig)

Q1, Q2, Q3, Q4 = out("q1"), out("q2"), out("q3"), out("q4")
df = load()

# ---------- Q1: what a simpler analysis would conclude ----------
e = pd.read_csv(Q1 / "q1_effects.csv").set_index("term")
fig, ax = plt.subplots(1, 2, figsize=(5.2, 2.2))
labs = ["Raw comparison", "Log-OLS, income linear", "Gamma, income linear", "Final: Gamma, income curve"]
for a, term, title in [(ax[0], "Kidhome", "Each young child"), (ax[1], "Education: Basic (vs Graduation)", "Basic education")]:
    v = [e.loc[term, c + "_pct"] for c in ["unadj", "logols", "gamma", "gspline"]]
    lo = [e.loc[term, c + "_lo"] for c in ["unadj", "logols", "gamma", "gspline"]]
    hi = [e.loc[term, c + "_hi"] for c in ["unadj", "logols", "gamma", "gspline"]]
    y = np.arange(4)[::-1]; cols = [GREY, GREY, GREY, S1]
    a.barh(y, v, color=cols, height=.6)
    a.errorbar(v, y, xerr=[np.array(v) - np.array(lo), np.array(hi) - np.array(v)], fmt="none", ecolor=INK2, elinewidth=.7, capsize=2)
    for yi, vi, l_ in zip(y, v, lo): a.text(min(l_, 0) - 3, yi, f"{vi:.0f}%", ha="right", va="center", fontsize=7, color=INK2)
    a.axvline(0, color=INK2, lw=.6); a.set_xlim(-115, 45); a.set_title(title); grid(a, "x")
    a.set_yticks(y); a.set_yticklabels(labs if a is ax[0] else [])
fig.supxlabel("Difference in mean spending (%), 95% CI", fontsize=7.5, color=INK2, y=0.02)
save(fig, "q1_simple_vs_final")

# ---------- Q1: Gamma vs ordinary regression ----------
df["logInc"] = np.log(df.Income); df["Age10"] = df.Age / 10
RHS = "bs(logInc, df=4) + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths"
o = smf.ols("np.log(TotalSpend) ~ " + RHS, df).fit(); st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
mod = smf.glm("TotalSpend ~ " + RHS, df, family=sm.families.Gamma(sm.families.links.Log()))
g = min([mod.fit(start_params=st.values, method="newton", maxiter=500), mod.fit()], key=lambda r: r.deviance)
mu, yv = g.fittedvalues.values, df.TotalSpend.values; cv = np.sqrt(g.scale)
sigma = smf.ols("TotalSpend ~ " + RHS, df).fit().resid.std()
emp = pd.DataFrame({"mu": mu, "y": yv, "b": pd.qcut(mu, 10, labels=False)}).groupby("b").agg(m=("mu", "mean"), my=("y", "mean"), sd=("y", "std"))
fig, ax = plt.subplots(1, 2, figsize=(5.0, 2.3), gridspec_kw={"width_ratios": [1.3, 1]})
a = ax[0]; xs = np.linspace(mu.min(), np.percentile(mu, 99.5), 200)
a.scatter(mu, yv, s=2, color="k", alpha=.15, lw=0)
a.fill_between(xs, xs * (1 - cv), xs * (1 + cv), color=S1, alpha=.22, lw=0, label="Gamma: spread grows")
a.plot(xs, xs - sigma, color=S2, ls="--", lw=1.1, label="Normal: same spread"); a.plot(xs, xs + sigma, color=S2, ls="--", lw=1.1)
a.plot(xs, xs, color=INK2, lw=.9)
a.axhspan(-700, 0, color=S2, alpha=.07); a.text(xs.max() * .97, -350, "negative spending", ha="right", fontsize=6.5, color=S2)
a.set(xlim=(0, xs.max()), ylim=(-700, 2800), xlabel="Predicted mean spend", ylabel="Actual spend", title="A  Two assumptions about the spread")
a.legend(loc="upper left", fontsize=6.5)
a = ax[1]; m = np.linspace(0, emp.my.max() * 1.05, 100)
a.plot(emp.my, emp.sd, "o", color=S3, ms=4, label="Actual (10 groups)", zorder=5)
a.plot(m, cv * m, color=S1, lw=1.6, label="Gamma"); a.axhline(sigma, color=S2, ls="--", lw=1.4, label="Normal")
a.set(xlabel="Mean spend in group", ylabel="SD of spend", ylim=(0, 1100), title="B  Spread vs mean"); a.legend(loc="upper left", fontsize=6.5); grid(a)
save(fig, "q1_gamma_vs_normal")

# ---------- Q1: income curve and its slope ----------
ic = pd.read_csv(Q1 / "q1c_income_curve_grid.csv"); k = ic.income / 1000
fig, ax = plt.subplots(1, 2, figsize=(5.0, 2.15))
a = ax[0]; a.fill_between(k, ic.mult_lo, ic.mult_hi, color=S1, alpha=.2, lw=0); a.plot(k, ic.multiplier, color=S1, lw=1.6)
a.axhline(1, color=GREY, ls="--", lw=.7)
for v in [20, 51.5, 65, 90]:
    yv_ = float(np.exp(np.interp(np.log(v * 1000), np.log(ic.income), np.log(ic.multiplier))))
    a.plot(v, yv_, "o", color=S1, ms=3); a.annotate(f"×{yv_:.2f}", (v, yv_), xytext=(-4, 5), textcoords="offset points", ha="right", fontsize=6.5, color=INK2)
a.set(xlabel="Income (thousands)", ylabel="× median-income spend", title="A  Fitted income curve"); grid(a, "both")
a = ax[1]; a.plot(k, ic.elasticity, color=S3, lw=1.6); a.axhline(1, color=GREY, ls="--", lw=.7)
a.set(xlabel="Income (thousands)", ylabel="% spend per 1% income", title="B  Its slope (elasticity)"); grid(a, "both")
save(fig, "q1_income_curve")

# ---------- Q1: Shapley shares ----------
sh = pd.read_csv(Q1 / "q1_shapley_gamma_deviance.csv", index_col=0)
sh = sh.sort_values("share_of_explained_deviance_pct")
names = {"Kidhome": "Young children", "Teenhome": "Teenagers"}
fig, a = plt.subplots(figsize=(2.6, 2.1))
y = np.arange(len(sh)); a.barh(y, sh.share_of_explained_deviance_pct, color=[S1 if i >= len(sh) - 2 else GREY for i in y], height=.6)
for yi, v in zip(y, sh.share_of_explained_deviance_pct): a.text(v + 1.5, yi, f"{v:.0f}%", va="center", fontsize=7, color=INK2)
a.set_yticks(y); a.set_yticklabels([names.get(i, i) for i in sh.index]); a.set_xlim(0, 85)
a.set_xlabel("Share of explained deviance (%)"); grid(a, "x")
save(fig, "q1_shapley")

# ---------- Q2: share of customers vs spending by style ----------
seg = pd.read_csv(Q2 / "q2_segment_profiles.csv", index_col=0)
fig, a = plt.subplots(figsize=(2.5, 2.1)); x = np.arange(3); w = .38
for i, (row, c, lab) in enumerate([("pct", S1, "Customers"), ("share_of_total_spend_pct", S2, "Spending")]):
    v = seg.loc[row, ["S1", "S2", "S3"]].astype(float).values
    b = a.bar(x + (i - .5) * w, v, w, color=c, label=lab)
    for bi in b: a.text(bi.get_x() + bi.get_width() / 2, bi.get_height() + 1.2, f"{bi.get_height():.0f}%", ha="center", fontsize=6.8, color=INK2)
a.set_xticks(x); a.set_xticklabels(["Value-\nseeking", "Wine-\nfocused", "Affluent\ncatalogue"], fontsize=7)
a.set_ylim(0, 75); a.set_ylabel("Share (%)"); a.legend(loc="upper left"); grid(a)
save(fig, "q2_styles_share")

# ---------- Q3: acceptance by earlier campaigns; adjusted effects; model comparison ----------
r = pd.read_csv(Q3 / "q3_rates.csv"); r = r[r.variable == "PrevAcc"]
fig, a = plt.subplots(figsize=(2.4, 2.1)); x = np.arange(len(r))
a.bar(x, 100 * r.rate, .6, color=S1)
a.errorbar(x, 100 * r.rate, yerr=[100 * (r.rate - r.lo), 100 * (r.hi - r.rate)], fmt="none", ecolor=INK2, elinewidth=.7, capsize=2)
for xi, v, hi in zip(x, 100 * r.rate, 100 * r.hi): a.text(xi, hi + 2, f"{v:.0f}%", ha="center", fontsize=7, color=INK2)
a.axhline(15.3, color=GREY, ls="--", lw=.7); a.set_xticks(x); a.set_xticklabels(r.level); a.set_ylim(0, 100)
a.set(xlabel="Earlier campaigns accepted", ylabel="Accepted last campaign (%)"); grid(a)
save(fig, "q3_prev")

t = pd.read_csv(Q3 / "q3_logit_explanatory.csv", index_col=0); t = t[t.model == "A"]
lab = {"PrevAccepted": "Each earlier campaign accepted", "C(Marital)[T.Single]": "Single", "C(Edu, Treatment('Graduation'))[T.PhD]": "PhD",
       "C(Edu, Treatment('Graduation'))[T.Master]": "Master", "TenureMonths": "Each month of tenure", "Kidhome": "Each young child*",
       "Teenhome": "Each teenager", "logSpend": "Spending (log)", "logInc": "Income (log)", "Age10": "Age (+10 yrs)"}
t = t.loc[list(lab)][::-1]
fig, a = plt.subplots(figsize=(3.2, 2.3)); y = np.arange(len(t))
a.errorbar(t.AME_pp, y, xerr=[t.AME_pp - t.AME_lo, t.AME_hi - t.AME_pp], fmt="o", color=S1, ms=3.5, elinewidth=.8, capsize=2)
a.axvline(0, color=INK2, lw=.6); a.set_yticks(y); a.set_yticklabels([lab[i] for i in t.index], fontsize=7)
a.set_xlabel("Change (percentage points)", fontsize=7); grid(a, "x")
save(fig, "q3_ame")

p = pd.read_csv(Q3 / "q3_model_performance.csv")
pick = [("T0 (demographics/tenure)", "logit_L2", "Demographics only"), ("Explanatory logit A (11 terms)", "logit (unpenalised)", "Our model (11 terms)"),
        ("Scenario A (T0+T1 w/o Recency+T2)", "logit_L2", "26 fields, logistic"), ("Scenario A (T0+T1 w/o Recency+T2)", "grad_boost", "26 fields, boosting")]
vals = [p[(p.features == f) & (p.model == m)].AUC_mean.iloc[0] for f, m, _ in pick]
fig, a = plt.subplots(figsize=(3.0, 2.0)); y = np.arange(len(pick))[::-1]
a.barh(y, vals, color=[GREY, S1, GREY, GREY], height=.6)
for yi, v in zip(y, vals): a.text(v + .004, yi, f"{v:.3f}", va="center", fontsize=7, color=INK2)
a.set_yticks(y); a.set_yticklabels([l for _, _, l in pick], fontsize=7); a.set_xlim(.7, .9)
a.set_xlabel("AUC on unseen customers"); grid(a, "x")
save(fig, "q3_models")

# ---------- Q4: 3x3 matrix, profiles, gains ----------
mx = pd.read_csv(Q4 / "q4_priority_matrix.csv")
order = ["Low", "Mid", "High"]
acc = mx.pivot(index="PropTier", columns="SpendTierAdj", values="resp_rate").loc[order[::-1], order] * 100
pc = mx.pivot(index="PropTier", columns="SpendTierAdj", values="pct_customers").loc[order[::-1], order]
fig, a = plt.subplots(figsize=(2.8, 2.3))
a.imshow(acc.values, cmap="Blues", vmin=0, vmax=55)
for i in range(3):
    for j in range(3):
        col_ = "white" if acc.values[i, j] > 30 else INK
        a.text(j, i - .08, f"{acc.values[i, j]:.0f}%", ha="center", va="center", fontsize=8.5, fontweight="bold", color=col_)
        a.text(j, i + .25, f"{pc.values[i, j]:.0f}% of cust.", ha="center", va="center", fontsize=5.6, color=col_)
a.set_xticks(range(3)); a.set_xticklabels(order); a.set_yticks(range(3)); a.set_yticklabels(order[::-1])
a.set_xlabel("Value (spend vs same-cohort customers)"); a.set_ylabel("Response (Q3 score)")
for s in a.spines.values(): s.set_visible(False)
save(fig, "q4_matrix")

pr = pd.read_csv(Q4 / "q4_profiles.csv")
fig, a = plt.subplots(figsize=(3.2, 2.2)); x = np.arange(4); w = .27
for i, (col, c, l) in enumerate([("pct_customers", S1, "Customers"), ("pct_of_acceptors", S2, "Acceptors"), ("pct_of_total_spend", S3, "Spending")]):
    b = a.bar(x + (i - 1) * w, pr[col], w, color=c, label=l)
    for bi in b: a.text(bi.get_x() + bi.get_width() / 2, bi.get_height() + 1, f"{bi.get_height():.0f}", ha="center", fontsize=6.3, color=INK2)
a.set_xticks(x); a.set_xticklabels(["P1\nEngaged", "P2\nResponsive", "P3\nHigh value", "P4\nLow prio."], fontsize=6.5)
a.set_ylim(0, 72); a.set_yticks([0, 20, 40, 60]); a.set_ylabel("Share of total (%)"); a.legend(loc="upper center", ncol=3, fontsize=6.5, bbox_to_anchor=(.5, 1.04)); grid(a)
save(fig, "q4_profiles")

oo = pd.read_csv(Q3 / "q3_oof_predictions.csv"); yy = oo.Response.values; s_ = np.argsort(-oo.p_Q4.values)
cum = 100 * np.cumsum(yy[s_]) / yy.sum(); xx = 100 * np.arange(1, len(yy) + 1) / len(yy)
fig, a = plt.subplots(figsize=(2.4, 2.1))
a.plot(xx, cum, color=S1, lw=1.6, label="Ranked by score"); a.plot([0, 100], [0, 100], color=GREY, ls="--", lw=.8, label="Random")
i20 = int(round(.2 * len(yy))) - 1; a.plot(20, cum[i20], "o", color=S1, ms=4)
a.annotate(f"Top 20%:\n{cum[i20]:.0f}% of acceptors", (20, cum[i20]), xytext=(56, 40), textcoords="data", fontsize=6.8, color=INK2, va="center",
           arrowprops=dict(arrowstyle="-", color=GREY, lw=.6))
a.set(xlim=(0, 100), ylim=(0, 102), xlabel="Contacted (%)", ylabel="Acceptors reached (%)"); a.legend(loc="lower right", fontsize=6.3); grid(a, "both")
save(fig, "q4_gains")

# ---------- appendix: why not monthly spend ----------
d = df.copy(); d["monthly"] = d.TotalSpend / d.TenureMonths.clip(lower=0.25)
d["band"] = pd.cut(d.TenureMonths, [0, 1, 3, 6, 12, 18, 24.5], include_lowest=True, labels=["≤1", "1–3", "3–6", "6–12", "12–18", "18–24"])
gg = d.groupby("band", observed=True).agg(total=("TotalSpend", "median"), monthly=("monthly", "median"))
fig, ax = plt.subplots(1, 2, figsize=(4.8, 1.9))
ax[0].bar(gg.index.astype(str), gg.total, color=S1); ax[0].set(title="A  Median total spend", xlabel="Tenure (months)"); grid(ax[0])
ax[1].bar(gg.index.astype(str), gg.monthly, color=S2); ax[1].set(title="B  Median spend per month", xlabel="Tenure (months)"); grid(ax[1])
for a in ax: a.tick_params(axis="x", labelsize=6.5)
save(fig, "appx_monthly_spend")
print("saved slide figures to", FIG)
