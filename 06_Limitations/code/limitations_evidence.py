"""Limitations: the data facts behind each limitation in the report (small groups, campaign heterogeneity,
data age, leakage scenario). Causal identification cannot be checked from the data (no randomisation flag)."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import pandas as pd
from clean import load, DATA, PREV
from paths import out
from tee import tee_to
tee_to(out("limitations") / "limitations_evidence.txt")

raw = pd.read_csv(DATA, sep="\t"); df = load()
print("== Small groups (primary sample, n = %d) ==" % len(df))
small = pd.DataFrame([("Education = Basic", (df.Edu == "Basic").sum()), ("3 children + teens at home", (df.Children == 3).sum()),
                      ("2 young children", (df.Kidhome == 2).sum()), ("Complained (last 2 years)", df.Complain.sum()),
                      ("9+ web visits last month", (df.NumWebVisitsMonth >= 9).sum())], columns=["group", "n"])
print(small.to_string(index=False)); small.to_csv(out("limitations") / "small_groups.csv", index=False)
print("\n== Campaign heterogeneity (raw file acceptance rates) ==")
acc = raw[PREV + ["Response"]].mean().round(4); print(acc.to_string()); acc.to_csv(out("limitations") / "campaign_acceptance_rates.csv")
print(f"\n== Data age == enrolment {pd.to_datetime(raw.Dt_Customer, format='%d-%m-%Y').min().date()} to "
      f"{pd.to_datetime(raw.Dt_Customer, format='%d-%m-%Y').max().date()}")
print("\n== Undocumented fields == Z_CostContact unique values:", sorted(raw.Z_CostContact.unique()),
      "; Z_Revenue unique values:", sorted(raw.Z_Revenue.unique()))
print("\n== No randomisation/contact flag == the file has no field recording who was contacted in each campaign,"
      " so acceptance cannot be separated from exposure and no causal (uplift) effect can be estimated.")
