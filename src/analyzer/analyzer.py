'''This python script is used to analyze the data collected from IoT sensors. It performs various statistical analyses and visualizations to gain insights from the sensor data.'''

import pandas as pd 
import numpy as np 

SENSOR = ["co","humidity","lpg","smoke","temp"]
EVENT = ["light","motion"]
REQUIRED =["ts", "device", *SENSOR, *EVENT]
ZSCORE = ["co", "temp", "humidity"]


def minmax_scale(values:np.ndarray) -> np.ndarray:
    """Scale the input values to the range [0, 1] using min-max scaling."""
    minimum = np.min(values)
    maximum = np.max(values)
    if maximum ==minimum:
        raise ValueError("Cannot scale a constant aarray: minimum equals maximumm ")
    return (values - minimum) / (maximum - minimum)

class IoTSensorAnalyzer:
    '''holds the data collected from IoT sensors and provides methods to analyze it.  
    '''
    def __init__(self):
        '''create an empty telemetary bookk'''
        self.__raw_data=None
        self.__is_loaded=False

    def load_data(self, path):
        """Read and validate the csv file data here used 
        """
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
        """Show an error if no data is not loaded yet"""
        if not self.__is_loaded:
            raise ValueError("No data loaded. Call load_data() first.")

    def get_overview(self):
        """ return an overview of the loaded data."""
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
        """return the number of missing valu for each required column."""
        self.__require_loaded()
        return self.__raw_data[REQUIRED].isna().sum().rename("missing_count")

    def get_summary_stats(self):
        """return the count, mean, min, max and std for each sensor."""
        self.__require_loaded()
        return self.__raw_data[SENSOR].agg(
            ["count", "mean", "min", "max", "std"]
        )


    def compute_zscores(self):
        """return the z-scores for each sensor in ZSCORE."""
        self.__require_loaded()
        values = self.__raw_data[ZSCORE]
        means = values.mean()
        stds = values.std(ddof=0).replace(0,float("nan"))
        return (((values - means)/stds).add_suffix("_zscore"))
    


    def get_device_summary(self):
        """return the count, mean, min and max per sensor for each device."""
        self.__require_loaded()
        return self.__raw_data.groupby("device")[SENSOR].agg(
            ["count", "mean", "min", "max"]
        )

    def compute_event_percentages(self, by_device=False):
        """return percentages of valid readings with light/motion true."""
        self.__require_loaded()
        if by_device:
            return (
                self.__raw_data.groupby("device")[EVENT]
                .mean()
                .mul(100)
                .rename(columns=lambda x: f"{x}_percentage")
            )
        else:
            return (
                self.__raw_data[EVENT].mean().mul(100).rename(
                    lambda x: f"{x}_percentage"
                )
            )
    def minmax_scale_channel(self,column:str) ->np.ndarray:
        """ rturns the selceted sensor readeings scaled to [0, 1] """
        self.__require_loaded()

        if column not in SENSOR:
            raise ValueError(
                f"Unknown sensor {column!r}. Valid choices: {', '.join(SENSOR)}."
            )

        arr = self.__raw_data[column].to_numpy(dtype=float)
        return minmax_scale(arr)
    def describe_array(self, column: str) -> dict:
        """return the shape, memory size, dtype, and flags of a sensor array."""
        self.__require_loaded()

        if column not in SENSOR:
            raise ValueError(
                f"Unknown sensor {column!r}. Valid choices: {', '.join(SENSOR)}."
            )

        arr = self.__raw_data[column].to_numpy(dtype=float)
        return {
            "shape": arr.shape,
            "nbytes": arr.nbytes,
            "dtype": str(arr.dtype),
            "C_CONTIGUOUS": arr.flags["C_CONTIGUOUS"],
            "F_CONTIGUOUS": arr.flags["F_CONTIGUOUS"],
            "OWNDATA": arr.flags["OWNDATA"],
        }