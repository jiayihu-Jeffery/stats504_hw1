# 04 Results

*Report section: **Methods** and **Results***. Each subfolder answers one question of the client brief. The root [`README.md`](../README.md) maps every number in the final report to its file.

| Folder | Question | Final method | Headline in the report |
|---|---|---|---|
| [`Q1_Spending`](Q1_Spending) | Who spends more? | Gamma regression, income as a smooth curve | Income and young children explain about 90% of what the model explains; about 38% less spending per young child. |
| [`Q2_Patterns`](Q2_Patterns) | How do customers differ in how, what and where they buy? | k-means on 11 shopping-style measures | Three styles. Affluent catalogue buyers are 32% of customers but 62% of spending. |
| [`Q3_Response`](Q3_Response) | Who accepts campaigns? | One pre-specified logistic regression | Acceptance rises from 9% to 82% with earlier acceptances. On unseen customers, ranking accuracy is 0.84. |
| [`Q4_Priorities`](Q4_Priorities) | Whom should campaigns focus on? | Value × response profiles P1–P4 | P1 (17% of customers) holds 46% of acceptors and 43% of spending. P1 traits: earlier acceptance, higher income, no young children. |

**Run order:** Q1 → Q2 → Q3 (needs Q2 styles) → Q4 (needs Q3 out-of-fold scores). `run_all.py` at the root handles this.
