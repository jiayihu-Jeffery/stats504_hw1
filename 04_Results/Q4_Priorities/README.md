# Q4: Which customer profiles should future marketing prioritise?

*Report section: **Results → Q4 Priorities** (full report §6)*

## Analyses
| Script | What it does |
|---|---|
| `code/q4_targeting.py` | Builds the **priority matrix** from the tenure-adjusted value tier (spend ranked within 6-month joining cohorts) × the tertile of the out-of-fold Scenario A score, and merges the cells into **profiles P1–P4**. Also compares against unadjusted value; builds the **budget table** (contact top 10/20/30/50%) for the Scenario A, T0 and Scenario B scores; and a **conditional profit curve** that assumes `Z_CostContact` = cost and `Z_Revenue` = revenue, which the client has not confirmed. |
| `code/q4b_followup.py` | Analyses requested in the client review: (1) **Scorecard A** (6 items) and **Scorecard N** (no campaign history needed), integer points with cross-validated performance, plus score bands; simple **rules** compared with the model; a depth-3 tree as a cross-check. (2) **New customers** (joined ≤ 6 months ago). (3) **P3 vs P1** comparison and **acceptance of each earlier campaign by profile**. (4) **Product preference index by profile.** |

## Key results
**Profiles** `[Robust]`:

| Profile | Share of customers | Accepted last campaign | Share of acceptors | Share of spending |
|---|---|---|---|---|
| P1 Engaged high-value | 15.9% | 44.7% | 46.5% | 40.9% |
| P2 Responsive, lower-spend | 17.4% | 31.2% | 35.5% | 8.9% |
| P3 High value, low response | 17.5% | 5.6% | 6.5% | 32.7% |
| P4 Low priority | 49.2% | 3.6% | 11.6% | 17.5% |

**Targeting tools:**

- **Budget:** contacting the top 20% by score reaches 63.9% of acceptors (48.9% acceptance). The top 30% reaches 76.1%.
- **Scorecard A:** AUC 0.831; reaches 60.1% of acceptors at 20% contact. Suggested cut-off: 34 points or more. Scorecard N: AUC 0.756 and 47.1%.
- **Rule R1** ("accepted any earlier campaign"): flags 21.0% of customers, with 40.7% acceptance and 55.8% of acceptors.

**Other findings:**

- **New customers:** 25.8% of the base, with 9.4% acceptance vs 17.4% for everyone else. Ranked among themselves by Scorecard A, the top fifth holds 69.4% of new-customer acceptors.
- **Campaigns appealed to different profiles:**
  - P1 accepted campaigns 1, 4, 5 and the last one;
  - campaign 3 was accepted by 23.2% of P2;
  - campaign 4 was the only campaign P3 accepted at about the average rate (7.6% vs 7.7%).
- **Conditional profit** (only if the cost/revenue assumption holds): contacting everyone loses 2,668 units; contacting the top ≈ 14% earns +975.

## Files
- `output/q4_priority_matrix.csv`, `q4_profiles.csv`, `q4_profiles_unadjusted.csv`, `q4_profile_change.csv`, `q4_customer_tiers.csv`
- `output/q4_budget_table.csv`, `q4_profit_conditional.csv`
- `output/q4b_scorecards.csv`, `q4b_scorecard_performance.csv`, `q4b_scorecard_bands.csv`, `q4b_rules.csv`
- `output/q4b_new_customers*.csv`, `q4b_P3_vs_P1.csv`, `q4b_campaign_by_profile.csv`, `q4b_product_index.csv`, `q4b_results.txt`
- Figures:
  - `figures/q4_priority_matrix.png`
  - `figures/q4_profit_curve_conditional.png`
  - `figures/q4b_profile_campaigns_products.png`
