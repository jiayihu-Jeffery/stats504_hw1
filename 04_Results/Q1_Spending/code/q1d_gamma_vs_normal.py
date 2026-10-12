"""Q1d: why a Gamma model rather than ordinary (Normal, constant-variance) regression - a teaching figure.
Same fitted mean for both; only the assumed spread around it differs."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load
from paths import out, fig
OUT = out("q1"); FIG = fig("q1")

df = load(); df["logInc"] = np.log(df.Income); df["Age10"] = df.Age / 10
RHS = "bs(logInc, df=4) + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths"
o = smf.ols("np.log(TotalSpend) ~ " + RHS, df).fit(); st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
mod = smf.glm("TotalSpend ~ " + RHS, df, family=sm.families.Gamma(sm.families.links.Log()))
g = min([mod.fit(start_params=st.values, method="newton", maxiter=500), mod.fit()], key=lambda r: r.deviance)
mu, y = g.fittedvalues.values, df.TotalSpend.values
phi = g.scale; cv = np.sqrt(phi)                                   # Gamma: SD = sqrt(phi) * mu
sigma = smf.ols("TotalSpend ~ " + RHS, df).fit().resid.std()       # Normal: one SD for everyone

bins = pd.qcut(mu, 10, labels=False)
emp = pd.DataFrame({"mu": mu, "y": y, "b": bins}).groupby("b").agg(mean_fitted=("mu", "mean"), mean_y=("y", "mean"), sd_y=("y", "std"))
emp.round(2).to_csv(OUT / "q1d_spread_by_decile.csv")

BLUE, ORANGE, GREY, INK2 = "#2a78d6", "#eb6834", "#8a8984", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})
fig_, ax = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1.35, 1, 1.1]})

# A: scatter with the two assumed +-1 SD bands around the same fitted mean
a = ax[0]
a.scatter(mu, y, s=5, color="k", alpha=.18, lw=0, label="Customers")
xs = np.linspace(mu.min(), np.percentile(mu, 99.5), 300)
a.plot(xs, xs, color=INK2, lw=1.2, label="Fitted mean μ")
a.fill_between(xs, xs * (1 - cv), xs * (1 + cv), color=BLUE, alpha=.22, lw=0, label=f"Gamma: μ ± {cv:.2f}·μ (spread grows)")
a.plot(xs, xs - sigma, color=ORANGE, lw=1.4, ls="--", label=f"Normal: μ ± {sigma:.0f} (same spread)")
a.plot(xs, xs + sigma, color=ORANGE, lw=1.4, ls="--")
a.axhspan(-700, 0, color=ORANGE, alpha=.07); a.text(xs.max() * .98, -330, "negative spending:\nimpossible, but the Normal band reaches here",
                                                     ha="right", va="center", fontsize=8, color=ORANGE)
a.errorbar(emp.mean_fitted, emp.mean_y, yerr=emp.sd_y, fmt="o", color="#1baf7a", ms=4, capsize=3, lw=1.2, label="Actual mean ± SD (10 groups)")
a.set(xlim=(0, xs.max()), ylim=(-700, 2900), xlabel="Model-predicted mean spend μ", ylabel="Actual two-year spend",
      title="A  Same fitted mean, two assumptions about the spread")
a.legend(loc="upper left", fontsize=7.6)

# B: spread vs mean: data, Gamma (proportional), Normal (flat)
a = ax[1]
a.plot(emp.mean_y, emp.sd_y, "o", color="#1baf7a", ms=6, label="Actual SD in each group", zorder=5)
m = np.linspace(0, emp.mean_y.max() * 1.05, 200)
a.plot(m, cv * m, color=BLUE, lw=2, label="Gamma: SD ∝ mean")
a.axhline(sigma, color=ORANGE, lw=2, ls="--", label="Normal: SD constant")
pw = np.polyfit(np.log(emp.mean_y), np.log(emp.sd_y), 1)
a.plot(m[1:], np.exp(pw[1]) * m[1:] ** pw[0], color=GREY, lw=1.2, ls=":", label=f"Best fit: SD ∝ mean^{pw[0]:.2f}")
a.set(xlabel="Mean spend in group", ylabel="Standard deviation of spend", title="B  Spread grows with the mean", ylim=(0, 1100))
a.legend(loc="upper left", fontsize=7.6)

# C: implied distribution for a low and a high spender
a = ax[2]
for m0, c in [(150, "#555555"), (1000, "k")]:
    grid = np.linspace(-800, 3000, 800)
    near = y[(mu > m0 * .8) & (mu < m0 * 1.25)]
    a.hist(near, bins=np.arange(0, 2800, 60), density=True, color=c, alpha=.12)
    a.plot(grid, stats.gamma.pdf(grid, a=1 / phi, scale=m0 * phi), color=BLUE, lw=2 if m0 == 1000 else 1.4)
    a.plot(grid, stats.norm.pdf(grid, m0, sigma), color=ORANGE, lw=2 if m0 == 1000 else 1.4, ls="--")
    pk = m0 * (1 - phi)                                             # Gamma mode
    a.annotate(f"μ = {m0}", (pk, stats.gamma.pdf(pk, a=1 / phi, scale=m0 * phi)), xytext=(-8, 0) if m0 < 500 else (0, 8),
               textcoords="offset points", fontsize=8.5, color=INK2, ha="right" if m0 < 500 else "center", fontweight="bold")
a.axvspan(-800, 0, color=ORANGE, alpha=.07)
a.plot([], [], color=BLUE, lw=2, label="Gamma: skewed, wider when μ is larger")
a.plot([], [], color=ORANGE, lw=2, ls="--", label="Normal: symmetric, same width")
a.hist([], color="k", alpha=.15, label="Actual customers with μ near that value")
a.set(xlim=(-800, 2800), xlabel="Two-year spend", ylabel="Density", title="C  What each model expects for one customer")
a.legend(loc="upper right", fontsize=7.6)

fig_.suptitle(f"Why Gamma rather than ordinary regression (final Q1 model, n = {len(df)}; Gamma φ = {phi:.2f}, Normal σ = {sigma:.0f})", fontsize=10.5)
plt.tight_layout(); plt.savefig(FIG / "q1d_gamma_vs_normal.png", dpi=150); plt.close()
lin = smf.ols("TotalSpend ~ " + RHS, df).fit()
summary = (f"Gamma dispersion phi = {phi:.3f} (SD = {cv:.2f} x mean); Normal residual SD = {sigma:.1f}\n"
           f"Across deciles of fitted mean: SD of spend grows as mean^{pw[0]:.2f} (variance ~ mean^{2 * pw[0]:.2f}; Normal assumes 0, Gamma 2)\n"
           f"Ordinary regression on raw spend: {100 * np.mean(lin.fittedvalues < 0):.1f}% of fitted values negative (min {lin.fittedvalues.min():.0f})\n")
(OUT / "q1d_gamma_vs_normal.txt").write_text(summary); print(summary)
