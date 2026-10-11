# 01 Dataset

*Report section: **Dataset***

## Source
- *Customer Personality Analysis*, Kaggle `imakash3011/customer-personality-analysis`; licence CC0: Public Domain. The data were provided by Dr. Omar Romero-Hernandez.
- `data/marketing_campaign.csv` is the raw file (tab-separated): 2,240 customers × 29 fields.
- `data/meta.json` is the Kaggle metadata, including the one-line field definitions.

The fields cover:

- demographics: birth year, education, marital status, household income, children and teenagers at home;
- enrolment date (2012-07-30 to 2014-06-29);
- recency (days since last purchase);
- two-year spending on wine, fruit, meat, fish, sweets and gold;
- purchases through web, catalog and store, plus deal purchases;
- web visits in the last month;
- complaints;
- acceptance of campaigns 1–5 and of the last campaign (`Response`).

## Analyses in this section

| Script | What it does | Output |
|---|---|---|
| `code/data_audit.py` | Structure, missing values, constant columns, category values, outliers, duplicates, enrolment range, campaign acceptance rates | `output/01_data_audit.txt` |
| `code/cleaning_log.py` | Row counts at each cleaning step, for the primary sample and both sensitivity samples | `output/00_cleaning_log.txt` |

The cleaning rules live in `common/clean.py` (`load()`), which every analysis uses.

## Cleaning steps (primary sample)

| Step | Removed | Remaining |
|---|---|---|
| Raw data | – | 2,240 |
| Missing income | 24 | 2,216 |
| Birth year < 1930 (1893, 1899, 1900) | 3 | 2,213 |
| Income = 666,666 (placeholder) | 1 | 2,212 |
| Marital status "Absurd"/"YOLO" | 4 | 2,208 |
| Duplicates (identical on all 28 non-ID fields; 358 raw rows in 176 groups) | 182 | **2,026** |

**Other decisions:**

- **Recoding:**
  - Married/Together → Partnered.
  - Single/Divorced/Widow/Alone → Single.
  - "2n Cycle" → Master (an assumption).
- **Flagged records:** seven customers with income above 150k have implausible spending patterns. They are flagged (`Flag_HighIncome`) and dropped only in a sensitivity sample.
- **Removed columns:** `Z_CostContact` (= 3) and `Z_Revenue` (= 11) are constant and undocumented, so they were removed.

**Sensitivity samples:**

- duplicates kept: n = 2,208;
- flagged high-income records dropped: n = 2,019.
