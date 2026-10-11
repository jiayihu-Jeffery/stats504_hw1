# Execution Prompt：Customer Personality Analysis

You are a senior statistical consultant. You are carrying out a client analysis with reproducible Python (pandas, statsmodels, scikit-learn, matplotlib). Work in `customer_personality/`. The data are in `data/marketing_campaign.csv` (tab-separated). The variable documentation is in `data/meta.json`. The prior audit is in `ANALYSIS_PLAN.md` and `output/01_data_audit.txt`.

## Client questions
1. Which demographic and household characteristics are associated with higher total spending?
2. How do purchasing patterns, product preferences, and channels differ across customers?
3. Which characteristics and behaviors are associated with a higher likelihood of accepting a campaign?
4. Which customer profiles should be prioritized in future marketing?

The client asked for three things:
- practical guidance on where to spend marketing resources;
- a clear separation between descriptive patterns and conclusions strong enough to act on;
- explicit limitations.

## Rules
- Never invent data, results, definitions, or client requirements. Every number in the report must come from a script output saved in `output/`.
- Label every unconfirmed assumption as an assumption. The undocumented items are: the snapshot date, the campaign timeline, whether all customers were contacted, the meaning of `Z_CostContact`/`Z_Revenue`, the currency, and `2n Cycle`.
- Use association language throughout. Campaigns were not shown to be randomized, so response propensity ≠ incremental (causal) effect.
- Fix seeds. Put cleaning in one shared module that every analysis imports.

## Fixed data decisions (apply in `scripts/clean.py`)
- **Drop**: rows with missing Income (24); `Year_Birth` < 1930 (3); Income = 666,666 (1).
- **Deduplicate**: 358 rows are identical on all 28 non-ID fields (176 groups). Keep one row per group; this is the primary sample. Reason: if duplicates stay in, the same record can land in both the training and test folds, which inflates cross-validated AUC for flexible models (random forest 0.875 → 0.847; logistic regression is unchanged). Rerun the headline results on the non-deduplicated data as a sensitivity check.
- **Recode**:
  - Marital: Married/Together → Partnered. Single/Divorced/Widow/Alone → Single. Absurd/YOLO → drop.
  - Education: 2n Cycle → Master (assumption). Keep Basic, but flag its small n.
- **Drop columns**: `Z_CostContact` and `Z_Revenue` (constants).
- **Derive**:
  - `TotalSpend` = sum of the 6 `Mnt*` columns.
  - `TotalPurch` = Web + Catalog + Store purchases.
  - `Children` = Kidhome + Teenhome.
  - `Age` = 2014 − Year_Birth. The reference year is an assumption; it only shifts the intercept.
  - `TenureMonths` = months from `Dt_Customer` to the latest enrolment date.
  - `PrevAccepted` = sum of AcceptedCmp1–5.
  - `AvgTicket` = TotalSpend / TotalPurch (NaN when TotalPurch = 0).
- Flag, but keep, the 7 customers with Income > 150k whose spending pattern looks implausible.
- Save a cleaning log with row counts at each step.

## Variable availability tiers (for Q3)
Define these tiers at the moment a future campaign is sent:
- **T0, always known**: Income, Age, Education, Marital, Kidhome, Teenhome, TenureMonths.
- **T1, known only if measured before the campaign**: `Mnt*`, channel purchases, NumDealsPurchases, NumWebVisitsMonth, Recency, Complain.
- **T2, known if earlier campaigns preceded it**: AcceptedCmp1–5.

The snapshot date is unknown. Accepting the last campaign may itself have lowered Recency and raised spending.

Report two scenarios:
- **Scenario A (conservative, primary)**: T0 + T2, plus T1 *without* Recency.
- **Scenario B**: all tiers.

State that Scenario B is valid only if the client confirms that T1 was measured before the campaign.

## Analysis steps

**Q1 — spending (`scripts/q1_spend.py`)**
1. Descriptives: median, mean, and IQR of TotalSpend by income quartile, Kidhome, Teenhome, Children, Education, and Marital, plus a boxplot.
2. Primary model: Gamma GLM with log link, TotalSpend ~ log(Income) + Kidhome + Teenhome + Age + Education + Marital + TenureMonths. Use a Gamma GLM because the business cares about mean spend.
3. Robustness check: OLS on log(TotalSpend) with HC3 standard errors.
4. Report coefficients as % differences with 95% CIs.
5. Show unadjusted and adjusted effects side by side. Teenhome's sign changes from about 0 unadjusted to about −21% adjusted; explain this as conditioning, not as a contradiction.
6. Rank "most relevant" characteristics with a dominance analysis or Shapley R² decomposition, not by coefficient size.
7. Diagnostics:
   - Test income non-linearity with a spline.
   - Test the Income × Kidhome interaction.
   - Check VIF and residual plots.
