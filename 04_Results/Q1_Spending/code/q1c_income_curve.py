"""Q1c: shape of the income curve f(log Income) in the final Gamma GLM, relative to median income, with 95% HC3 bands."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from patsy import build_design_matrices
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load
from paths import out, fig
OUT = out("q1"); FIG = fig("q1")
warnings.filterwarnings("ignore")

df = load()
df["logInc"] = np.log(df.Income); df["Age10"] = df.Age / 10
RHS = ("bs(logInc, df=4) + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths")
FAM = sm.families.Gamma(sm.families.links.Log())

# same fitting rule as q1_spend.fit_gamma: Newton from smearing-adjusted log-OLS start, keep lower deviance
o = smf.ols("np.log(TotalSpend) ~ " + RHS, df).fit()
st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
mod = smf.glm("TotalSpend ~ " + RHS, df, family=FAM)
cands = [mod.fit(start_params=st.values, method="newton", maxiter=500, cov_type="HC3")]
try: cands.append(mod.fit(cov_type="HC3"))
except Exception: pass
m = min(cands, key=lambda r: r.deviance)

# f(x) - f(median) with delta-method bands; other covariates cancel in the difference
med = float(df.Income.median())
lo_i, hi_i = df.Income.quantile([.01, .99])
grid = np.exp(np.linspace(np.log(lo_i), np.log(hi_i), 200))
ref = dict(Kidhome=0, Teenhome=0, Age10=df.Age10.median(), Edu="Graduation", Marital="Partnered",
           TenureMonths=df.TenureMonths.median(), TotalSpend=1.0)
new = pd.DataFrame([dict(ref, Income=v, logInc=np.log(v)) for v in list(grid) + [med]])
X = np.asarray(build_design_matrices([m.model.data.design_info], new)[0])
D = X[:-1] - X[-1]
f = D @ m.params.values
se = np.sqrt(np.einsum("ij,jk,ik->i", D, m.cov_params().values, D))
slope = np.gradient(f, np.log(grid))                          # elasticity d log(mu) / d log(Income)
curve = pd.DataFrame({"income": grid, "f_minus_f_median": f, "lo": f - 1.96 * se, "hi": f + 1.96 * se,
                      "multiplier": np.exp(f), "mult_lo": np.exp(f - 1.96 * se), "mult_hi": np.exp(f + 1.96 * se),
                      "elasticity": slope})
curve.round(4).to_csv(OUT / "q1c_income_curve_grid.csv", index=False)

fig_, ax = plt.subplots(1, 3, figsize=(14, 4))
k = grid / 1000
ax[0].fill_between(k, curve.lo, curve.hi, color="#9ecae1", alpha=.6, lw=0)
ax[0].plot(k, f, color="#08519c", lw=2); ax[0].axhline(0, color="grey", lw=.8, ls="--")
ax[0].set(xscale="log", xlabel="Income (thousands, log scale)", ylabel=r"$\hat f(\log\,$Income$) - \hat f($median$)$",
          title="(A) The curve as the model sees it (log scale)")
ax[0].set_xticks([5, 10, 20, 35, 50, 80]); ax[0].set_xticklabels(["5", "10", "20", "35", "50", "80"])
ax[1].fill_between(k, curve.mult_lo, curve.mult_hi, color="#fdae6b", alpha=.6, lw=0)
ax[1].plot(k, curve.multiplier, color="#d94801", lw=2); ax[1].axhline(1, color="grey", lw=.8, ls="--")
for v in [20, 35, 65, 80, 90]:
    y = float(np.exp(np.interp(np.log(v * 1000), np.log(grid), f)))
    ax[1].plot(v, y, "o", color="#d94801", ms=4); ax[1].annotate(f"×{y:.2f}", (v, y), xytext=(4, -10), textcoords="offset points", fontsize=8)
ax[1].set(xlabel="Income (thousands)", ylabel="Mean spend ÷ mean spend at median income",
          title=f"(B) As a multiplier vs median income ({med / 1000:.1f}k)")
ax[2].plot(k, slope, color="#238b45", lw=2); ax[2].axhline(1, color="grey", lw=.8, ls="--")
ax[2].set(xlabel="Income (thousands)", ylabel="Elasticity: % spend per 1% income", title="(C) Slope of the curve")
for a in ax: a.grid(alpha=.25)
sub = df.Income[(df.Income >= lo_i) & (df.Income <= hi_i)] / 1000
for a in ax[:2]:
    yl = a.get_ylim(); a.plot(sub, np.full(len(sub), yl[0]), "|", color="k", alpha=.08, ms=8); a.set_ylim(yl)
fig_.suptitle(f"Income curve in the final Q1 Gamma model (n = {len(df)}; 1st–99th income percentile; 95% HC3 bands; "
              "other factors held fixed)", fontsize=10)
plt.tight_layout(); plt.savefig(FIG / "q1c_income_curve.png", dpi=150); plt.close()

pts = [10000, 20000, 35000, med, 65000, 80000, 90000]
print(pd.DataFrame({"income": pts,
                    "multiplier": [float(np.exp(np.interp(np.log(v), np.log(grid), f))) for v in pts],
                    "elasticity": [float(np.interp(np.log(v), np.log(grid), slope)) for v in pts]}).round(2).to_string(index=False))
print("income range plotted:", round(lo_i), "-", round(hi_i))
