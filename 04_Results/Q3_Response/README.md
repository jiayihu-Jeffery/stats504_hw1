# Q3: Who accepts campaigns?

*Report sections: **Methods → Q3** and **Results → Q3**; Figure 2A. The score also feeds Q4 (Figure 2C).*

## Final model
**One pre-specified logistic regression (model A)** of accepting the last campaign (`Response`, 15.3%). It has 11 terms:

- earlier campaigns accepted;
- single;
- education (Basic / Master / PhD vs Graduation);
- tenure;
- teenagers and young children;
- log spending, log income and age.

Standard errors are HC1. Results are reported as odds ratios and average marginal effects (AME, in percentage points).

The same model **scores customers for Q4**: under 5×5 repeated stratified CV, each customer is scored by fits that left them out (`run_cv_formula()`). The scores are saved as `p_Q4` in `output/q3_oof_predictions.csv`.

**Why this model:**
- **Fixed in advance:** the variables were chosen before fitting (no stepwise selection), so p-values are not inflated by trial and error.
- **Spending checked:** spending might be boosted by the campaign itself, so model A0 refits without it. The other effects barely change (odds ratios: earlier acceptance 4.05 → 4.29, single 3.02 → 2.98, teenagers 0.42 → 0.40).
- **Recency left out:** days since the last purchase could itself change when a customer accepts. Model B, which adds it, is reported only as a sensitivity check.
- **One model for both jobs:** larger 26-field models (L2 logistic regression, gradient boosting) ranked unseen customers only slightly better (AUC 0.858 and 0.852 vs 0.839).
- **Not over-fitted** (`q3b_overfit_checks.py`):
  - in-sample AUC 0.846 vs cross-validated 0.839, with 26 events per parameter;
  - VIFs ≤ 3.4;
  - Master vs PhD effects differ (p = 0.002), so they are not merged.

## Results used in the report
| Statement | Number | File |
|---|---|---|
| Acceptance by earlier campaigns accepted (Fig. 2A) | 8.6 / 31.2 / 51.4 / 82.0% for 0 / 1 / 2 / 3+ | `output/q3_rates.csv` |
| Single, PhD, teenager (otherwise-similar customers) | AME +10.2, +6.6, −7.9 points | `output/q3_logit_explanatory.csv` (model A) |
| Model A coefficients (equation in the report) | — | `output/q3_logit_A_coefficients.csv` |
| Ranking accuracy on unseen customers; top tenth acceptance | AUC 0.839; 62.6% | `output/q3_model_performance.csv` |
| With recency (Challenges) | AUC 0.881 | `output/q3_model_performance.csv` (model B) |
| Duplicates kept (Challenges) | AUC 0.846 vs 0.839 | `output/q3_sensitivity.csv` |

## Scripts
| Script | What it does |
|---|---|
| `code/q3_response.py` | Acceptance rates (Wilson CIs). Models A, B and A0. Out-of-fold scoring of A and B. Comparison models (L2 logistic and gradient boosting on T0, Scenario A and Scenario B fields). Permutation importance, calibration and gains, and the three sensitivity samples. |
| `code/q3b_overfit_checks.py` | Nested models and events per parameter. VIFs. Master vs PhD tests (Wald, merged model, bootstrap). Size and penalty checks for the 26-field model. |

## Files
- `output/q3_rates.csv`, `q3_logit_A_coefficients.csv`, `q3_logit_explanatory.csv` (models A, B, A0)
- `output/q3_model_performance.csv`, `q3_oof_predictions.csv` (input to Q4), `q3_sensitivity.csv`, `q3_results.txt`
- `output/q3_scoring_model_coefficients.csv`, `q3_permutation_importance.csv`: the 26-field comparison model (supplementary)
- `output/q3b_*.csv`, `q3b_results.txt`: overfitting and education checks
- `figures/q3_rates.png`, `q3_calibration_gains.png`, `q3_permutation_importance.png`
