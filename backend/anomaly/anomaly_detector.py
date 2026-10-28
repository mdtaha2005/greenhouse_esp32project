"""
Greenhouse Environmental Anomaly Detector
Evaluates sensor telemetry against customizable thresholds with unit conversion for:
- Temperature (°C)
- Humidity (%)
- Solar Light (Lux / Intensity %)
- Air Quality Index (AQI)
- Estimated CO2 (ppm)
- Estimated Oxygen (O2 %)
"""

from typing import Dict, List, Tuple, Any, Optional
import math


def adc_to_lux(light_adc: float) -> int:
    """
    Convert 12-bit ADC light reading (0-4095) to estimated Illuminance in Lux (lx).
    Typical range: 0 lx (pitch dark) to 65,000 lx (bright direct solar irradiance).
    """
    if light_adc is None or light_adc <= 0:
        return 0
    ratio = min(1.0, max(0.0, float(light_adc) / 4095.0))
    # Non-linear power curve matching human eye and photoresistor lux response
    lux = (ratio ** 1.6) * 65000.0
    return int(round(lux))


def adc_to_aqi(gas_adc: float) -> Tuple[int, str]:
    """
    Convert MQ-135 12-bit ADC reading (0-4095) to Air Quality Index (AQI 0-500)
    and descriptive category.
    """
    if gas_adc is None or gas_adc <= 0:
        return 50, "Good"
    
    # Calibrated mapping for typical MQ-135 sensor in ambient room conditions
    g = float(gas_adc)
    if g < 2600:
        aqi = int(20 + (g / 2600.0) * 30)  # 20 - 50 (Good)
    elif g <= 3200:
        aqi = int(50 + ((g - 2600.0) / 600.0) * 50)  # 51 - 100 (Moderate / Clean)
    elif g <= 3600:
        aqi = int(100 + ((g - 3200.0) / 400.0) * 100)  # 101 - 200 (Unhealthy / Elevated)
    else:
        aqi = int(200 + min(300, ((g - 3600.0) / 495.0) * 300))  # 201 - 500 (Hazardous)

    aqi = max(1, min(500, aqi))

    if aqi <= 50:
        cat = "Good"
    elif aqi <= 100:
        cat = "Moderate"
    elif aqi <= 150:
        cat = "Elevated"
    elif aqi <= 200:
        cat = "Unhealthy"
    else:
        cat = "Hazardous"

    return aqi, cat


def estimate_co2_ppm(gas_adc: float) -> int:
    """Estimate CO2 concentration in ppm from MQ-135 ADC reading."""
    if gas_adc is None:
        return 400
    scaled = 400 + (gas_adc / 4095.0) * 1600
    return int(max(350, min(3000, round(scaled))))


def estimate_oxygen_pct(light_adc: float, gas_adc: float) -> float:
    """Estimate Oxygen level (%) dynamically."""
    l = light_adc or 2000.0
    g = gas_adc or 2000.0
    o2 = 20.95 + 0.35 * (l / 4095.0) - 0.45 * (g / 4095.0)
    return round(float(max(19.2, min(21.6, o2))), 2)


DEFAULT_THRESHOLDS = {
    "name": "Custom Live Thresholds",
    "temp_low": 15.0,
    "temp_high": 40.0,
    "humidity_low": 25.0,
    "humidity_high": 85.0,
    "lux_low": 2000,
    "lux_high": 55000,
    "aqi_high": 150,
    "gas_high": 3400,
    "co2_high": 1800,
    "co2_low": 350,
    "o2_low": 19.8
}

CROP_PRESETS = {
    "general": DEFAULT_THRESHOLDS,
    "tomato": DEFAULT_THRESHOLDS,
    "cucumber": DEFAULT_THRESHOLDS,
    "leafy_greens": DEFAULT_THRESHOLDS,
    "seedlings": DEFAULT_THRESHOLDS
}


