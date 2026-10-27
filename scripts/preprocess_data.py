from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Define paths relative to the project root
# --------------------------------------------------

# Example:
# D:/Downloads/test/scripts/preprocess.py
#               -> parent: scripts
#               -> parent.parent: test (project root)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "server_metrics.csv"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

CLEAN_FILE = OUTPUT_DIR / "server_metrics_clean.csv"


# --------------------------------------------------
# 2. Define the expected numerical columns
# --------------------------------------------------

NUMERIC_COLUMNS = [
    "cpu_percent",
    "memory_percent",
    "response_time_ms",
    "http_5xx_count",
]


# --------------------------------------------------
# 3. Check whether the input dataset exists
# --------------------------------------------------

print(f"Project root: {PROJECT_ROOT}")
print(f"Input dataset: {RAW_FILE}")
print(f"Output file: {CLEAN_FILE}")

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"\nRaw dataset not found: {RAW_FILE}\n"
        "Please run gen_data.py first and verify that "
        "server_metrics.csv exists in data/raw."
    )


# --------------------------------------------------
# 4. Load the original dataset
# --------------------------------------------------

df = pd.read_csv(RAW_FILE)

required_columns = [
    "timestamp",
    "host",
    *NUMERIC_COLUMNS,
]

missing_columns = set(required_columns) - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

if df.empty:
    raise ValueError("The input dataset contains no records.")

print("\n--- Original Dataset ---")
print(f"Number of records: {len(df)}")


# --------------------------------------------------
# 5. Convert measurements to numeric values
# --------------------------------------------------

# Invalid numeric strings become NaN so they can be handled.
for column in NUMERIC_COLUMNS:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# --------------------------------------------------
# 6. Validate timestamps and host information
# --------------------------------------------------

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce",
)

# Records without a valid timestamp or host cannot be
# reliably associated with an operational observation.
df = df.dropna(subset=["timestamp", "host"]).copy()

if df.empty:
    raise ValueError(
        "No valid records remain after timestamp validation."
    )


# --------------------------------------------------
# 7. Report missing values before cleaning
# --------------------------------------------------

print("\n--- Missing Values Before Cleaning ---")
print(df[NUMERIC_COLUMNS].isna().sum())


# --------------------------------------------------
# 8. Handle missing numerical measurements
# --------------------------------------------------

for column in NUMERIC_COLUMNS:

    # A median cannot be calculated if every value is missing.
    if df[column].notna().sum() == 0:
        raise ValueError(
            f"Column '{column}' has no valid numeric measurements."
        )

    median_value = df[column].median()

    # Fill missing measurements using the column median.
    df[column] = df[column].fillna(median_value)


# --------------------------------------------------
# 9. Validate measurement ranges
# --------------------------------------------------

# These checks flag invalid measurements rather than
# silently modifying them.

df["invalid_measurement"] = (
    ~df["cpu_percent"].between(0, 100)
    | ~df["memory_percent"].between(0, 100)
    | (df["response_time_ms"] < 0)
    | (df["http_5xx_count"] < 0)
)


# --------------------------------------------------
# 10. Flag potentially unusual operational observations
# --------------------------------------------------

# These are illustrative thresholds for the training lab,
# not universal production alert thresholds.

df["anomaly_flag"] = (
    (df["cpu_percent"] >= 90)
    | (df["memory_percent"] >= 90)
    | (df["response_time_ms"] >= 800)
    | (df["http_5xx_count"] >= 10)
)


# --------------------------------------------------
# 11. Assign an investigation status
# --------------------------------------------------

df["investigation_status"] = "Normal"

# Invalid measurements take priority in the status label.
df.loc[
    df["invalid_measurement"],
    "investigation_status",
] = "Invalid measurement"

# Only valid measurements are given the Investigate status.
df.loc[
    df["anomaly_flag"] & ~df["invalid_measurement"],
    "investigation_status",
] = "Investigate"


# --------------------------------------------------
# 12. Format timestamps consistently
# --------------------------------------------------

df["timestamp"] = df["timestamp"].dt.strftime(
    "%Y-%m-%dT%H:%M:%S"
)


# --------------------------------------------------
# 13. Save the processed dataset
# --------------------------------------------------

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    CLEAN_FILE,
    index=False,
)


# --------------------------------------------------
# 14. Display processing results
# --------------------------------------------------

print("\n--- Processing Results ---")

print(f"Records processed: {len(df)}")

remaining_missing = int(
    df[NUMERIC_COLUMNS].isna().sum().sum()
)

print(
    f"Missing numerical values remaining: {remaining_missing}"
)

print(
    "Records flagged for investigation: "
    f"{int(df['anomaly_flag'].sum())}"
)

print(
    "Records with invalid measurements: "
    f"{int(df['invalid_measurement'].sum())}"
)

print("\n--- Investigation Status Counts ---")
print(df["investigation_status"].value_counts())

print(f"\nProcessed dataset saved successfully:\n{CLEAN_FILE}")
