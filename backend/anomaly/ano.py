"""
Test Script for Greenhouse Anomaly Detector
"""

from anomaly_detector import detect_anomalies_detailed, CROP_PRESETS

print("=" * 65)
print("GREENHOUSE ANOMALY DETECTOR - TEST SUITE")
print("=" * 65)

test_scenarios = [
    {
        "name": "Optimal Conditions",
        "temp": 24.0, "hum": 65.0, "light": 2000, "gas": 800,
        "crop": "general"
    },
    {
        "name": "Compound: Heat Stress & Wilting",
        "temp": 36.5, "hum": 32.0, "light": 3200, "gas": 1200,
        "crop": "tomato"
    },
    {
        "name": "Compound: Fungal Outbreak Risk",
        "temp": 26.0, "hum": 94.0, "light": 1800, "gas": 900,
        "crop": "cucumber"
    },
    {
        "name": "Compound: Frost & Condensation Hazard",
        "temp": 8.5, "hum": 91.0, "light": 400, "gas": 950,
        "crop": "leafy_greens"
    },
    {
        "name": "Critical Toxic Gas / Combustion Leak",
        "temp": 28.0, "hum": 60.0, "light": 2200, "gas": 2850,
        "crop": "general"
    }
]

for sc in test_scenarios:
    thresholds = CROP_PRESETS[sc["crop"]]
    res = detect_anomalies_detailed(
        temperature=sc["temp"],
        humidity=sc["hum"],
        light=sc["light"],
        gas=sc["gas"],
        thresholds=thresholds
    )
    print(f"\n--- Scenario: {sc['name']} ({thresholds['name']}) ---")
    print(f"Inputs: Temp={sc['temp']}C, Humidity={sc['hum']}%, Light={sc['light']}, Gas={sc['gas']}")
    print(f"Status: {res['status']} (Severity Score: {res['severity_score']}/100)")
    if res['anomalies']:
        print("Anomalies Detected:")
        for a in res['anomalies']:
            print(f"  * {a}")
    if res['remediations']:
        print("Recommended Remediation:")
        for r in res['remediations']:
            print(f"  -> {r}")

print("\n" + "=" * 65)
print("All anomaly detector tests executed successfully!")