"""Run the whole analysis in dependency order (each step writes into its own report-section folder).

    python run_all.py            # all analyses + summary figures + report HTML
    python run_all.py --no-report
"""
import os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "01_Dataset/code/data_audit.py",
    "01_Dataset/code/cleaning_log.py",
    "02_Goals_and_Questions/code/preliminary_eda.py",
    "04_Results/Q1_Spending/code/q1_spend.py",
    "04_Results/Q2_Patterns/code/q2_patterns.py",
    "04_Results/Q2_Patterns/code/q2b_complaints_webvisits_products.py",
    "04_Results/Q3_Response/code/q3_response.py",
    "04_Results/Q4_Priorities/code/q4_targeting.py",
    "04_Results/Q4_Priorities/code/q4b_followup.py",
    "03_Methods/Robustness/code/q4c_sensitivity.py",
    "05_Challenges/code/duplicates_leakage.py",
    "05_Challenges/code/gamma_fit_check.py",
    "05_Challenges/code/tenure_and_timing.py",
    "06_Limitations/code/limitations_evidence.py",
]
REPORT = ["report/code/summary_figures.py", "report/code/build_summary.py", "report/code/build_report.py"]

if __name__ == "__main__":
    steps = STEPS + ([] if "--no-report" in sys.argv else REPORT)
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONWARNINGS="ignore")
    for s in steps:
        t = time.time()
        r = subprocess.run([sys.executable, str(ROOT / s)], cwd=ROOT, env=env, capture_output=True, text=True)
        status = "OK  " if r.returncode == 0 else "FAIL"
        print(f"{status} {s}  ({time.time() - t:.0f}s)")
        if r.returncode:
            print(r.stderr[-2000:]); sys.exit(1)
