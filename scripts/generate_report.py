from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Define paths relative to the project root
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "server_metrics_clean.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operations_summary.txt"
)


# --------------------------------------------------
# 2. Load the processed dataset
# --------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Processed dataset not found: {INPUT_FILE}\n"
        "Run preprocess.py first."
    )

df = pd.read_csv(INPUT_FILE)

if df.empty:
    raise ValueError(
        "The processed dataset contains no records."
    )


# --------------------------------------------------
# 3. Generate operational statistics
# --------------------------------------------------

summary = {
    "Total observations": len(df),

    "Unique hosts": df["host"].nunique(),

    "Average CPU utilization (%)": round(
        df["cpu_percent"].mean(), 2
    ),

    "Maximum CPU utilization (%)": round(
        df["cpu_percent"].max(), 2
    ),

    "Average memory utilization (%)": round(
        df["memory_percent"].mean(), 2
    ),

    "Average response time (ms)": round(
        df["response_time_ms"].mean(), 2
    ),

    "Total HTTP 5xx errors": int(
        df["http_5xx_count"].sum()
    ),

    "Records flagged for investigation": int(
        df["anomaly_flag"].sum()
    ),
}


# --------------------------------------------------
# 4. Build the report
# --------------------------------------------------

report = [
    "AIOPS OPERATIONAL DATA SUMMARY",
    "=" * 35,
    "",
]

for key, value in summary.items():
    report.append(f"{key}: {value}")


# --------------------------------------------------
# 5. Add investigation details
# --------------------------------------------------

report.extend([
    "",
    "Investigation Details",
    "-" * 35,
])

investigations = df[df["anomaly_flag"]]

if investigations.empty:
    report.append(
        "No observations were flagged for investigation."
    )
else:
    for _, row in investigations.iterrows():
        report.append(
            f"{row['timestamp']} | "
            f"{row['host']} | "
            f"CPU={row['cpu_percent']}% | "
            f"Memory={row['memory_percent']}% | "
            f"Latency={row['response_time_ms']} ms | "
            f"HTTP 5xx={row['http_5xx_count']}"
        )


# --------------------------------------------------
# 6. Save the report to a text file
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)


# --------------------------------------------------
# 7. Display the report
# --------------------------------------------------

print("\n".join(report))

print(
    f"\nReport saved successfully to:\n{OUTPUT_FILE}"
)
