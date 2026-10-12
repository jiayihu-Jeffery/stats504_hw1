Customer Personality Analysis - two-page consultant report (LaTeX)

Overleaf: synced with GitHub (jiayihu-Jeffery/two_page_summary_latex). Compiler: pdfLaTeX (default).
Files: main.tex, figures/summary_fig1.pdf, figures/summary_fig2.pdf (vector figures,
built by report/code/summary_figures.py in the analysis repository).

Page-length knobs at the top of main.tex:
  \BodySize / \BodySkip  body font size and line spacing (currently 9.2pt / 10.8pt)
  \FigWidth              width of Figure 2 (currently 0.82\linewidth)
  \FigOneWidth           width of Figure 1 (currently \linewidth)
  geometry margins       0.5in top/bottom, 0.6in left/right
Verified locally: compiles without errors or overfull boxes and gives exactly 2 pages (Tectonic/XeTeX).
If Overleaf's pdfLaTeX produces a third page, lower \FigWidth slightly (e.g. 0.78\linewidth).
