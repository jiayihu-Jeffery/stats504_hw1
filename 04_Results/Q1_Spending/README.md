# Q1: Which demographic and household characteristics are associated with higher spending?

*Report section: **Results → Q1 Spending** (full report §5.1)*

## Analyses (`code/q1_spend.py`)
1. **Descriptives:** median, mean and IQR of 2-year total spend by income quartile, young children, teenagers, children, education and marital status.
2. **Primary model:** Gamma GLM (log link) with HC3 standard errors. The model is `TotalSpend ~ log(Income) + Kidhome + Teenhome + Age + Education + Marital + Tenure`. Results are reported as % differences, unadjusted and adjusted side by side.
3. **Recommended functional form:** the same model with a B-spline (4 df) in log income. The fit improves markedly (deviance 846 vs 1,495).
4. **Robustness model:** log-OLS with HC3 standard errors.
5. **Relative importance:** Shapley R² decomposition of the log-OLS model.
6. **Diagnostics:** spline vs linear income, the income × young-children interaction, VIF, residual plots.
7. **Spend concentration.**
8. **Sensitivity:** the models re-run with duplicates kept and with flagged records dropped.

## Key results
- **Relative importance:** income accounts for 58.9% and young children for 31.5% of the explained variation (total R² = 0.695). Tenure adds 5.4%. Education, age, teenagers and marital status each add 2% or less. `[Robust]`
- **Young children:** −38.5% spending per young child (95% CI −42.8 to −33.9), under the spline model. Simpler models give up to −62%. `[Robust]`
- **Teenagers:** −15.2% per teenager (−20.7 to −9.4) after adjustment. On the log scale the unadjusted association is about 0, so the effect appears only once like is compared with like.
- **Tenure:** +4.3–4.4% spend per month. This motivates the tenure-adjusted value used in Q4.
- **No reliable association:** education, marital status and age, once income is modelled properly.
- **Concentration:** the top 20% of customers produce 52.3% of spending. `[Descriptive]`

## Files
- `output/q1_descriptives.csv`: spend by group.
- `output/q1_effects.csv`: % effects (unadjusted, Gamma, log-OLS, spline).
- `output/q1_shapley_r2.csv`: relative importance.
- `output/q1_sensitivity.csv`: effects under each sensitivity sample.
- `output/q1_results.txt`: the full log.
- Figures:
  - `figures/q1_spend_boxplots.png`
  - `figures/q1_shapley.png`
  - `figures/q1_diagnostics.png`: the income shape and residuals.
