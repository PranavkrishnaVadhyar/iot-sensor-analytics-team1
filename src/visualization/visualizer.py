
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class IoTTelemetryVisualizer:

    SENSOR_COLUMNS = ["co", "humidity", "lpg", "smoke", "temp"]

    REQUIRED_COLUMNS = [
        "datetime", "device", "co", "temp", "humidity",
        "lpg", "smoke", "co_roll_median",
        "co_roll_q1", "co_roll_q3",
        "rolling_iqr_spike", "day_period"
    ]

    def __init__(self, data, report_dir="reports", device=None):

        missing_columns = [
            column for column in self.REQUIRED_COLUMNS
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(f"Missing columns: {missing_columns}")

        self.data = data.copy()
        self.data["datetime"] = pd.to_datetime(self.data["datetime"])

        devices = self.data["device"].unique()

        if len(devices) == 0:
            raise ValueError("No device data available.")

        self.device = device if device is not None else devices[0]

        if self.device not in devices:
            raise ValueError("Selected device is not present in the data.")

        self.device_data = self.data[
            self.data["device"] == self.device
        ].copy()

        self.device_data = self.device_data.sort_values("datetime")

        self.report_dir = report_dir
        os.makedirs(self.report_dir, exist_ok=True)

    def plot_co_envelope(self):
        data = self.device_data
        fig, ax1 = plt.subplots(figsize=(14, 6))

        ax1.plot( data["datetime"],data["co"],label="CO Reading",color="blue",alpha=0.5)

        ax1.plot(
            data["datetime"],data["co_roll_median"],label="15-Minute Rolling Median",color="red"
        )

        ax1.fill_between(
            data["datetime"],data["co_roll_q1"],data["co_roll_q3"],color="orange",alpha=0.3,label="Rolling IQR"
        )

        ax1.set_xlabel("Time")
        ax1.set_ylabel("CO Level")
        ax1.set_title(f"CO Telemetry Envelope - {self.device}")
        ax1.legend(loc="upper left")

        ax2 = ax1.twinx()

        ax2.plot(data["datetime"],data["temp"], color="green",alpha=0.5,
            label="Temperature"
        )

        ax2.set_ylabel("Temperature (°C)")
        ax2.legend(loc="upper right")

        anomaly_mask = (
            data["rolling_iqr_spike"].astype(str).str.lower().isin(["true", "1", "yes"])
        )

        anomalies = data[anomaly_mask]

        if not anomalies.empty:
            highest_anomaly = anomalies.loc[anomalies["co"].idxmax()]

            ax1.annotate(
                "Highest Anomaly",
                xy=(highest_anomaly["datetime"], highest_anomaly["co"]),xytext=(20, 30),
                textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color="black")
            )

        fig.tight_layout()

        file_path = os.path.join(
            self.report_dir, "primary_envelope.png"
        )

        plt.savefig(file_path, dpi=300)
        plt.show()
        plt.close()

    def plot_heatmap_and_violin(self):

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        correlation = self.data[self.SENSOR_COLUMNS].corr()

        sns.heatmap(
            correlation,annot=True,cmap="coolwarm", fmt=".2f",ax=axes[0]
        )

        axes[0].set_title("Sensor Correlation Heatmap")

        sns.violinplot(
            data=self.data,x="device",y="co",hue="day_period", split=True,ax=axes[1]
        )

        axes[1].set_title("CO Distribution: Day vs Night")
        axes[1].set_xlabel("Device MAC Address")
        axes[1].set_ylabel("CO Level")
        axes[1].tick_params(axis="x", rotation=45)

        for label in axes[1].get_xticklabels():
            label.set_horizontalalignment("right")

        sns.despine(ax=axes[1])

        fig.tight_layout()

        file_path = os.path.join(
            self.report_dir, "correlation_heatmap.png"
        )

        plt.savefig(file_path, dpi=300)
        plt.show()
        plt.close()
