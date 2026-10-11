# common/: shared code

These modules are imported by every analysis script. Each script locates this folder automatically, so it can be run from anywhere.

| File | Purpose |
|---|---|
| `paths.py` | Repository map: the report section → folder mapping (`SEC`), plus `out(section)` and `fig(section)` helpers, the data path and the random seed (503). |
| `clean.py` | `load(dedup=True, drop_flagged=False)` returns the analysis sample (see `01_Dataset/README.md`). It applies all cleaning rules, recodes categories, and derives `TotalSpend`, `TotalPurch`, `Children`, `Age`, `TenureMonths`, `PrevAccepted` and `AvgTicket`, plus the tenure-adjusted value tier `SpendTierAdj`. It also defines the variable-availability tiers T0, T1 and T2 used in Q3. |
| `scorecard.py` | Integer-points scorecard helpers: `cats`, `CARDS`, `fit_card`, `score`, `capture`. Used by Q4 and the robustness re-runs. |
| `tee.py` | Copies printed results into a text log in the section's `output/` folder. |
