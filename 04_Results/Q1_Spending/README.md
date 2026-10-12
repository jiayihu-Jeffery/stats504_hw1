# Q1: Who spends more?

*Report sections: **Methods → Q1** and **Results → Q1**; Figure 1A–C.*

## Final model
A **Gamma regression (log link)** of two-year total spending. Income enters as a 4-df B-spline in log income. The other terms are young children, teenagers, tenure, age, education and single. Standard errors are HC3. The fit is on all 2,026 customers.

Coefficients are in `output/q1_final_model_coefficients.csv`.

**Why this model:**
- **Spending fits a Gamma model:** it is positive and right-skewed, and its spread grows with the mean.
- **Gamma beats the alternatives:** by AIC it is better than lognormal and inverse-Gaussian models (`q1b_distribution_check.py`).
- **It models average spending,** which is what drives revenue.
- **Income bends:** the spline cuts the deviance from 1,495 to 846 (deviance R² 0.738).

## Scripts
| Script | What it does |
|---|---|
| `code/q1_spend.py` | Fits the model. Covers descriptives; unadjusted vs adjusted effects; the linear vs spline Gamma models (`fit_gamma()` starts Newton's method from a log-OLS fit); the log-OLS comparison; VIFs; spend concentration; sensitivity samples; and the Shapley decomposition of explained deviance (section `[6b]`). |
| `code/q1b_distribution_check.py` | Gamma vs lognormal vs inverse Gaussian, same mean structure, AIC. |
| `code/q1c_income_curve.py` | The fitted income curve with 95% HC3 bands, as a multiplier vs median income (Figure 1A). |
| `code/q1d_gamma_vs_normal.py` | Teaching figure: why Gamma rather than ordinary regression. Covers spread vs mean, and negative predictions from OLS. |

## Results used in the report
- **Relative importance (Fig. 1B):** income explains 70.1% and young children 21.1% of the explained deviance. Tenure explains 4.9%; education, teenagers, age and marital status each explain ≤ 2.3% (`output/q1_shapley_gamma_deviance.csv`).
- **Young children:** −38.5% spending per young child (95% CI −42.8 to −33.9). Simpler models give −59% to −74% (`output/q1_effects.csv`).
- **Teenagers:** −15.2% per teenager.
- **Tenure:** +4.3% spending per month. This motivates Q4's tenure-adjusted value.
- **Income curve (Fig. 1A):** relative to median income (51.5k), spending is ×0.16 at 20k, ×2.07 at 65k and ×4.37 at 90k (`output/q1_final_model_income_curve.csv`).
- **Concentration:** the top 20% of customers produce 52.3% of spending.
- **No reliable association:** education, marital status and age, once income is modelled properly.

## Files
- **Final model:** `output/q1_final_model_coefficients.csv`, `q1_final_model_income_curve.csv`, `q1c_income_curve_grid.csv`
- **Shapley shares:** `output/q1_shapley_gamma_deviance.csv`. The log-OLS version is in `q1_shapley_r2.csv`.
- **Effects:** `output/q1_effects.csv`, `q1_sensitivity.csv`, `q1_descriptives.csv`, `q1_results.txt`
- **Distribution and spread checks:** `output/q1b_distribution_check.csv`, `q1d_spread_by_decile.csv`, `q1d_gamma_vs_normal.txt`
- **Figures:** `figures/q1c_income_curve.png`, `q1d_gamma_vs_normal.png`, `q1_shapley.png`, `q1_spend_boxplots.png`, `q1_diagnostics.png`
