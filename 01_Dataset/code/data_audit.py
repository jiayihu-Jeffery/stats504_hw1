"""Data audit: structure, missingness, anomalies, documentation gaps."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import pandas as pd, numpy as np
from clean import DATA
from paths import out
from tee import tee_to
tee_to(out("dataset") / "01_data_audit.txt")
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 50)

df = pd.read_csv(DATA, sep="\t")
print("shape", df.shape)
print(df.dtypes.value_counts())
print("\n== missing ==\n", df.isna().sum()[df.isna().sum() > 0])
print("\nID unique:", df.ID.is_unique)
dup = df.drop(columns="ID").duplicated(keep=False)
print("rows identical except ID:", dup.sum(), " (distinct groups:", df.drop(columns='ID')[dup].drop_duplicates().shape[0], ")")

print("\n== constant cols ==")
for c in df.columns:
    if df[c].nunique() == 1: print(c, df[c].iloc[0])

print("\n== categorical ==")
print(df.Education.value_counts()); print(df.Marital_Status.value_counts())

num = df.select_dtypes("number").drop(columns=["ID"])
print("\n== numeric summary ==\n", num.describe(percentiles=[.01,.5,.99]).T.round(1))

print("\nYear_Birth < 1930:\n", df.loc[df.Year_Birth < 1930, ["ID","Year_Birth","Income","Dt_Customer"]])
print("\nIncome top 8:", df.Income.nlargest(8).tolist())

d = pd.to_datetime(df.Dt_Customer, format="%d-%m-%Y")
print("\nDt_Customer range:", d.min().date(), "->", d.max().date())
print(d.dt.to_period("Q").value_counts().sort_index())

mnt = [c for c in df if c.startswith("Mnt")]
chan = ["NumWebPurchases","NumCatalogPurchases","NumStorePurchases"]
df["TotalSpend"] = df[mnt].sum(axis=1)
df["TotalPurch"] = df[chan].sum(axis=1)
print("\nTotalSpend summary:", df.TotalSpend.describe().round(0).to_dict())
print("TotalPurch==0:", (df.TotalPurch==0).sum(), "; of those spend>0:", ((df.TotalPurch==0)&(df.TotalSpend>0)).sum())
print("Deals > channel total:", (df.NumDealsPurchases > df.TotalPurch).sum(),
      " -> deals likely a subset/overlap of channel purchases (undocumented)")
print("Recency range:", df.Recency.min(), df.Recency.max())
print("NumWebVisitsMonth > 10:", (df.NumWebVisitsMonth>10).sum())

cmp = ["AcceptedCmp1","AcceptedCmp2","AcceptedCmp3","AcceptedCmp4","AcceptedCmp5","Response"]
print("\n== campaign acceptance rates ==\n", df[cmp].mean().round(4))
print("Complain rate:", round(df.Complain.mean(),4), "n=", df.Complain.sum())
df["PrevAccepted"] = df[cmp[:5]].sum(axis=1)
print("\nPrev accepted count dist:\n", df.PrevAccepted.value_counts().sort_index())
print("\nResponse rate by # prior acceptances:\n", df.groupby("PrevAccepted").Response.agg(["mean","size"]).round(3))
print("\nPairwise campaign overlap (corr):\n", df[cmp].corr().round(2))

# tenure relative to latest enrolment date (reference date unknown)
ref = d.max()
df["TenureDays"] = (ref - d).dt.days
print("\ncorr(TenureDays, TotalSpend)=%.3f  corr(TenureDays, Response)=%.3f" %
      (df.TenureDays.corr(df.TotalSpend), df.TenureDays.corr(df.Response)))
print("Share enrolled < 730 days before latest enrolment:", round((df.TenureDays < 730).mean(),3))
