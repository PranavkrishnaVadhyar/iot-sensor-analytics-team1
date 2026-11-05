# iot-sensor-analytics-team1

Semester 1 Python group project for ingesting, analyzing, and visualizing IoT sensor data.

## Project overview

TODO: Describe the sensors, dataset, and questions the analysis will answer.
The planned workflow loads sensor readings, cleans and summarizes them, and exports a Plotly dashboard.

## Team members

- TODO: Name, student ID, and responsibility for each team member.

## Project structure

```text
.
|-- README.md                          # Project documentation & execution guide
|-- requirements.txt                   # Dependencies (numpy, pandas, matplotlib, seaborn, plotly)
|-- run_pipeline.py                    # Standalone CLI entry point
|-- data/
|   |-- raw/
|   |   `-- air_quality_iot_raw.csv    # Raw, uncleaned input dataset
|   `-- processed/
|       |-- air_quality_iot_clean.csv  # Curated, validated clean dataset
|       `-- iot_telemetry_audit.log    # Audit report of filtered/rejected records
|-- src/
|   |-- __init__.py
|   |-- ingestion.py                   # Defensive reader, range auditor & CSV exporter
|   |-- analyzer.py                    # IoTSensorAnalyzer class (NumPy / Pandas)
|   `-- visualizer.py                  # Matplotlib, Seaborn & Plotly outputs
|-- notebooks/
|   `-- development_cycle.ipynb        # EDA, trials, tests & unit assertions
`-- reports/
    |-- figures/                       # Generated PNGs (git-ignored)
    |   |-- primary_envelope.png
    |   |-- correlation_heatmap.png
    |   `-- distribution_regimes.png
    |-- interactive_dashboard.html     # Interactive Plotly dashboard
    `-- Project Report PDF
```

## How to run

From the project root, create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_pipeline.py
```

Then open `reports/interactive_dashboard.html` in a browser.

## Notes

- Generated figures (`*.png`) are not committed; run the pipeline to regenerate them in `reports/figures/`.
