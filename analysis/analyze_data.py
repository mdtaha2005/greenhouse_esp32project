"""
Greenhouse Telemetry & Anomaly Analysis Report
Generates descriptive statistics, correlation matrices, and anomaly distribution breakdown.
"""

import pandas as pd
import numpy as np
import os

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "clean_greenhouse_data.csv"))


def analyze_data():
    print("=" * 65)
    print("GREENHOUSE TELEMETRY COMPREHENSIVE REPORT")
    print("=" * 65)

    if not os.path.exists(CSV_PATH):
        print(f"Clean CSV not found at {CSV_PATH}. Run prepare_data.py first.")
        return

    df = pd.read_csv(CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print(f"\n[Dataset Metadata]")
    print(f"  * Total Clean Records: {len(df)}")
    print(f"  * Start Time: {df['timestamp'].min()}")
    print(f"  * End Time:   {df['timestamp'].max()}")
    print(f"  * Duration:   {df['timestamp'].max() - df['timestamp'].min()}")

    print(f"\n[Environmental Sensor Statistics]")
    stats_cols = ["temperature", "humidity", "light", "gas", "vpd_kpa", "dew_point_c"]
    stats_df = df[stats_cols].describe().T[["count", "mean", "std", "min", "50%", "max"]]
    stats_df.columns = ["Count", "Mean", "Std", "Min", "Median", "Max"]
    print(stats_df.to_string())

    print(f"\n[Sensor Pearson Correlation Matrix]")
    corr_df = df[["temperature", "humidity", "light", "gas", "vpd_kpa"]].corr()
    print(corr_df.round(3).to_string())

    print(f"\n[Environmental Condition Breakdown]")
    cond_counts = df["condition"].value_counts()
    for cond, count in cond_counts.items():
        pct = (count / len(df)) * 100
        print(f"  * {cond:<10}: {count:>5} readings ({pct:>5.1f}%)")

    print(f"\n[Recent 5 Telemetry Records]")
    print(df[["timestamp", "temperature", "humidity", "light", "gas", "vpd_kpa", "condition"]].tail().to_string(index=False))

    print("\n" + "=" * 65)


if __name__ == "__main__":
    analyze_data()