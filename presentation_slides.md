# 📊 Presentation: Smart Greenhouse Environmental Monitoring & Anomaly Detection System

---

## 🖥️ Slide 1: Title Slide
### **Smart Greenhouse Environmental Monitoring & Anomaly Detection System**
*An IoT, Real-Time Analytics & Closed-Loop Control Platform for Precision Agriculture*

* **Presenter / Team**: Greenhouse IoT Engineering Team
* **Key Technologies**: ESP32 Microcontroller, Flask REST API, SQLite, Python Analytics, Streamlit

---

## 🖥️ Slide 2: Problem Statement & System Architecture
### **The Challenge & The 5-Stage Engineering Solution**

* **Problem**: Uncontrolled thermal spikes, moisture deficit, stale air, or hazardous gas leaks cause irreversible crop damage, yield loss, and fungal infections.
* **Our Solution**: An end-to-end automated closed-loop system:
  $$\text{Sensors} \longrightarrow \text{Database} \longrightarrow \text{Data Analytics} \longrightarrow \text{Anomaly Detection} \longrightarrow \text{Hardware Actuation}$$

```
[ ESP32 Sensors ] ──▶ [ Flask + SQLite DB ] ──▶ [ Data Analytics & VPD ] ──▶ [ Anomaly Engine ] ──▶ [ Hardware Relays / Dashboard ]
```

---

## 🖥️ Slide 3: Stage 1 — Sensor Data Acquisition (Edge Layer)
### **Hardware Sensing & Signal Conversion**

* **Sensors & Pinout**:
  * **DHT22 / DHT11** (`GPIO 4`): High-accuracy Temperature ($^\circ\text{C}$) & Relative Humidity ($\%$).
  * **LDR Photoresistor** (`GPIO 34`): Ambient solar light converted from 12-bit ADC to **Lux ($\text{lx}$)**.
  * **MQ-135 Gas Sensor** (`GPIO 35`): Hazardous combustion & air quality converted from ADC to **AQI (Air Quality Index)**.
* **Sampling & Transmission**:
  * Analog signal smoothing on the ESP32 to eliminate electrical noise.
  * Packaged into JSON and transmitted over Wi-Fi via HTTP `POST /data` every $2-3$ seconds.

---

## 🖥️ Slide 4: Stage 2 — Ingestion & Database Management
### **Flask REST Backend & ACID-Compliant Storage**

* **API Ingestion Engine**:
  * High-performance Python **Flask REST API** (`backend/app.py`) running on port `5000`.
  * Non-blocking ingestion endpoint (`POST /data`) with CORS support.
* **Relational SQLite Database (`greenhouse.db`)**:
  * Structured table `sensor_data`: `(id, timestamp, temperature, humidity, light, gas)`.
  * High-precision ISO-8601 timestamps attached to every incoming reading for chronological integrity.

---

## 🖥️ Slide 5: Stage 3 — Data Analytics & Plant Physiology
### **Agronomic Modeling & Climate Trends**

* **Vapor Pressure Deficit (VPD)**:
  * Calculated in $\text{kPa}$ from temperature and humidity to monitor plant transpiration stress:
    * $0.8 - 1.4\text{ kPa} \implies$ **🟢 Optimal Transpiration Sweet-Spot**
* **Atmospheric Gas Dynamics**:
  * **$\text{CO}_2$ Availability ($\text{ppm}$)**: Tracks carbon assimilation for photosynthesis.
  * **Oxygen ($\text{O}_2\%$) Modeling**: Dynamic atmospheric oxygen balance.
* **Statistical Insights**:
  * Pearson correlation matrices & Holt’s Double Exponential Smoothing for short-term trend projection.

---

## 🖥️ Slide 6: Stage 4 — Anomaly Detection Engine
### **Rule-Based & Compound Condition Intelligence**

* **Multi-Factor Agricultural Hazard Rules**:
  * 🔥 **High Temperature Alert**: Overheating conditions ($\text{Temp} > 40.0^\circ\text{C}$).
  * 🫁 **Air Quality / Smoke Spike**: Elevated contaminants ($\text{AQI} > 150$).
  * 🍄 **Compound Hazards**: Warm stagnant air + high humidity (Fungal Risk) or high heat + dry air (Wilt Risk).
* **Machine Learning Anomaly Scoring**:
  * Multivariate Mahalanobis Distance ($D_M$) evaluates multi-sensor deviations from baseline distributions.
* **Contextual Remediation**:
  * Generates instant corrective actions (e.g. *"Activate misting & cooling fans"*).

---

## 🖥️ Slide 7: Stage 5 — Hardware Output, Actuation & Dashboard
### **Closed-Loop Feedback & Real-Time HMI**

* **1. Edge Hardware Actuation**:
  * The backend returns anomaly flags in the **HTTP POST Response** back to the ESP32.
  * The ESP32 triggers physical hardware on GPIO pins:
    * **Relay Modules**: Switches ON cooling fans, exhaust vents, or misting water pumps.
    * **Status LED / Alarm**: Real-time visual and audible alert signaling.
* **2. Interactive Streamlit Dashboard**:
  * Live KPI cards with instant deltas ($\Delta$).
  * **Threshold Sliders**: Allows operators to set custom limits for all metrics on the fly.
  * Interactive time-series trend charts with threshold boundary lines.

---

## 🖥️ Slide 8: Results & Conclusion
### **Project Impact & Key Takeaways**

* **Summary of Achievements**:
  * ✅ Fully integrated IoT hardware node streaming live physical sensor data.
  * ✅ Robust backend and database infrastructure maintaining continuous history.
  * ✅ Advanced agronomic analytics (VPD, $\text{CO}_2$, $\text{O}_2$, Lux, AQI).
  * ✅ Dual anomaly detection engine with actionable operator checklists.
  * ✅ Closed-loop hardware actuation protecting crops 24/7.
* **Agricultural Value**: Maximizes photosynthetic yield, prevents crop disease, and conserves water and energy.
