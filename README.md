# 🌱 Smart Greenhouse Environmental Monitoring & Anomaly Detection System

An end-to-end IoT, Machine Learning, and Real-Time Telemetry Platform for precision greenhouse agriculture. Monitors Temperature, Relative Humidity, Solar Irradiance, and Air Quality / Gas levels with advanced compound agricultural anomaly detection, Vapor Pressure Deficit (VPD) modeling, predictive forecasting, and an interactive Streamlit dashboard.

---

## 🏛️ System Architecture

```
[ ESP32 Hardware Node ] ──(WiFi / HTTP POST)──▶ [ Flask REST Backend ] (Port 5000)
  ├── DHT22 (Temp & Humidity)                          │
  ├── LDR (Solar Light ADC)                            ▼
  └── MQ-135 (Air Quality ADC)                 [ SQLite Database ] (greenhouse.db)
                                                       │
        ┌────────────────────────┬─────────────────────┴───────────────────┐
        ▼                        ▼                                         ▼
[ Streamlit Dashboard ]   [ ML Anomaly Engine ]                 [ Data Pipelines ]
  ├── Crop Profiles        ├── Mahalanobis Distance               ├── ETL (prepare_data.py)
  ├── Compound Alerts      ├── Feature Engineering (VPD)          ├── Stats (analyze_data.py)
  ├── Threshold Tuning     ├── Predictive Forecast (Holt)         └── Plots (visualize_data.py)
  └── Remediation Advice   └── Anomaly Scoring (0-100%)
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Backend API
The Flask backend ingests real-time sensor streams and provides REST endpoints.
```bash
python backend/app.py
```
* Backend runs at: `http://0.0.0.0:5000`
* Active Endpoints:
  * `POST /data`: Sensor ingestion (`temperature`, `humidity`, `light`, `gas`)
  * `GET /latest`: Last 10 records
  * `GET /history?limit=100`: Filterable historical dataset
  * `GET /stats?crop=tomato`: Environmental aggregates & latest anomaly state
  * `GET /anomalies?limit=50`: Filtered anomaly events
  * `GET /health`: Service health check

### 3. Launch the Interactive Dashboard
```bash
streamlit run dashboard/dashboard.py
```
* Features:
  * **Crop Presets**: General Greenhouse, Tomatoes, Cucumbers, Leafy Greens, Seedlings.
  * **Custom Threshold Sliders**: Fine-tune temperature, humidity, light, and gas bounds.
  * **Vapor Pressure Deficit (VPD)**: Real-time transpiration stress indicator in $\text{kPa}$.
  * **Compound Agricultural Anomaly Detection**:
    * Heat Stress & Wilting Risk
    * Fungal & Mildew Disease Risk
    * Frost & Condensation Hazard
    * Leaf Scorching Risk
    * Toxic Gas / Combustion Leak Spikes
  * **Actionable Remediation Guidance**: Contextual steps for greenhouse operators.
  * **Interactive Altair Charts**: Threshold shaded bands & critical boundaries.
  * **CSV Export**: One-click download of telemetry and anomaly logs.

---

## 🔌 Hardware Setup & Firmware (`esp32/`)

* **Firmware**: Open [`esp32/greenhouse_esp32.ino`](esp32/greenhouse_esp32.ino) in Arduino IDE, set your Wi-Fi SSID/password and backend IP, and flash to your ESP32.
* **Wiring Guide**: See [`esp32/circuit_guide.md`](esp32/circuit_guide.md) for full schematic pinout table and ADC configuration.
* **Sensor Simulator (Optional)**: If testing without physical hardware:
  ```bash
  python esp32/sensor_simulator.py --scenario normal --interval 2.5
  ```

---

## 🧠 Machine Learning & Forecasting (`ml/`)

* **Train Model**:
  ```bash
  python ml/train_model.py
  ```
* **Features & Algorithms**:
  * **Multivariate Mahalanobis Distance**: Multi-dimensional deviation scoring from empirical baseline.
  * **Agronomic Feature Extraction**: Computes VPD, Dew Point, and Heat Index.
  * **Predictive Forecasting**: Holt's Double Exponential Smoothing for $10-30$ minute early warning threshold breach alerts.

---

## 📊 Data Preparation & Analytics (`analysis/`)

```bash
# Clean raw database records & calculate agronomic metrics
python analysis/prepare_data.py

# Generate statistical summary report and Pearson correlation matrix
python analysis/analyze_data.py

# Export high-resolution summary charts
python analysis/visualize_data.py
```
