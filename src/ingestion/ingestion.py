import csv
import os
from datetime import datetime


class TelemetryIngestor:

    def __init__(self, input_file, output, clean_name="air_quality_iot_clean.csv", log_name="iot_telemetry_audit.log"):

        self.input_file = input_file
        self.output = output
        self.clean_file = os.path.join(output, clean_name)
        self.log_file = os.path.join(output, log_name)

        self.min_temp = -10
        self.max_temp = 60
        self.humid_min = 0
        self.humid_max = 100
        self.gas_min = 0

        self.header = None
        self.valid_rows = []
        self.rejected = []        
        self.total = 0
        self.reason_counts = {}

    def check_row(self, row):
        
        reason = None
        try:
            temp = float(row["temp"])
            humidity = float(row["humidity"])
            co = float(row["co"])
            lpg = float(row["lpg"])
            smoke = float(row["smoke"])

            if temp < self.min_temp or temp > self.max_temp:
                reason = "Temp out of range"
            elif humidity < self.humid_min or humidity > self.humid_max:
                reason = "Humidity out of range"
            elif co < self.gas_min or lpg < self.gas_min or smoke < self.gas_min:
                reason = "Negative gas values"

        except KeyError:
            reason = "Missing field"
        except (ValueError, TypeError):

            reason = "Malformed value"

        return reason

    def read_file(self):
        
        self.valid_rows = []
        self.rejected = []
        self.total = 0
        self.reason_counts = {}

        with open(self.input_file, newline="") as f:
            reader = csv.DictReader(f)
            self.header = reader.fieldnames

            for row in reader:
                self.total = self.total + 1
                reason = self.check_row(row)

                if reason is None:
                    self.valid_rows.append(row)
                else:
                   
                    self.rejected.append((reader.line_num, reason))

        for line_no, reason in self.rejected:
            self.reason_counts[reason] = self.reason_counts.get(reason, 0) + 1

    def write_clean_csv(self):
        with open(self.clean_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writeheader()
            writer.writerows(self.valid_rows)

    def write_audit_log(self):
        with open(self.log_file, "w") as f:
            f.write("IoT TELEMETRY AUDIT LOG\n")
            f.write(f"Time: {datetime.now()}\n\n")
            f.write("Bounds used:\n")
            f.write(f"  temp: {self.min_temp} to {self.max_temp}\n")
            f.write(f"  humidity: {self.humid_min} to {self.humid_max}\n")
            f.write(f"  co, lpg, smoke: >= {self.gas_min}\n\n")
            f.write(f"Total records: {self.total}\n")
            f.write(f"Valid records: {len(self.valid_rows)}\n")
            f.write(f"Corrupted records: {len(self.rejected)}\n\n")
            f.write("Rejections by reason:\n")
            for reason, count in self.reason_counts.items():
                f.write(f"  {reason}: {count}\n")
            f.write("\nRejected lines:\n")
            for line_no, reason in self.rejected:
                f.write(f"  line {line_no}: {reason}\n")

    def run(self):
        
        if not os.path.isfile(self.input_file):
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        os.makedirs(self.output, exist_ok=True)

        self.read_file()
        self.write_clean_csv()
        self.write_audit_log()

        assert len(self.valid_rows) + len(self.rejected) == self.total
        print("Total:", self.total, "| Valid:", len(self.valid_rows), "| Rejected:", len(self.rejected))



if __name__ == "__main__":
    TelemetryIngestor("data/raw/air_quality_iot_raw.csv", "data/processed").run()