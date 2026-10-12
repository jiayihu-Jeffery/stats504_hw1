"""Q1 (continued): which response distribution suits spend best? Compare Gamma, lognormal and inverse-Gaussian
models with the SAME mean structure (B-spline in log income + household covariates) by AIC on the original spend scale."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy.stats import skew
from clean import load
from paths import out
from tee import tee_to
OUT = out("q1"); tee_to(OUT / "q1b_distribution_check.txt")

df = load(); df["logInc"] = np.log(df.Income); df["Age10"] = df.Age / 10; y = df.TotalSpend.values
RHS = ("bs(logInc, df=4) + Kidhome + Teenhome + Age10 + C(Edu, Treatment('Graduation')) + C(Marital) + TenureMonths")
print(f"n = {len(df)}; spend min = {y.min()}, median = {np.median(y):.0f}, mean = {y.mean():.0f}, skewness = {skew(y):.2f}")

o = smf.ols("np.log(TotalSpend) ~ " + RHS, df).fit()
st = o.params.copy(); st["Intercept"] += np.log(np.mean(np.exp(o.resid)))
def glm(fam):
    m = smf.glm("TotalSpend ~ " + RHS, df, family=fam)
    return m.fit(start_params=st.values, method="newton", maxiter=500)
gam = glm(sm.families.Gamma(sm.families.links.Log()))
ig = glm(sm.families.InverseGaussian(sm.families.links.Log()))
k = len(o.params) + 1                                  # mean parameters + one dispersion/variance parameter
ll_lognormal = o.llf - np.log(y).sum()                 # log-likelihood of spend (Jacobian of the log transform)
res = pd.DataFrame([
    dict(distribution="Gamma (log link)", loglik=gam.llf, AIC=-2 * gam.llf + 2 * k),
    dict(distribution="Lognormal (log-OLS)", loglik=ll_lognormal, AIC=-2 * ll_lognormal + 2 * k),
    dict(distribution="Inverse Gaussian (log link)", loglik=ig.llf, AIC=-2 * ig.llf + 2 * k)])
res["delta_AIC_vs_best"] = res.AIC - res.AIC.min()
res = res.sort_values("AIC"); res.round(1).to_csv(OUT / "q1b_distribution_check.csv", index=False)
print("Same mean structure; AIC on the spend scale (lower = better):"); print(res.round(1).to_string(index=False))
