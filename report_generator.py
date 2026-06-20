"""
Report Generator
Exports alerts, logs, and baseline data to CSV reports.
"""

import csv
import os
from datetime import datetime
from . import database as db


def ensure_report_dir(report_path):
    os.makedirs(report_path, exist_ok=True)
    return report_path


def _timestamp_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_full_report(report_path):
    """
    Generates a comprehensive CSV report combining alerts, logs, and summary.
    Returns the file path of the created report.
    """
    ensure_report_dir(report_path)
    filename = f"FIM_Report_{_timestamp_str()}.csv"
    filepath = os.path.join(report_path, filename)

    alerts = db.get_alerts(limit=10000)
    counts = db.get_alert_counts()
    baseline_count = db.get_baseline_count()
    watch_paths = db.get_watch_paths()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header block
        writer.writerow(["FILE INTEGRITY MONITORING SYSTEM — SECURITY REPORT"])
        writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        # Summary
        writer.writerow(["SUMMARY"])
        writer.writerow(["Monitored Files", baseline_count])
        writer.writerow(["Total Alerts", counts["total"]])
        writer.writerow(["Modified Files", counts["modified"]])
        writer.writerow(["Deleted Files", counts["deleted"]])
        writer.writerow(["New Files", counts["created"]])
        writer.writerow(["Unacknowledged", counts["unread"]])
        writer.writerow([])

        # Watched paths
        writer.writerow(["MONITORED PATHS"])
        writer.writerow(["Path", "Type", "Added On"])
        for p in watch_paths:
            writer.writerow([p["path"], p["path_type"], p["added_on"]])
        writer.writerow([])

        # Alerts table
        writer.writerow(["ALERTS"])
        writer.writerow(["ID", "Timestamp", "File Path", "Event Type",
                          "Severity", "Old Hash", "New Hash", "Acknowledged"])
        for a in alerts:
            writer.writerow([
                a["id"], a["timestamp"], a["file_path"], a["event_type"],
                a["severity"],
                a["old_hash"][:16] + "..." if a["old_hash"] else "N/A",
                a["new_hash"][:16] + "..." if a["new_hash"] else "N/A",
                "Yes" if a["acknowledged"] else "No"
            ])

    return filepath


def generate_alerts_report(report_path):
    """Alerts-only CSV."""
    ensure_report_dir(report_path)
    filename = f"FIM_Alerts_{_timestamp_str()}.csv"
    filepath = os.path.join(report_path, filename)
    alerts = db.get_alerts(limit=10000)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Timestamp", "File Path", "Event Type",
                          "Severity", "Old Hash", "New Hash", "Acknowledged"])
        for a in alerts:
            writer.writerow([
                a["id"], a["timestamp"], a["file_path"], a["event_type"],
                a["severity"],
                a["old_hash"][:16] + "..." if a["old_hash"] else "N/A",
                a["new_hash"][:16] + "..." if a["new_hash"] else "N/A",
                "Yes" if a["acknowledged"] else "No"
            ])
    return filepath


def generate_logs_report(report_path):
    """Logs-only CSV."""
    ensure_report_dir(report_path)
    filename = f"FIM_Logs_{_timestamp_str()}.csv"
    filepath = os.path.join(report_path, filename)
    logs = db.get_logs(limit=10000)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Timestamp", "File Path", "Event Type",
                          "Status", "Details"])
        for l in logs:
            writer.writerow([l["id"], l["timestamp"], l["file_path"],
                              l["event_type"], l["status"],
                              l.get("details", "")])
    return filepath


def generate_baseline_report(report_path):
    """Baseline snapshot CSV."""
    ensure_report_dir(report_path)
    filename = f"FIM_Baseline_{_timestamp_str()}.csv"
    filepath = os.path.join(report_path, filename)
    entries = db.get_baseline()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "File Path", "SHA-256 Hash",
                          "File Size (bytes)", "Last Modified", "Baseline Created"])
        for e in entries:
            writer.writerow([e["id"], e["file_path"], e["sha256_hash"],
                              e["file_size"], e["last_modified"],
                              e["baseline_created"]])
    return filepath
