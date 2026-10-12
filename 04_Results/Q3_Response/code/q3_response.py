"""Q3: characteristics and behaviours associated with accepting the last campaign (Response)."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load, SEED, T0_NUM, T1_NO_RECENCY, T2
from paths import out, fig
OUT = out("q3"); FIG = fig("q3")
pd.set_option("display.width", 220)

def prep(d):
    d = d.copy()
    for lev in ["Basic", "Master", "PhD"]: d["Edu_" + lev] = (d.Edu == lev).astype(int)   # ref = Graduation
    d["Single"] = (d.Marital == "Single").astype(int)
    return d
T0 = T0_NUM + ["Edu_Basic", "Edu_Master", "Edu_PhD", "Single"]
SETS = {"T0 (demographics/tenure)": T0,
        "Scenario A (T0+T1 w/o Recency+T2)": T0 + T1_NO_RECENCY + T2,
        "Scenario B (all, incl. Recency)": T0 + T1_NO_RECENCY + T2 + ["Recency"]}
MODELS = {"logit_L2": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000)),
          "grad_boost": lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300,
                                                               l2_regularization=1.0, random_state=SEED)}

df = prep(load()); N = len(df); y = df.Response.values; base = y.mean()
seg = pd.read_csv(out("q2") / "q2_segment_assignments.csv"); df = df.merge(seg, on="ID", how="left")
rep = [f"Q3 — primary sample n = {N}; Response rate = {base:.4f} ({y.sum()} acceptors)"]

# ---------- descriptive rates with Wilson CIs ----------
df["RecencyBin"] = pd.cut(df.Recency, [-1, 24, 49, 74, 99], labels=["0-24", "25-49", "50-74", "75-99"])
df["TenureTertile"] = pd.qcut(df.TenureMonths, 3, labels=["newest", "middle", "longest"])
df["PrevAcc"] = df.PrevAccepted.clip(upper=3).map({0: "0", 1: "1", 2: "2", 3: "3+"})
rows = []
for g in ["IncomeQ", "Children", "Kidhome", "Teenhome", "Edu", "Marital", "PrevAcc", "SpendTier",
          "Segment", "TenureTertile", "RecencyBin"]:
    for lev, s in df.groupby(g, observed=True).Response:
        lo, hi = proportion_confint(s.sum(), len(s), method="wilson")
        rows.append(dict(variable=g, level=str(lev), n=len(s), acceptors=int(s.sum()), rate=s.mean(), lo=lo, hi=hi))
rates = pd.DataFrame(rows); rates.to_csv(OUT / "q3_rates.csv", index=False)
rep += ["\n[1] Response rate by group (Wilson 95% CI)", rates.round(3).to_string(index=False)]

fig, ax = plt.subplots(2, 3, figsize=(15, 7.5)); ax = ax.ravel()
for a, g, t in zip(ax, ["PrevAcc", "IncomeQ", "Children", "TenureTertile", "Segment", "RecencyBin"],
                   ["Prior campaigns accepted (1-5)", "Income quartile", "Children + teens at home",
                    "Tenure tertile", "Q2 style segment", "Recency, days (Scenario B only)"]):
    r = rates[rates.variable == g]
    a.bar(r.level, r.rate, yerr=[r.rate - r.lo, r.hi - r.rate], capsize=3, color="#3B6EA5" if g != "RecencyBin" else "#999999")
    a.axhline(base, ls="--", c="k", lw=.8); a.set(title=t, ylabel="Acceptance rate, last campaign")
    for x, (n_, v) in enumerate(zip(r.n, r.rate)): a.text(x, 0.01, f"n={n_}", ha="center", fontsize=7, color="white")
fig.suptitle(f"Acceptance of last campaign by group (n = {N}; dashed = overall {base:.1%}; bars = Wilson 95% CI)")
plt.tight_layout(); plt.savefig(FIG / "q3_rates.png", dpi=140); plt.close()

# ---------- explanatory logistic regressions ----------
df["logInc"] = np.log(df.Income); df["logSpend"] = np.log(df.TotalSpend); df["Age10"] = df.Age / 10
df["Recency10"] = df.Recency / 10
fA = ("Response ~ logInc + Age10 + Kidhome + Teenhome + TenureMonths + C(Edu, Treatment('Graduation')) "
      "+ C(Marital) + logSpend + PrevAccepted")
out = []
fA0 = fA.replace(" + logSpend", "")   # sensitivity: drop spend (a possibly campaign-affected T1 variable)
for lab, f in [("A", fA), ("B", fA + " + Recency10"), ("A0_no_spend", fA0)]:
    m = smf.logit(f, df).fit(disp=0, cov_type="HC1")
    if lab == "A":   # full coefficient table (log-odds scale) of the explanatory model
        pd.DataFrame({"coef": m.params, "se": m.bse, "z": m.tvalues, "p": m.pvalues}).round(4).to_csv(OUT / "q3_logit_A_coefficients.csv")
    me = m.get_margeff(at="overall").summary_frame()
    ci = m.conf_int()
    t = pd.DataFrame({"OR": np.exp(m.params), "OR_lo": np.exp(ci[0]), "OR_hi": np.exp(ci[1]), "p": m.pvalues}).drop("Intercept")
    t["AME_pp"] = 100 * me["dy/dx"]; t["AME_lo"] = 100 * me["Conf. Int. Low"]; t["AME_hi"] = 100 * me["Cont. Int. Hi."]
    t["model"] = lab; out.append(t)
    rep += [f"\n[2] Explanatory logit, model {lab} (HC1 SEs; pseudo-R2 = {m.prsquared:.3f}; n = {int(m.nobs)}). "
            "Units: logInc/logSpend per 1 log-unit (~2.7x); Age per 10y; Tenure per month; Recency per 10 days; AME in percentage points",
            t.drop(columns="model").round(3).to_string()]
pd.concat(out).round(4).to_csv(OUT / "q3_logit_explanatory.csv")
# vif check for logInc vs logSpend
rep += [f"corr(logInc, logSpend) = {df.logInc.corr(df.logSpend):.3f}"]

# ---------- predictive models ----------
def run_cv(d, feats, mk, n_rep=5, seed=SEED):
    yy = d.Response.values; X = d[feats].values
    rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=n_rep, random_state=seed)
    oof = np.zeros((n_rep, len(d))); aucs, aps = [], []
    for i, (tr, te) in enumerate(rskf.split(X, yy)):
        m = mk().fit(X[tr], yy[tr]); p = m.predict_proba(X[te])[:, 1]
        oof[i // 5, te] = p; aucs.append(roc_auc_score(yy[te], p)); aps.append(average_precision_score(yy[te], p))
    return oof.mean(0), np.array(aucs), np.array(aps)

def topk(yy, p, frac):
    k = int(round(frac * len(yy))); idx = np.argsort(-p)[:k]; return yy[idx].mean()

def run_cv_formula(d, f, n_rep=5, seed=SEED):
    yy = d.Response.values; oof = np.zeros((n_rep, len(d))); aucs, aps = [], []
    for i, (tr, te) in enumerate(RepeatedStratifiedKFold(n_splits=5, n_repeats=n_rep, random_state=seed).split(d, yy)):
        m = smf.logit(f, d.iloc[tr]).fit(disp=0); p = m.predict(d.iloc[te]).values
        oof[i // 5, te] = p; aucs.append(roc_auc_score(yy[te], p)); aps.append(average_precision_score(yy[te], p))
    return oof.mean(0), np.array(aucs), np.array(aps)

rng = np.random.default_rng(SEED)
res, oofs = [], {}
# explanatory logits (pre-specified 11 terms; B adds recency) scored out-of-fold: model A is carried to Q4
EXPL = {"Explanatory logit A (11 terms)": fA, "Explanatory logit B (+Recency)": fA + " + Recency10"}
for ename, f in EXPL.items():
    p, aucs, aps = run_cv_formula(df, f)
    oofs[(ename, "logit")] = p; top = topk(y, p, .1); bs = []
    for _ in range(1000):
        ix = rng.integers(0, N, N); bs.append(topk(y[ix], p[ix], .1) / y[ix].mean())
    res.append(dict(features=ename, model="logit (unpenalised)", n_features=11 + ("Recency" in ename),
                    AUC_mean=aucs.mean(), AUC_sd=aucs.std(), PRAUC_mean=aps.mean(), PRAUC_sd=aps.std(),
                    top10_rate=top, top10_lift=top / base, lift_lo=np.percentile(bs, 2.5), lift_hi=np.percentile(bs, 97.5)))
for sname, feats in SETS.items():
    for mname, mk in MODELS.items():
        p, aucs, aps = run_cv(df, feats, mk)
        oofs[(sname, mname)] = p
        top = topk(y, p, .1)
        bs = []
        for _ in range(1000):
            ix = rng.integers(0, N, N); bs.append(topk(y[ix], p[ix], .1) / y[ix].mean())
        res.append(dict(features=sname, model=mname, n_features=len(feats),
                        AUC_mean=aucs.mean(), AUC_sd=aucs.std(), PRAUC_mean=aps.mean(), PRAUC_sd=aps.std(),
                        top10_rate=top, top10_lift=top / base, lift_lo=np.percentile(bs, 2.5), lift_hi=np.percentile(bs, 97.5)))
res = pd.DataFrame(res); res.to_csv(OUT / "q3_model_performance.csv", index=False)
rep += [f"\n[3] Predictive performance, 5x5 repeated stratified CV (base rate {base:.3f}). "
        "Top-10% metrics use repeat-averaged out-of-fold scores; lift CI = 1000 bootstrap resamples.",
        res.round(3).to_string(index=False)]

# choose model for Q4: logistic unless boosting beats it by > 0.01 AUC (Scenario A)
A = "Scenario A (T0+T1 w/o Recency+T2)"
ra = res[res.features == A].set_index("model")
chosen = "grad_boost" if ra.loc["grad_boost", "AUC_mean"] - ra.loc["logit_L2", "AUC_mean"] > 0.01 else "logit_L2"
EA = "Explanatory logit A (11 terms)"
rep += [f"Best larger model (Scenario A): {chosen}, AUC {ra.loc[chosen, 'AUC_mean']:.3f} vs explanatory logit A "
        f"{res.loc[res.features == EA, 'AUC_mean'].iloc[0]:.3f}. Model carried to Q4: explanatory logit A "
        "(one transparent model for explanation and targeting; the larger models rank only slightly better)."]
o = pd.DataFrame({"ID": df.ID, "Response": y})
for (s, m), p in oofs.items():
    if s.startswith("Explanatory"): o["p_expl_" + ("A" if " A " in s else "B")] = p; continue
    o[f"p_{'T0' if s.startswith('T0') else s.split()[1]}_{m}"] = p
o["p_Q4"] = oofs[(EA, "logit")]
o.to_csv(OUT / "q3_oof_predictions.csv", index=False)
# FINAL SCORING MODEL refit on all customers (the version that would score future customers):
# standardized L2-logistic coefficients; the model's input is (x - feature_mean) / feature_sd
pipe = MODELS["logit_L2"]().fit(df[SETS[A]].values, y)
coefA = pd.DataFrame({"feature": ["(intercept)"] + SETS[A], "std_coef": [pipe[-1].intercept_[0]] + list(pipe[-1].coef_[0]),
                      "feature_mean": [np.nan] + list(pipe[0].mean_), "feature_sd": [np.nan] + list(pipe[0].scale_)})
coefA["abs"] = coefA.std_coef.abs(); coefA.loc[0, "abs"] = np.inf
coefA = coefA.sort_values("abs", ascending=False).drop(columns="abs")
coefA.round(4).to_csv(OUT / "q3_scoring_model_coefficients.csv", index=False)
rep += ["\nFINAL SCORING MODEL (Scenario A, L2 logistic, C=1, standardized inputs) refit on all customers:", coefA.round(3).to_string(index=False)]

# calibration + gains
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
for (s, m), p in oofs.items():
    if s.startswith("Explanatory"):
        if s != EA: continue
    elif m != chosen and not s.startswith("Scenario A"): continue
    lab = f"{'T0' if s.startswith('T0') else s.split()[0] + ' ' + s.split()[1]}, {m}"
    fr, mp = calibration_curve(y, p, n_bins=10, strategy="quantile")
    ax[0].plot(mp, fr, "o-", ms=3, label=lab)
    order = np.argsort(-p); cum = np.cumsum(y[order]) / y.sum()
    ax[1].plot(np.arange(1, N + 1) / N, cum, label=lab)
ax[0].plot([0, 1], [0, 1], "k--", lw=.8); ax[0].set(xlabel="Mean predicted probability (decile)", ylabel="Observed acceptance rate", title="Calibration (out-of-fold)")
ax[1].plot([0, 1], [0, 1], "k--", lw=.8, label="random targeting")
ax[1].set(xlabel="Share of customers contacted (ranked by score)", ylabel="Share of all acceptors reached", title="Cumulative gains (out-of-fold)")
for a in ax: a.legend(fontsize=7)
fig.suptitle(f"Q3 predictive models (n = {N}, {y.sum()} acceptors)"); plt.tight_layout()
plt.savefig(FIG / "q3_calibration_gains.png", dpi=140); plt.close()

# permutation importance (Scenario A, both models, repeat-1 folds)
feats = SETS[A]; X = df[feats].values
imp = {m: np.zeros(len(feats)) for m in MODELS}
from sklearn.model_selection import StratifiedKFold
for tr, te in StratifiedKFold(5, shuffle=True, random_state=SEED).split(X, y):
    for m, mk in MODELS.items():
        mod = mk().fit(X[tr], y[tr])
        imp[m] += permutation_importance(mod, X[te], y[te], scoring="roc_auc", n_repeats=10, random_state=SEED).importances_mean / 5
imp = pd.DataFrame(imp, index=feats).sort_values("logit_L2", ascending=False)
imp.round(4).to_csv(OUT / "q3_permutation_importance.csv")
rep += ["\n[4] Permutation importance (drop in AUC when feature shuffled), Scenario A", imp.round(4).to_string()]
fig, a = plt.subplots(figsize=(8, 6))
top = imp.head(12)[::-1]; yy_ = np.arange(len(top))
a.barh(yy_ - .2, top.logit_L2, .4, label="logistic (L2)"); a.barh(yy_ + .2, top.grad_boost, .4, label="gradient boosting")
a.set_yticks(yy_); a.set_yticklabels(top.index); a.set(xlabel="Mean drop in out-of-fold AUC", title=f"Permutation importance, Scenario A (n = {N})")
a.legend(); plt.tight_layout(); plt.savefig(FIG / "q3_permutation_importance.png", dpi=140); plt.close()

# ---------- sensitivity ----------
sens = []
for lab, kw in [("primary (dedup)", {}), ("not deduplicated", dict(dedup=False)), ("dedup, flagged dropped", dict(drop_flagged=True))]:
    d = prep(load(**kw))
    dd = d.assign(logInc=np.log(d.Income), logSpend=np.log(d.TotalSpend), Age10=d.Age / 10)
    p, aucs, aps = run_cv_formula(dd, fA)
    sens.append(dict(sample=lab, n=len(d), model="explanatory logit A (CV)", AUC=aucs.mean(), PRAUC=aps.mean(),
                     top10_lift=topk(d.Response.values, p, .1) / d.Response.mean()))
    for m, mk in MODELS.items():
        p, aucs, aps = run_cv(d, SETS[A], mk, n_rep=5)
        yy = d.Response.values
        sens.append(dict(sample=lab, n=len(d), model=m, AUC=aucs.mean(), PRAUC=aps.mean(), top10_lift=topk(yy, p, .1) / yy.mean()))
    mm = smf.logit(fA, d.assign(logInc=np.log(d.Income), logSpend=np.log(d.TotalSpend), Age10=d.Age / 10)).fit(disp=0)
    sens.append(dict(sample=lab, n=len(d), model="explanatory logit A (odds ratios)",
                     **{f"OR_{v}": np.exp(mm.params[v]) for v in ["PrevAccepted", "Kidhome", "Teenhome", "TenureMonths",
                                                                   "logSpend", "C(Marital)[T.Single]", "C(Edu, Treatment('Graduation'))[T.PhD]"]}))
sens = pd.DataFrame(sens); sens.to_csv(OUT / "q3_sensitivity.csv", index=False)
rep += ["\n[S] Sensitivity — Scenario A predictive performance and explanatory ORs (model A)", sens.round(3).to_string(index=False)]

txt = "\n".join(rep); print(txt); (OUT / "q3_results.txt").write_text(txt + "\n")
