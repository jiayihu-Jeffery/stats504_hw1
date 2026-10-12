"""Q4 (continued): how large must the randomised hold-out be to measure campaign uplift in P1+P2?
Two-sided two-proportion z-test, alpha = 0.05, power = 0.80. ASSUMPTION: the acceptance rate of contacted
P1+P2 customers equals last campaign's observed rate; the variance uses that rate for both arms."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import numpy as np, pandas as pd
from scipy.stats import norm
from paths import out
from tee import tee_to
OUT = out("q4"); tee_to(OUT / "q4d_holdout_power.txt")

pro = pd.read_csv(OUT / "q4_profiles.csv", index_col=0)
sub = pro[pro.index.str.startswith(("P1", "P2"))]
N = int(sub.n.sum()); p = float((sub.n * sub.resp_rate).sum() / N)
Z = norm.ppf(0.975) + norm.ppf(0.80)
print(f"P1+P2: N = {N}, observed acceptance p = {p:.3f}; alpha = 0.05 (two-sided), power = 0.80")

rows = []
for f in [0.10, 0.15, 0.20, 0.50]:
    n0, n1 = f * N, (1 - f) * N
    mde = Z * np.sqrt(p * (1 - p) * (1 / n0 + 1 / n1))
    need = {d: Z ** 2 * p * (1 - p) * (1 / f + 1 / (1 - f)) / d ** 2 for d in (0.05, 0.10, 0.15)}
    rows.append(dict(holdout_share=f, holdout_n_in_P1P2=round(n0), mde_pp_in_P1P2=100 * mde,
                     total_needed_for_5pp=round(need[0.05]), total_needed_for_10pp=round(need[0.10]),
                     holdout_needed_for_10pp=round(f * need[0.10]), total_needed_for_15pp=round(need[0.15])))
res = pd.DataFrame(rows).round({"holdout_share": 2, "mde_pp_in_P1P2": 1}); res.to_csv(OUT / "q4d_holdout_power.csv", index=False)
print(res.to_string(index=False))
print("\nReading: with P1+P2 of this size, a 15% hold-out detects only uplifts of about the MDE shown; "
      "detecting a 10-point uplift needs the total targeted group shown (apply the design to the full customer base).")
