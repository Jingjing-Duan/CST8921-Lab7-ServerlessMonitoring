"""
send_telemetry.py — CST8921 Lab 7 sample data sender

Streams the provided sample wind-turbine telemetry into an Azure Event Hub.
This replaces WindTurbineDataGenerator.exe — no Visual Studio required, runs
on Windows / macOS / Linux.

SETUP
-----
1. python -m venv .venv
   # Windows:  .venv\\Scripts\\activate
   # mac/linux: source .venv/bin/activate
2. pip install azure-eventhub
3. Set your connection string + hub name below (or via environment variables):
       set EVENTHUB_CONNECTION_STRING=Endpoint=sb://...    (Windows)
       export EVENTHUB_CONNECTION_STRING=Endpoint=sb://...  (mac/linux)
   Use the namespace-level RootManageSharedAccessKey connection string from:
       Event Hub Namespace -> Shared access policies -> RootManageSharedAccessKey
4. python send_telemetry.py

By default it loops the dataset forever at SEND_INTERVAL seconds so you can
watch the Function fire and the Logic App email arrive. Ctrl+C to stop.
"""

import os
import sys
import json
import time
import argparse

try:
    from azure.eventhub import EventHubProducerClient, EventData
except ImportError:
    sys.exit("Missing dependency. Run:  pip install azure-eventhub")

# --- Configuration (env vars take precedence) --------------------------------
CONNECTION_STRING = os.getenv("EVENTHUB_CONNECTION_STRING", "<PASTE_NAMESPACE_CONNECTION_STRING>")
EVENT_HUB_NAME = os.getenv("EVENTHUB_NAME", "turbine-telemetry")
DATA_FILE = os.getenv("TELEMETRY_FILE", "sample_telemetry.json")
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", "2.0"))  # seconds between events


def load_records(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Send sample turbine telemetry to Event Hub.")
    parser.add_argument("--once", action="store_true", help="Send the dataset a single pass, then exit.")
    parser.add_argument("--interval", type=float, default=SEND_INTERVAL, help="Seconds between events.")
    parser.add_argument("--file", default=DATA_FILE, help="Path to the telemetry JSON file.")
    args = parser.parse_args()

    if CONNECTION_STRING.startswith("<PASTE"):
        sys.exit("Set EVENTHUB_CONNECTION_STRING (or edit CONNECTION_STRING in this file) first.")

    records = load_records(args.file)
    print(f"Loaded {len(records)} records from {args.file}")
    print(f"Sending to hub '{EVENT_HUB_NAME}' every {args.interval}s "
          f"({'single pass' if args.once else 'looping — Ctrl+C to stop'})\n")

    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STRING, eventhub_name=EVENT_HUB_NAME
    )

    sent = 0
    try:
        with producer:
            while True:
                for rec in records:
                    batch = producer.create_batch()
                    batch.add(EventData(json.dumps(rec)))
                    producer.send_batch(batch)
                    sent += 1
                    flag = "URGENT?" if (rec["windSpeed"] > 15 and rec["generatedPower"] < 5) else "healthy"
                    print(f"[{sent:04d}] {rec['deviceId']} @ {rec['timestamp']} "
                          f"wind={rec['windSpeed']} power={rec['generatedPower']} -> {flag}")
                    time.sleep(args.interval)
                if args.once:
                    break
    except KeyboardInterrupt:
        print(f"\nStopped. Total events sent: {sent}")


if __name__ == "__main__":
    main()
