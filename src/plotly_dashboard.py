
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_dashboard(data, output_file="reports/interactive_dashboard.html"):

    data = data.copy()

    if "co" not in data.columns:
        raise ValueError("Dataset must contain a 'co' column.")
    if "datetime" not in data.columns:
        if "ts" in data.columns:
            data["datetime"] = pd.to_datetime(
                data["ts"], unit="s", errors="coerce"
            )
        else:
            raise ValueError("Dataset must contain 'datetime' or 'ts'.")

    else:
        data["datetime"] = pd.to_datetime(
            data["datetime"], errors="coerce"
        )

    data["co"] = pd.to_numeric(data["co"], errors="coerce")

    data = data.dropna(subset=["datetime", "co"]).copy()

    if data.empty:
        raise ValueError("No valid sensor data available for visualization.")

    if "device" not in data.columns:
        data["device"] = "Device"

    data["device"] = data["device"].fillna("Unknown Device").astype(str)


    data = data.sort_values(["device", "datetime"]).reset_index(drop=True)

    sensor_columns = [
        "co", "temp", "humidity", "lpg","smoke", "light", "motion"]

    available_sensors = [column for column in sensor_columns if column in data.columns]

    for column in available_sensors:
        data[column] = pd.to_numeric(data[column], errors="coerce" )
    data["co_roll_median"] = float("nan")
    data["co_roll_q1"] = float("nan")
    data["co_roll_q3"] = float("nan")

    for device_name, group in data.groupby("device", sort=False):

        group = group.sort_values("datetime")

        rolling_data = group.set_index("datetime")["co"].rolling("15min",min_periods=1)

        rolling_median = rolling_data.median()
        rolling_q1 = rolling_data.quantile(0.25)
        rolling_q3 = rolling_data.quantile(0.75)

        data.loc[group.index, "co_roll_median"] = (rolling_median.to_numpy())

        data.loc[group.index, "co_roll_q1"] = (rolling_q1.to_numpy() )

        data.loc[group.index, "co_roll_q3"] = (rolling_q3.to_numpy())

    data["rolling_iqr"] = (data["co_roll_q3"] - data["co_roll_q1"])

    data["upper_threshold"] = (data["co_roll_median"] + 2.5 * data["rolling_iqr"])

    data["lower_threshold"] = (data["co_roll_median"] - 2.5 * data["rolling_iqr"] ).clip(lower=0)

    hover_columns = [
        column for column in available_sensors
        if column != "co"]

    
    fig = px.line( data,x="datetime",y="co",color="device",custom_data=hover_columns,
        title="IoT Environmental Sensor Dashboard",labels={"datetime": "Date and Time","co": "Carbon Monoxide (CO)","device": "Sensor Device"} )

    hover_text = ("<b>Time:</b> %{x}<br>""<b>CO:</b> %{y:.3f}<br>")

    for index, column in enumerate(hover_columns):
        hover_text += (f"<b>{column.upper()}:</b> " f"%{{customdata[{index}]}}<br>")

    hover_text += "<extra></extra>"

    fig.update_traces(hovertemplate=hover_text
    )
    for device_name, group in data.groupby("device", sort=False):

        group = group.sort_values("datetime")

        fig.add_trace(go.Scatter(x=group["datetime"],y=group["co_roll_median"],mode="lines",name=f"{device_name} - Rolling Median",line=dict(dash="dash", width=2),
                hovertemplate=("Time: %{x}<br>""Rolling Median: %{y:.3f}""<extra></extra>" )))
        fig.add_trace(go.Scatter(x=group["datetime"],y=group["upper_threshold"],mode="lines",name=f"{device_name} - Upper Threshold",
                line=dict(dash="dot", width=1.5),
                hovertemplate=("Time: %{x}<br>"
                    "Upper Threshold: %{y:.3f}" "<extra></extra>")))

        fig.add_trace(go.Scatter(x=group["datetime"], y=group["lower_threshold"],mode="lines",name=f"{device_name} - Lower Threshold",
                line=dict(dash="dot", width=1.5),hovertemplate=("Time: %{x}<br>" "Lower Threshold: %{y:.3f}" "<extra></extra>")))

        if "rolling_iqr_spike" in group.columns:

            anomaly_flags = (group["rolling_iqr_spike"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"]))

            anomalies = group[anomaly_flags]

            if not anomalies.empty:

                fig.add_trace(go.Scatter(x=anomalies["datetime"], y=anomalies["co"],mode="markers",name=f"{device_name} - Anomalies",marker=dict(symbol="x",
                                                                                                                                                 
                             size=10,color="red"),
                        hovertemplate=("<b>ANOMALY DETECTED</b><br>""Time: %{x}<br>""CO: %{y:.3f}<extra></extra>")))

    fig.update_xaxes(rangeslider_visible=True,rangeselector=dict(buttons=[dict(count=1,label="1h",step="hour",stepmode="backward"),
                dict(
                    count=6,label="6h",step="hour",stepmode="backward"),
                dict(count=1,label="1d", step="day",stepmode="backward"),
                dict(step="all",label="All")]))

    fig.update_layout(template="plotly_white",height=750,hovermode="x unified",legend_title="Chart Details",xaxis_title="Date and Time",
        yaxis_title="CO Reading",title_x=0.5)

    os.makedirs(os.path.dirname(output_file) or ".",exist_ok=True)

    fig.write_html(output_file,include_plotlyjs=True,full_html=True)


if __name__ == "__main__":

    input_file = "data/iot_telemetry_data.csv"

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Processed dataset not found: {input_file}")

    analyzed_data = pd.read_csv(input_file)

    create_dashboard(analyzed_data)
