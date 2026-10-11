"""Challenge: model fitting. (1) statsmodels' default IRLS stops at a poor Gamma-GLM solution for this data;
Newton started from the smearing-adjusted log-OLS fit reaches a much lower deviance. (2) A straight line in
log(income) misrepresents the S-shaped income effect; a B-spline fits far better."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from clean import load
from paths import out
from tee import tee_to
tee_to(out("challenges") / "gamma_fit_check.txt")

df = load(); df["logInc"] = np.log(df.Income); df["Age10"] = df.Age / 10
FAM = sm.families.Gamma(sm.families.links.Log())
RHS = "logInc + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths"
RHS_SPL = "bs(logInc, df=4) + " + RHS.replace("logInc + ", "")

def newton(rhs):
    o = smf.ols("np.log(TotalSpend) ~ " + rhs, df).fit()
    st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
    return smf.glm("TotalSpend ~ " + rhs, df, family=FAM).fit(start_params=st.values, method="newton", maxiter=500)

irls = smf.glm("TotalSpend ~ " + RHS, df, family=FAM).fit()
nw = newton(RHS); spl = newton(RHS_SPL)
rows = [dict(fit="linear log(income), default IRLS", deviance=irls.deviance, income_coef=irls.params.logInc, kidhome_pct=100 * (np.exp(irls.params.Kidhome) - 1)),
        dict(fit="linear log(income), Newton from OLS start", deviance=nw.deviance, income_coef=nw.params.logInc, kidhome_pct=100 * (np.exp(nw.params.Kidhome) - 1)),
        dict(fit="B-spline log(income), Newton from OLS start", deviance=spl.deviance, income_coef=np.nan, kidhome_pct=100 * (np.exp(spl.params.Kidhome) - 1))]
res = pd.DataFrame(rows); res.round(3).to_csv(out("challenges") / "gamma_fit_check.csv", index=False)
print(f"Gamma GLM (log link), n = {len(df)}; null deviance = {nw.null_deviance:.1f}")
print(res.round(3).to_string(index=False))
print("\nDefault IRLS gives a negative income elasticity and higher deviance -> rejected. Spline cuts deviance further and"
      " shrinks the young-children effect: the reported (recommended) estimate is the spline model's.")
