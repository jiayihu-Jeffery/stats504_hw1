# Q3: Which characteristics and behaviours are associated with accepting a campaign?

*Report section: **Results → Q3 Response** (full report §5.3)*

## Analyses (`code/q3_response.py`)
1. **Acceptance rates** of the last campaign (`Response`, 15.3%) by group, with Wilson 95% CIs.
2. **Explanatory logistic regressions:** model A (Scenario A) and model B (adds recency). Pre-specified, no stepwise selection. Reported as odds ratios and average marginal effects with HC1 standard errors.
3. **Predictive models:** L2 logistic regression and histogram gradient boosting, each on three feature sets (T0; Scenario A; Scenario B). Evaluated by 5×5 repeated stratified CV: ROC-AUC, PR-AUC, top-decile rate and lift (bootstrap CI), calibration, gains.
4. **Permutation importance** (Scenario A).
5. **Out-of-fold predicted probabilities**, saved for Q4.
6. **Sensitivity:** duplicates kept and flagged records dropped.

## Key results
- **Earlier acceptance:** acceptance is 8.6% / 31.2% / 51.4% / 82.0% for 0 / 1 / 2 / 3+ earlier campaigns accepted. The adjusted odds ratio is 4.05 per campaign (+12.8 percentage points). `[Robust]`
- **Other characteristics, adjusted:**
  - single vs partnered: OR 3.03 (+10.2 points);
  - PhD: OR 2.05 (+6.6 points);
  - tenure: +1.0 point per month;
  - each teenager: OR 0.42 (−7.9 points). `[Robust]`
- **Predictive accuracy:**

  | Feature set | AUC | Top-decile acceptance |
  |---|---|---|
  | T0 (demographics and tenure) | 0.755 | – |
  | **Scenario A (primary)** | **0.858** | **67.0%** (lift 4.4×) |
  | Scenario B (adds recency) | 0.894 | – |

  Gradient boosting (0.852) does not beat logistic regression, so the logistic model is used in Q4.
- **Recency:** 27.0% acceptance at 0–24 days vs 7.3% at 75–99 days. It is used only in Scenario B because its timing relative to the campaign is unconfirmed.

## Files
- `output/q3_rates.csv`: acceptance rates.
- `output/q3_logit_explanatory.csv`: odds ratios and marginal effects.
- `output/q3_model_performance.csv`: predictive accuracy.
- `output/q3_permutation_importance.csv`
- `output/q3_oof_predictions.csv`: input to Q4.
- `output/q3_sensitivity.csv`
- `output/q3_results.txt`: the full log.
- Figures:
  - `figures/q3_rates.png`
  - `figures/q3_calibration_gains.png`
  - `figures/q3_permutation_importance.png`
