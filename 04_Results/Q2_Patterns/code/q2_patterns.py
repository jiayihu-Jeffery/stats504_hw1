"""Q2: purchasing patterns, product preferences, channels; style-based segmentation."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.decomposition import PCA
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from clean import load, SEED, MNT, CHAN
from paths import out, fig
OUT = out("q2"); FIG = fig("q2")
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)

df = load(); N = len(df)
PROD = ["Wine", "Fruit", "Meat", "Fish", "Sweets", "Gold"]
for c, n in zip(MNT, PROD): df["sh_" + n] = df[c] / df.TotalSpend
for c, n in zip(CHAN, ["Web", "Catalog", "Store"]): df["ch_" + n] = df[c] / df.TotalPurch.replace(0, np.nan)
# NumDealsPurchases can exceed TotalPurch (3 raw rows) -> overlap undocumented; ratio capped at 1
df["DealRatio"] = (df.NumDealsPurchases / df.TotalPurch.replace(0, np.nan)).clip(upper=1)
SH = ["sh_" + p for p in PROD]; CH = ["ch_Web", "ch_Catalog", "ch_Store"]
rep = [f"Q2 — primary sample n = {N}"]

# ---------- 1. descriptives ----------
vars_ = SH + CH + ["DealRatio", "NumWebVisitsMonth", "AvgTicket", "TotalPurch"]
for g in ["IncomeQ", "Children"]:
    t = df.groupby(g, observed=True)[vars_].mean()
    t.insert(0, "n", df.groupby(g, observed=True).size())
    t.round(3).to_csv(OUT / f"q2_profile_by_{g}.csv")
    rep += [f"\n[1] Mean behaviour by {g}", t.round(3).to_string()]
rep += ["\nOverall means:", df[vars_].mean().round(3).to_string()]

fig, ax = plt.subplots(2, 2, figsize=(13, 8.5))
cols6 = ["#7B2D43", "#E39B3B", "#B8473A", "#3E7CB1", "#C77DB4", "#D4B33A"]
for j, g in enumerate(["IncomeQ", "Children"]):
    t = df.groupby(g, observed=True)[SH].mean(); t.columns = PROD
    t.plot.bar(stacked=True, ax=ax[0, j], color=cols6, rot=0, width=.75)
    ax[0, j].set(ylabel="Mean share of customer's spend", xlabel=g, title=f"Product mix by {g}")
    ax[0, j].legend(fontsize=8, ncol=3, loc="lower right")
    t = df.groupby(g, observed=True)[CH].mean(); t.columns = ["Web", "Catalog", "Store"]
    t.plot.bar(stacked=True, ax=ax[1, j], color=["#5DA5DA", "#F15854", "#60BD68"], rot=0, width=.75)
    ax[1, j].set(ylabel="Mean share of customer's purchases", xlabel=g, title=f"Channel mix by {g}")
    ax[1, j].legend(fontsize=8, loc="lower right")
fig.suptitle(f"Product and channel mix (n = {N}; channel shares exclude {df.TotalPurch.eq(0).sum()} customers with 0 recorded purchases)")
plt.tight_layout(); plt.savefig(FIG / "q2_mix_by_income_children.png", dpi=140); plt.close()

fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
for a, v, lab in [(ax[0], "DealRatio", "Deal purchases / total purchases"), (ax[1], "NumWebVisitsMonth", "Web visits last month"),
                  (ax[2], "AvgTicket", "Spend per purchase")]:
    t = df.groupby("Children")[v].mean(); a.bar(t.index.astype(str), t.values, color="#3B6EA5")
    a.set(xlabel="Children + teens at home", ylabel=lab, title=lab)
fig.suptitle(f"Price sensitivity and engagement by household size (n = {N})")
plt.tight_layout(); plt.savefig(FIG / "q2_engagement_by_children.png", dpi=140); plt.close()

# ---------- 2. style segmentation ----------
FEATS = SH + CH + ["DealRatio", "NumWebVisitsMonth"]
cl = df.dropna(subset=FEATS).copy()
X = StandardScaler().fit_transform(cl[FEATS])
rep += [f"\n[2] Segmentation sample: {len(cl)} (excluded {N - len(cl)} with no recorded channel purchases)",
        "Features (standardised): " + ", ".join(FEATS) + "  — TotalSpend and Income deliberately excluded"]
sel = []
for k in range(3, 6):
    km = KMeans(k, n_init=50, random_state=SEED).fit(X)
    gm = GaussianMixture(k, n_init=5, random_state=SEED, covariance_type="full").fit(X)
    sizes = np.bincount(km.labels_) / len(X)
    sel.append(dict(k=k, kmeans_silhouette=silhouette_score(X, km.labels_, random_state=SEED, sample_size=len(X)),
                    kmeans_min_size_pct=100 * sizes.min(), gmm_bic=gm.bic(X)))
sel = pd.DataFrame(sel).round(3); sel.to_csv(OUT / "q2_k_selection.csv", index=False)
rep += ["k selection:", sel.to_string(index=False)]
ok = sel[sel.kmeans_min_size_pct >= 5]
K = int(ok.loc[ok.kmeans_silhouette.idxmax(), "k"])
rep += [f"Chosen k = {K} (highest K-means silhouette among k with every segment >= 5%)"]
km = KMeans(K, n_init=50, random_state=SEED).fit(X)

# order segments by mean TotalSpend so labels are stable/readable (S1 = lowest spend)
raw = km.labels_
order = pd.Series(cl.TotalSpend.values).groupby(raw).mean().sort_values().index
relabel = {old: f"S{i + 1}" for i, old in enumerate(order)}
cl["Segment"] = [relabel[l] for l in raw]

# stability: bootstrap ARI
rng = np.random.default_rng(SEED); aris = []
for b in range(100):
    idx = rng.integers(0, len(X), len(X))
    kb = KMeans(K, n_init=10, random_state=b).fit(X[idx])
    aris.append(adjusted_rand_score(raw, kb.predict(X)))
aris = np.array(aris)
rep += [f"Bootstrap stability (100 resamples): ARI mean = {aris.mean():.3f}, 5th-95th pct = "
        f"[{np.percentile(aris, 5):.3f}, {np.percentile(aris, 95):.3f}]"]

# Feature-weighting sensitivity: product shares (6 columns, summing to 1) get twice the weight of channel shares
# (3 columns) in plain standardized K-means. Re-cluster with each block (products, channels, deal ratio, web visits)
# carrying equal total weight and compare partitions.
blk_w = np.array([1 / np.sqrt(len(SH))] * len(SH) + [1 / np.sqrt(len(CH))] * len(CH) + [1.0, 1.0])
km_w = KMeans(K, n_init=50, random_state=SEED).fit(X * blk_w)
ari_w = adjusted_rand_score(raw, km_w.labels_)
sil_main = silhouette_score(X, raw, random_state=SEED, sample_size=len(X))
xt_w = pd.crosstab(cl.Segment, km_w.labels_)
recov = (xt_w.max(axis=1) / xt_w.sum(axis=1))          # share of each segment that stays together under equal weights
xt_w.to_csv(OUT / "q2_weighting_crosstab.csv")
pd.DataFrame([dict(check="equal block weights vs standard", ARI=ari_w, silhouette_standard=sil_main,
                   **{f"{sg}_kept_together": recov[sg] for sg in recov.index})]).round(3).to_csv(OUT / "q2_weighting_sensitivity.csv", index=False)
rep += [f"Block-weighting sensitivity (products/channels/deal/visits equally weighted): ARI vs main partition = {ari_w:.3f}; "
        f"silhouette of main partition = {sil_main:.3f} (clusters overlap; read as tendencies). Share of each segment kept "
        f"together under equal weights: " + ", ".join(f"{sg} {100 * recov[sg]:.0f}%" for sg in recov.index), xt_w.to_string()]

# ---------- 3. profiles ----------
prof_vars = FEATS + ["TotalSpend", "AvgTicket", "TotalPurch", "Recency", "Income", "Age", "Kidhome", "Teenhome",
                     "Children", "TenureMonths", "Response", "PrevAccepted"]
prof = cl.groupby("Segment")[prof_vars].mean()
prof.insert(0, "n", cl.groupby("Segment").size()); prof.insert(1, "pct", (100 * prof.n / len(cl)).round(1))
prof["pct_Partnered"] = cl.groupby("Segment").Marital.apply(lambda s: (s == "Partnered").mean())
prof["pct_PhD"] = cl.groupby("Segment").Edu.apply(lambda s: (s == "PhD").mean())
prof["share_of_total_spend_pct"] = 100 * cl.groupby("Segment").TotalSpend.sum() / cl.TotalSpend.sum()
prof.round(3).T.to_csv(OUT / "q2_segment_profiles.csv")
rep += ["\n[3] Segment profiles (means)", prof.round(3).T.to_string()]

# ---------- 4. segment x spend tier ----------
ct = pd.crosstab(cl.Segment, cl.SpendTier, margins=True)
ctp = pd.crosstab(cl.Segment, cl.SpendTier, normalize="index").round(3)
ct.to_csv(OUT / "q2_segment_by_spendtier.csv")
rep += ["\n[4] Segment x spend tier (counts)", ct.to_string(), "Row %", (100 * ctp).to_string()]

# ---------- 5. PCA plot ----------
pca = PCA(2, random_state=SEED).fit(X); Z = pca.transform(X)
fig, a = plt.subplots(figsize=(7.5, 6))
pal = ["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#B07AA1"]
for i, s in enumerate(sorted(cl.Segment.unique())):
    m = cl.Segment.values == s
    a.scatter(Z[m, 0], Z[m, 1], s=6, alpha=.5, color=pal[i], label=f"{s} (n={m.sum()})")
a.set(xlabel=f"PC1 ({100 * pca.explained_variance_ratio_[0]:.0f}% of variance)",
      ylabel=f"PC2 ({100 * pca.explained_variance_ratio_[1]:.0f}% of variance)",
      title=f"Style segments on first two principal components (n = {len(cl)})")
a.legend(markerscale=3); plt.tight_layout(); plt.savefig(FIG / "q2_segments_pca.png", dpi=140); plt.close()
load_ = pd.DataFrame(pca.components_.T, index=FEATS, columns=["PC1", "PC2"]).round(3)
rep += ["\nPCA loadings", load_.to_string()]

# heatmap of standardized segment centres
cen = pd.DataFrame(X, columns=FEATS).groupby(cl.Segment.values).mean()
fig, a = plt.subplots(figsize=(10, 3.2))
im = a.imshow(cen.values, cmap="RdBu_r", vmin=-1.5, vmax=1.5, aspect="auto")
a.set_xticks(range(len(FEATS))); a.set_xticklabels([f.replace("sh_", "").replace("ch_", "") for f in FEATS], rotation=45, ha="right")
a.set_yticks(range(len(cen))); a.set_yticklabels(cen.index)
for i in range(cen.shape[0]):
    for j in range(cen.shape[1]): a.text(j, i, f"{cen.values[i, j]:.1f}", ha="center", va="center", fontsize=7)
plt.colorbar(im, label="Standardised mean (z)"); a.set_title(f"Segment centres (n = {len(cl)})")
plt.tight_layout(); plt.savefig(FIG / "q2_segment_centres.png", dpi=140); plt.close()

cl[["ID", "Segment"]].to_csv(OUT / "q2_segment_assignments.csv", index=False)
txt = "\n".join(rep); print(txt); (OUT / "q2_results.txt").write_text(txt + "\n")
