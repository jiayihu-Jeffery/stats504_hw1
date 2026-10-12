# 03 Methods → Robustness

*Report: the footnote under the Q4 table ("Changing the cleaning choices moves no profile share by more than 1.3 points").*

Headline results were re-run on three samples:

1. the primary deduplicated sample (n = 2,026);
2. duplicates kept (n = 2,208);
3. the seven flagged high-income records dropped (n = 2,019).

| Script | What it re-runs | Output |
|---|---|---|
| `code/q4c_sensitivity.py` | The full Q4 pipeline on each sample: out-of-fold Q3 score → tenure-adjusted tiers → profiles. The supplementary scorecards are also re-run. | `output/q4c_profile_sensitivity.csv`, `output/q4c_tool_sensitivity.csv`, `output/q4c_results.txt` |

The Q1 and Q3 sensitivity re-runs are built into their own scripts:

- `04_Results/Q1_Spending/output/q1_sensitivity.csv`
- `04_Results/Q3_Response/output/q3_sensitivity.csv`

## Results

The three numbers in each line are for the primary, duplicates-kept and flagged-dropped samples.

- **Q1:** the young-child effect is −38.5% / −37.5% / −36.9%. Teenager and tenure effects are equally stable.
- **Q3:**
  - out-of-fold AUC of the model is 0.839 / 0.846 / 0.838;
  - the odds ratio for earlier acceptance is 4.05 / 4.14 / 4.03.
- **Q4:**
  - no profile's share of customers, acceptance, share of acceptors or share of spending moves by more than 1.3 points (max 1.29);
  - capture at 20% contact is 59.7% / 61.6% / 59.4%.
