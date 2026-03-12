import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

TIMELINE_FILE = os.path.join("output", "timeline.csv")
OUTPUT_FILE = os.path.join("output", "correlation_alerts.csv")

SUSPICIOUS_EXECUTABLES = {
    "POWERSHELL.EXE",
    "CMD.EXE",
    "RUNDLL32.EXE",
    "BITSADMIN.EXE",
    "CERTUTIL.EXE",
    "MSHTA.EXE",
    "WMIC.EXE",
    "CSCRIPT.EXE",
    "WSCRIPT.EXE",
    "PSEXEC.EXE",
}

USB_EXEC_WINDOW_MINUTES = 30
RDP_SUCCESS_WINDOW_MINUTES = 10


def parse_time(value: str) -> Optional[datetime]:
    if not value:
        return None

    value = str(value).strip()
    if not value:
        return None

    candidates = [
        value,
        value.replace("Z", "+00:00"),
        value.replace("Z", ""),
    ]

    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            pass

    fallback_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d.%m.%Y %H:%M:%S",
    ]

    for fmt in fallback_formats:
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass

    return None


def safe_read_csv(path: str) -> List[Dict]:
    if not os.path.exists(path):
        print(f"[-] Dosya bulunamadı, atlanıyor: {path}")
        return []

    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_timeline() -> List[Dict]:
    rows = safe_read_csv(TIMELINE_FILE)
    events = []

    for row in rows:
        ts = parse_time(row.get("timestamp", ""))
        if not ts:
            continue

        events.append({
            "timestamp": ts,
            "source": row.get("source", ""),
            "event_type": row.get("event_type", ""),
            "description": row.get("description", ""),
            "artifact": row.get("artifact", ""),
            "user": row.get("user", ""),
            "severity": row.get("severity", "info"),
            "raw_ref": row.get("raw_ref", ""),
        })

    return sorted(events, key=lambda x: x["timestamp"])


def make_alert(
    correlation_type: str,
    severity: str,
    first_seen: datetime,
    last_seen: datetime,
    summary: str,
    details: str,
    artifact_1: str = "",
    artifact_2: str = "",
    user: str = "",
) -> Dict:
    return {
        "correlation_type": correlation_type,
        "severity": severity,
        "first_seen": first_seen.isoformat(),
        "last_seen": last_seen.isoformat(),
        "summary": summary,
        "details": details,
        "artifact_1": artifact_1,
        "artifact_2": artifact_2,
        "user": user,
    }


def correlate_usb_then_execution(events: List[Dict]) -> List[Dict]:
    """
    USB registry izi geldikten sonra kısa süre içinde şüpheli program çalışmış mı?
    """
    alerts = []

    usb_events = [e for e in events if e["source"] == "USBSTOR"]
    exec_events = [e for e in events if e["event_type"] == "PROGRAM_EXECUTION"]

    for usb in usb_events:
        window_end = usb["timestamp"] + timedelta(minutes=USB_EXEC_WINDOW_MINUTES)

        for exe in exec_events:
            exe_name = (exe["artifact"] or "").upper()

            if exe_name not in SUSPICIOUS_EXECUTABLES:
                continue

            if usb["timestamp"] <= exe["timestamp"] <= window_end:
                alerts.append(
                    make_alert(
                        correlation_type="USB_THEN_SUSPICIOUS_EXECUTION",
                        severity="high",
                        first_seen=usb["timestamp"],
                        last_seen=exe["timestamp"],
                        summary="USB takılma izi sonrası şüpheli program çalıştırılmış olabilir.",
                        details=(
                            f"USB artefact: {usb['artifact']} | "
                            f"Sonrasında çalıştırılan executable: {exe['artifact']} | "
                            f"Zaman farkı: {(exe['timestamp'] - usb['timestamp']).total_seconds() / 60:.1f} dakika"
                        ),
                        artifact_1=usb["artifact"],
                        artifact_2=exe["artifact"],
                        user=exe["user"],
                    )
                )

    return alerts


