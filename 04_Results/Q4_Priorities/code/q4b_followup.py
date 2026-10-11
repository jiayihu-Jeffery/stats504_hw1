"""Follow-up analyses requested in client review:
 (1) executable targeting rules + Excel scorecards (cross-validated)
 (2) new customers (joined in the last 6 months)
 (3) P3 vs P1 deep dive, incl. acceptance of each earlier campaign
 (4) relative product preference index by profile
(The complaints / web-visit / segment product-index analyses live in 04_Results/Q2_Patterns/code/q2b_*.py.)
"""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint
from scipy.stats import fisher_exact, spearmanr, mannwhitneyu
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier, export_text
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load, SEED, MNT, CHAN, PREV
from paths import out, fig
OUT = out("q4"); FIG = fig("q4")
pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)

df = load(); N = len(df)
df = df.merge(pd.read_csv(OUT / "q4_customer_tiers.csv")[["ID", "Profile", "PropTier"]], on="ID")
df = df.merge(pd.read_csv(out("q3") / "q3_oof_predictions.csv")[["ID", "p_Q4", "p_T0_logit_L2"]], on="ID")
df = df.merge(pd.read_csv(out("q2") / "q2_segment_assignments.csv"), on="ID", how="left")
y = df.Response.values; base = y.mean(); TOT = y.sum()
rep = [f"Q4b follow-up — n = {N}, acceptors = {TOT}"]

def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson"); return lo, hi

# ======================= (1) scorecards =======================
from scorecard import cats, CARDS, fit_card, score, capture
C = cats(df)

rng = np.random.default_rng(SEED)
card_rows, card_tables = [], {}
for cname, vars_ in CARDS.items():
    aucs, caps = [], []
    for tr, te in RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED).split(C, y):
        pts = fit_card(C.iloc[tr], y[tr], vars_)
        s = score(C.iloc[te], pts, vars_).values
        aucs.append(roc_auc_score(y[te], s)); caps.append(capture(y[te], s, .2, rng)[0])
    pts = fit_card(C, y, vars_)
    tab = pd.DataFrame([dict(item=v, answer=l, points=p) for (v, l), p in pts.items()])
    card_tables[cname] = tab
    s_full = score(C, pts, vars_)
    df["score_" + cname.split()[1]] = s_full
    card_rows.append(dict(scorecard=cname, items=len(vars_), cv_AUC_mean=np.mean(aucs), cv_AUC_sd=np.std(aucs),
                          cv_top20_capture_pct=100 * np.mean(caps), max_points=int(tab.groupby("item").points.max().sum())))
cr = pd.DataFrame(card_rows); cr.to_csv(OUT / "q4b_scorecard_performance.csv", index=False)
pd.concat([t.assign(scorecard=k) for k, t in card_tables.items()]).to_csv(OUT / "q4b_scorecards.csv", index=False)
rep += ["\n[1a] Scorecards: integer points = round(10 x logistic coefficient), lowest answer = 0 points. "
        "Performance from 5x5 repeated CV (points re-derived in each training fold).", cr.round(3).to_string(index=False)]
for k, t in card_tables.items():
    rep += [f"\n{k}", t.to_string(index=False)]

# score bands -> observed acceptance (full-data points; descriptive calibration table for Excel use)
band_rows = []
for col, cname in [("score_A", "Scorecard A"), ("score_N", "Scorecard N")]:
    q = df[col]
    cuts = np.unique(np.quantile(q, [0, .5, .7, .8, .9, 1]))
    df[col + "_band"] = pd.cut(q, cuts, include_lowest=True)
    for b, g in df.groupby(col + "_band", observed=True):
        lo, hi = wilson(g.Response.sum(), len(g))
        band_rows.append(dict(scorecard=cname, points=str(b), n=len(g), pct_customers=100 * len(g) / N,
                              acceptance=g.Response.mean(), lo=lo, hi=hi, pct_of_acceptors=100 * g.Response.sum() / TOT))
bands = pd.DataFrame(band_rows); bands.to_csv(OUT / "q4b_scorecard_bands.csv", index=False)
rep += ["\n[1b] Observed acceptance by scorecard points band (full data)", bands.round(3).to_string(index=False)]

# ======================= (1c) simple rules =======================
RULES = {
    "R1 Accepted any earlier campaign": df.PrevAccepted >= 1,
    "R2 R1 OR (no teenagers AND joined 12+ months ago)": (df.PrevAccepted >= 1) | ((df.Teenhome == 0) & (df.TenureMonths >= 12)),
    "R3 R1 OR (no teenagers AND single)": (df.PrevAccepted >= 1) | ((df.Teenhome == 0) & (df.Marital == "Single")),
    "R4 R1 OR (top-third spend AND no teenagers)": (df.PrevAccepted >= 1) | ((df.SpendTier == "High") & (df.Teenhome == 0)),
}
rule_rows = []
ordA = np.argsort(-df.p_Q4.values)
for rname, m in RULES.items():
    m = m.values; k = m.sum(); lo, hi = wilson(y[m].sum(), k)
    capA = y[ordA[:k]].sum() / TOT
    rule_rows.append(dict(rule=rname, flagged=k, pct_customers=100 * k / N, acceptance=y[m].mean(), lo=lo, hi=hi,
                          pct_acceptors_captured=100 * y[m].sum() / TOT,
                          model_A_capture_same_volume_pct=100 * capA))
