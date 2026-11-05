"""Defensive line-by-line file reader, range auditor and CSV exporter.

Reads data/raw/air_quality_iot_raw.csv, rejects malformed or out-of-range
records (logged to data/processed/iot_telemetry_audit.log) and exports the
validated rows to data/processed/air_quality_iot_clean.csv.
"""

# TODO: Implement defensive reader, range auditing and clean CSV export.