def detect_anomalies_detailed(
    temperature: float,
    humidity: float,
    light: float,
    gas: float,
    thresholds: Optional[Dict[str, Any]] = None,
    prev_temperature: Optional[float] = None,
    prev_gas: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates readings against customizable thresholds across real-world units.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    t_low = thresholds.get("temp_low", 15.0)
    t_high = thresholds.get("temp_high", 40.0)
    h_low = thresholds.get("humidity_low", 25.0)
    h_high = thresholds.get("humidity_high", 85.0)
    lux_low = thresholds.get("lux_low", 2000)
    lux_high = thresholds.get("lux_high", 55000)
    aqi_high = thresholds.get("aqi_high", 150)
    co2_high = thresholds.get("co2_high", 1800)
    co2_low = thresholds.get("co2_low", 350)
    o2_low = thresholds.get("o2_low", 19.8)

    # Convert to real-world units
    lux_val = adc_to_lux(light)
    aqi_val, aqi_cat = adc_to_aqi(gas)
    co2_val = estimate_co2_ppm(gas)
    o2_val = estimate_oxygen_pct(light, gas)

    anomalies: List[str] = []
    remediations: List[str] = []

    metrics_status = {
        "temperature": "NORMAL",
        "humidity": "NORMAL",
        "light": "NORMAL",
        "gas": "NORMAL",
        "co2": "NORMAL",
        "oxygen": "NORMAL"
    }

    # 1. Temperature Check
    if temperature is not None:
        if temperature > t_high:
            anomalies.append(f"High Temperature Alert ({temperature:.1f}C > {t_high}C)")
            metrics_status["temperature"] = "WARNING"
            remediations.append("Activate cooling fans or misting system to lower temperature.")
        elif temperature < t_low:
            anomalies.append(f"Low Temperature Alert ({temperature:.1f}C < {t_low}C)")
            metrics_status["temperature"] = "WARNING"
            remediations.append("Turn on greenhouse heating units.")

    # 2. Humidity Check
    if humidity is not None:
        if humidity > h_high:
            anomalies.append(f"High Humidity Alert ({humidity:.1f}% > {h_high}%)")
            metrics_status["humidity"] = "WARNING"
            remediations.append("Increase air circulation / ventilation to purge excess moisture.")
        elif humidity < h_low:
            anomalies.append(f"Low Humidity Alert ({humidity:.1f}% < {h_low}%)")
            metrics_status["humidity"] = "WARNING"
            remediations.append("Turn on misting / humidification system.")

    # 3. Light Check (in Lux)
    if lux_val > lux_high:
        anomalies.append(f"Excessive Solar Irradiance ({lux_val:,} lx > {lux_high:,} lx)")
        metrics_status["light"] = "WARNING"
        remediations.append("Deploy shade cloth to prevent leaf scorch.")
    elif lux_val < lux_low:
        anomalies.append(f"Low Light Level ({lux_val:,} lx < {lux_low:,} lx)")
        metrics_status["light"] = "WARNING"
        remediations.append("Switch on supplemental LED grow lights.")

    # 4. Air Quality Check (in AQI)
    if aqi_val > aqi_high:
        anomalies.append(f"Poor Air Quality / AQI Spike ({aqi_val} AQI [{aqi_cat}] > {aqi_high} AQI)")
        metrics_status["gas"] = "WARNING"
        remediations.append("Engage emergency exhaust fans to clear hazardous fumes.")

    # 5. Estimated CO2 Check
    if co2_val > co2_high:
        anomalies.append(f"Elevated CO2 / Stale Air ({co2_val} ppm > {co2_high} ppm)")
        metrics_status["co2"] = "WARNING"
        remediations.append("Increase fresh air exchange rate.")
    elif co2_val < co2_low:
        anomalies.append(f"CO2 Depletion for Photosynthesis ({co2_val} ppm < {co2_low} ppm)")
        metrics_status["co2"] = "WARNING"
        remediations.append("Provide fresh ventilation or supplemental CO2 injection.")

    # 6. Estimated Oxygen Check
    if o2_val < o2_low:
        anomalies.append(f"Low Oxygen Level ({o2_val:.1f}% < {o2_low}%)")
        metrics_status["oxygen"] = "WARNING"
        remediations.append("Improve ventilation and inspect for air stagnation.")

    # Overall Status
    if len(anomalies) > 0:
        status = "ANOMALY"
        severity_score = min(100, 40 + len(anomalies) * 15)
    else:
        status = "NORMAL"
        severity_score = 0

    return {
        "status": status,
        "severity_score": severity_score,
        "anomalies": anomalies,
        "warnings": anomalies,
        "criticals": [],
        "compound_alerts": [],
        "remediations": list(dict.fromkeys(remediations)),
        "metrics_status": metrics_status,
        "lux": lux_val,
        "aqi": aqi_val,
        "aqi_category": aqi_cat,
        "co2_ppm": co2_val,
        "oxygen_pct": o2_val
    }


def detect_anomalies(temperature: float, humidity: float, light: float, gas: float) -> Tuple[str, List[str]]:
    res = detect_anomalies_detailed(temperature, humidity, light, gas)
    return res["status"], res["anomalies"]