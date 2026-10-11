# STATS 504 HW1: Customer Personality Analysis (Consulting Project)

A statistical consulting analysis for a retail client. The client asked four questions:

- **Q1.** Who spends more?
- **Q2.** How do purchasing patterns, product preferences and channels differ?
- **Q3.** Who is more likely to accept a marketing campaign?
- **Q4.** Which customer profiles should future marketing prioritise?

**Final deliverable:** [`report/two_page_summary.pdf`](report/two_page_summary.pdf), a two-page consultant team summary.
**Full report:** [`report/report.pdf`](report/report.pdf), the detailed consultant report with appendices.

## Repository layout: folders follow the report's headings

| Report heading | Folder | What is inside |
|---|---|---|
| Dataset | [`01_Dataset/`](01_Dataset) | Raw data, data audit, cleaning log |
| Goals and questions | [`02_Goals_and_Questions/`](02_Goals_and_Questions) | Client requirements, analysis plan, preliminary EDA |
| Methods | [`03_Methods/`](03_Methods) | Method overview; [`Robustness/`](03_Methods/Robustness) holds the sensitivity re-runs |
| Results | [`04_Results/`](04_Results) | One subfolder per question |
| Results → Q1 Spending | [`04_Results/Q1_Spending/`](04_Results/Q1_Spending) | Gamma regression, spline, Shapley R² |
| Results → Q2 Patterns | [`04_Results/Q2_Patterns/`](04_Results/Q2_Patterns) | Product/channel mixes, style segmentation, complaints, web visits |
| Results → Q3 Response | [`04_Results/Q3_Response/`](04_Results/Q3_Response) | Acceptance rates, explanatory logit, predictive models |
| Results → Q4 Priorities | [`04_Results/Q4_Priorities/`](04_Results/Q4_Priorities) | Priority profiles, scorecards, rules, new customers, budget |
| Challenges | [`05_Challenges/`](05_Challenges) | Evidence for each challenge: duplicates, model fitting, tenure, timing |
| Limitations | [`06_Limitations/`](06_Limitations) | Data facts behind each limitation |
| (deliverables) | [`report/`](report) | Final PDFs, Markdown sources, figure and build scripts |
| (shared code) | [`common/`](common) | Cleaning, paths, scorecard helpers used by every analysis |

Every analysis folder has the same structure:

- `README.md`: what was done and why, with the key results;
- `code/`: the scripts;
- `output/`: result tables and text logs (the data behind the report);
- `figures/`: plots, where the section has any.

## Reproduce everything

```bash
pip install -r requirements.txt
python run_all.py          # runs all analyses in dependency order, then rebuilds figures and report HTML
```

The full run takes about 1 minute. To recreate the PDFs, open `report/two_page_summary.html` and `report/report.html` in a browser and print to PDF (Letter, no headers or footers).

**Dependency order:**

1. dataset audit and cleaning
2. Q1
3. Q2
4. Q3 (needs Q2 segments)
5. Q4 (needs Q3 out-of-fold scores and Q2 segments)
6. robustness, challenges, limitations
7. report

## Data

*Customer Personality Analysis* dataset (Kaggle, `imakash3011/customer-personality-analysis`; licence CC0: Public Domain), provided by Dr. Omar Romero-Hernandez. It has 2,240 customers and 29 fields. After cleaning, the analysis sample is 2,026 customers (see [`01_Dataset`](01_Dataset)).

## Key assumptions (unconfirmed with the client)

- The snapshot date and the campaign timeline are unknown. "Days since last purchase" (recency) is therefore excluded from all recommendations.
- "2n Cycle" education is treated as Master level.
- Age is measured relative to 2014.
- `Z_CostContact` (3) and `Z_Revenue` (11) are undocumented constants and are used only in a labelled conditional scenario.
