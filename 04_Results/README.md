# 04 Results

*Report section: **Results***. Each subfolder is one question of the client brief:

| Folder | Question | Headline |
|---|---|---|
| [`Q1_Spending`](Q1_Spending) | Who spends more? | Income and young children account for about 90% of the variation the model explains. Each young child is associated with ≈ 38% lower spending. |
| [`Q2_Patterns`](Q2_Patterns) | How do patterns differ? | Three stable shopping styles. Affluent catalog buyers are 32% of customers but 62% of spending. |
| [`Q3_Response`](Q3_Response) | Who accepts campaigns? | Earlier acceptance is the strongest signal (8.6% → 82%). The primary model's AUC is 0.858. |
| [`Q4_Priorities`](Q4_Priorities) | Whom to prioritise? | P1 + P2 (one-third of customers) hold 82% of acceptors. A 6-question scorecard reaches 60% of acceptors at 20% contact. |

**Run order:** Q1 → Q2 (`q2_patterns.py`, then `q2b_...`) → Q3 → Q4 (`q4_targeting.py`, then `q4b_followup.py`). `run_all.py` at the root handles this.