rules = pd.DataFrame(rule_rows); rules.to_csv(OUT / "q4b_rules.csv", index=False)
rep += ["\n[1c] Simple rules (pre-specified from Q3 findings on the SAME data -> some optimism). "
        "Compared with contacting the same number of customers ranked by the Scenario A model score.",
        rules.round(3).to_string(index=False)]

# data-driven rule cross-check: depth-3 tree, cross-validated
Xt = pd.DataFrame({"PrevAccepted": df.PrevAccepted, "TenureMonths": df.TenureMonths, "Teenhome": df.Teenhome,
                   "Kidhome": df.Kidhome, "Single": (df.Marital == "Single").astype(int), "PhD": (df.Edu == "PhD").astype(int),
                   "TotalSpend": df.TotalSpend, "Income": df.Income})
tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=50, random_state=SEED)
pt = cross_val_predict(tree, Xt, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED), method="predict_proba")[:, 1]
tree.fit(Xt, y)
rep += [f"\n[1d] Cross-check: depth-3 decision tree (min leaf 50), 5-fold CV AUC = {roc_auc_score(y, pt):.3f}",
        export_text(tree, feature_names=list(Xt.columns), show_weights=True)]

# ======================= (2) new customers =======================
new = df.TenureMonths <= 6
rows = []
for lab, m in [("joined in last 6 months", new), ("joined 6+ months ago", ~new)]:
    g = df[m]; lo, hi = wilson(g.Response.sum(), len(g))
    rows.append(dict(group=lab, n=len(g), pct=100 * len(g) / N, acceptance=g.Response.mean(), lo=lo, hi=hi,
                     mean_spend=g.TotalSpend.mean(), median_spend=g.TotalSpend.median(), mean_prev_accepted=g.PrevAccepted.mean(),
                     pct_any_prev=100 * (g.PrevAccepted > 0).mean(), mean_income=g.Income.mean(),
                     pct_high_adj_value=100 * (g.SpendTierAdj == "High").mean(),
                     pct_in_P1=100 * g.Profile.str.startswith("P1").mean(), pct_in_P2=100 * g.Profile.str.startswith("P2").mean(),
                     pct_in_P3=100 * g.Profile.str.startswith("P3").mean(), pct_in_P4=100 * g.Profile.str.startswith("P4").mean()))
nc = pd.DataFrame(rows)
g = df[new]
within = []
for col, lab in [("p_Q4", "Scenario A model"), ("p_T0_logit_L2", "T0 model"), ("score_A", "Scorecard A"), ("score_N", "Scorecard N")]:
    within.append(dict(score=lab, AUC_within_new=roc_auc_score(g.Response, g[col]),
                       top20pct_of_new_capture=100 * capture(g.Response.values, g[col].values, .2, rng)[0],
                       top20pct_of_new_rate=capture(g.Response.values, g[col].values, .2, rng)[1]))
within = pd.DataFrame(within)
nc.to_csv(OUT / "q4b_new_customers.csv", index=False); within.to_csv(OUT / "q4b_new_customers_scores.csv", index=False)
rep += ["\n[2] New customers (TenureMonths <= 6)", nc.round(3).T.to_string(),
        "Ranking quality WITHIN new customers (out-of-fold model scores; scorecards use full-data points)", within.round(3).to_string(index=False)]

# ======================= (3) P3 vs P1 =======================
df["DealRatio"] = (df.NumDealsPurchases / df.TotalPurch.replace(0, np.nan)).clip(upper=1)
for c, n in zip(MNT, ["Wine", "Fruit", "Meat", "Fish", "Sweets", "Gold"]): df["sh_" + n] = df[c] / df.TotalSpend
for c, n in zip(CHAN, ["Web", "Catalog", "Store"]): df["ch_" + n] = df[c] / df.TotalPurch.replace(0, np.nan)
feats = ["Income", "Age", "Kidhome", "Teenhome", "TenureMonths", "TotalSpend", "AvgTicket", "TotalPurch", "DealRatio",
         "NumWebVisitsMonth", "ch_Web", "ch_Catalog", "ch_Store", "sh_Wine", "sh_Meat", "sh_Fish", "sh_Fruit", "sh_Sweets", "sh_Gold",
         "PrevAccepted", "Complain", "Recency"]
