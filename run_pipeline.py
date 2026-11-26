import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")

from src.ingestion.ingestion import TelemetryIngestor
from src.analysis.analyze_data import IoTSensorAnalyzer
from src.visualization.create_dashboard import IoTTelemetryVisualizer

     
log_file_name = "iot_telemetry_audit.log"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report-dir", default="reports")
    args = parser.parse_args()

    try:
        #ingestion
        print("=" * 60)
        print("Ingestion: reading and auditing the raw file")
        print("=" * 60)
        ingestor = TelemetryIngestor(args.input, args.output_dir, "iot_telemetry_data.csv", log_name=log_file_name)
        ingestor.run()

        print(f"Raw records     : {ingestor.total}")
        print(f"Clean records   : {len(ingestor.valid_rows)}")
        print(f"Faulty records  : {len(ingestor.rejected)}")


        for reason, count in ingestor.reason_counts.items():
            print(f"    {reason}: {count}")

        
        print(f"Clean CSV       : {ingestor.clean_file}")
        print(f"Audit log       : {ingestor.log_file}")

        if len(ingestor.valid_rows) == 0:
            print("ERROR: no valid records left after ingestion")
            return 1

        
        if os.path.getsize(ingestor.clean_file) == 0 or os.path.getsize(ingestor.log_file) == 0:
            print("ERROR: an output file is empty")
            return 1


        print()
        print("=" * 60)
        
        print("Analysis: loading the clean file into IoTSensorAnalyzer")
        print("=" * 60)


        analyzer = IoTSensorAnalyzer()
        analyzer.load_data(ingestor.clean_file)

        print(analyzer.get_overview())
        print()

        print(analyzer.get_summary_stats())
        print()

        print(analyzer.compute_zscores().head())
        
        print()
        print("=" * 60)
        print("Visualization")
        print("=" * 60)
        os.makedirs(args.report_dir, exist_ok=True)



        if hasattr(analyzer, "get_analysis_data"):
            analysis_data = analyzer.get_analysis_data()
            visualizer = IoTTelemetryVisualizer(analysis_data, report_dir=args.report_dir)
            visualizer.plot_co_envelope()
            visualizer.plot_heatmap_and_violin()
        else:
            print("Skipped: analyzer.get_analysis_data() does not exist yet")

    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1

    print()
    print("Pipeline finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())