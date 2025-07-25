import subprocess, sys

scripts = [
    "Automated ETL/fetch-stock-prices.py",
    "Analytics/update-positions.py",
    "Analytics/compute-performance.py",
    "Analytics/compute-risk-metrics.py",
    "Analytics/predict-price.py"
]


for script in scripts:
    print(f"Running {script}...")
    subprocess.run([sys.executable, script], check=True)  # <-- key change
    print(f"{script} done.\n")

print("ETL pipeline completed successfully.")
