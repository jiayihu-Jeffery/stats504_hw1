# 03 Methods → Robustness

*Report: the Methods "Robustness" bullet, the Q4 footnote, and Appendix A*

Every headline result was re-run on three samples:

1. the primary deduplicated sample (n = 2,026);
2. duplicates kept (n = 2,208);
3. the seven flagged high-income records dropped (n = 2,019).

| Script | What it re-runs | Output |
|---|---|---|
| `code/q4c_sensitivity.py` | The full Q4 pipeline on each sample: out-of-fold Scenario A score → tenure-adjusted tiers → profiles → Scorecard A/N cross-validation | `output/q4c_profile_sensitivity.csv`, `output/q4c_tool_sensitivity.csv`, `output/q4c_results.txt` |

The Q1 and Q3 sensitivity re-runs are built into their own scripts:

- `04_Results/Q1_Spending/output/q1_sensitivity.csv`
- `04_Results/Q3_Response/output/q3_sensitivity.csv`

## Results

- **Q1.** The young-child effect is −38.5% / −37.5% / −36.9% under the spline model on the three samples. Teenager and tenure effects are equally stable.
- **Q3.** Scenario A logistic AUC is 0.858 / 0.863 / 0.865. The odds ratio for earlier acceptance is 4.05 / 4.14 / 4.03.
- **Q4.** No profile's share of customers, acceptors or spending moves by more than 1.3 percentage points. Model capture at 20% contact is 63.9–64.7%. Scorecard A capture is 60.1–60.9%. Scorecard N AUC is 0.755–0.757.
