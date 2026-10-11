"""Shared cleaning module. Every analysis script imports `load()` from here.

Assumptions (unconfirmed with client) are marked ASSUMPTION.
"""
import numpy as np
import pandas as pd
from paths import DATA_FILE as DATA, SEED  # noqa: F401  (SEED re-exported for analysis scripts)

MNT = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
CHAN = ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
PREV = ["AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5"]

# Variable availability tiers at the time a future campaign is sent
T0_NUM = ["Income", "Age", "Kidhome", "Teenhome", "TenureMonths"]
T0_CAT = ["Edu", "Marital"]
T1_NO_RECENCY = MNT + CHAN + ["NumDealsPurchases", "NumWebVisitsMonth", "Complain"]
T2 = PREV


def load(dedup=True, drop_flagged=False, log=None):
    """Return the analysis sample.

    dedup=True       -> primary sample (one row per group of rows identical on all non-ID fields)
    drop_flagged     -> additionally drop the flagged Income > 150k records (sensitivity)
    log              -> optional list; (step, rows) tuples are appended
    """
    step = (lambda s, d: log.append((s, len(d)))) if log is not None else (lambda s, d: None)
    df = pd.read_csv(DATA, sep="\t")
    step("raw", df)
    df = df.dropna(subset=["Income"]); step("drop missing Income", df)
    df = df[df.Year_Birth >= 1930]; step("drop Year_Birth < 1930", df)
    df = df[df.Income != 666666]; step("drop Income = 666,666", df)
    df = df[~df.Marital_Status.isin(["Absurd", "YOLO"])]; step("drop Marital_Status Absurd/YOLO", df)
    if dedup:
        df = df.drop_duplicates(subset=[c for c in df.columns if c != "ID"], keep="first")
        step("deduplicate (identical on all non-ID fields)", df)
    df = df.drop(columns=["Z_CostContact", "Z_Revenue"]).copy()

    df["Marital"] = df.Marital_Status.map({"Married": "Partnered", "Together": "Partnered",
                                           "Single": "Single", "Divorced": "Single",
                                           "Widow": "Single", "Alone": "Single"})
    df["Edu"] = df.Education.replace({"2n Cycle": "Master"})  # ASSUMPTION: 2n Cycle ~ Master level
    df["Dt"] = pd.to_datetime(df.Dt_Customer, format="%d-%m-%Y")
    df["TenureMonths"] = (df.Dt.max() - df.Dt).dt.days / 30.44  # relative to latest enrolment date
    df["Age"] = 2014 - df.Year_Birth  # ASSUMPTION: reference year 2014 (only shifts intercepts)
    df["TotalSpend"] = df[MNT].sum(axis=1)
    df["TotalPurch"] = df[CHAN].sum(axis=1)
    df["Children"] = df.Kidhome + df.Teenhome
    df["PrevAccepted"] = df[PREV].sum(axis=1)
    df["AvgTicket"] = df.TotalSpend / df.TotalPurch.replace(0, np.nan)
    df["Flag_HighIncome"] = (df.Income > 150000).astype(int)
    if drop_flagged:
        df = df[df.Flag_HighIncome == 0].copy(); step("drop flagged Income > 150k", df)

    df["IncomeQ"] = pd.qcut(df.Income, 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
    df["SpendTier"] = pd.qcut(df.TotalSpend, 3, labels=["Low", "Mid", "High"])
    # Tenure-adjusted value: rank spend among customers who joined in the same 6-month window.
    # (Avoids assuming a snapshot date; all customers joined < 24 months before the latest enrolment.)
    df["TenureBand"] = pd.cut(df.TenureMonths, [-0.01, 6, 12, 18, 24], labels=["0-6m", "6-12m", "12-18m", "18-24m"])
    df["SpendPctInBand"] = df.groupby("TenureBand", observed=True).TotalSpend.rank(pct=True)
    df["SpendTierAdj"] = pd.cut(df.SpendPctInBand, [0, 1 / 3, 2 / 3, 1], labels=["Low", "Mid", "High"])
    return df.reset_index(drop=True)
