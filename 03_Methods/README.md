# 03 Methods

*Report section: **Methods (final models)***. The code for each method sits with its results under `04_Results/Q*/code/`. This folder summarises the design. [`Robustness/`](Robustness) holds the Q4 sensitivity re-runs.

| Question | Final method in the report | Why |
|---|---|---|
| Q1 Spending | Gamma regression (log link) with HC3 SEs. Income enters as a 4-df B-spline in log income. Importance comes from a Shapley decomposition of explained deviance. | Spending is positive and skewed, and its spread grows with the mean; Gamma fitted best by AIC. The model targets *average* spending. Income is strongly non-linear. Shapley splits importance fairly among correlated predictors. |
| Q2 Patterns | k-means (k = 3 by silhouette, 50 starts) on 11 standardised style measures: product shares, channel shares, discount share, web visits. Bootstrap ARI checks stability and an equal-weight re-run checks weighting. | Groups describe *how* customers shop rather than restating spending (Q1). |
| Q3 Response | One pre-specified logistic regression (HC1 SEs, average marginal effects). It is scored out of fold under 5×5 repeated stratified CV. | Fixed variables avoid inflated significance. Larger 26-field models were only slightly better on unseen customers (0.858 / 0.852 vs 0.839), so one transparent model explains and scores. |
| Q4 Priorities | Tenure-adjusted value (spending percentile within 6-month joining cohorts) × the out-of-fold Q3 score, each split at its top third, gives P1–P4. Profile traits are compared with all customers. | A target should both respond and spend. Out-of-fold scores avoid optimistic profiles. Tenure adjustment avoids undervaluing new customers. |

**Data timing.** Variables are grouped by whether they are known when a campaign is sent:

- **T0:** demographics and tenure (always known).
- **T1:** spending, purchases, web visits, complaints (known only if recorded before the campaign).
- **T2:** earlier campaigns 1–5.

Accepting the last campaign may itself change recency (days since the last purchase), so recency is left out of every recommendation. It appears only in sensitivity checks (Q3 model B).

**Sensitivity samples:**

- primary deduplicated (n = 2,026);
- duplicates kept (2,208);
- 7 flagged high incomes dropped (2,019).

See [`Robustness/`](Robustness).

**Seed:** 503 throughout (`common/paths.py`).
