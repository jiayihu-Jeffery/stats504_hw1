"""01 Dataset - cleaning log: row counts at each cleaning step for the primary and sensitivity samples."""
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common").is_dir()); sys.path.insert(0, str(ROOT / "common"))
import pandas as pd
from clean import load, DATA
from paths import out
OUT = out("dataset")

lines = []
for label, kw in [("PRIMARY (deduplicated)", dict(dedup=True)),
                  ("SENSITIVITY: not deduplicated", dict(dedup=False)),
                  ("SENSITIVITY: deduplicated, flagged high-income dropped", dict(dedup=True, drop_flagged=True))]:
    log = []; d = load(log=log, **kw)
    lines.append(f"== {label} ==")
    prev = None
    for s, n in log:
        lines.append(f"  {s:50s} {n:5d}" + ("" if prev is None else f"  (-{prev - n})")); prev = n
    lines.append(f"  final n = {len(d)}; Response rate = {d.Response.mean():.4f}; "
                 f"flagged Income>150k = {d.Flag_HighIncome.sum()}; TotalPurch==0: {(d.TotalPurch == 0).sum()}")
raw = pd.read_csv(DATA, sep="\t")
g = raw.drop(columns="ID"); dup = g[g.duplicated(keep=False)]
lines.append(f"\nRaw duplicate check: {len(dup)} rows in {dup.drop_duplicates().shape[0]} groups identical on all non-ID fields")
d = load()
lines.append("\nPrimary sample category counts:")
lines.append(d.Edu.value_counts().to_string()); lines.append(d.Marital.value_counts().to_string())
txt = "\n".join(lines); print(txt)
(OUT / "00_cleaning_log.txt").write_text(txt + "\n")
