'''This python script is used to analyze the data collected from IoT sensors. It performs various statistical analyses and visualizations to gain insights from the sensor data.'''

import pandas as pd 
import numpy as np 

SENSOR_COLUMNS = ["co","humidity","lpg","smoke","temp"]
EVENT_COLUMNS = ["light","motion"]
REQUIRED_COLUMNS =["ts", "device", *SENSOR_COLUMNS, *EVENT_COLUMNS]
ZSCORE_COLUMNS = ["co", "temp", "humidity"]


class IoTSensorAnalyzer:
    #holds the data collected from IoT sensors and provides methods to analyze it.  

    def __init__(self):
        #create an empty telemetary book
        self.__raw_data=None
        self.__is_loaded=False

