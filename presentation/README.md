# presentation/: material for the slides

The slides live in a separate repository, [`jiayihu-Jeffery/stats504_presentation`](https://github.com/jiayihu-Jeffery/stats504_presentation), which is synced with Overleaf. This folder builds what they need from the analysis outputs.

| Path | Content |
|---|---|
| `code/slide_figures.py` | Slide figures, written to `figures/*.pdf` and `*.png`. Copy the PDFs into the slides repository's `figures/`. |
| `code/slide_numbers.py` | Numbers used only on the slides. It writes `output/slide_numbers.txt`, `raw_example_customers.csv`, `income_form_comparison.csv` and `split_comparison.csv`. |

Both scripts run at the end of `run_all.py`.
