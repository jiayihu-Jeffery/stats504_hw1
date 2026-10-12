# report/: final deliverable

| File | Content |
|---|---|
| `final_report.pdf` | **Final two-page consultant report**: dataset, goals and questions, methods, results (2 figures, 2 tables), challenges, limitations. |
| `latex/main.tex` | LaTeX source. It compiles with pdfLaTeX (Overleaf) or Tectonic. Layout knobs (`\BodySize`, `\BodySkip`, `\FigWidth`, `\FigOneWidth`) are at the top. |
| `latex/figures/summary_fig1.pdf`, `summary_fig2.pdf` | Vector figures used by the LaTeX source. |
| `code/summary_figures.py` | Builds `figures/summary_fig1.*` (income curve, Shapley shares, spend by income and kids, shopping styles) and `figures/summary_fig2.*` (past response, profiles, targeting curve). It reads the section outputs. |
| `output/summary_fig_spend_by_income_kids.csv` | Data for Figure 1C. |

**Rebuild:**

1. Run `python run_all.py` from the repository root.
2. Copy `figures/summary_fig*.pdf` into `latex/figures/`.
3. Compile `latex/main.tex`.
4. Check that the report is still two pages.

The root [`README.md`](../README.md) maps every number in the report to the output file that produced it.
