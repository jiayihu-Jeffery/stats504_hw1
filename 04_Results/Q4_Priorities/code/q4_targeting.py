"""Q4: prioritisation — spend tier x out-of-fold response propensity (Scenario A), budget table, conditional profit."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load, SEED, MNT, CHAN
from paths import out, fig
OUT = out("q4"); FIG = fig("q4")
pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)

df = load(); N = len(df)
df = df.merge(pd.read_csv(out("q3") / "q3_oof_predictions.csv").drop(columns="Response"), on="ID")
df = df.merge(pd.read_csv(out("q2") / "q2_segment_assignments.csv"), on="ID", how="left")
df["Segment"] = df.Segment.fillna("unassigned")
y = df.Response.values; base = y.mean()
df["PropTier"] = pd.qcut(df.p_Q4, 3, labels=["Low", "Mid", "High"])
PROD = dict(zip(MNT, ["Wine", "Fruit", "Meat", "Fish", "Sweets", "Gold"]))
CHN = dict(zip(CHAN, ["Web", "Catalog", "Store"]))
rep = [f"Q4 — n = {N}; propensity score = out-of-fold Scenario A logistic (q3_oof_predictions.csv: p_Q4)"]

def cell_summary(g):
    lo, hi = proportion_confint(g.Response.sum(), len(g), method="wilson")
    sh = (g[MNT].div(g.TotalSpend, axis=0)).mean().sort_values(ascending=False)
    ch = (g[CHAN].div(g.TotalPurch.replace(0, np.nan), axis=0)).mean()
    seg = g.Segment.value_counts(normalize=True)
    return pd.Series(dict(n=len(g), pct_customers=100 * len(g) / N, mean_spend=g.TotalSpend.mean(),
                          pct_of_total_spend=100 * g.TotalSpend.sum() / df.TotalSpend.sum(),
                          resp_rate=g.Response.mean(), resp_lo=lo, resp_hi=hi,
                          pct_of_acceptors=100 * g.Response.sum() / y.sum(), mean_pred=g.p_Q4.mean(),
                          dominant_segment=f"{seg.index[0]} ({100 * seg.iloc[0]:.0f}%)",
                          top_products=f"{PROD[sh.index[0]]} {100 * sh.iloc[0]:.0f}%, {PROD[sh.index[1]]} {100 * sh.iloc[1]:.0f}%",
                          channel_mix=" / ".join(f"{CHN[c]} {100 * ch[c]:.0f}%" for c in CHAN),
                          mean_income=g.Income.mean(), mean_kidhome=g.Kidhome.mean(), mean_teenhome=g.Teenhome.mean(),
                          pct_single=100 * (g.Marital == "Single").mean(), mean_prev_accepted=g.PrevAccepted.mean(),
                          mean_tenure_m=g.TenureMonths.mean(), pct_joined_last_6m=100 * (g.TenureMonths <= 6).mean(), deal_ratio=(g.NumDealsPurchases / g.TotalPurch.replace(0, np.nan)).clip(upper=1).mean(),
                          web_visits=g.NumWebVisitsMonth.mean()))

VALUE = "SpendTierAdj"   # primary value measure: spend tier relative to customers who joined in the same 6-month window
rep += ["Value tier = spend tertile WITHIN 6-month tenure band (tenure-adjusted); unadjusted version reported as sensitivity"]
mat = df.groupby([VALUE, "PropTier"], observed=True).apply(cell_summary)
mat.to_csv(OUT / "q4_priority_matrix.csv")
num = ["n", "pct_customers", "mean_spend", "pct_of_total_spend", "resp_rate", "resp_lo", "resp_hi", "pct_of_acceptors",
       "mean_income", "mean_kidhome", "mean_teenhome", "pct_single", "mean_prev_accepted", "mean_tenure_m", "pct_joined_last_6m", "deal_ratio", "web_visits"]
mat_print = mat.copy(); mat_print[num] = mat_print[num].astype(float).round(3)
rep += ["\n[1] Priority matrix: tenure-adjusted spend tier x propensity tier (tertiles)", mat_print.T.to_string()]

# heatmap
fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
for a, col, ttl, fmt in [(ax[0], "resp_rate", "Observed acceptance rate", "{:.0%}"), (ax[1], "pct_of_total_spend", "Share of all spend (%)", "{:.0f}")]:
    M = mat[col].astype(float).unstack().loc[["High", "Mid", "Low"], ["Low", "Mid", "High"]]
    nM = mat["n"].astype(float).unstack().loc[["High", "Mid", "Low"], ["Low", "Mid", "High"]]
    im = a.imshow(M.values, cmap="Blues"); plt.colorbar(im, ax=a)
    a.set_xticks(range(3)); a.set_xticklabels(M.columns); a.set_yticks(range(3)); a.set_yticklabels(M.index)
    a.set(xlabel="Predicted response propensity tier (out-of-fold)", ylabel="Spend tier vs same-tenure customers", title=ttl)
    for i in range(3):
        for j in range(3):
            a.text(j, i, fmt.format(M.values[i, j]) + f"\nn={int(nM.values[i, j])}", ha="center", va="center",
                   color="white" if M.values[i, j] > np.nanmax(M.values) * .6 else "black", fontsize=9)
fig.suptitle(f"Priority matrix (n = {N}; tenure-adjusted spend tertiles x Scenario A score tertiles)")
plt.tight_layout(); plt.savefig(FIG / "q4_priority_matrix.png", dpi=140); plt.close()

# ---------- profiles (cells merged after inspecting the matrix) ----------
def profile(r, value=VALUE):
    if r.PropTier == "High" and r[value] == "High": return "P1 Engaged high-value"
    if r.PropTier == "High": return "P2 Responsive, lower-spend"
    if r[value] == "High": return "P3 High-value, low-propensity"
    return "P4 Low priority for campaigns"
df["Profile"] = df.apply(profile, axis=1)
df["Profile_unadj"] = df.apply(lambda r: profile(r, "SpendTier"), axis=1)
pro_u = df.groupby("Profile_unadj").apply(cell_summary); pro_u.to_csv(OUT / "q4_profiles_unadjusted.csv")
xt = pd.crosstab(df.Profile_unadj, df.Profile, margins=True); xt.to_csv(OUT / "q4_profile_change.csv")
p4u = df[df.Profile_unadj.str.startswith("P4")]
rep += ["\n[1c] Unadjusted (raw 2-yr spend) vs tenure-adjusted profile membership (rows = unadjusted)", xt.to_string(),
        f"Customers in unadjusted P4 who move to P3 under tenure adjustment: {((df.Profile_unadj.str.startswith('P4')) & (df.Profile.str.startswith('P3'))).sum()}; "
        f"their mean tenure = {df.loc[(df.Profile_unadj.str.startswith('P4')) & (df.Profile.str.startswith('P3')), 'TenureMonths'].mean():.1f} months",
        "Unadjusted profiles (sensitivity):", pro_u[["n", "pct_customers", "resp_rate", "pct_of_acceptors", "pct_of_total_spend", "mean_tenure_m"]].astype(float).round(3).to_string()]
pro = df.groupby("Profile").apply(cell_summary)
pro_print = pro.copy(); pro_print[num] = pro_print[num].astype(float).round(3)
pro.to_csv(OUT / "q4_profiles.csv")
rep += ["\n[1b] Profiles (tenure-adjusted value) = merged matrix cells: P1 = High spend x High propensity; P2 = Low/Mid spend x High propensity; "
        "P3 = High spend x Low/Mid propensity; P4 = Low/Mid spend x Low/Mid propensity", pro_print.T.to_string()]

# ---------- budget table ----------
rng = np.random.default_rng(SEED)
def budget(p, label):
    rows = []
    order = np.argsort(-p)
    for frac in [.1, .2, .3, .5, 1.0]:
        k = int(round(frac * N)); idx = order[:k]
        bs_cap, bs_rate = [], []
        for _ in range(1000):
            ix = rng.integers(0, N, N); pp, yy = p[ix], y[ix]
            o = np.argsort(-pp)[:k]; bs_cap.append(yy[o].sum() / yy.sum()); bs_rate.append(yy[o].mean())
        rows.append(dict(score=label, contact_pct=int(100 * frac), contacted=k, acceptors=int(y[idx].sum()),
                         pct_acceptors_captured=100 * y[idx].sum() / y.sum(),
                         cap_lo=100 * np.percentile(bs_cap, 2.5), cap_hi=100 * np.percentile(bs_cap, 97.5),
                         response_rate=y[idx].mean(), rate_lo=np.percentile(bs_rate, 2.5), rate_hi=np.percentile(bs_rate, 97.5),
                         lift_vs_all=y[idx].mean() / base))
    return rows
bud = pd.DataFrame(budget(df.p_Q4.values, "Scenario A (primary)") + budget(df.p_T0_logit_L2.values, "T0 only (new customers)")
                   + budget(df.p_B_logit_L2.values, "Scenario B (needs client confirmation)"))
bud.to_csv(OUT / "q4_budget_table.csv", index=False)
rep += [f"\n[2] Budget table (contact top x% by out-of-fold score; overall rate {base:.3f}; 95% bootstrap CIs)",
        bud.round(3).to_string(index=False)]

# ---------- conditional profit curve ----------
# ASSUMPTION (unconfirmed): Z_CostContact = 3 = cost per contact; Z_Revenue = 11 = revenue per acceptance.
COST, REV = 3, 11
fr = np.arange(1, N + 1) / N
fig, a = plt.subplots(figsize=(7.5, 4.6))
prof_rows = []
for col, lab in [("p_Q4", "Scenario A score"), ("p_T0_logit_L2", "T0-only score")]:
    o = np.argsort(-df[col].values); cumacc = np.cumsum(y[o]); profit = REV * cumacc - COST * np.arange(1, N + 1)
    a.plot(100 * fr, profit, label=lab)
    k = profit.argmax(); prof_rows.append(dict(score=lab, best_contact_pct=100 * fr[k], best_profit=profit[k],
                                               rate_at_best=cumacc[k] / (k + 1), profit_contact_all=profit[-1]))
a.axhline(0, c="k", lw=.8); a.set(xlabel="% of customers contacted (ranked by score)", ylabel="Profit (units of Z_Revenue/Z_CostContact)",
                                  title=f"CONDITIONAL profit curve: assumes cost {COST}/contact, revenue {REV}/acceptance (n = {N})")
a.title.set_fontsize(9); a.legend(); plt.tight_layout(); plt.savefig(FIG / "q4_profit_curve_conditional.png", dpi=140); plt.close()
prof = pd.DataFrame(prof_rows); prof.to_csv(OUT / "q4_profit_conditional.csv", index=False)
rep += [f"\n[3] CONDITIONAL profit (assumes cost {COST}/contact, revenue {REV}/acceptance; break-even rate = {COST / REV:.3f}). "
        "In-sample out-of-fold scores; not validated on a future campaign.", prof.round(3).to_string(index=False)]

df[["ID", "SpendTier", "SpendTierAdj", "PropTier", "Profile", "Profile_unadj", "p_Q4", "Segment"]].to_csv(OUT / "q4_customer_tiers.csv", index=False)
txt = "\n".join(rep); print(txt); (OUT / "q4_results.txt").write_text(txt + "\n")
