# 02 Goals and questions

*Report section: **Goals and questions***

## Client requirements (from the client brief)

The client asked four questions:

1. Which demographic and household characteristics are associated with higher overall spending?
2. How do purchasing patterns, product preferences and shopping channels differ across customers?
3. Which characteristics and behaviours are associated with a greater likelihood of accepting a campaign?
4. Which customer profiles should future marketing prioritise?

The client also expects the report to:

- produce practical guidance on allocating marketing resources;
- separate descriptive relationships from conclusions that can support decisions;
- state the data limitations.

## Files

| File | Content |
|---|---|
| `analysis_plan.md` | Our initial plan (in Chinese): client needs, our method suggestions, the data audit, questions for the client, and the plan for each question. |
| `execution_prompt.md` | The revised, step-by-step execution specification after an internal senior-analyst review. Changes include deduplicating before validation, segmenting by style rather than value, and the variable-availability tiers. |
| `code/preliminary_eda.py` | The first exploratory pass used to write the plan. |
| `output/02_preliminary_eda.txt`, `figures/` | The preliminary EDA results. |

**Note:** the preliminary EDA used provisional cleaning and kept the duplicate records. Its numbers are exploratory and superseded by `04_Results`.
