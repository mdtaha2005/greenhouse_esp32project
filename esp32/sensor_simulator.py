"""
Greenhouse Sensor Simulator
Simulates realistic continuous telemetry with diurnal cycles and optional anomaly injection.
"""

import time
import math
import random
import argparse
import requests
from datetime import datetime

DEFAULT_SERVER = "http://localhost:5000/data"


class GreenhouseSimulator:
    def __init__(self, server_url: str = DEFAULT_SERVER, interval: float = 2.5):
        self.server_url = server_url
        self.interval = interval
        self.tick = 0
        
        # Base environmental state
        self.base_temp = 24.5
        self.base_humidity = 68.0
        self.base_light = 2200
        self.base_gas = 850

    def generate_reading(self, scenario: str = "normal") -> dict:
        self.tick += 1
        
        # Diurnal solar cycle simulation (sinusoidal day/night transition)
        cycle_rad = (self.tick % 120) / 120.0 * 2 * math.pi
        
        temp_cycle = 4.0 * math.sin(cycle_rad - math.pi / 2) # Warmer during midday
        light_cycle = 1200 * max(0.0, math.sin(cycle_rad - math.pi / 2)) # Solar peak
        hum_cycle = -8.0 * math.sin(cycle_rad - math.pi / 2) # Drier when warm
        
        temp = self.base_temp + temp_cycle + random.uniform(-0.3, 0.3)
        humidity = self.base_humidity + hum_cycle + random.uniform(-0.8, 0.8)
        light = self.base_light + light_cycle + random.uniform(-40, 40)
        gas = self.base_gas + random.uniform(-25, 25)

        # Inject Scenarios
        if scenario == "heatwave":
            temp += 12.0 # ~37C
            humidity -= 28.0 # ~35% (Heat stress + wilting)
            light += 800
        elif scenario == "fungal":
            temp = 26.5
            humidity = 95.0 # High saturation & warm temp
        elif scenario == "frost":
            temp = 7.5 # Cold chill
            humidity = 92.0 # Condensation
            light = 350
        elif scenario == "gas_leak":
            gas = 2850 # Critical gas spike
            temp += 2.0
        elif scenario == "darkness":
            light = 150 # Low light / photoperiod deficit
            temp -= 3.0
        elif scenario == "scorching":
            temp = 36.0
            light = 3950 # Severe direct irradiance

        return {
            "temperature": round(temp, 1),
            "humidity": round(max(5.0, min(100.0, humidity)), 1),
            "light": int(max(0, min(4095, light))),
            "gas": int(max(0, min(4095, gas))),
            "timestamp": datetime.now().isoformat()
        }

    def run(self, scenario: str = "normal", count: int = 0):
        print("=" * 65)
        print(f"Greenhouse Sensor Simulator -> {self.server_url}")
        print(f"Scenario: [{scenario.upper()}] | Interval: {self.interval}s")
        print("Press Ctrl+C to stop.")
        print("=" * 65)

        sent = 0
        try:
            while True:
                payload = self.generate_reading(scenario)
                try:
                    resp = requests.post(self.server_url, json=payload, timeout=4)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent -> Temp: {payload['temperature']:>4.1f}C | Hum: {payload['humidity']:>4.1f}% | Light: {payload['light']:>4} | Gas: {payload['gas']:>4} => Status: {resp.status_code}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection Error: {e}")

                sent += 1
                if count > 0 and sent >= count:
                    print(f"\nCompleted {sent} transmissions.")
                    break

                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nSimulator stopped by operator.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Greenhouse Sensor Simulator")
    parser.add_argument("--server", type=str, default=DEFAULT_SERVER, help="Flask backend URL")
    parser.add_argument("--interval", type=float, default=2.5, help="Seconds between posts")
    parser.add_argument("--scenario", type=str, default="normal",
                        choices=["normal", "heatwave", "fungal", "frost", "gas_leak", "darkness", "scorching"],
                        help="Anomaly scenario to inject")
    parser.add_argument("--count", type=int, default=0, help="Number of packets to send (0 = infinite)")

    args = parser.parse_args()
    sim = GreenhouseSimulator(server_url=args.server, interval=args.interval)
    sim.run(scenario=args.scenario, count=args.count)
