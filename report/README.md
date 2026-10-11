# report/: deliverables

| File | Content |
|---|---|
| `two_page_summary.pdf` | **Final deliverable**: two-page consultant team summary, covering dataset, goals and questions, methods, results (with 2 figures), challenges and limitations. |
| `two_page_summary.md` / `.html` | Source and rendered version of the summary. |
| `report.pdf` | Full consultant report (revision 2, after client review): executive summary, profile cards, scorecards, appendices A–E. |
| `report.md` / `.html` | Source and rendered version of the full report. |
| `archive/report_v1.md` | First version of the full report, before the client review. |
| `code/summary_figures.py` | Builds `figures/summary_fig1.png` and `summary_fig2.png` from the section outputs (palette: validated categorical slots 1–3). |
| `code/build_summary.py`, `code/build_report.py` | Render the Markdown to self-contained HTML with images embedded. |
| `output/summary_fig_spend_by_income_kids.csv` | Data for Figure 1B. |

**Rebuild:**

1. Run `python run_all.py` from the repository root.
2. Open each `.html` file in a browser and print it to PDF (Letter, no headers or footers).
3. Check that the summary is still two pages.

Every number in both documents comes from the `output/` folder of the section that produced it. Appendix D of the full report maps each table and figure to its source file.