p1, p3 = df[df.Profile.str.startswith("P1")], df[df.Profile.str.startswith("P3")]
rows = []
for f in feats:
    a, b = p1[f].dropna(), p3[f].dropna(); sd = np.sqrt((a.var() + b.var()) / 2)
    rows.append(dict(feature=f, P1_mean=a.mean(), P3_mean=b.mean(), std_diff_P3_minus_P1=(b.mean() - a.mean()) / sd if sd > 0 else 0))
for lab, fn in [("pct_single", lambda d: 100 * (d.Marital == "Single").mean()), ("pct_PhD", lambda d: 100 * (d.Edu == "PhD").mean()),
                ("pct_joined_last_6m", lambda d: 100 * (d.TenureMonths <= 6).mean())]:
    rows.append(dict(feature=lab, P1_mean=fn(p1), P3_mean=fn(p3), std_diff_P3_minus_P1=np.nan))
cmp13 = pd.DataFrame(rows); cmp13.to_csv(OUT / "q4b_P3_vs_P1.csv", index=False)
rep += ["\n[3a] P3 vs P1 (both high tenure-adjusted value). std_diff = (P3 - P1)/pooled SD; |d|>0.5 = large",
        cmp13.round(3).to_string(index=False)]

prev_rows = []
for prof, g in df.groupby("Profile"):
    r = {"profile": prof, "n": len(g)}
    for c in PREV + ["Response"]:
        r[c] = g[c].mean()
    prev_rows.append(r)
r = {"profile": "ALL", "n": N}; r.update({c: df[c].mean() for c in PREV + ["Response"]}); prev_rows.append(r)
prev = pd.DataFrame(prev_rows); prev.to_csv(OUT / "q4b_campaign_by_profile.csv", index=False)
rep += ["\n[3b] Acceptance rate of each campaign by profile (campaign order/timing unconfirmed)", prev.round(3).to_string(index=False)]
# P3 acceptors of earlier campaigns
p3any = p3[p3.PrevAccepted > 0]
rep += [f"P3 customers who accepted >=1 earlier campaign: {len(p3any)} of {len(p3)}; "
        f"most common: " + ", ".join(f"{c}={int(p3[c].sum())}" for c in PREV)]
# P3 channel/product detail vs overall (to suggest pilot channel/offer)
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
cols = PREV
x = np.arange(len(cols)); w = .2
for i, prof in enumerate(sorted(df.Profile.unique())):
    vals = prev.set_index("profile").loc[prof, cols].values
    ax[0].bar(x + (i - 1.5) * w, vals, w, label=prof)
ax[0].set_xticks(x); ax[0].set_xticklabels([c.replace("AcceptedCmp", "Campaign ") for c in cols])
ax[0].set(ylabel="Acceptance rate", title="Earlier campaigns: acceptance by profile"); ax[0].legend(fontsize=7)

# ======================= (4) product preference index =======================
SH = ["sh_Wine", "sh_Meat", "sh_Fish", "sh_Fruit", "sh_Sweets", "sh_Gold"]
idx_rows = []
for grp in ["Profile"]:
    t = df.groupby(grp)[SH].mean() / df[SH].mean() * 100
    t.index = [f"{grp}: {i}" for i in t.index]; idx_rows.append(t)
    a = df.groupby(grp)[MNT].mean()
    a.index = [f"{grp}: {i} (mean spend)" for i in a.index]; idx_rows.append(a)
pidx = pd.concat(idx_rows).round(1); pidx.to_csv(OUT / "q4b_product_index.csv")
rep += ["\n[4] Product preference index = group mean share / overall mean share x 100 (100 = average); "
        "plus mean absolute spend per category", pidx.to_string()]
t = df.groupby("Profile")[SH].mean() / df[SH].mean() * 100
im = ax[1].imshow(t.values, cmap="RdBu_r", vmin=40, vmax=160, aspect="auto")
ax[1].set_xticks(range(len(SH))); ax[1].set_xticklabels([s.replace("sh_", "") for s in SH])
ax[1].set_yticks(range(len(t))); ax[1].set_yticklabels([i.split(" ", 1)[0] for i in t.index])
for i in range(t.shape[0]):
    for j in range(t.shape[1]): ax[1].text(j, i, f"{t.values[i, j]:.0f}", ha="center", va="center", fontsize=8)
ax[1].set_title("Product preference index (100 = average share)"); plt.colorbar(im, ax=ax[1])
fig.suptitle(f"Profiles: earlier-campaign response and relative product preference (n = {N})")
plt.tight_layout(); plt.savefig(FIG / "q4b_profile_campaigns_products.png", dpi=140); plt.close()

# complainers by profile (the complaint analysis itself is in 04_Results/Q2_Patterns)
cm = df.Complain == 1
rep += [f"\n[5] Complainers by profile: {cm.sum()} total; " + repr(df[cm].Profile.value_counts().to_dict())]

txt = "\n".join(rep); print(txt); (OUT / "q4b_results.txt").write_text(txt + "\n")
