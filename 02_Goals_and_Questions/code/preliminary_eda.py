"""Preliminary exploratory analysis for Q1-Q3 (NOT final results)."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
pd.set_option("display.width", 200)
from clean import DATA
from paths import out, fig
from tee import tee_to
tee_to(out("goals") / "02_preliminary_eda.txt")
FIGDIR = fig("goals")

df = pd.read_csv(DATA, sep="\t")
mnt = ["MntWines","MntFruits","MntMeatProducts","MntFishProducts","MntSweetProducts","MntGoldProds"]
chan = ["NumWebPurchases","NumCatalogPurchases","NumStorePurchases"]
prev = ["AcceptedCmp1","AcceptedCmp2","AcceptedCmp3","AcceptedCmp4","AcceptedCmp5"]

# --- provisional cleaning (decisions to be confirmed) ---
n0 = len(df)
df = df[(df.Year_Birth >= 1930) & (df.Income.fillna(0) < 600000)].dropna(subset=["Income"]).copy()
print(f"provisional analysis sample: {len(df)} of {n0} (dropped NA income, birth<1930, income=666666)")
df["Dt"] = pd.to_datetime(df.Dt_Customer, format="%d-%m-%Y")
df["TenureMonths"] = (df.Dt.max() - df.Dt).dt.days / 30.44
df["Age2014"] = 2014 - df.Year_Birth            # reference year is an assumption
df["Children"] = df.Kidhome + df.Teenhome
df["Marital"] = df.Marital_Status.replace({"Married":"Partnered","Together":"Partnered",
                    "Single":"Single","Divorced":"Single","Widow":"Single","Alone":"Single",
                    "Absurd":"Other","YOLO":"Other"})
df["Edu"] = df.Education.replace({"2n Cycle":"Master"})   # 2n Cycle ~ Master (to confirm)
df["TotalSpend"] = df[mnt].sum(axis=1)
df["TotalPurch"] = df[chan].sum(axis=1)
df["PrevAccepted"] = df[prev].sum(axis=1)
df["IncQ"] = pd.qcut(df.Income, 4, labels=["Q1 low","Q2","Q3","Q4 high"])

# ================= Q1 spending =================
print("\n=== Q1: median TotalSpend by group ===")
for g in ["IncQ","Kidhome","Teenhome","Children","Edu","Marital"]:
    print(df.groupby(g, observed=True).TotalSpend.agg(["median","mean","size"]).round(0), "\n")
print("Spearman with TotalSpend:")
print(df[["Income","Age2014","Kidhome","Teenhome","TenureMonths","Recency"]]
      .corrwith(df.TotalSpend, method="spearman").round(3))

m1 = smf.ols("np.log(TotalSpend) ~ np.log(Income) + Kidhome + Teenhome + Age2014 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths",
             data=df).fit(cov_type="HC3")
print("\nOLS log(TotalSpend), HC3 SEs:\n", m1.summary().tables[1], "\nR2=%.3f" % m1.rsquared)
m1b = smf.ols("np.log(TotalSpend) ~ np.log(Income) + Kidhome + Teenhome", data=df).fit()
print("R2 income+kids+teens only = %.3f" % m1b.rsquared)

# ================= Q2 purchasing patterns =================
shares = df[mnt].div(df.TotalSpend, axis=0); shares.columns = [c.replace("Mnt","") for c in mnt]
cs = df[chan].div(df.TotalPurch.replace(0, np.nan), axis=0); cs.columns = ["Web","Catalog","Store"]
print("\n=== Q2: overall mean product share ===\n", shares.mean().round(3))
print("\nproduct share by income quartile:\n", shares.groupby(df.IncQ, observed=True).mean().round(3))
print("\nproduct share by Children:\n", shares.groupby(df.Children).mean().round(3))
print("\nchannel share by income quartile:\n", cs.groupby(df.IncQ, observed=True).mean().round(3))
print("\nchannel share by Children:\n", cs.groupby(df.Children).mean().round(3))
print("\nDeals purchases / web visits by Children:\n",
      df.groupby("Children")[["NumDealsPurchases","NumWebVisitsMonth","TotalPurch"]].mean().round(2))
print("\nSpend concentration: top 20%% customers' share of total spend = %.3f" %
      (df.TotalSpend.nlargest(int(.2*len(df))).sum() / df.TotalSpend.sum()))

# ================= Q3 campaign response =================
print("\n=== Q3: Response rate by group ===")
for g in ["IncQ","Children","Edu","Marital","PrevAccepted"]:
    print(df.groupby(g, observed=True).Response.agg(["mean","size"]).round(3), "\n")
df["RecencyBin"] = pd.cut(df.Recency, [-1,24,49,74,99], labels=["0-24","25-49","50-74","75-99"])
df["TenureT"] = pd.qcut(df.TenureMonths, 3, labels=["newest","mid","oldest"])
for g in ["RecencyBin","TenureT"]:
    print(df.groupby(g, observed=True).Response.agg(["mean","size"]).round(3), "\n")

y = df.Response.values
cv = StratifiedKFold(5, shuffle=True, random_state=503)
demo_num = ["Income","Age2014","Kidhome","Teenhome"]; demo_cat = ["Edu","Marital"]
beh = ["Recency","TenureMonths","NumDealsPurchases","NumWebVisitsMonth","Complain"] + mnt + chan
sets = {"A demographics": (demo_num, demo_cat),
        "B demo + behaviour/tenure": (demo_num+beh, demo_cat),
        "C B + prior campaigns": (demo_num+beh+prev, demo_cat),
        "D prior campaigns only": (prev, [])}
print("5-fold CV AUC (L2 logistic):")
for name, (nu, ca) in sets.items():
    pre = ColumnTransformer([("n", StandardScaler(), nu)] + ([("c", OneHotEncoder(drop="first"), ca)] if ca else []))
    p = cross_val_predict(make_pipeline(pre, LogisticRegression(max_iter=2000, C=1.0)),
                          df[nu+ca], y, cv=cv, method="predict_proba")[:, 1]
    top = p >= np.quantile(p, .9)
    print(f"  {name:28s} AUC={roc_auc_score(y,p):.3f}  top-decile resp rate={y[top].mean():.3f} (lift {y[top].mean()/y.mean():.2f}x)")
print("  base rate =", round(y.mean(), 3))

# ================= figures =================
fig, ax = plt.subplots(1, 3, figsize=(14, 4))
ax[0].scatter(df.Income/1000, df.TotalSpend, s=5, alpha=.4, c=df.Children, cmap="viridis")
ax[0].set(xlabel="Income ($k)", ylabel="Total 2-yr spend", title="Spend vs income (colour = #children)")
df.boxplot("TotalSpend", by="Children", ax=ax[1], grid=False); ax[1].set(title="Spend by # children", xlabel="")
shares.groupby(df.IncQ, observed=True).mean().plot.bar(stacked=True, ax=ax[2], rot=0, colormap="tab20")
ax[2].set(title="Product share by income quartile", ylabel="share"); ax[2].legend(fontsize=7)
plt.suptitle(""); plt.tight_layout(); plt.savefig(FIGDIR / "q1_q2_overview.png", dpi=130)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
r = df.groupby("PrevAccepted").Response.mean(); ax[0].bar(r.index, r.values, color="#4C72B0")
ax[0].set(xlabel="# prior campaigns accepted", ylabel="Response rate (last campaign)", title="Response vs prior acceptances")
r = df.groupby("RecencyBin", observed=True).Response.mean(); ax[1].bar(r.index.astype(str), r.values, color="#55A868")
ax[1].set(xlabel="Recency (days)", title="Response vs recency")
plt.tight_layout(); plt.savefig(FIGDIR / "q3_response.png", dpi=130)
print("\nfigures saved")
