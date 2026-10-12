# Q4: Whom should campaigns focus on?

*Report sections: **Methods → Q4** and **Results → Q4**; Figure 2B–C.*

## Method
Two dimensions, crossed into four profiles. A customer worth targeting should both respond and spend.

- **Value:** spending percentile among customers who joined in the same 6-month window. Spending grows about 4% per month of tenure, so raw totals would undervalue new customers.
- **Response:** the out-of-fold Q3 score (`p_Q4`).
- **Profiles:** each dimension is split at its top third.
  - P1 = high value × high response;
  - P2 = high response, lower value;
  - P3 = high value, lower response;
  - P4 = the rest.

  The 3 × 3 matrix shows the break: the middle response third behaves like the lowest (acceptance 7% vs 3%), not like the top (36%).
- **Who they are:** each profile's average traits are compared with all customers.

## Results used in the report
| Profile | Customers | Accepted | Share of acceptors | Share of spending |
|---|---|---|---|---|
| P1 Engaged | 16.7% | 41.6% | 45.5% | 42.6% |
| P2 Responsive | 16.6% | 30.4% | 32.9% | 9.3% |
| P3 High value | 16.6% | 6.8% | 7.4% | 31.0% |
| P4 Low priority | 50.0% | 4.3% | 14.2% | 17.1% |

- **P1 traits vs all customers** (`output/q4_profile_traits.csv`):

  | Trait | P1 | All customers |
  |---|---|---|
  | Accepted an earlier campaign | 66% | 21% |
  | Average income | 75k | 52k |
  | No young children | 92% | 58% |
  | No teenagers | 76% | 52% |
  | Tenure | 14 months | 12 months |
  | Discount share | 10% | 24% |

- **Budget (Fig. 2C, `output/q4_budget_table.csv`):** contacting the top 20% by score finds 59.7% of acceptors, with 45.7% accepting. The top 30% finds 74.2%.
- **Offers by profile (`output/q4b_campaign_by_profile.csv`):** campaign 3 was accepted by 21.4% of P2 (7.5% overall). P3 accepted every earlier campaign at a below-average rate.
- **Hold-out sizing (`output/q4d_holdout_power.txt`):**
  - P1 + P2 has 675 customers with 36.0% acceptance. A 15% hold-out there detects only uplifts of 14.5 points or more.
  - Detecting a 10-point uplift needs about 1,418 targeted customers, with 213 held out.
- **Robustness (`03_Methods/Robustness`):** across the three samples, no profile share moves by more than 1.3 points (max 1.29).

## Scripts
| Script | What it does |
|---|---|
| `code/q4_targeting.py` | Tenure-adjusted value tiers × score tertiles → priority matrix and profiles P1–P4. Also: profile traits, the unadjusted-value comparison, the budget table, and a conditional profit curve (only if `Z_CostContact` and `Z_Revenue` are cost and revenue). |
| `code/q4b_followup.py` | Acceptance of each campaign by profile (cited in the report). Supplementary: integer-points scorecards (A: AUC 0.831; N, demographics only: AUC 0.756), one-line rules, a depth-3 tree, new customers, P3 vs P1, product preference by profile. |
| `code/q4d_holdout_power.py` | Two-proportion power calculation for a randomised hold-out (α = 0.05, power 0.8). |

## Files
- **Profiles:** `output/q4_profiles.csv`, `q4_profile_traits.csv`, `q4_priority_matrix.csv`, `q4_customer_tiers.csv`, `q4_profiles_unadjusted.csv`, `q4_profile_change.csv`
- **Targeting:** `output/q4_budget_table.csv`, `q4_profit_conditional.csv`, `q4_results.txt`
- **Follow-up analyses:** `output/q4b_campaign_by_profile.csv`, `q4b_scorecards.csv`, `q4b_scorecard_performance.csv`, `q4b_scorecard_bands.csv`, `q4b_rules.csv`, `q4b_new_customers*.csv`, `q4b_P3_vs_P1.csv`, `q4b_product_index.csv`, `q4b_results.txt`
- **Hold-out sizing:** `output/q4d_holdout_power.csv`, `.txt`
- **Figures:** `figures/q4_priority_matrix.png`, `q4_profit_curve_conditional.png`, `q4b_profile_campaigns_products.png`
