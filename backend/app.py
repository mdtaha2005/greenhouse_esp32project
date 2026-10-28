"""
Greenhouse Monitoring System - REST API Backend
Flask API providing ingestion, query endpoints, statistics, and anomaly detection.
"""

from flask import Flask, request, jsonify, make_response
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory / anomaly module to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "anomaly"))
from anomaly_detector import detect_anomalies_detailed, CROP_PRESETS

app = Flask(__name__)
DB_NAME = os.path.join(os.path.dirname(__file__), "greenhouse.db")


# CORS Middleware Helper
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


def get_db_connection():
    """Create a thread-safe database connection."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Ensure sensor_data table and indexes exist."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            light INTEGER,
            gas INTEGER
        )
    """)
    # Index for fast ordered queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sensor_data_id ON sensor_data (id DESC)")
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def home():
    """Root health check endpoint."""
    return "Greenhouse backend is running!"


@app.route("/health", methods=["GET"])
def health():
    """Detailed health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) as cnt, MAX(timestamp) as last_ts FROM sensor_data")
        row = cursor.fetchone()
        count = row["cnt"] if row else 0
        last_ts = row["last_ts"] if row else None
        conn.close()
        return jsonify({
            "status": "healthy",
            "server_time": datetime.now().isoformat(),
            "total_records": count,
            "last_reading_time": last_ts
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/data", methods=["POST"])
def receive_data():
    """
    Ingestion endpoint for ESP32 and sensor telemetry.
    Accepts JSON: { "temperature": float, "humidity": float, "light": int, "gas": int }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Invalid or missing JSON payload"}), 400

    temperature = data.get("temperature")
    humidity = data.get("humidity")
    light = data.get("light")
    gas = data.get("gas")
    timestamp = data.get("timestamp") or datetime.now().isoformat()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_data (timestamp, temperature, humidity, light, gas)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, temperature, humidity, light, gas))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Evaluate real-time anomaly
        anomaly_info = detect_anomalies_detailed(
            temperature=temperature,
            humidity=humidity,
            light=light,
            gas=gas
        )

        return jsonify({
            "status": "saved",
            "id": new_id,
            "timestamp": timestamp,
            "condition": anomaly_info["status"],
            "severity_score": anomaly_info["severity_score"],
            "alerts": anomaly_info["anomalies"]
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/latest", methods=["GET"])
def latest():
    """
    Backward-compatible endpoint returning last 10 rows as raw list of tuples/rows.
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT id, timestamp, temperature, humidity, light, gas
            FROM sensor_data
            ORDER BY id DESC
            LIMIT 10
        """)
        rows = [list(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/history", methods=["GET"])
def history():
    """
    Query historical sensor data with flexible limit and pagination.
    Example: /history?limit=100
    """
    limit = request.args.get("limit", default=100, type=int)
    limit = max(1, min(limit, 2000))

    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT id, timestamp, temperature, humidity, light, gas
            FROM sensor_data
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({
            "count": len(results),
            "data": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """
    Aggregate statistics (min, max, avg, count) and latest anomaly status.
    """
    crop = request.args.get("crop", default="general", type=str)
    thresholds = CROP_PRESETS.get(crop, CROP_PRESETS["general"])

    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_count,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(temperature) as avg_temp,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(humidity) as avg_humidity,
                MIN(light) as min_light,
                MAX(light) as max_light,
                AVG(light) as avg_light,
                MIN(gas) as min_gas,
                MAX(gas) as max_gas,
                AVG(gas) as avg_gas
            FROM sensor_data
        """)
        agg = dict(cursor.fetchone())

        # Get latest reading
        cur_latest = conn.execute("""
            SELECT id, timestamp, temperature, humidity, light, gas
            FROM sensor_data
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        latest_data = dict(cur_latest) if cur_latest else None
        conn.close()

        latest_anomaly = None
        if latest_data:
            latest_anomaly = detect_anomalies_detailed(
                temperature=latest_data.get("temperature"),
                humidity=latest_data.get("humidity"),
                light=latest_data.get("light"),
                gas=latest_data.get("gas"),
                thresholds=thresholds
            )

        return jsonify({
            "aggregates": agg,
            "latest_reading": latest_data,
            "current_status": latest_anomaly,
            "crop_profile": thresholds["name"]
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/anomalies", methods=["GET"])
def get_anomalies():
    """
    Returns recent readings that trigger anomaly alerts.
    """
    limit = request.args.get("limit", default=100, type=int)
    crop = request.args.get("crop", default="general", type=str)
    thresholds = CROP_PRESETS.get(crop, CROP_PRESETS["general"])

    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT id, timestamp, temperature, humidity, light, gas
            FROM sensor_data
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        anomaly_records = []
        for r in rows:
            eval_res = detect_anomalies_detailed(
                temperature=r.get("temperature"),
                humidity=r.get("humidity"),
                light=r.get("light"),
                gas=r.get("gas"),
                thresholds=thresholds
            )
            if eval_res["status"] != "NORMAL":
                record = r.copy()
                record["condition"] = eval_res["status"]
                record["severity_score"] = eval_res["severity_score"]
                record["alerts"] = eval_res["anomalies"]
                record["remediations"] = eval_res["remediations"]
                anomaly_records.append(record)

        return jsonify({
            "total_inspected": len(rows),
            "anomaly_count": len(anomaly_records),
            "anomalies": anomaly_records
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    init_database()
    print("Starting Greenhouse Backend API on 0.0.0.0:5000...")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )