# STATS 504 HW1: Customer Personality Analysis (Consulting Project)

**Team:** Shirley, Jiayi

A retail client's marketing department asked four questions about its customers. We answered them in a two-page consultant report:

- **Final report:** [`report/final_report.pdf`](report/final_report.pdf)
- **LaTeX source:** [`report/latex/main.tex`](report/latex/main.tex), compiled with pdfLaTeX on Overleaf or locally with Tectonic.

This README is the guide to the project. For each section of the report it says:

- what we did;
- what we found;
- why we chose that method;
- where the code and the numbers are.

Every number in the report comes from an `output/` file listed below.

| Report section | What it says | Where to look |
|---|---|---|
| Dataset | 2,240 customers, 29 fields; 2,026 after cleaning | [§1](#1-dataset), [`01_Dataset/`](01_Dataset) |
| Goals and questions | Four client questions; three kinds of evidence kept apart | [§2](#2-goals-and-questions), [`02_Goals_and_Questions/`](02_Goals_and_Questions) |
| Methods and Results, Q1 | Gamma regression; income and young children drive spending | [§3](#3-q1-who-spends-more), [`04_Results/Q1_Spending/`](04_Results/Q1_Spending) |
| Methods and Results, Q2 | k-means on shopping style; three styles | [§4](#4-q2-how-do-customers-differ-in-how-what-and-where-they-buy), [`04_Results/Q2_Patterns/`](04_Results/Q2_Patterns) |
| Methods and Results, Q3 | One logistic regression explains acceptance and scores customers | [§5](#5-q3-who-accepts-campaigns), [`04_Results/Q3_Response/`](04_Results/Q3_Response) |
| Methods and Results, Q4 | Value × response profiles P1–P4; who P1 customers are | [§6](#6-q4-whom-should-campaigns-focus-on), [`04_Results/Q4_Priorities/`](04_Results/Q4_Priorities) |
| Challenges | Data timing, duplicates, model fitting | [§7](#7-challenges), [`05_Challenges/`](05_Challenges) |
| Limitations | Association not cause; scope; small groups; no costs | [§8](#8-limitations), [`06_Limitations/`](06_Limitations) |

---

## 1. Dataset

**Report:** Kaggle's public *Customer Personality Analysis* data has 2,240 customers and 29 fields. We removed 32 rows with missing or impossible values and collapsed 182 exact duplicates, which leaves **2,026 customers**. Amounts are in an unspecified currency.

**What we did:**

- **Audit:** checked every field (types, ranges, missing values, impossible values).
- **Cleaning rules:**
  - drop 32 rows: missing income (24), birth year before 1930 (3), income of 666,666 (1), and marital status "Absurd" or "YOLO" (4);
  - map "Alone" to single and "2n Cycle" education to Master;
  - flag 7 records with income above 150k without dropping them;
  - collapse 182 exact duplicates.

All of this lives in one function, `load()` in [`common/clean.py`](common/clean.py), so every analysis uses the same sample.

**Sensitivity samples:** each main result is re-run on two alternative samples.

| Sample | Call | n |
|---|---|---|
| Primary | `load()` | 2,026 |
| Duplicates kept | `load(dedup=False)` | 2,208 |
| Flagged high incomes dropped | `load(drop_flagged=True)` | 2,019 |

**Where:**

- **Code:** [`01_Dataset/code/data_audit.py`](01_Dataset/code/data_audit.py), [`01_Dataset/code/cleaning_log.py`](01_Dataset/code/cleaning_log.py)
- **Output:** `01_Dataset/output/01_data_audit.txt`, `01_Dataset/output/00_cleaning_log.txt`

## 2. Goals and questions

**The four questions:**

1. Who spends more?
2. How do customers differ in what and where they buy?
3. Who tends to accept a campaign?
4. Which customers should future campaigns focus on?

The brief asks us to separate patterns from conclusions that can guide decisions. The report therefore keeps **three kinds of evidence** apart:

- **Group comparisons** describe customers.
- **Model results** compare otherwise-similar customers.
- **The targeting score** is the only result tested on customers it was not fitted on, so only it is ready to guide whom to contact.

**Where:**

- **Brief and plan:** [`02_Goals_and_Questions/README.md`](02_Goals_and_Questions/README.md), [`02_Goals_and_Questions/analysis_plan.md`](02_Goals_and_Questions/analysis_plan.md)
- **Preliminary EDA:** [`02_Goals_and_Questions/code/preliminary_eda.py`](02_Goals_and_Questions/code/preliminary_eda.py)

![Figure 1](report/figures/summary_fig1.png)

*Report Figure 1:*

- *(A) fitted income curve;*
- *(B) Shapley shares of explained deviance;*
- *(C) median spend by income quartile and young children;*
- *(D) shopping styles' share of customers and spending.*

*Built by [`report/code/summary_figures.py`](report/code/summary_figures.py).*

## 3. Q1: Who spends more?

**Final model: a Gamma regression with a log link, with income as a smooth curve.** It is fitted on all 2,026 customers, with HC3 robust standard errors:

> log μ̂ = 7.83 + f̂(log Income) − 0.486·Kids − 0.165·Teens + 0.043·Tenure(months) − 0.024·Age/10 − 0.005·Basic + 0.004·Master + 0.003·PhD + 0.009·Single

Here μ̂ is mean two-year spending and f̂ is a 4-df B-spline in log income.

**Why this model:**

- **Spending is positive, right-skewed, and its spread grows with the mean.** Ordinary regression assumes a constant spread and predicts negative spending for 12% of customers (`output/q1d_gamma_vs_normal.txt`); Gamma suits this kind of data.
- **Gamma fitted best:** by AIC it beat lognormal and inverse-Gaussian models with the same mean structure.
- **It models average spending,** which is what drives revenue.
- **Income bends:** spending barely moves at low incomes and rises sharply between about 40k and 80k. The spline cut the deviance from 1,495 (linear) to 846, and the model explains 74% of the variation (deviance R² 0.738).
- **The simple version misleads:** without modelling income properly, the young-child gap looks nearly twice as large (−62% to −74% instead of −38%), and education appears to matter when it does not.

**Results:**

| Report statement | Number | Source file |
|---|---|---|
| Income and young children explain about 90% of what the model explains (Fig. 1B) | 70.1% + 21.1% | `output/q1_shapley_gamma_deviance.csv` |
| Each young child: about 38% less spending | −38.5% (95% CI −42.8% to −33.9%) | `output/q1_effects.csv` (`gspline_*`), `output/q1_final_model_coefficients.csv` |
| Each teenager: about 15% less | −15.2% | `output/q1_effects.csv` |
| Lower spending with children holds at every income level (Fig. 1C) | median spend by quartile and kids | `report/output/summary_fig_spend_by_income_kids.csv` |
| Income curve: ×0.16 at 20k, ×2.07 at 65k, ×4.37 at 90k vs median (Fig. 1A) | multipliers | `output/q1_final_model_income_curve.csv`, `output/q1c_income_curve_grid.csv` |
| Top fifth of customers bring in 52% of spending | 52.3% | `output/q1_results.txt` |
| Gamma fits better than lognormal and inverse Gaussian | AIC | `output/q1b_distribution_check.csv` |

**Code** (all paths in [`04_Results/Q1_Spending/`](04_Results/Q1_Spending)):

- `code/q1_spend.py`:
  - `fit_gamma()` fits the model, starting Newton's method from a log-OLS fit;
  - the spline model is `RHS_SPL`;
  - section `[6b]` computes the Shapley decomposition over all 2⁷ sub-models.
- `code/q1b_distribution_check.py`: compares the three distributions by AIC.
- `code/q1c_income_curve.py`: draws the income curve with 95% bands.
- `code/q1d_gamma_vs_normal.py`: teaching figure contrasting Gamma with ordinary regression (`figures/q1d_gamma_vs_normal.png`).

## 4. Q2: How do customers differ in how, what and where they buy?

**Method: k-means clustering on shopping style.** We grouped customers by *how* they shop, using 11 standardised measures:

- spending shares of the six product groups (wine, meat, fish, fruit, sweets, gold);
- purchase shares of the three channels (web, catalogue, store);
- the share of purchases made on discount;
- monthly website visits.

Spending and income were left out, so the groups describe style rather than repeating Q1.

**Why this method:**

- **Three groups:** we tried 3–5 groups and kept 3, which separated customers most clearly (silhouette 0.21 vs 0.17 and 0.16). Every group still holds at least 5% of customers.
- **Stable under resampling:** bootstrap resamples give almost the same groups (ARI 0.94).
- **Sensitive to weighting:** weighting the four feature types equally moves the line between value-seeking and wine-focused shoppers (ARI 0.38).
  - The affluent catalogue group is solid: 87% of its members stay together.
  - The other two are tendencies: 77% and 53% stay together.

**Results:**

| Style | Customers / spending | Purchases (2 yrs) | Per purchase | On discount | Largest product shares | Web / catalogue / store |
|---|---|---|---|---|---|---|
| Value-seeking variety | 25% / 6% | 7 | 16 | 33% | fish, fruit, sweets 34%; gold 22% | 34 / 8 / 58% |
| Wine-focused browsers | 43% / 32% | 12 | 30 | 30% | wine 63% | 38 / 12 / 50% |
| Affluent catalogue | 32% / 62% | 18 | 65 | 9% | wine 44%; meat 32% | 26 / 30 / 45% |
| All customers | | 13 | 38 | 24% | wine 46%; meat 25% | 33 / 17 / 50% |

**What lies behind the styles:**

- **Income:** from the lowest to the highest income quarter, catalogue purchases rise from 7% to 29%.
- **Children:** families with two or more children buy about 43% on discount, against 9% for those without.
- **Website visits:** frequent visitors spend *less* (Spearman −0.47), so visits signal browsing, not value.

**Code** ([`04_Results/Q2_Patterns/`](04_Results/Q2_Patterns)):

- `code/q2_patterns.py`: features, choice of k, k-means, bootstrap ARI, weighting check and profiles.
- `code/q2b_complaints_webvisits_products.py`: product preference index, complaints, web visits.

**Output:**

| Content | File |
|---|---|
| Choice of k | `output/q2_k_selection.csv` |
| Style table | `output/q2_segment_profiles.csv` |
| Weighting check | `output/q2_weighting_sensitivity.csv` |
| By income quarter | `output/q2_profile_by_IncomeQ.csv` |
| By number of children | `output/q2_profile_by_Children.csv` |
| Web visits | `output/q2b_results.txt` |

![Figure 2](report/figures/summary_fig2.png)

*Report Figure 2:*

- *(A) acceptance by number of earlier campaigns accepted;*
- *(B) profile shares of customers, acceptors and spending;*
- *(C) acceptors found when contacting customers in score order, on customers not used to fit the model.*

## 5. Q3: Who accepts campaigns?

**Final model: one pre-specified logistic regression.** It both explains acceptance and scores customers for Q4:

> logit p̂ = −2.19 + 1.398·PrevAccepted + 1.107·Single + 0.716·PhD + 0.107·Tenure(months) − 0.863·Teens + 0.563·Kids + 0.293·log Spend − 0.383·log Income + 0.072·Age/10 − 1.461·Basic + 0.094·Master

Each term multiplies the odds of accepting: by about 4 per earlier campaign accepted, about 3 for being single and about 2 for a PhD. Each teenager at home more than halves the odds.

**Why this model:**

- **Variables fixed in advance:** trial and error does not inflate significance. We use HC1 robust standard errors and report average marginal effects in percentage points.
- **Spending checked:** spending might be boosted by the campaign itself, so we refitted without it. The other effects barely changed:

  | Odds ratio | With spending | Without spending |
  |---|---|---|
  | Earlier campaigns accepted | 4.05 | 4.29 |
  | Single | 3.02 | 2.98 |
  | Teenagers | 0.42 | 0.40 |

- **The positive Kids term:** it is positive only because income is held fixed. Overall, families with young children accept less.
- **Days since the last purchase is left out,** because accepting could itself change it.
- **Why one model for both jobs:** larger models using all 26 fields (L2 logistic, gradient boosting) ranked unseen customers only slightly better (AUC 0.858 and 0.852 vs 0.839). One transparent model is easier to explain and to use.
- **Not over-fitted:** in-sample AUC 0.846 vs cross-validated 0.839, with 26 events per parameter. Master and PhD effects really differ (p = 0.002), so they are kept apart.

**Results:**

| Report statement | Number | Source file |
|---|---|---|
| Acceptance rises from 9% (no earlier campaign) to 82% (three or more) (Fig. 2A) | 8.6 / 31.2 / 51.4 / 82.0% | `output/q3_rates.csv` |
| Singles +10 points, PhD +7, teenager −8 (otherwise-similar customers) | AME 10.2 / 6.6 / −7.9 | `output/q3_logit_explanatory.csv` (model A) |
| Ranking accuracy on unseen customers 0.84; top tenth accepts at 63% | AUC 0.839, 62.6% | `output/q3_model_performance.csv` |
| With recency 0.88 (Challenges) | AUC 0.881 | `output/q3_model_performance.csv` |
| Duplicates flatter the model 0.839 → 0.846 (Challenges) | CV AUC | `output/q3_sensitivity.csv` |

**Code** ([`04_Results/Q3_Response/`](04_Results/Q3_Response)):

- `code/q3_response.py`:
  - acceptance rates with Wilson CIs;
  - models A, B (adds recency) and A0 (drops spending);
  - `run_cv_formula()` scores model A out of fold under 5×5 repeated stratified CV; these scores (`p_Q4` in `output/q3_oof_predictions.csv`) go to Q4;
  - the larger comparison models and permutation importance are also here.
- `code/q3b_overfit_checks.py`:
  - nested models and events per parameter;
  - VIFs;
  - Master vs PhD tests;
  - size and penalty checks for the 26-field model.

## 6. Q4: Whom should campaigns focus on?

**Method: two dimensions, value × response, crossed into four profiles.** A customer worth targeting should both respond and spend.

- **Value:** spending ranked only against customers who joined in the same 6-month window. Newer customers have had less time to buy (+4% spending per month of tenure), so a raw total would undervalue them.
- **Response:** the Q3 score, computed for each customer from a fit that left them out.
- **Profiles:** each dimension is split at its top third.

| Profile | Definition | Customers | Accepted | Share of acceptors | Share of spending | Suggested action |
|---|---|---|---|---|---|---|
| P1 Engaged | high value, high response | 16.7% | 41.6% | 45.5% | 42.6% | Top priority; wine/meat ranges by catalogue and store |
| P2 Responsive | high response, lower value | 16.6% | 30.4% | 32.9% | 9.3% | Cheap web/email offers with a discount |
| P3 High value | high value, lower response | 16.6% | 6.8% | 7.4% | 31.0% | Skip the usual offer; trial a different one on a small group |
| P4 Low priority | the rest | 50.0% | 4.3% | 14.2% | 17.1% | No paid outreach; welcome new customers separately |

**Who the P1 customers are**, compared with all customers:

| Trait | P1 | All customers |
|---|---|---|
| Accepted an earlier campaign | 66% | 21% |
| Average income | 75k | 52k |
| No young children | 92% | 58% |
| No teenagers at home | 76% | 52% |
| Tenure | 14 months | 12 months |

They spend mostly on wine and meat, buy through catalogue and store, and seldom use discounts. **Customers with these traits should be approached first.**

**Other results:**

| Report statement | Number | Source file |
|---|---|---|
| Profile table | — | `output/q4_profiles.csv` |
| P1 traits vs all customers | — | `output/q4_profile_traits.csv` |
| Top 20% by score finds 60% of acceptors (46% accept); top 30% finds 74% (Fig. 2C) | 59.7%, 45.7%, 74.2% | `output/q4_budget_table.csv` |
| Campaign 3 accepted by 21% of P2 (8% overall); P3 below average on every campaign | — | `output/q4b_campaign_by_profile.csv` |
| A 10-point lift needs about 1,420 targeted customers (210 held back) | 1,418 / 213 | `output/q4d_holdout_power.txt` |
| Changing the cleaning choices moves no profile share by more than 1.3 points | max 1.29 | `03_Methods/Robustness/output/q4c_profile_sensitivity.csv` |

**Code:**

- [`04_Results/Q4_Priorities/code/q4_targeting.py`](04_Results/Q4_Priorities/code/q4_targeting.py): tiers, profiles, traits, budget table.
- [`04_Results/Q4_Priorities/code/q4d_holdout_power.py`](04_Results/Q4_Priorities/code/q4d_holdout_power.py): hold-out sample size.
- [`04_Results/Q4_Priorities/code/q4b_followup.py`](04_Results/Q4_Priorities/code/q4b_followup.py): campaign-by-profile rates.
- [`03_Methods/Robustness/code/q4c_sensitivity.py`](03_Methods/Robustness/code/q4c_sensitivity.py): re-runs the whole Q4 pipeline (out-of-fold score, tiers, profiles) on the three samples.

## 7. Challenges

| Challenge in the report | Evidence | Where |
|---|---|---|
| **Undocumented timing.** We do not know whether purchases and visits were recorded before or after the last campaign, so days since the last purchase is left out. Adding it lifts ranking accuracy from 0.84 to 0.88, possibly only because of the campaign itself. | Recency gradient: 27% acceptance at 0–24 days vs 7% at 75–99 days | `05_Challenges/code/tenure_and_timing.py`; `04_Results/Q3_Response/output/q3_model_performance.csv` |
| **Duplicates** flattered the model (0.839 → 0.846), so we removed them. | 358 raw rows fall in 176 identical groups | `05_Challenges/code/duplicates_leakage.py`; `04_Results/Q3_Response/output/q3_sensitivity.csv` |
| **Model fitting.** The standard Gamma fit stalled, so we refitted it with a more reliable method. | Default IRLS stops at deviance 3,042 with a negative income effect; Newton from a log-OLS start reaches 1,495 | `05_Challenges/code/gamma_fit_check.py` |
| **Tenure vs the two-year window** (behind Q4's value measure) | Spending +4.3% per month of tenure; 57 recent joiners move from P4 to P3 once value is tenure-adjusted | `05_Challenges/code/tenure_and_timing.py`; `04_Results/Q4_Priorities/output/q4_profile_change.csv` |

## 8. Limitations

| Limitation in the report | Evidence | Where |
|---|---|---|
| Associations, not causes: without knowing who received each campaign, "likely to accept" is not "buys because of it" | No contact or control-group field in the data | [`06_Limitations/README.md`](06_Limitations/README.md) |
| Behaviour-based scores are optimistic if those data post-date the campaign | See the timing challenge | `05_Challenges/output/tenure_and_timing.txt` |
| Results apply to offers like the last one (acceptance 1–15% across campaigns) and to 2012–14 customers | Acceptance of each campaign | `06_Limitations/output/campaign_acceptance_rates.csv` |
| Small groups give rough estimates (e.g. 19 complainers) | Group sizes | `06_Limitations/output/small_groups.csv` |
| No cost data for profit estimates | `Z_CostContact` and `Z_Revenue` are undocumented constants | `04_Results/Q4_Priorities/output/q4_profit_conditional.csv` (conditional scenario only) |

---

## Supplementary analyses (not in the two-page report)

These were done along the way. They support the report but are not cited in it.

- **Q1** ([`04_Results/Q1_Spending/`](04_Results/Q1_Spending)):
  - unadjusted vs adjusted effects, log-OLS comparison and VIFs (`q1_spend.py`);
  - Shapley R² of the log-OLS model (`output/q1_shapley_r2.csv`);
  - the Gamma vs ordinary-regression teaching figure (`q1d_gamma_vs_normal.py`).
- **Q2:**
  - product preference index by style;
  - complaints vs acceptance (19 complainers, Fisher p = 1.0) in `q2b_complaints_webvisits_products.py`.
- **Q3:**
  - the 26-field L2 logistic and gradient-boosting models, permutation importance and calibration (`q3_response.py`);
  - overfitting and education checks (`q3b_overfit_checks.py`).
- **Q4** (`q4b_followup.py`):
  - integer-points scorecards (Scorecard A: AUC 0.831; Scorecard N, demographics only: AUC 0.756);
  - one-line rules;
  - a depth-3 decision tree;
  - new-customer analysis;
  - P3 vs P1 comparison.

  The scorecards were dropped from the final report in favour of describing P1's traits. A conditional profit curve, which assumes `Z_CostContact` and `Z_Revenue` are cost and revenue, is in `q4_targeting.py`.

## Repository layout

Folders follow the report's headings. Every analysis folder has the same structure:

- `README.md`;
- `code/`;
- `output/` (tables and logs behind the report);
- `figures/`.

| Folder | Report section |
|---|---|
| [`01_Dataset/`](01_Dataset) | Dataset |
| [`02_Goals_and_Questions/`](02_Goals_and_Questions) | Goals and questions (brief, plan, preliminary EDA) |
| [`03_Methods/`](03_Methods) | Methods overview; [`Robustness/`](03_Methods/Robustness) holds the Q4 sensitivity re-runs |
| [`04_Results/Q1_Spending/`](04_Results/Q1_Spending) … [`Q4_Priorities/`](04_Results/Q4_Priorities) | Results, one folder per question |
| [`05_Challenges/`](05_Challenges) | Challenges |
| [`06_Limitations/`](06_Limitations) | Limitations |
| [`report/`](report) | Final PDF, LaTeX source, figure script |
| [`common/`](common) | Shared code: data loading and cleaning, paths, seed (503) |

## Reproduce

```bash
pip install -r requirements.txt
python run_all.py
```

`run_all.py` runs every analysis in dependency order and then rebuilds the two report figures. The run takes about two minutes:

1. dataset audit and cleaning
2. Q1
3. Q2
4. Q3 (needs the Q2 styles)
5. Q4 (needs the Q3 out-of-fold scores)
6. robustness, challenges, limitations
7. report figures

To rebuild the PDF:

1. Copy `report/figures/summary_fig*.pdf` into `report/latex/figures/`.
2. Compile `report/latex/main.tex` with pdfLaTeX (Overleaf) or `tectonic main.tex`.
3. Check that the report is still two pages. Layout knobs (`\BodySize`, `\BodySkip`, `\FigWidth`) are at the top of `main.tex`.

## Data and assumptions

**Data:** *Customer Personality Analysis* (Kaggle, `imakash3011/customer-personality-analysis`, CC0), provided by Dr. Omar Romero-Hernandez. The raw file is in `01_Dataset/`.

**Assumptions not yet confirmed with the client:**

- The snapshot date and campaign timeline are unknown, so recency is excluded from all recommendations.
- "2n Cycle" education is treated as Master.
- Age is measured relative to 2014.
- `Z_CostContact` (3) and `Z_Revenue` (11) are used only in a labelled conditional scenario.
