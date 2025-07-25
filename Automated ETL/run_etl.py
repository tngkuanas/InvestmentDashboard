import subprocess

scripts = [
    "fetch-stock-prices.py",
    "update-positions.py",
    "compute-performance.py",
    "compute-risk-metrics.py",
    "predict-price.py"
]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script], check=True)
    print(f"{script} completed.\n")

print("ETL pipeline completed successfully.")
