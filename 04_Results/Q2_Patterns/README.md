# Q2: How do purchasing patterns, product preferences and channels differ across customers?

*Report section: **Results → Q2 Patterns** (full report §5.2)*

## Analyses
| Script | What it does |
|---|---|
| `code/q2_patterns.py` | (1) Product shares, channel shares, deal ratio, web visits and spend per purchase by income quartile and number of children. (2) **Style segmentation:** K-means on standardised composition features only (6 product shares, 3 channel shares, deal ratio, web visits). Spending and income are excluded. k is chosen from 3–5 by silhouette and a minimum segment size of 5%. (3) Bootstrap stability (100 resamples, ARI). (4) Segment profiles. (5) Segment × spend tier. (6) PCA plot. |
| `code/q2b_complaints_webvisits_products.py` | Product preference index by segment (share and absolute spend), complaint analysis (Fisher exact and Mann–Whitney tests), and acceptance and spending by web-visit band. Runs after `q2_patterns.py`. |

## Key results `[Descriptive]`
- **Overall mix:** wine is 46% of the average customer's spending and meat 25%. Store accounts for 50% of purchases, web 33%, catalog 17%.
- **Income:** the catalog share rises from 7% to 29% across income quartiles, while the deal share falls from 37% to 8%.
- **Children:** customers with two or more children make about 43% of purchases on deals, against 9% for those without children.
- **Segments:** k = 3, silhouette 0.207, very stable (ARI 0.94, 5th–95th percentile 0.90–0.97).

  | Segment | Share of customers | Share of spending | Defining trait |
  |---|---|---|---|
  | S1 Value-seeking variety shoppers | 25.3% | 6.5% | Fish, fruit, sweets and gold shares about 2× average |
  | S2 Wine-focused browsers | 43.1% | 31.7% | Wine 63% of spending |
  | S3 Affluent catalog buyers | 31.6% | 61.8% | Catalog 30% of purchases |

- **Web visits:** they signal browsing, not value. Spearman correlation with spending is −0.47, and with web purchases −0.09. The 9+ visits group (n = 91) accepted the last campaign at 31.9%.
- **Complaints:** only 19 customers complained. Their acceptance (15.8%) is no different from everyone else's (15.3%; p = 1.0).

## Files
- `output/q2_*.csv` and `q2_results.txt`: k selection, segment profiles, segment × spend tier, mixes by group, segment assignments (used by Q3/Q4).
- `output/q2b_product_index_segment.csv`, `q2b_web_visits.csv`, `q2b_results.txt`.
- Figures:
  - `figures/q2_mix_by_income_children.png`
  - `figures/q2_engagement_by_children.png`
  - `figures/q2_segment_centres.png`
  - `figures/q2_segments_pca.png`
