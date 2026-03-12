import csv
import json
import os
from collections import Counter

OUTPUT_DIR = "output"
TIMELINE_FILE = os.path.join(OUTPUT_DIR, "timeline.csv")
ALERTS_FILE = os.path.join(OUTPUT_DIR, "correlation_alerts.json")
REPORT_JSON = os.path.join(OUTPUT_DIR, "report_summary.json")
REPORT_TXT = os.path.join(OUTPUT_DIR, "report_summary.txt")


def load_timeline():
    events = []
    if not os.path.exists(TIMELINE_FILE):
        return events

    with open(TIMELINE_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)

    return events


def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return []

    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError:
            return []


def summarize_timeline(events):
    source_counter = Counter()
    event_counter = Counter()

    for event in events:
        source = event.get("source", "unknown")
        event_type = event.get("event_type", "unknown")

        source_counter[source] += 1
        event_counter[event_type] += 1

    return {
        "total_events": len(events),
        "by_source": dict(source_counter),
        "by_event_type": dict(event_counter)
    }


def summarize_alerts(alerts):
    severity_counter = Counter()

    for alert in alerts:
        severity = alert.get("severity", "unknown")
        severity_counter[severity] += 1

    return {
        "total_alerts": len(alerts),
        "by_severity": dict(severity_counter),
        "alerts": alerts
    }


def build_report():
    events = load_timeline()
    alerts = load_alerts()

    timeline_summary = summarize_timeline(events)
    alerts_summary = summarize_alerts(alerts)

    report = {
        "project": "Bozkurt Izi",
        "timeline_summary": timeline_summary,
        "alerts_summary": alerts_summary
    }

    return report


def save_report(report):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("=== BOZKURT IZI RAPOR OZETI ===\n\n")
        f.write(f"Toplam Timeline Olayi : {report['timeline_summary']['total_events']}\n")
        f.write(f"Toplam Alert          : {report['alerts_summary']['total_alerts']}\n\n")

        f.write("Kaynaklara Gore Olaylar:\n")
        for source, count in report["timeline_summary"]["by_source"].items():
            f.write(f" - {source}: {count}\n")

        f.write("\nEvent Type Dagilimi:\n")
        for event_type, count in report["timeline_summary"]["by_event_type"].items():
            f.write(f" - {event_type}: {count}\n")

        f.write("\nSeverity Dagilimi:\n")
        for severity, count in report["alerts_summary"]["by_severity"].items():
            f.write(f" - {severity}: {count}\n")

        f.write("\nAlert Detaylari:\n")
        for idx, alert in enumerate(report["alerts_summary"]["alerts"], start=1):
            f.write(f"\n[{idx}] {alert}\n")


def main():
    print("[*] Report engine çalışıyor...")
    report = build_report()
    save_report(report)
    print(f"[+] Rapor oluşturuldu: {REPORT_JSON}")
    print(f"[+] Metin özeti oluşturuldu: {REPORT_TXT}")