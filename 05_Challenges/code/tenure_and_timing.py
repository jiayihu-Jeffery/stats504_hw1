"""Challenges: (1) every customer joined within the 2-year spending window, so raw spend partly measures tenure;
(2) the timing of behaviour fields vs the last campaign is undocumented (recency could be affected by accepting).
Collects the evidence from the data and from the Q1/Q3/Q4 outputs."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from clean import load
from paths import out
from tee import tee_to
tee_to(out("challenges") / "tenure_and_timing.txt")

df = load()
print("== (1) Tenure vs the 2-year spending window ==")
print(f"Enrolment dates: {df.Dt.min().date()} to {df.Dt.max().date()}; max tenure relative to latest enrolment = "
      f"{df.TenureMonths.max():.1f} months (< 24) -> no customer was observed for the full 2-year window.")
t = df.groupby("TenureBand", observed=True).TotalSpend.agg(["size", "median", "mean"]).round(0)
print("Spend by 6-month joining band:"); print(t.to_string())
r, p = spearmanr(df.TenureMonths, df.TotalSpend); print(f"Spearman(tenure, spend) = {r:.3f} (p = {p:.1e})")
eff = pd.read_csv(out("q1") / "q1_effects.csv").set_index("term")
print(f"Adjusted association (Q1 Gamma GLM): +{eff.loc['Tenure +1 month', 'gamma_pct']:.1f}% spend per month of tenure")
chg = pd.read_csv(out("q4") / "q4_profile_change.csv", index_col=0)
print("Effect of tenure-adjusting value tiers on Q4 profiles (rows = raw spend, cols = tenure-adjusted):"); print(chg.to_string())
print("\n== (2) Undocumented timing of behaviour fields (recency) ==")
rates = pd.read_csv(out("q3") / "q3_rates.csv"); print(rates[rates.variable == "RecencyBin"].round(3).to_string(index=False))
perf = pd.read_csv(out("q3") / "q3_model_performance.csv")
print("Scenario A (no recency) vs Scenario B (with recency):")
print(perf[["features", "model", "AUC_mean", "top10_rate"]].round(3).to_string(index=False))
print("Recency is kept out of all recommendations until the client confirms it was recorded before the campaign.")
