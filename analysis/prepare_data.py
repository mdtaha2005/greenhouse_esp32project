"""
Greenhouse Data Preparation & ETL Pipeline
Cleans telemetry, enforces physical sensor bounds, computes agronomic features (VPD, Dew Point),
and applies rule-based anomaly labeling.
"""

import sqlite3
import pandas as pd
import numpy as np
import math
import os
import sys

# Add anomaly detector to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "anomaly")))
from anomaly_detector import detect_anomalies_detailed

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "greenhouse.db"))
OUTPUT_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "clean_greenhouse_data.csv"))


def compute_vpd(temp: float, hum: float) -> float:
    if pd.isna(temp) or pd.isna(hum) or hum <= 0:
        return np.nan
    vp_sat = 0.61078 * math.exp((17.27 * temp) / (temp + 237.3))
    vp_act = vp_sat * (hum / 100.0)
    return round(max(0.0, vp_sat - vp_act), 3)


def compute_dew_point(temp: float, hum: float) -> float:
    if pd.isna(temp) or pd.isna(hum) or hum <= 0:
        return np.nan
    a, b = 17.27, 237.7
    h_ratio = max(0.01, min(1.0, hum / 100.0))
    alpha = ((a * temp) / (b + temp)) + math.log(h_ratio)
    return round((b * alpha) / (a - alpha), 2)


def prepare_data():
    print("=" * 65)
    print("GREENHOUSE DATA PREPARATION & ETL PIPELINE")
    print("=" * 65)

    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}.")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT id, timestamp, temperature, humidity, light, gas
        FROM sensor_data
        ORDER BY timestamp ASC
    """, conn)
    conn.close()

    print(f"Raw readings loaded: {len(df)}")

    # 1. Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 2. Drop nulls and exact duplicates
    df = df.dropna(subset=["temperature", "humidity", "light", "gas"])
    df = df.drop_duplicates(subset=["timestamp", "temperature", "humidity", "light", "gas"])

    # 3. Physical sensor sanity boundaries
    df = df[
        (df["temperature"] >= -20.0) & (df["temperature"] <= 65.0) &
        (df["humidity"] >= 0.0) & (df["humidity"] <= 100.0) &
        (df["light"] >= 0) & (df["light"] <= 4095) &
        (df["gas"] >= 0) & (df["gas"] <= 4095)
    ]

    # 4. Feature Engineering (VPD & Dew Point)
    df["vpd_kpa"] = df.apply(lambda r: compute_vpd(r["temperature"], r["humidity"]), axis=1)
    df["dew_point_c"] = df.apply(lambda r: compute_dew_point(r["temperature"], r["humidity"]), axis=1)

    # 5. Rule-based anomaly evaluation
    conditions = []
    severity_scores = []
    anomaly_flags = []

    for _, row in df.iterrows():
        eval_res = detect_anomalies_detailed(
            temperature=row["temperature"],
            humidity=row["humidity"],
            light=row["light"],
            gas=row["gas"]
        )
        conditions.append(eval_res["status"])
        severity_scores.append(eval_res["severity_score"])
        anomaly_flags.append(1 if eval_res["status"] != "NORMAL" else 0)

    df["condition"] = conditions
    df["severity_score"] = severity_scores
    df["is_anomaly"] = anomaly_flags

    # 6. Sort and Export
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nSanitized & Engineered readings: {len(df)}")
    print(f"Anomalies identified: {df['is_anomaly'].sum()} ({(df['is_anomaly'].mean()*100):.1f}%)")
    print(f"\nSaved clean dataset to -> {OUTPUT_CSV}")
    print("=" * 65)


if __name__ == "__main__":
    prepare_data()