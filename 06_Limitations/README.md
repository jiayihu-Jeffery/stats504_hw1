# 06 Limitations

*Report section: **Limitations***. `code/limitations_evidence.py` collects the data facts behind each limitation. Its outputs are `output/limitations_evidence.txt`, `small_groups.csv` and `campaign_acceptance_rates.csv`.

| Limitation | Evidence |
|---|---|
| **Association, not causation** | The file has no field recording who was contacted in each campaign, and no randomisation. A high predicted acceptance does not mean the campaign *causes* purchases. We recommend a random 10–20% hold-out in the next campaign. |
| **Possible leakage** | The snapshot date is unknown, so the behaviour fields (spend, purchases, recency) may post-date the last campaign. Behaviour-based scores are therefore optimistic if those fields were recorded after the campaign. Recency is left out of every recommendation (`05_Challenges`). |
| **Generalisability** | Campaign acceptance ranges from 1.34% (campaign 2) to 14.9% (last campaign, raw file). The campaigns differed in unknown ways, so the tools apply to offers like the last one. Enrolments span 2012-07 to 2014-06. |
| **Small groups and many comparisons** | Basic education (49), 3 children (45), 2 young children (41), complaints (19), 9+ web visits (91). Single descriptive differences in these groups are exploratory. |
| **Undocumented costs** | `Z_CostContact` = 3 and `Z_Revenue` = 11 are constant and undocumented, so profit figures are only conditional (Q4) and are not part of the final report. |
