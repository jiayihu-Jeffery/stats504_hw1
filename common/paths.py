"""Central map of the repository layout. Folders mirror the headings of the final report."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "01_Dataset" / "data" / "marketing_campaign.csv"
SEED = 503

SEC = {
    "dataset":     ROOT / "01_Dataset",
    "goals":       ROOT / "02_Goals_and_Questions",
    "robustness":  ROOT / "03_Methods" / "Robustness",
    "q1":          ROOT / "04_Results" / "Q1_Spending",
    "q2":          ROOT / "04_Results" / "Q2_Patterns",
    "q3":          ROOT / "04_Results" / "Q3_Response",
    "q4":          ROOT / "04_Results" / "Q4_Priorities",
    "challenges":  ROOT / "05_Challenges",
    "limitations": ROOT / "06_Limitations",
    "report":      ROOT / "report",
}


def out(section):
    """Output (data) folder of a report section; created on demand."""
    p = SEC[section] / "output"; p.mkdir(parents=True, exist_ok=True); return p


def fig(section):
    """Figure folder of a report section; created on demand."""
    p = SEC[section] / "figures"; p.mkdir(parents=True, exist_ok=True); return p
