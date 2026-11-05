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
|-- README.md
|-- .gitignore
|-- requirements.txt
|-- data/                  # Small sample datasets only
|-- src/
|   |-- ingestion/         # Data loading and validation
|   |-- analysis/          # Cleaning, statistics, and anomaly detection
|   `-- visualization/     # Plotly charts and dashboard export
|-- reports/
|   `-- iot_dashboard.html # Placeholder for the generated dashboard
`-- docs/
    `-- architecture.md   # Design notes and diagrams
```

## How to run

From the project root, create a virtual environment and install the starter dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Open `reports/iot_dashboard.html` in a browser to view the placeholder.
The data pipeline and dashboard generator are not implemented yet.
TODO: Add the pipeline command when the implementation is ready.

## Data policy

Commit only small, non-sensitive sample datasets under `data/`.
Keep large or raw datasets outside the repository, or in the ignored `data/raw/` and `data/large/` folders.
