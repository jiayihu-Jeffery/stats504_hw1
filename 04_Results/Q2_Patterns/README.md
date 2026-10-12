# Q2: How do customers differ in how, what and where they buy?

*Report sections: **Methods → Q2** and **Results → Q2** (style table); Figure 1D.*

## Analyses
| Script | What it does |
|---|---|
| `code/q2_patterns.py` | (1) Product shares, channel shares, deal ratio, web visits and spend per purchase by income quartile and number of children. (2) **Style segmentation:** K-means on standardised composition features only (6 product shares, 3 channel shares, deal ratio, web visits). Spending and income are excluded. k is chosen from 3–5 by silhouette and a minimum segment size of 5%. (3) Bootstrap stability (100 resamples, ARI). (4) Segment profiles. (5) Segment × spend tier. (6) PCA plot. |
| `code/q2b_complaints_webvisits_products.py` | Product preference index by segment (share and absolute spend), complaint analysis (Fisher exact and Mann–Whitney tests), and acceptance and spending by web-visit band. Runs after `q2_patterns.py`. |

## Key results
- **Overall mix:** wine is 46% of the average customer's spending and meat 25%. Store accounts for 50% of purchases, web 33%, catalogue 17%.
- **Income:** the catalogue share rises from 7% to 29% across income quartiles, while the deal share falls from 37% to 8%.
- **Children:** customers with two or more children make about 43% of purchases on deals, against 9% for those without children.
- **Segments:** k = 3, silhouette 0.207 (the clusters overlap). Stable under resampling (bootstrap ARI 0.94, 5th–95th percentile 0.90–0.97), but **sensitive to feature weighting**. With products, channels, deal ratio and visits weighted equally, the ARI is 0.38. 87% of S3 stays together (robust), against 77% of S1 and 53% of S2 (tendencies).

  | Segment | Share of customers | Share of spending | Defining trait |
  |---|---|---|---|
  | S1 Value-seeking variety shoppers | 25.3% | 6.5% | Fish, fruit, sweets and gold shares about 2× average |
  | S2 Wine-focused browsers | 43.1% | 31.7% | Wine 63% of spending |
  | S3 Affluent catalogue buyers | 31.6% | 61.8% | Catalogue 30% of purchases |

- **Web visits:** they signal browsing, not value. Spearman correlation with spending is −0.47, and with web purchases −0.09. The 9+ visits group (n = 91) accepted the last campaign at 31.9%.
- **Complaints:** only 19 customers complained. Their acceptance (15.8%) is no different from everyone else's (15.3%; p = 1.0).

## How the report uses these results
- **Style table:**
  - shares of customers and spending;
  - purchases in two years;
  - spend per purchase;
  - discount share;
  - largest product shares;
  - web / catalogue / store mix.

  Source: `output/q2_segment_profiles.csv`. The "All customers" row comes from `q2_results.txt` (overall means).
- **Income and children:** `output/q2_profile_by_IncomeQ.csv` and `q2_profile_by_Children.csv`.
- **Web visits vs spending:** `output/q2b_results.txt`.
- **Choice of k:** `output/q2_k_selection.csv` (silhouette 0.207 / 0.174 / 0.164 for k = 3 / 4 / 5).
- **Stability and weighting:** `output/q2_results.txt` and `q2_weighting_sensitivity.csv`.
- **Complaints:** not cited in the report beyond the small-group limitation.

## Files
- `output/q2_*.csv` and `q2_results.txt`: k selection, segment profiles, segment × spend tier, mixes by group, segment assignments (used by Q3/Q4).
- `output/q2_weighting_sensitivity.csv`, `q2_weighting_crosstab.csv`: the equal-block-weight re-clustering.
- `output/q2b_product_index_segment.csv`, `q2b_web_visits.csv`, `q2b_results.txt`.
- Figures:
  - `figures/q2_mix_by_income_children.png`
  - `figures/q2_engagement_by_children.png`
  - `figures/q2_segment_centres.png`
  - `figures/q2_segments_pca.png`
