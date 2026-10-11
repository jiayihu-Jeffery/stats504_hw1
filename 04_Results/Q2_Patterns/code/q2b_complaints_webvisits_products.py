"""Q2 (continued): complaints, website visits, and relative product preference by style segment."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint
from scipy.stats import fisher_exact, spearmanr, mannwhitneyu
from clean import load, MNT, CHAN
from paths import out, fig
OUT = out("q2")
pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)

df = load(); N = len(df)
df = df.merge(pd.read_csv(OUT / "q2_segment_assignments.csv"), on="ID", how="left")
rep = [f"Q2b — complaints, website visits, product preference by segment; n = {N}"]

def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson"); return lo, hi

df["DealRatio"] = (df.NumDealsPurchases / df.TotalPurch.replace(0, np.nan)).clip(upper=1)
for c, n in zip(MNT, ["Wine", "Fruit", "Meat", "Fish", "Sweets", "Gold"]): df["sh_" + n] = df[c] / df.TotalSpend
for c, n in zip(CHAN, ["Web", "Catalog", "Store"]): df["ch_" + n] = df[c] / df.TotalPurch.replace(0, np.nan)

# ---------- product preference index by style segment ----------
SH = ["sh_Wine", "sh_Meat", "sh_Fish", "sh_Fruit", "sh_Sweets", "sh_Gold"]
t = df.groupby("Segment")[SH].mean() / df[SH].mean() * 100; t.index = [f"Segment: {i}" for i in t.index]
a = df.groupby("Segment")[MNT].mean(); a.index = [f"Segment: {i} (mean spend)" for i in a.index]
pidx = pd.concat([t, a]).round(1); pidx.to_csv(OUT / "q2b_product_index_segment.csv")
rep += ["\n[1] Product preference index = segment mean share / overall mean share x 100 (100 = average); "
        "plus mean absolute spend per category", pidx.to_string()]

# ---------- complaints ----------
cm = df.Complain == 1
tab = [[int(df.Response[cm].sum()), int((1 - df.Response[cm]).sum())], [int(df.Response[~cm].sum()), int((1 - df.Response[~cm]).sum())]]
_, pf = fisher_exact(tab)
lo1, hi1 = wilson(df.Response[cm].sum(), cm.sum()); lo0, hi0 = wilson(df.Response[~cm].sum(), (~cm).sum())
u = mannwhitneyu(df.TotalSpend[cm], df.TotalSpend[~cm])
rep += [f"\n[2] Complaints: {cm.sum()} customers ({100 * cm.mean():.2f}%) complained in the last 2 years.",
        f"  Acceptance: complained {df.Response[cm].mean():.3f} [{lo1:.3f}, {hi1:.3f}] vs not {df.Response[~cm].mean():.3f} [{lo0:.3f}, {hi0:.3f}]; Fisher exact p = {pf:.3f}",
        f"  Median spend: complained {df.TotalSpend[cm].median():.0f} vs not {df.TotalSpend[~cm].median():.0f}; Mann-Whitney p = {u.pvalue:.3f}"]

# ---------- website visits ----------
df["VisitBand"] = pd.cut(df.NumWebVisitsMonth, [-1, 2, 5, 8, 100], labels=["0-2", "3-5", "6-8", "9+"])
vrows = []
for b, g in df.groupby("VisitBand", observed=True):
    lo, hi = wilson(g.Response.sum(), len(g))
    vrows.append(dict(visits=str(b), n=len(g), acceptance=g.Response.mean(), lo=lo, hi=hi, median_spend=g.TotalSpend.median(),
                      web_share=g.ch_Web.mean(), deal_ratio=g.DealRatio.mean(), web_purchases=g.NumWebPurchases.mean(),
                      mean_kidhome=g.Kidhome.mean()))
vis = pd.DataFrame(vrows); vis.to_csv(OUT / "q2b_web_visits.csv", index=False)
rs, ps = spearmanr(df.NumWebVisitsMonth, df.TotalSpend); rw, pw = spearmanr(df.NumWebVisitsMonth, df.NumWebPurchases)
rep += ["\n[3] Website visits last month", vis.round(3).to_string(index=False),
        f"  Spearman(visits, total spend) = {rs:.3f}; Spearman(visits, web purchases) = {rw:.3f}"]

txt = "\n".join(rep); print(txt); (OUT / "q2b_results.txt").write_text(txt + "\n")
