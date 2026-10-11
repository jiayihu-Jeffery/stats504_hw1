"""Challenge: duplicate records. Shows how keeping the 358 identical rows inflates cross-validated accuracy
(identical rows land in both training and test folds). Same features/models/CV as Q3 Scenario A."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score
from clean import load, DATA, SEED, T0_NUM, T1_NO_RECENCY, T2
from paths import out
from tee import tee_to
tee_to(out("challenges") / "duplicates_leakage.txt")

raw = pd.read_csv(DATA, sep="\t"); g = raw.drop(columns="ID"); dup = g[g.duplicated(keep=False)]
print(f"Raw file: {len(dup)} rows fall in {dup.drop_duplicates().shape[0]} groups identical on all 28 non-ID fields; "
      f"keeping one row per group removes {len(dup) - dup.drop_duplicates().shape[0]} rows.")

FEATS = T0_NUM + ["Edu_Basic", "Edu_Master", "Edu_PhD", "Single"] + T1_NO_RECENCY + T2
MODELS = {"logistic (L2)": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000)),
          "gradient boosting": lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300,
                                                                      l2_regularization=1.0, random_state=SEED)}
def prep(d):
    d = d.copy()
    for lev in ["Basic", "Master", "PhD"]: d["Edu_" + lev] = (d.Edu == lev).astype(int)
    d["Single"] = (d.Marital == "Single").astype(int); return d

rows = []
for label, kw in [("deduplicated (primary)", {}), ("duplicates kept", dict(dedup=False))]:
    d = prep(load(**kw)); X, y = d[FEATS].values, d.Response.values
    for m, mk in MODELS.items():
        aucs = [roc_auc_score(y[te], mk().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1])
                for tr, te in RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED).split(X, y)]
        rows.append(dict(sample=label, n=len(d), model=m, cv_AUC=np.mean(aucs)))
res = pd.DataFrame(rows); res.round(4).to_csv(out("challenges") / "duplicates_leakage.csv", index=False)
print("\nScenario A, 5x5 repeated stratified CV:"); print(res.round(3).to_string(index=False))
print("\nFlexible models gain more from duplicates (memorised twins in the test fold) -> deduplicate before validation.")
