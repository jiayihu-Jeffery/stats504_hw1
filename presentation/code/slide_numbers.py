"""Numbers used only on the slides (not in the two-page report). Output: presentation/output/slide_numbers.txt."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from clean import load, DATA
from paths import out

OUT = ROOT / "presentation" / "output"; OUT.mkdir(parents=True, exist_ok=True)
df = load(); rep = []

# 1. why regression rather than pairwise correlations
rep += ["[1] Pairwise relations (primary sample)",
        f"corr(young children, income) = {df.Kidhome.corr(df.Income):.2f}; corr(young children, spend) = {df.Kidhome.corr(df.TotalSpend):.2f}; "
        f"corr(income, spend) = {df.Income.corr(df.TotalSpend):.2f}",
        f"mean income: with young children {df.Income[df.Kidhome > 0].mean():,.0f}; without {df.Income[df.Kidhome == 0].mean():,.0f}",
        f"spend: mean {df.TotalSpend.mean():.0f}, median {df.TotalSpend.median():.0f}, skewness {df.TotalSpend.skew():.2f}"]

# 2. three raw customers and the Q2 style features of the first one
raw = pd.read_csv(DATA, sep="\t")
cols = ["ID", "Year_Birth", "Education", "Marital_Status", "Income", "Kidhome", "Teenhome", "Dt_Customer", "Recency",
        "MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds",
        "NumDealsPurchases", "NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases", "NumWebVisitsMonth",
        "AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5", "Response"]
ex = raw[raw.ID.isin([5524, 2174, 4141])].set_index("ID").loc[[5524, 2174, 4141], cols[1:]]
ex.T.to_csv(OUT / "raw_example_customers.csv")
rep += ["\n[2] Three raw customers (transposed)", ex.T.to_string()]
c = raw[raw.ID == 5524].iloc[0]
mnt = ["MntWines", "MntMeatProducts", "MntFishProducts", "MntFruits", "MntSweetProducts", "MntGoldProds"]
tot = c[mnt].sum(); purch = c[["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]].sum()
feat = {f"share_{m[3:]}": c[m] / tot for m in mnt}
feat.update({"share_web": c.NumWebPurchases / purch, "share_catalog": c.NumCatalogPurchases / purch, "share_store": c.NumStorePurchases / purch,
             "discount_share": min(c.NumDealsPurchases / purch, 1), "web_visits": c.NumWebVisitsMonth, "total_spend": tot, "total_purchases": purch})
rep += ["\n[2b] Customer 5524 -> 11 style measures", pd.Series(feat).round(3).to_string()]

# 3. raw vs log income inside the spline Gamma model
df["logInc"] = np.log(df.Income); df["Inc10k"] = df.Income / 1e4; df["Age10"] = df.Age / 10
REST = " + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths"
def fit(inc):
    rhs = inc + REST
    o = smf.ols("np.log(TotalSpend) ~ " + rhs, df).fit(); st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
    mod = smf.glm("TotalSpend ~ " + rhs, df, family=sm.families.Gamma(sm.families.links.Log()))
    cands = [mod.fit(start_params=st.values, method="newton", maxiter=500)]
    try: cands.append(mod.fit())
    except Exception: pass
    return min(cands, key=lambda r: r.deviance)
rows = []
for lab, inc in [("income, straight line", "Inc10k"), ("log income, straight line", "logInc"),
                 ("income, spline", "bs(Inc10k, df=4)"), ("log income, spline (final)", "bs(logInc, df=4)")]:
    m = fit(inc); rows.append(dict(model=lab, deviance=m.deviance, AIC=m.aic, deviance_R2=1 - m.deviance / m.null_deviance,
                                   young_child_pct=100 * (np.exp(m.params["Kidhome"]) - 1)))
inc_tab = pd.DataFrame(rows).round(3); inc_tab.to_csv(OUT / "income_form_comparison.csv", index=False)
rep += ["\n[3] Income form inside the Gamma model", inc_tab.to_string(index=False)]

# 4. why tenure-adjusted value rather than spend per month
d = df.copy(); d["monthly"] = d.TotalSpend / d.TenureMonths.clip(lower=0.25)
d["band"] = pd.cut(d.TenureMonths, [0, 1, 3, 6, 12, 18, 24.5], include_lowest=True)
mm = d.groupby("band", observed=True).agg(n=("ID", "size"), median_total=("TotalSpend", "median"), median_per_month=("monthly", "median"))
rep += ["\n[4] Total vs per-month spend by tenure band", mm.round(1).to_string(),
        f"Spearman with tenure: total {d.TotalSpend.corr(d.TenureMonths, 'spearman'):.2f}, per month {d.monthly.corr(d.TenureMonths, 'spearman'):.2f}"]

# 5. split at the top third vs at the median (both dimensions)
t = pd.read_csv(out("q4") / "q4_customer_tiers.csv")[["ID", "Profile", "p_Q4"]]
d = df.merge(t, on="ID")
cr = d.groupby(pd.cut(d.TenureMonths, [-0.01, 6, 12, 18, 24])).TotalSpend.rank(pct=True)
hv, hp = cr > .5, d.p_Q4 > d.p_Q4.median()
tot_a, tot_s = d.Response.sum(), d.TotalSpend.sum()
def summ(mask, lab):
    x = d[mask]; return dict(group=lab, pct_customers=100 * mask.mean(), acceptance=100 * x.Response.mean(),
                             pct_acceptors=100 * x.Response.sum() / tot_a, pct_spend=100 * x.TotalSpend.sum() / tot_s)
cmp = pd.DataFrame([summ(hv & hp, "median split: high x high"), summ(d.Profile.str.startswith("P1"), "top-third split: P1")]).round(1)
cmp.to_csv(OUT / "split_comparison.csv", index=False)
rep += ["\n[5] Median split vs top-third split", cmp.to_string(index=False)]

txt = "\n".join(rep); print(txt); (OUT / "slide_numbers.txt").write_text(txt + "\n")