def correlate_rdp_fail_then_success(events: List[Dict]) -> List[Dict]:
    """
    Aynı user+IP bağlamında failed logon sonrası kısa sürede success var mı?
    """
    alerts = []

    failed_events = [e for e in events if e["event_type"] == "RDP_FAILED_LOGON"]
    success_events = [e for e in events if e["event_type"] == "RDP_SUCCESS_LOGON"]

    for fail in failed_events:
        fail_user = (fail["user"] or "").strip().lower()
        fail_ip = (fail["artifact"] or "").strip()

        window_end = fail["timestamp"] + timedelta(minutes=RDP_SUCCESS_WINDOW_MINUTES)

        for success in success_events:
            success_user = (success["user"] or "").strip().lower()
            success_ip = (success["artifact"] or "").strip()

            if fail_user and success_user and fail_user != success_user:
                continue

            if fail_ip and success_ip and fail_ip != success_ip:
                continue

            if fail["timestamp"] <= success["timestamp"] <= window_end:
                alerts.append(
                    make_alert(
                        correlation_type="RDP_FAIL_THEN_SUCCESS",
                        severity="critical",
                        first_seen=fail["timestamp"],
                        last_seen=success["timestamp"],
                        summary="Başarısız RDP girişlerini kısa sürede başarılı giriş izlemiş.",
                        details=(
                            f"User={success['user']} IP={success['artifact']} | "
                            f"Önce failed logon, sonra success logon görülmüş."
                        ),
                        artifact_1=fail["artifact"],
                        artifact_2=success["artifact"],
                        user=success["user"],
                    )
                )

    return alerts


def correlate_burst_activity(events: List[Dict]) -> List[Dict]:
    """
    Kısa sürede farklı kaynaklardan yoğun olay akışı var mı?
    Basit incident burst sezgisi.
    """
    alerts = []

    if not events:
        return alerts

    window_minutes = 15

    for i in range(len(events)):
        start_event = events[i]
        window_end = start_event["timestamp"] + timedelta(minutes=window_minutes)

        window = []
        sources = set()
        high_count = 0

        for j in range(i, len(events)):
            if events[j]["timestamp"] > window_end:
                break

            window.append(events[j])
            sources.add(events[j]["source"])

            if events[j]["severity"] in ("high", "critical"):
                high_count += 1

        if len(window) >= 3 and len(sources) >= 2 and high_count >= 2:
            alerts.append(
                make_alert(
                    correlation_type="MULTI_SOURCE_ACTIVITY_BURST",
                    severity="high",
                    first_seen=window[0]["timestamp"],
                    last_seen=window[-1]["timestamp"],
                    summary="Kısa süre içinde çok kaynaklı ve yüksek şiddetli olay kümesi tespit edildi.",
                    details=(
                        f"Olay sayısı={len(window)} | "
                        f"Kaynak sayısı={len(sources)} | "
                        f"High/Critical olay sayısı={high_count}"
                    ),
                    artifact_1=",".join(sorted(sources)),
                    artifact_2="",
                    user="",
                )
            )

    return alerts


def deduplicate_alerts(alerts: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []

    for alert in alerts:
        key = (
            alert["correlation_type"],
            alert["first_seen"],
            alert["last_seen"],
            alert["summary"],
            alert["artifact_1"],
            alert["artifact_2"],
            alert["user"],
        )
        if key not in seen:
            seen.add(key)
            unique.append(alert)

    return unique


def write_alerts(alerts: List[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "correlation_type",
            "severity",
            "first_seen",
            "last_seen",
            "summary",
            "details",
            "artifact_1",
            "artifact_2",
            "user",
        ])

        for a in alerts:
            writer.writerow([
                a["correlation_type"],
                a["severity"],
                a["first_seen"],
                a["last_seen"],
                a["summary"],
                a["details"],
                a["artifact_1"],
                a["artifact_2"],
                a["user"],
            ])


def print_summary(alerts: List[Dict]) -> None:
    print("[*] Correlation özeti")
    print(f"    Toplam alert sayısı : {len(alerts)}")

    by_type = {}
    by_severity = {}

    for alert in alerts:
        by_type[alert["correlation_type"]] = by_type.get(alert["correlation_type"], 0) + 1
        by_severity[alert["severity"]] = by_severity.get(alert["severity"], 0) + 1

    print("    Tipe göre dağılım:")
    for t, count in sorted(by_type.items()):
        print(f"      - {t}: {count}")

    print("    Severity dağılımı:")
    for sev, count in sorted(by_severity.items()):
        print(f"      - {sev}: {count}")


def build_correlations(events: List[Dict]) -> List[Dict]:
    alerts = []

    alerts.extend(correlate_usb_then_execution(events))
    alerts.extend(correlate_rdp_fail_then_success(events))
    alerts.extend(correlate_burst_activity(events))

    alerts = deduplicate_alerts(alerts)
    return alerts


def main():
    events = load_timeline()
    alerts = build_correlations(events)
    write_alerts(alerts, OUTPUT_FILE)

    print(f"[+] Correlation alerts oluşturuldu: {OUTPUT_FILE}")
    print_summary(alerts)


if __name__ == "__main__":
    main()