8. Report the concentration of spend (the share of spend from the top 20% of customers).

**Q2 — patterns (`scripts/q2_patterns.py`)**
1. Describe how the following vary by income quartile and by Children, with charts:
   - product shares (each `Mnt` / TotalSpend);
   - channel shares;
   - deal-purchase ratio, web visits, and AvgTicket.
2. Segment by **style, not value**. Use KMeans or a GMM on standardized behavioral-composition features only: product shares, channel shares, deal ratio, and web visits. **Exclude TotalSpend and Income**; otherwise the segments just reproduce the income split from Q1.
   - Choose k between 3 and 5 by silhouette or BIC, interpretability, and a minimum segment size of at least 5%.
   - Check stability with bootstrap ARI.
3. Profile each segment by demographics and spend, after clustering.
4. Cross-tabulate segment by spend tier (tertiles). This is the input to Q4.
5. Provide a 2-D PCA plot.

**Q3 — campaign response (`scripts/q3_response.py`)**
- The outcome is `Response` (last campaign; about 15% positive).
- Describe acceptance rates with Wilson 95% CIs by key groups and by PrevAccepted.
- **Explanatory model**: a pre-specified, parsimonious logistic regression on T0 variables + log(TotalSpend) + Recency (Scenario B only) + PrevAccepted.
  - Do not use stepwise selection.
  - Do not enter all 6 `Mnt` columns, because they are collinear with income.
  - Report odds ratios and average marginal effects with CIs.
- **Predictive models** (one for each tier set: T0, Scenario A, Scenario B):
  - Fit L2 logistic regression and a gradient-boosting model.
  - Use 5×5 repeated stratified CV.
  - Report:
    - ROC-AUC and PR-AUC (mean ± SD);
    - top-decile response rate and lift with bootstrap CIs;
    - a calibration plot;
    - a cumulative gains curve.
  - Use permutation importance for interpretation.
- Save **out-of-fold** predicted probabilities for Q4.

**Q4 — prioritization (`scripts/q4_targeting.py`)**
1. Build a priority matrix: spend tier × response-propensity tier, using the out-of-fold Scenario A probabilities. For each cell, report:
   - size;
   - mean spend;
   - observed response rate;
   - dominant Q2 segment;
   - preferred channel and products.
2. Turn the matrix into 3–4 named, actionable profiles.
3. Build a budget table: if the company contacts the top 10%, 20%, or 30% by predicted propensity, show the share of all acceptors it captures and the response rate it achieves, compared with contacting everyone.
4. Profit curve: add it only as a clearly labeled conditional scenario that assumes `Z_CostContact` = cost per contact and `Z_Revenue` = revenue per acceptance (break-even rate = 3/11 ≈ 27%). It requires client confirmation.
5. Recommend a validation design: in each priority group, randomly hold out 10–20% from contact, so the next campaign measures true uplift.

## Report (English, about 10–12 pages plus appendix; `report/`)
Sections:
1. Executive summary: one page of actionable recommendations.
2. Background and questions.
3. Data and cleaning.
4. Methods, briefly.
5. Findings for Q1–Q3.
6. Recommendations for Q4.
7. Limitations:
   - unknown snapshot date and leakage risk;
   - tenure versus the 2-year spending window;
   - duplicates;
   - campaigns that differ in unknown ways, so models generalize only to campaigns like the last one;
   - observational design;
   - data from 2012–14, with unknown representativeness;
   - small subgroups;
   - multiple comparisons;
   - privacy considerations of household-based targeting.
8. Questions for the client.
9. Appendix: sensitivity analyses (non-deduplicated sample, Scenario B, excluding the 7 flagged high-income records) and model details. Missing income is only 1.1%, so complete-case analysis is enough; do not add multiple imputation.

Tag each key finding with one evidence label:
- **[Descriptive]**;
- **[Robust association]**: holds after adjustment and across sensitivity checks;
- **[Decision-ready]**: robust, uses only variables available before the campaign, and validated out-of-sample.

## Acceptance checks before you finish
- Every number in the report traces to a file in `output/`.
- No claim says or implies causation.
- Q3/Q4 conclusions rely only on Scenario A unless a Scenario B result is explicitly labeled.
- The deduplicated and non-deduplicated samples give the same headline conclusions; if they do not, report the difference.
- Every figure has labeled axes and units, and a sample size in the caption.
- Recommendations cover profile size, the reason for prioritizing it, the suggested channel and offer, and the uncertainty involved.
