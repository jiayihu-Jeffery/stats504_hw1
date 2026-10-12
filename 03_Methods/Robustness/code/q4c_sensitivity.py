"""Sensitivity of Q4 deliverables (profiles, budget capture, scorecards) to the cleaning decisions.
Re-runs the full Q4 pipeline - out-of-fold Q3 explanatory-logit score, tenure-adjusted tiers, profiles, Scorecard A/N CV -
on (1) primary deduplicated sample, (2) duplicates kept, (3) flagged high-income records dropped."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score
from clean import load, SEED, T0_NUM, T1_NO_RECENCY, T2
from paths import out, fig
OUT = out("robustness")
from scorecard import cats, CARDS, fit_card, score, capture
pd.set_option("display.width", 220)

T0 = T0_NUM + ["Edu_Basic", "Edu_Master", "Edu_PhD", "Single"]
FEATS_A = T0 + T1_NO_RECENCY + T2

def prep(d):
    d = d.copy()
    for lev in ["Basic", "Master", "PhD"]: d["Edu_" + lev] = (d.Edu == lev).astype(int)
    d["Single"] = (d.Marital == "Single").astype(int)
    return d

FA = ("Response ~ logInc + Age10 + Kidhome + Teenhome + TenureMonths + C(Edu, Treatment('Graduation')) "
      "+ C(Marital) + logSpend + PrevAccepted")   # Q3 explanatory logit A, carried to Q4

def oof_scenario_a(d):
    """Out-of-fold score of the Q3 explanatory logit A (5x5 repeated stratified CV, averaged over repeats)."""
    d = d.assign(logInc=np.log(d.Income), logSpend=np.log(d.TotalSpend), Age10=d.Age / 10)
    y = d.Response.values; oof = np.zeros((5, len(d)))
    for i, (tr, te) in enumerate(RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED).split(d, y)):
        oof[i // 5, te] = smf.logit(FA, d.iloc[tr]).fit(disp=0).predict(d.iloc[te]).values
    return oof.mean(0)

def profile(r):
    if r.PropTier == "High" and r.SpendTierAdj == "High": return "P1"
    if r.PropTier == "High": return "P2"
    if r.SpendTierAdj == "High": return "P3"
    return "P4"

rows, card_rows = [], []
for label, kw in [("primary (dedup)", {}), ("duplicates kept", dict(dedup=False)), ("flagged high-income dropped", dict(drop_flagged=True))]:
    d = prep(load(**kw)); y = d.Response.values; N = len(d)
    d["p"] = oof_scenario_a(d)
    d["PropTier"] = pd.qcut(d.p, 3, labels=["Low", "Mid", "High"])
    d["Profile"] = d.apply(profile, axis=1)
    o = np.argsort(-d.p.values)
    top20 = y[o[:int(round(.2 * N))]].sum() / y.sum(); top30 = y[o[:int(round(.3 * N))]].sum() / y.sum()
    for pf, g in d.groupby("Profile"):
        rows.append(dict(sample=label, n=N, profile=pf, pct_customers=100 * len(g) / N, acceptance=100 * g.Response.mean(),
                         pct_acceptors=100 * g.Response.sum() / y.sum(), pct_spend=100 * g.TotalSpend.sum() / d.TotalSpend.sum()))
    rng = np.random.default_rng(SEED); Ccat = cats(d)
    rec = dict(sample=label, n=N, model_AUC=roc_auc_score(y, d.p), model_top20_capture=100 * top20, model_top30_capture=100 * top30)
    for cname, vars_ in CARDS.items():
        aucs, caps = [], []
        for tr, te in RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED).split(Ccat, y):
            pts = fit_card(Ccat.iloc[tr], y[tr], vars_); s = score(Ccat.iloc[te], pts, vars_).values
            aucs.append(roc_auc_score(y[te], s)); caps.append(capture(y[te], s, .2, rng)[0])
        k = cname.split()[1]
        rec[f"scorecard{k}_AUC"] = np.mean(aucs); rec[f"scorecard{k}_top20_capture"] = 100 * np.mean(caps)
    card_rows.append(rec)

prof = pd.DataFrame(rows); cards = pd.DataFrame(card_rows)
prof.round(2).to_csv(OUT / "q4c_profile_sensitivity.csv", index=False)
cards.round(4).to_csv(OUT / "q4c_tool_sensitivity.csv", index=False)
wide = prof.pivot(index="profile", columns="sample", values=["pct_customers", "acceptance", "pct_acceptors", "pct_spend"]).round(1)
txt = "\n".join(["Q4 sensitivity: full Q4 pipeline re-run per sample (OOF Q3 explanatory logit, tenure-adjusted tiers, profiles, scorecard CV)",
                 "\n[1] Profiles", wide.to_string(),
                 "\n[2] Targeting tools (held-out performance)", cards.round(3).to_string(index=False)])
print(txt); (OUT / "q4c_results.txt").write_text(txt + "\n")
