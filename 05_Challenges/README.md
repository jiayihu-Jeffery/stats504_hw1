# 05 Challenges

*Report section: **Challenges***. Each challenge in the report has a script that reproduces its evidence.

| Challenge | Script | Evidence (from `output/`) | How we handled it |
|---|---|---|---|
| **Duplicate records** | `code/duplicates_leakage.py` | 358 raw rows fall in 176 identical groups. Keeping them raises cross-validated AUC under Scenario A: gradient boosting 0.852 → 0.864, logistic 0.858 → 0.863. | Deduplicated before any validation; duplicates-kept results reported as a sensitivity check. |
| **Model fitting** | `code/gamma_fit_check.py` | The default IRLS fit of the Gamma GLM stops at deviance 3,042 with a *negative* income coefficient (−0.65). Newton from the smearing-adjusted OLS start reaches 1,495. A spline in log income reaches 846. | Newton fit kept as the lowest-deviance solution; spline model used for the recommended estimates. |
| **Tenure vs the 2-year window** | `code/tenure_and_timing.py` (part 1) | Maximum tenure is 23 months (< 24), so no customer was observed for the full window. Spend rises with tenure (+4.3% per month, adjusted). | Built a tenure-adjusted value tier for Q4. 57 recent joiners moved from P4 to P3. |
| **Undocumented timing** | `code/tenure_and_timing.py` (part 2) | Recency gradient: 27.0% acceptance at 0–24 days vs 7.3% at 75–99 days. Adding recency lifts AUC from 0.858 to 0.894. | Recency excluded from every recommendation. Scenario B is reported separately and conditionally. |
| **Usability for the client** | see `04_Results/Q4_Priorities/code/q4b_followup.py` | Scorecard A (AUC 0.831) loses little against the full model (0.858). | Translated the model into an Excel-ready points scorecard and simple rules. |

**Output files:** `duplicates_leakage.csv/.txt`, `gamma_fit_check.csv/.txt`, `tenure_and_timing.txt`.
