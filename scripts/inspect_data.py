from pathlib import Path

import pandas as pd

# Locate the project root:
# scripts/insp_data.py -> scripts -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Build the absolute path to the raw dataset.
file_path = PROJECT_ROOT / "data" / "raw" / "server_metrics.csv"

# Check that the dataset exists before trying to read it.
if not file_path.exists():
    raise FileNotFoundError(
        f"Dataset not found: {file_path}\n"
        "Run gen_data.py first and verify that the CSV "
        "exists in the project's data/raw folder."
    )

# Load the dataset.
df = pd.read_csv(file_path)

print("\n--- First five records ---")
print(df.head())

print("\n--- Dataset dimensions ---")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print("\n--- Column data types ---")
print(df.dtypes)

print("\n--- Missing values per column ---")
print(df.isnull().sum())

print("\n--- Numerical statistics ---")
print(df.describe())
