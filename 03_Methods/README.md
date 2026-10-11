# 03 Methods

*Report section: **Methods***

The code for each method sits with the result it produces, under `04_Results/Q*/code/`. This folder summarises the design. Its subfolder [`Robustness/`](Robustness) holds the sensitivity re-runs.

| Question | Method | Why |
|---|---|---|
| Q1 Spending | Gamma GLM (log link) with HC3 standard errors. Income enters as a B-spline. Log-OLS as a robustness check. Shapley R² decomposition for relative importance. | Models *mean* spend (revenue). Income is strongly non-linear. Shapley shares explained variance fairly among correlated predictors. |
| Q2 Patterns | Product and channel mixes by group. K-means (k chosen from 3–5 by silhouette and minimum size; bootstrap ARI for stability) on composition features only. Product preference index. | Segments describe *how* customers shop rather than restating spend (Q1). |
| Q3 Response | Wilson CIs. Pre-specified logistic regression reported as odds ratios and average marginal effects. L2 logistic vs gradient boosting under 5×5 repeated stratified CV (ROC-AUC, PR-AUC, top-decile lift with bootstrap CIs, calibration, gains). Permutation importance. | Explanation and targeting need different tools. Out-of-sample metrics guard against over-fitting. |
| Q4 Priorities | Tenure-adjusted value tier × tertile of out-of-fold predicted acceptance → four profiles. Integer-points scorecards. Simple rules. Budget table. Conditional profit curve. | Combines value, style and responsiveness. Out-of-fold scores avoid optimistic profiles. |

**Variable availability tiers.** Variables are grouped by whether they are known when a campaign is sent:

- **T0, always known:** demographics and tenure.
- **T1, known only if recorded before the campaign:** spending, purchases, web visits, complaints.
- **T2, known if earlier campaigns came first:** campaigns 1–5.

Accepting the last campaign may itself have changed recency, so we use two scenarios:

- **Scenario A (primary):** T0 + T2 + T1 without recency.
- **Scenario B:** everything, including recency. Valid only after the client confirms the data timing.

**Seed:** 503 throughout.
