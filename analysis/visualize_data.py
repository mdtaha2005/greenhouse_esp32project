"""
Greenhouse Telemetry Visualization
Generates multi-panel time-series figures with threshold overlays and exports summary charts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "clean_greenhouse_data.csv"))
OUTPUT_PNG = os.path.abspath(os.path.join(os.path.dirname(__file__), "greenhouse_summary_charts.png"))


def generate_visualizations(show_plot: bool = False):
    print("=" * 65)
    print("GENERATING GREENHOUSE VISUALIZATIONS")
    print("=" * 65)

    if not os.path.exists(CSV_PATH):
        print(f"CSV data not found at {CSV_PATH}. Run prepare_data.py first.")
        return

    df = pd.read_csv(CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    plt.subplots_adjust(hspace=0.25)

    # 1. Temperature
    ax1 = axes[0]
    ax1.plot(df["timestamp"], df["temperature"], color="#e65100", linewidth=1.5, label="Temperature (°C)")
    ax1.axhline(32.0, color="orange", linestyle="--", alpha=0.7, label="Upper Warning (32°C)")
    ax1.axhline(38.0, color="red", linestyle=":", alpha=0.8, label="Critical High (38°C)")
    ax1.axhline(18.0, color="blue", linestyle="--", alpha=0.7, label="Lower Warning (18°C)")
    ax1.set_ylabel("Temp (°C)", fontsize=11, fontweight="bold")
    ax1.set_title("Greenhouse Environmental Telemetry & Anomaly Bounds", fontsize=14, fontweight="bold", pad=12)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.9)

    # 2. Humidity
    ax2 = axes[1]
    ax2.plot(df["timestamp"], df["humidity"], color="#0288d1", linewidth=1.5, label="Humidity (%)")
    ax2.axhline(80.0, color="purple", linestyle="--", alpha=0.7, label="High Humidity (80%)")
    ax2.axhline(45.0, color="orange", linestyle="--", alpha=0.7, label="Low Humidity (45%)")
    ax2.set_ylabel("Humidity (%)", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.9)

    # 3. Light
    ax3 = axes[2]
    ax3.plot(df["timestamp"], df["light"], color="#fbc02d", linewidth=1.5, label="Light Irradiance (ADC)")
    ax3.axhline(3600, color="red", linestyle="--", alpha=0.7, label="Excessive Light (3600)")
    ax3.axhline(600, color="brown", linestyle="--", alpha=0.7, label="Low Light (600)")
    ax3.set_ylabel("Light (ADC)", fontsize=11, fontweight="bold")
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper right", framealpha=0.9)

    # 4. Gas / Air Quality
    ax4 = axes[3]
    ax4.plot(df["timestamp"], df["gas"], color="#7b1fa2", linewidth=1.5, label="MQ-135 Gas (ADC)")
    ax4.axhline(1800, color="orange", linestyle="--", alpha=0.7, label="Warning Gas (1800)")
    ax4.axhline(2500, color="red", linestyle=":", alpha=0.8, label="Critical Gas (2500)")
    ax4.set_ylabel("Gas (ADC)", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Time (HH:MM)", fontsize=11, fontweight="bold")
    ax4.grid(True, linestyle=":", alpha=0.6)
    ax4.legend(loc="upper right", framealpha=0.9)

    # Format Date/Time Axis
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200)
    print(f"Chart successfully saved to -> {OUTPUT_PNG}")

    if show_plot:
        plt.show()
    plt.close()


if __name__ == "__main__":
    generate_visualizations(show_plot=False)