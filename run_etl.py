import subprocess

scripts = [
    "Automated ETL/fetch-stock-prices.py",
    "Analytics/update-positions.py",
    "Analytics/compute-performance.py",
    "Analytics/compute-risk-metrics.py",
    "Analytics/predict-price.py"
]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script], check=True)
    print(f"{script} completed.\n")

print("ETL pipeline completed successfully.")
