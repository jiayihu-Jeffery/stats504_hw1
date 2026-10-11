"""Q1: demographic & household characteristics associated with total spending."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import itertools, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load
from paths import out, fig
OUT = out("q1"); FIG = fig("q1")
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)

df = load()
N = len(df)
rep = [f"Q1 — primary sample n = {N}"]

# ---------- 1. descriptives ----------
rows = []
for g in ["IncomeQ", "Kidhome", "Teenhome", "Children", "Edu", "Marital"]:
    for lev, s in df.groupby(g, observed=True).TotalSpend:
        rows.append(dict(variable=g, level=str(lev), n=len(s), median=s.median(), mean=s.mean(),
                         q25=s.quantile(.25), q75=s.quantile(.75)))
desc = pd.DataFrame(rows).round(1)
desc.to_csv(OUT / "q1_descriptives.csv", index=False)
rep += ["\n[1] TotalSpend by group", desc.to_string(index=False)]

fig, ax = plt.subplots(1, 3, figsize=(15, 4.3))
for a, g, t in [(ax[0], "IncomeQ", "Income quartile"), (ax[1], "Kidhome", "Children aged <13 at home (Kidhome)"),
                (ax[2], "Teenhome", "Teenagers at home (Teenhome)")]:
    levels = sorted(df[g].dropna().unique(), key=str) if g != "IncomeQ" else list(df[g].cat.categories)
    a.boxplot([df.loc[df[g] == l, "TotalSpend"] for l in levels], labels=[str(l) for l in levels], showfliers=False)
    a.set(title=t, ylabel="Total spend, last 2 years (currency unconfirmed)")
fig.suptitle(f"Total spend by household characteristics (n = {N}; outliers hidden)")
plt.tight_layout(); plt.savefig(FIG / "q1_spend_boxplots.png", dpi=140); plt.close()

# ---------- 2-4. models ----------
df["logInc"] = np.log(df.Income); df["logSpend"] = np.log(df.TotalSpend); df["Age10"] = df.Age / 10
RHS = "logInc + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths"
FAM = sm.families.Gamma(sm.families.links.Log())

def fit_gamma(rhs, d, cov_type="HC3"):
    """Gamma GLM (log link). Default IRLS can stop at a poor solution here, so start Newton from the
    smearing-adjusted log-OLS fit and keep whichever solution has the lower deviance."""
    d = d.assign(_ly=np.log(d.TotalSpend))
    o = smf.ols("_ly ~ " + rhs, d).fit()
    st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
    mod = smf.glm("TotalSpend ~ " + rhs, d, family=FAM)
    cands = [mod.fit(start_params=st.values, method="newton", maxiter=500, cov_type=cov_type)]
    try: cands.append(mod.fit(cov_type=cov_type))
    except Exception: pass
    return min(cands, key=lambda m: m.deviance)

gam = fit_gamma(RHS, df)
ols = smf.ols("logSpend ~ " + RHS, df).fit(cov_type="HC3")

def pct_table(m, label):
    ci = m.conf_int(); t = pd.DataFrame({"coef": m.params, "lo": ci[0], "hi": ci[1], "p": m.pvalues}).drop("Intercept")
    # log(Income): express as % difference for 10% higher income
    scale = pd.Series(1.0, index=t.index); scale["logInc"] = np.log(1.10)
    for c in ["coef", "lo", "hi"]:
        t[c + "_pct"] = (np.exp(t[c] * scale) - 1) * 100
    t["model"] = label
    return t

def nice(name):
    return (name.replace("C(Edu, Treatment('Graduation'))[T.", "Education: ").replace("C(Marital)[T.", "Marital: ")
                .replace("]", " (vs Graduation)" if "Edu" in name else " (vs Partnered)")
                .replace("logInc", "Income +10%").replace("Age10", "Age +10 yrs").replace("TenureMonths", "Tenure +1 month"))

tg, to = pct_table(gam, "Gamma GLM"), pct_table(ols, "log-OLS")
adj = pd.DataFrame({"term": [nice(i) for i in tg.index],
                    "gamma_pct": tg.coef_pct, "gamma_lo": tg.lo_pct, "gamma_hi": tg.hi_pct, "gamma_p": tg.p,
                    "logols_pct": to.coef_pct, "logols_lo": to.lo_pct, "logols_hi": to.hi_pct, "logols_p": to.p}).round(3)

# unadjusted (single-predictor Gamma GLMs) for the same terms
unadj = []
for var, f in [("logInc", "logInc"), ("Kidhome", "Kidhome"), ("Teenhome", "Teenhome"), ("Age10", "Age10"),
               ("Edu", "C(Edu, Treatment('Graduation'))"), ("Marital", "C(Marital)"), ("TenureMonths", "TenureMonths")]:
    t = pct_table(fit_gamma(f, df), "unadj"); unadj.append(t)
un = pd.concat(unadj); un.index = [nice(i) for i in un.index]
for c in ["coef", "lo", "hi"]:
    adj["unadj_" + {"coef": "pct", "lo": "lo", "hi": "hi"}[c]] = adj.term.map(un[c + "_pct"]).round(1)
adj.to_csv(OUT / "q1_effects.csv", index=False)
rep += ["\n[2-5] % difference in MEAN spend (Gamma) / GEOMETRIC-MEAN spend (log-OLS), 95% CI, HC3 SEs. Income term = effect of 10% higher income. unadj = single-predictor Gamma GLM.",
        adj[["term", "unadj_pct", "unadj_lo", "unadj_hi", "gamma_pct", "gamma_lo", "gamma_hi", "gamma_p",
             "logols_pct", "logols_lo", "logols_hi", "logols_p"]].round(1).to_string(index=False),
        f"\nGamma GLM: deviance-based pseudo-R2 = {1 - gam.deviance / gam.null_deviance:.3f}; log-OLS R2 = {ols.rsquared:.3f}",
        f"log(Income) coefficient (elasticity): Gamma {gam.params.logInc:.3f}; log-OLS {ols.params.logInc:.3f}"]

# spline-in-income Gamma GLM (functional-form check; household coefficients reported alongside)
RHS_SPL = "bs(logInc, df=4) + " + RHS.replace("logInc + ", "")
gspl = fit_gamma(RHS_SPL, df)
tsp = pct_table(gspl, "Gamma spline")
adj["gspline_pct"] = adj.term.map(pd.Series(tsp.coef_pct.values, index=[nice(i) for i in tsp.index])).round(1)
adj["gspline_lo"] = adj.term.map(pd.Series(tsp.lo_pct.values, index=[nice(i) for i in tsp.index])).round(1)
adj["gspline_hi"] = adj.term.map(pd.Series(tsp.hi_pct.values, index=[nice(i) for i in tsp.index])).round(1)
adj.to_csv(OUT / "q1_effects.csv", index=False)
rep += ["\nGamma GLM with B-spline (df=4) in log(Income): household/demographic % effects (95% CI)",
        adj.loc[~adj.term.str.startswith("Income"), ["term", "gspline_pct", "gspline_lo", "gspline_hi"]].to_string(index=False),
        f"Gamma spline pseudo-R2 = {1 - gspl.deviance / gspl.null_deviance:.3f}"]

u_teen = smf.ols("np.log(TotalSpend) ~ Teenhome", df).fit(cov_type="HC3")
rep += [f"Unadjusted log-OLS Teenhome: {100*(np.exp(u_teen.params.Teenhome)-1):.1f}% (p = {u_teen.pvalues.Teenhome:.3f}) "
        "-> on the geometric-mean scale the unadjusted teen association is ~0; on the mean scale (Gamma) it is negative."]

# ---------- 6. Shapley R2 (dominance) on log-OLS ----------
groups = {"Income": "logInc", "Kidhome": "Kidhome", "Teenhome": "Teenhome", "Age": "Age10",
          "Education": "C(Edu)", "Marital": "C(Marital)", "Tenure": "TenureMonths"}
names = list(groups); cache = {}
def r2(S):
    S = tuple(sorted(S))
    if S not in cache:
        cache[S] = 0.0 if not S else smf.ols("logSpend ~ " + " + ".join(groups[s] for s in S), df).fit().rsquared
    return cache[S]
from math import factorial
k = len(names); shap = {}
for v in names:
    others = [n for n in names if n != v]; tot = 0
    for r in range(k):
        for S in itertools.combinations(others, r):
            w = factorial(r) * factorial(k - r - 1) / factorial(k)
            tot += w * (r2(S + (v,)) - r2(S))
    shap[v] = tot
sh = pd.Series(shap).sort_values(ascending=False)
shdf = pd.DataFrame({"shapley_R2": sh.round(4), "share_of_R2_pct": (100 * sh / sh.sum()).round(1)})
shdf.to_csv(OUT / "q1_shapley_r2.csv")
rep += [f"\n[6] Shapley R2 decomposition (log-OLS, total R2 = {sh.sum():.3f})", shdf.to_string()]

fig, a = plt.subplots(figsize=(7, 3.8))
a.barh(sh.index[::-1], 100 * sh.values[::-1] / sh.sum(), color="#3B6EA5")
a.set(xlabel="Share of explained variance in log(spend), %", title=f"Relative importance (Shapley R², total R² = {sh.sum():.2f}; n = {N})")
plt.tight_layout(); plt.savefig(FIG / "q1_shapley.png", dpi=140); plt.close()

# ---------- 7. diagnostics ----------
fam = sm.families.Gamma(sm.families.links.Log())
gam_nr = fit_gamma(RHS, df, cov_type="nonrobust")
spl = fit_gamma(RHS_SPL, df, cov_type="nonrobust")
df["logInc_c"] = df.logInc - df.logInc.mean()  # centred for numerical stability of the interaction fit
inter = fit_gamma(RHS.replace("logInc", "logInc_c") + " + logInc_c:Kidhome", df)
X = df[["logInc", "Kidhome", "Teenhome", "Age10", "TenureMonths"]].copy()
for lev in ["Basic", "Master", "PhD"]: X["Edu_" + lev] = (df.Edu == lev).astype(float)   # reference = Graduation
X["Marital_Single"] = (df.Marital == "Single").astype(float)
X = sm.add_constant(X)
vif = pd.Series([variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])], index=X.columns[1:]).round(2)
rep += ["\n[7] Diagnostics",
        f"Income spline (B-spline df=4) vs linear log(Income), Gamma deviance: {spl.deviance:.1f} vs {gam_nr.deviance:.1f}; "
        f"AIC {spl.aic:.1f} vs {gam_nr.aic:.1f}",
        f"Income x Kidhome interaction: coef = {inter.params['logInc_c:Kidhome']:.3f}, p = {inter.pvalues['logInc_c:Kidhome']:.4f}",
        "VIF:", vif.to_string()]
# spline shape: predicted spend over income grid at reference covariates
grid = pd.DataFrame({"Income": np.linspace(df.Income.quantile(.01), df.Income.quantile(.99), 100)})
grid["logInc"] = np.log(grid.Income)
for c, v in [("Kidhome", 0), ("Teenhome", 0), ("Age10", df.Age10.median()), ("Edu", "Graduation"),
             ("Marital", "Partnered"), ("TenureMonths", df.TenureMonths.median())]:
    grid[c] = v
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
ax[0].plot(grid.Income / 1000, spl.predict(grid), label="spline in log(Income)")
ax[0].plot(grid.Income / 1000, gam_nr.predict(grid), "--", label="linear in log(Income)")
ax[0].set(xlabel="Income ($k, currency unconfirmed)", ylabel="Predicted total spend",
          title="Income shape (no children, median age/tenure)"); ax[0].legend()
ax[1].scatter(np.log(gam_nr.fittedvalues), gam_nr.resid_deviance, s=4, alpha=.4)
ax[1].axhline(0, c="k", lw=.8); ax[1].set(xlabel="log fitted spend", ylabel="Deviance residual", title="Gamma GLM residuals")
ax[2].scatter(ols.fittedvalues, ols.resid, s=4, alpha=.4); ax[2].axhline(0, c="k", lw=.8)
ax[2].set(xlabel="Fitted log(spend)", ylabel="Residual", title="log-OLS residuals")
fig.suptitle(f"Q1 diagnostics (n = {N})"); plt.tight_layout(); plt.savefig(FIG / "q1_diagnostics.png", dpi=140); plt.close()

# ---------- 8. concentration ----------
s = df.TotalSpend.sort_values(ascending=False)
top20 = s.iloc[: int(round(.2 * N))].sum() / s.sum()
rep += [f"\n[8] Spend concentration: top 20% of customers account for {100 * top20:.1f}% of total spend; "
        f"top 10%: {100 * s.iloc[: int(round(.1 * N))].sum() / s.sum():.1f}%"]

# ---------- sensitivity: headline coefficients ----------
sens = []
for label, kw in [("primary (dedup)", {}), ("not deduplicated", dict(dedup=False)), ("dedup, flagged dropped", dict(drop_flagged=True))]:
    d = load(**kw); d["logInc"] = np.log(d.Income); d["Age10"] = d.Age / 10
    t = pct_table(fit_gamma(RHS, d), label); ts = pct_table(fit_gamma(RHS_SPL, d), label)
    o = pct_table(smf.ols("np.log(TotalSpend) ~ " + RHS, d).fit(cov_type="HC3"), label)
    row = {"sample": label, "n": len(d)}
    for i in ["logInc", "Kidhome", "Teenhome", "TenureMonths"]:
        row["Gamma: " + nice(i)] = round(t.loc[i, "coef_pct"], 1)
        row["logOLS: " + nice(i)] = round(o.loc[i, "coef_pct"], 1)
    for i in ["Kidhome", "Teenhome"]:
        row["GammaSpline: " + nice(i)] = round(ts.loc[i, "coef_pct"], 1)
    sens.append(row)
sens = pd.DataFrame(sens).set_index("sample").T; sens.to_csv(OUT / "q1_sensitivity.csv")
rep += ["\n[S] Sensitivity — Gamma GLM % effects", sens.to_string()]

txt = "\n".join(rep); print(txt); (OUT / "q1_results.txt").write_text(txt + "\n")
