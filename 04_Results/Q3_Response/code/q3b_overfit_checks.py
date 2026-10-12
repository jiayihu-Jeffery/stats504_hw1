"""Q3b: does the number of terms hurt the Q3 models (overfitting), and are coefficients muddled by overlap
(e.g. Master vs PhD)? Checks on the explanatory logit (model A) and on the L2 scoring model."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score
from clean import load, SEED, T0_NUM, T1_NO_RECENCY, T2
from paths import out
OUT = out("q3")
pd.set_option("display.width", 220)

df = load()
for lev in ["Basic", "Master", "PhD"]: df["Edu_" + lev] = (df.Edu == lev).astype(int)   # ref = Graduation
df["Single"] = (df.Marital == "Single").astype(int)
df["logInc"] = np.log(df.Income); df["logSpend"] = np.log(df.TotalSpend); df["Age10"] = df.Age / 10
y = df.Response.values
cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED)
splits = list(cv.split(df, y))
rep = [f"Q3b — overfitting and coefficient-overlap checks; n = {len(df)}, acceptors = {y.sum()}"]

# ---------- 1. explanatory logit: events per parameter, in-sample vs cross-validated AUC, nested models ----------
A_TERMS = ["logInc", "Age10", "Kidhome", "Teenhome", "TenureMonths", "Edu_Basic", "Edu_Master", "Edu_PhD", "Single",
           "logSpend", "PrevAccepted"]
NESTED = {"1 term: PrevAccepted": ["PrevAccepted"],
          "4 terms: + Single, Teens, Tenure": ["PrevAccepted", "Single", "Teenhome", "TenureMonths"],
          "7 terms: + PhD, Kids, logSpend": ["PrevAccepted", "Single", "Teenhome", "TenureMonths", "Edu_PhD", "Kidhome", "logSpend"],
          "11 terms: model A (reported)": A_TERMS}

def cv_auc_unpenalised(cols):
    aucs = []
    for tr, te in splits:
        m = smf.logit("Response ~ " + " + ".join(cols), df.iloc[tr]).fit(disp=0)
        aucs.append(roc_auc_score(y[te], m.predict(df.iloc[te])))
    return np.mean(aucs), np.std(aucs)

rows = []
for lab, cols in NESTED.items():
    m = smf.logit("Response ~ " + " + ".join(cols), df).fit(disp=0)
    a_cv, sd = cv_auc_unpenalised(cols)
    rows.append(dict(model=lab, params=len(cols) + 1, events_per_param=y.sum() / (len(cols) + 1),
                     AIC=m.aic, AUC_in_sample=roc_auc_score(y, m.predict(df)), AUC_cv=a_cv, AUC_cv_sd=sd))
nest = pd.DataFrame(rows); nest["optimism"] = nest.AUC_in_sample - nest.AUC_cv
nest.round(4).to_csv(OUT / "q3b_nested_models.csv", index=False)
rep += ["\n[1] Explanatory logit: nested models (unpenalised; 5x5 repeated stratified CV)", nest.round(3).to_string(index=False),
        "Rule of thumb: >= 10-20 events per parameter keeps logistic coefficients stable."]

# ---------- 2. overlap between predictors: VIF and correlations ----------
X = df[A_TERMS].assign(const=1.0)
vif = pd.Series([variance_inflation_factor(X.values, i) for i in range(len(A_TERMS))], index=A_TERMS, name="VIF")
vif.round(2).to_csv(OUT / "q3b_vif.csv")
rep += ["\n[2] Variance inflation factors, model A terms (5-10+ would signal problematic overlap)", vif.round(2).to_string()]
cor = df[["Edu_Master", "Edu_PhD", "Edu_Basic", "Age10", "logInc", "logSpend", "Single", "Kidhome", "Teenhome"]].corr().round(2)
rep += ["Correlations among education dummies and other terms", cor.loc[["Edu_Master", "Edu_PhD"]].to_string()]

# ---------- 3. Master vs PhD: raw rates, test of equal effects, merged model, bootstrap ----------
raw = df.groupby("Edu").Response.agg(["size", "mean"]).rename(columns={"size": "n", "mean": "rate"})
full = smf.logit("Response ~ " + " + ".join(A_TERMS), df).fit(disp=0, cov_type="HC1")
wald = full.t_test("Edu_PhD - Edu_Master = 0")
df["Edu_Postgrad"] = df.Edu_Master + df.Edu_PhD
merged_terms = [t for t in A_TERMS if t not in ("Edu_Master", "Edu_PhD")] + ["Edu_Postgrad"]
merged = smf.logit("Response ~ " + " + ".join(merged_terms), df).fit(disp=0, cov_type="HC1")
full_nr = smf.logit("Response ~ " + " + ".join(A_TERMS), df).fit(disp=0)
merged_nr = smf.logit("Response ~ " + " + ".join(merged_terms), df).fit(disp=0)
lr = 2 * (full_nr.llf - merged_nr.llf)
from scipy.stats import chi2
noedu_terms = [t for t in A_TERMS if not t.startswith("Edu_")]
noedu = smf.logit("Response ~ " + " + ".join(noedu_terms), df).fit(disp=0)
rng = np.random.default_rng(SEED); bs = []
for b in range(500):
    idx = rng.integers(0, len(df), len(df))
    try:
        mb = smf.logit("Response ~ " + " + ".join(A_TERMS), df.iloc[idx]).fit(disp=0)
        bs.append(mb.params[["Edu_Master", "Edu_PhD"]].values)
    except Exception: pass
bs = np.exp(np.array(bs))
edu = pd.DataFrame({"OR": np.exp(full.params[["Edu_Basic", "Edu_Master", "Edu_PhD"]]),
                    "p": full.pvalues[["Edu_Basic", "Edu_Master", "Edu_PhD"]]})
rep += ["\n[3] Education: raw acceptance rates", raw.round(3).to_string(),
        "Model A odds ratios vs Graduation", edu.round(3).to_string(),
        f"Wald test PhD = Master (log-odds diff {wald.effect[0]:.3f}, HC1): p = {float(wald.pvalue):.4f}",
        f"Merged 'Postgrad' (Master+PhD) model: OR = {np.exp(merged.params['Edu_Postgrad']):.3f}; "
        f"LR test vs separate dummies: chi2 = {lr:.2f}, df = 1, p = {chi2.sf(lr, 1):.4f}; "
        f"AIC separate {full_nr.aic:.1f} vs merged {merged_nr.aic:.1f} vs no education {noedu.aic:.1f}",
        f"Bootstrap (500): OR Master median {np.median(bs[:, 0]):.2f} [{np.percentile(bs[:, 0], 2.5):.2f}, {np.percentile(bs[:, 0], 97.5):.2f}]; "
        f"OR PhD median {np.median(bs[:, 1]):.2f} [{np.percentile(bs[:, 1], 2.5):.2f}, {np.percentile(bs[:, 1], 97.5):.2f}]; "
        f"PhD > Master in {100 * np.mean(bs[:, 1] > bs[:, 0]):.0f}% of resamples; "
        f"bootstrap corr(log OR Master, log OR PhD) = {np.corrcoef(np.log(bs).T)[0, 1]:.2f}"]
pd.DataFrame([dict(wald_p=float(wald.pvalue), lr_chi2=lr, lr_p=chi2.sf(lr, 1), aic_separate=full_nr.aic, aic_merged=merged_nr.aic,
                   aic_no_edu=noedu.aic, or_postgrad=np.exp(merged.params["Edu_Postgrad"]),
                   pct_boot_phd_gt_master=100 * np.mean(bs[:, 1] > bs[:, 0]))]).round(4).to_csv(OUT / "q3b_education_checks.csv", index=False)

# ---------- 4. scoring model: does adding inputs or weakening the penalty hurt out-of-sample AUC? ----------
T0 = T0_NUM + ["Edu_Basic", "Edu_Master", "Edu_PhD", "Single"]
ALL = T0 + T1_NO_RECENCY + T2
def cv_auc(cols, C):
    aucs = []
    for tr, te in splits:
        m = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000)).fit(df.iloc[tr][cols], y[tr])
        aucs.append(roc_auc_score(y[te], m.predict_proba(df.iloc[te][cols])[:, 1]))
    return np.mean(aucs)
imp = pd.read_csv(OUT / "q3_permutation_importance.csv", index_col=0)["logit_L2"].sort_values(ascending=False)
rows = []
for k in [5, 9, 15, 20, 26]:
    cols = list(imp.index[:k])
    rows.append(dict(inputs=k, C=1.0, AUC_cv=cv_auc(cols, 1.0)))
for C in [0.01, 0.1, 1.0, 10.0, 1e4]:
    rows.append(dict(inputs=26, C=C, AUC_cv=cv_auc(ALL, C)))
sc = pd.DataFrame(rows).drop_duplicates(["inputs", "C"])
sc.round(4).to_csv(OUT / "q3b_scoring_size_penalty.csv", index=False)
rep += ["\n[4] Scoring model: CV AUC by number of inputs (ranked by permutation importance; ranking uses all data, "
        "so small k is slightly flattered) and by penalty C (smaller = stronger shrinkage; 1e4 ~ unpenalised)", sc.round(4).to_string(index=False)]

txt = "\n".join(rep); print(txt); (OUT / "q3b_results.txt").write_text(txt + "\n")
