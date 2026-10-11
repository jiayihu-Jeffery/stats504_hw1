"""Shared scorecard helpers (used by q4b_followup.py and q4c_sensitivity.py)."""
import numpy as np, pandas as pd
import statsmodels.api as sm

def cats(d):
    c = pd.DataFrame(index=d.index)
    c["Earlier campaigns accepted"] = d.PrevAccepted.clip(upper=2).map({0: "0", 1: "1", 2: "2+"})
    c["Months since joining"] = d.TenureBand.astype(str)
    c["Teenagers at home"] = np.where(d.Teenhome > 0, "1+", "0")
    c["Young children at home"] = np.where(d.Kidhome > 0, "1+", "0")
    c["Marital status"] = d.Marital
    c["Education"] = np.where(d.Edu == "PhD", "PhD", "Other")
    c["2-yr spend tier"] = d.SpendTier.astype(str)
    c["Income quartile"] = d.IncomeQ.astype(str)
    return c
# Young-children item dropped from Scorecard A: its points were positive only because spend is in the card
# (a conditional effect that is confusing in a field tool); dropping it changed CV AUC 0.837 -> 0.831, top-20% capture 59.3% -> 59.9%.
CARDS = {"Scorecard A (existing customers)": ["Earlier campaigns accepted", "Months since joining", "Teenagers at home",
                                              "Marital status", "Education", "2-yr spend tier"],
         "Scorecard N (new customers: no history needed)": ["Months since joining", "Teenagers at home", "Young children at home",
                                                            "Marital status", "Education", "Income quartile"]}

def fit_card(Cd, yd, vars_, scale=10):
    X = pd.get_dummies(Cd[vars_], prefix_sep="=", dtype=float)
    # drop one level per variable (reference) to avoid collinearity
    drop = [X.filter(like=v + "=").columns[0] for v in vars_]
    m = sm.Logit(yd, sm.add_constant(X.drop(columns=drop))).fit(disp=0, method="bfgs", maxiter=2000)
    pts = {}
    for v in vars_:
        levels = sorted(Cd[v].unique())
        b = {l: (0.0 if f"{v}={l}" in drop else m.params.get(f"{v}={l}", 0.0)) for l in levels}
        mn = min(b.values())
        for l in levels: pts[(v, l)] = int(round(scale * (b[l] - mn)))
    return pts

def score(Cd, pts, vars_):
    return sum(Cd[v].map({l: p for (vv, l), p in pts.items() if vv == v}).fillna(0) for v in vars_)

def capture(yv, s, frac, rng):
    # contact top frac by score; random tie-break
    k = int(round(frac * len(yv))); o = np.lexsort((rng.random(len(s)), -s))[:k]
    return yv[o].sum() / yv.sum(), yv[o].mean()

