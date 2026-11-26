'''This python script is used to analyze the data collected from IoT sensors. It performs various statistical analyses and visualizations to gain insights from the sensor data.'''

import pandas as pd 
import numpy as np 

SENSOR = ["co","humidity","lpg","smoke","temp"]
EVENT = ["light","motion"]
REQUIRED =["ts", "device", *SENSOR, *EVENT]
ZSCORE = ["co", "temp", "humidity"]


def minmax_scale(values:np.ndarray) -> np.ndarray:
    minimum = np.min(values)
    maximum = np.max(values)
    if maximum ==minimum:
        raise ValueError("Cannot scale a constant aarray: minimum equals maximumm ")
    return (values - minimum) / (maximum - minimum)

class IoTSensorAnalyzer:

    def __init__(self):
        self.__raw_data=None
        self.__is_loaded=False

    def load_data(self, path):

        try:
            data = pd.read_csv(path)
        except pd.errors.EmptyDataError as exc:
            raise ValueError("The telemetry file has no rows.") from exc

        missing = set(REQUIRED) - set(data.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        if data.empty:
            raise ValueError("The telemetry file has no rows.")
        data = data[REQUIRED].copy()

        for column in ["ts", *SENSOR]:
            try:
                data[column] = pd.to_numeric(data[column], errors="raise")
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Column '{column}' must be numeric.") from exc
            if data[column].isin([float("inf"), float("-inf")]).any():
                raise ValueError(f"Column '{column}' contains infinite values.")

        devices = data["device"].str.strip()
        if devices.isna().any() or devices.eq("").any():
            raise ValueError("Every row must have a device ID.")
        data["device"] = devices

        for column in EVENT:
            values = data[column].astype("string").str.strip().str.lower()
            invalid = values.notna() & ~values.isin(["true", "false"])
            if invalid.any():
                raise ValueError(f"Column '{column}' must contain true/false.")
            data[column] = values.map({"true": True, "false": False}).astype(
                "boolean"
            )

        data["datetime"] = pd.to_datetime(data["ts"], unit="s", utc=True, errors="coerce")
 
        if data["datetime"].isna().any():
            raise ValueError("Column 'ts' must contain valid Unix seconds.")

        self.__raw_data= data 
        self.__is_loaded= True

    def __require_loaded(self):
        if not self.__is_loaded:
            raise ValueError("No data loaded. Call load_data() first.")

    def get_overview(self):
        self.__require_loaded()
        return pd.Series(
            {
                "total_readings": len(self.__raw_data),
                "number_of_devices": self.__raw_data["device"].nunique(),
                "start_time_utc": self.__raw_data["datetime"].min(),
                "end_time_utc": self.__raw_data["datetime"].max(),
                "duplicate_rows": int(
                    self.__raw_data.duplicated(subset=REQUIRED).sum()
                ),
            },
            name="overview",
        )

    def get_missing_values(self):
        self.__require_loaded()
        return self.__raw_data[REQUIRED].isna().sum().rename("missing_count")

    def get_summary_stats(self):
        self.__require_loaded()
        return self.__raw_data[SENSOR].agg(["count", "mean", "min", "max", "std"])


    def compute_zscores(self):
        self.__require_loaded()
        values = self.__raw_data[ZSCORE]
        means = values.mean()
        stds = values.std(ddof=0).replace(0,float("nan"))
        return (((values - means)/stds).add_suffix("_zscore"))
    


    def get_device_summary(self):
        self.__require_loaded()
        return self.__raw_data.groupby("device")[SENSOR].agg(["count", "mean", "min", "max"])

    def compute_event_percentages(self, by_device=False):
        self.__require_loaded()
        if by_device:
            return (
                self.__raw_data.groupby("device")[EVENT]
                .mean()
                .mul(100)
                .rename(columns=lambda x: f"{x}_percentage")
            )
        else:
            return (self.__raw_data[EVENT].mean().mul(100).rename(lambda x: f"{x}_percentage"))
        
    def minmax_scale_channel(self,column:str) ->np.ndarray:
        self.__require_loaded()

        if column not in SENSOR:
            raise ValueError(f"Unknown sensor {column!r}. Valid choices: {', '.join(SENSOR)}.")

        arr = self.__raw_data[column].to_numpy(dtype=float)
        return minmax_scale(arr)
    
    def describe_array(self, column: str) -> dict:
        self.__require_loaded()
        if column not in SENSOR:
            raise ValueError(f"Unknown sensor {column!r}. Valid choices: {', '.join(SENSOR)}.")
        arr = self.__raw_data[column].to_numpy(dtype=float)
        return {
            "shape": arr.shape,
            "nbytes": arr.nbytes,
            "dtype": str(arr.dtype),
            "C_CONTIGUOUS": arr.flags["C_CONTIGUOUS"],
            "F_CONTIGUOUS": arr.flags["F_CONTIGUOUS"],
            "OWNDATA": arr.flags["OWNDATA"],
        }

    def isolate_multichannel_anomalies(self, threshold=3.0):
        """Return anomaly counts and zero-based row positions for CO, temp, and humidity."""
        self.__require_loaded()

        co = self.__raw_data["co"].to_numpy(dtype=float)
        temp = self.__raw_data["temp"].to_numpy(dtype=float)
        humidity = self.__raw_data["humidity"].to_numpy(dtype=float)

        co_mean, co_std = np.mean(co), np.std(co)
        temp_mean, temp_std = np.mean(temp), np.std(temp)
        hum_mean, hum_std = np.mean(humidity), np.std(humidity)
        if co_std == 0 or temp_std == 0 or hum_std == 0:
            raise ValueError(
                "CO, temperature, and humidity must each have nonzero standard deviation."
            )

        z_co = (co - co_mean) / co_std
        z_temp = (temp - temp_mean) / temp_std
        z_hum = (humidity - hum_mean) / hum_std

        co_mask = np.abs(z_co) > threshold
        temp_mask = np.abs(z_temp) > threshold
        hum_mask = np.abs(z_hum) > threshold

        all_three = co_mask & temp_mask & hum_mask
        at_least_two = (
            (co_mask & temp_mask)
            | (co_mask & hum_mask)
            | (temp_mask & hum_mask)
        )
        any_one = co_mask | temp_mask | hum_mask
        normal = ~any_one

        all_three_indices = set(np.flatnonzero(all_three))
        at_least_two_indices = set(np.flatnonzero(at_least_two))

        co_list = z_co.tolist()
        temp_list = z_temp.tolist()
        hum_list = z_hum.tolist()

        loop_all_three = set()
        loop_at_least_two = set()
        for i in range(len(z_co)):
            count = sum(
                abs(value) > threshold
                for value in (co_list[i], temp_list[i], hum_list[i])
            )
            if count == 3:
                loop_all_three.add(i)
            if count >= 2:
                loop_at_least_two.add(i)

        return {
            "all_three_count": int(all_three.sum()),
            "at_least_two_count": int(at_least_two.sum()),
            "any_one_count": int(any_one.sum()),
            "normal_count": int(normal.sum()),
            "all_three_indices": all_three_indices,
            "at_least_two_indices": at_least_two_indices,
            "loop_all_three_indices": loop_all_three,
            "loop_at_least_two_indices": loop_at_least_two,
            "all_three_match": all_three_indices == loop_all_three,
            "at_least_two_match": at_least_two_indices == loop_at_least_two,
        }

    def fit_co_ols_model(self):
        self.__require_loaded()
        data = self.__raw_data[["co", "temp", "humidity"]].dropna()

        y = data["co"].to_numpy(dtype=float)
        temp = data["temp"].to_numpy(dtype=float)
        humidity = data["humidity"].to_numpy(dtype=float)
        X = np.column_stack([np.ones(len(y)), temp, humidity])

        beta_inv = np.linalg.inv(X.T @ X) @ X.T @ y
        beta_lstsq = np.linalg.lstsq(X, y, rcond=None)[0]
        methods_agree = np.allclose(beta_inv, beta_lstsq, rtol=1e-6, atol=0)

        predictions = X @ beta_lstsq
        residuals = y - predictions
        rss = residuals @ residuals

        centered_y = y - y.mean()
        tss = centered_y @ centered_y
        r2 = 1 - rss / tss if tss > 0 else np.nan

        return {
            "b0": float(beta_lstsq[0]),
            "b1": float(beta_lstsq[1]),
            "b2": float(beta_lstsq[2]),
            "r_squared": float(r2),
            "rss": float(rss),
            "methods_agree": bool(methods_agree),
        }

    def compute_rolling_envelope(self, window="15min", k=2.5):
        self.__require_loaded()
        data = self.__raw_data.copy().set_index("datetime").sort_index()
        frames = []

        for dev in data["device"].unique():
            frame = data.loc[data["device"] == dev].copy()
            co = frame["co"]
            rolling = co.rolling(window)

            median = rolling.median()
            q1 = rolling.quantile(0.25)
            q3 = rolling.quantile(0.75)
            iqr = q3 - q1
            spike = (iqr > 0) & ((co - median).abs() > k * iqr)

            frame["co_roll_median"] = median
            frame["co_roll_q1"] = q1
            frame["co_roll_q3"] = q3
            frame["co_roll_iqr"] = iqr
            frame["rolling_iqr_spike"] = spike
            frames.append(frame)
        return pd.concat(frames).reset_index()

    def build_co_pivot_table(self, bins, labels):
        self.__require_loaded()
        data = self.__raw_data.copy()
        data["temp_band"] = pd.cut(data["temp"], bins=bins, labels=labels)
        data["hour"] = data["datetime"].dt.hour

        def p95(s):
            return s.quantile(0.95)

        table = data.pivot_table(
            values="co",
            index=["device", "temp_band"],
            columns="hour",
            aggfunc=["mean", p95],
            margins=True,
            observed=True,
        )

        table.columns = [
            f"co_{stat}_all" if hour == "All" else f"co_{stat}_h{int(hour):02d}"
            for stat, hour in table.columns
        ]
        return table

    def rank_gas_spikes_long(self, top_n=10):
        self.__require_loaded()
        long = self.__raw_data.melt(
            id_vars=["ts", "device"],
            value_vars=["co", "lpg", "smoke"],
            var_name="sensor_type",
            value_name="reading",
        )

        long["zscore"] = long.groupby("sensor_type")["reading"].transform(lambda s: (s - s.mean()) / s.std(ddof=0))

        ranked = []
        for _, group in long.groupby("sensor_type", sort=False):
            valid = group.dropna(subset=["zscore"])
            ranked.append(valid.nlargest(top_n, "zscore"))

        return pd.concat(ranked, ignore_index=True)