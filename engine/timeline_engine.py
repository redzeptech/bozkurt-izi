import csv
import os
from datetime import datetime
from typing import List, Dict, Optional

OUTPUT_FILE = os.path.join("output", "timeline.csv")


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
        "%d.%m.%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    for fmt in fallback_formats:
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass

    return None


def get_first(row: Dict, keys: List[str], default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def normalize_event(
    timestamp: datetime,
    source: str,
    event_type: str,
    description: str,
    artifact: str = "",
    user: str = "",
    severity: str = "info",
    raw_ref: str = "",
) -> Dict:
    return {
        "timestamp": timestamp,
        "source": source,
        "event_type": event_type,
        "description": description,
        "artifact": artifact,
        "user": user,
        "severity": severity,
        "raw_ref": raw_ref,
    }


def safe_read_csv(path: str) -> List[Dict]:
    if not os.path.exists(path):
        print(f"[-] Dosya bulunamadı, atlanıyor: {path}")
        return []

    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if rows:
        print(f"[*] Okundu: {path} | Satır: {len(rows)} | Kolonlar: {list(rows[0].keys())}")
    else:
        print(f"[*] Okundu ama boş: {path}")

    return rows


def load_rdp_events() -> List[Dict]:
    file_path = os.path.join("output", "rdp_timeline.csv")
    rows = safe_read_csv(file_path)
    events = []
    skipped = 0

    for row in rows:
        ts = parse_time(get_first(row, ["time", "timestamp", "TimeCreated", "Date"]))
        if not ts:
            skipped += 1
            continue

        event_id = get_first(row, ["event_id", "EventID", "Id"])
        user = get_first(row, ["user", "User", "TargetUserName"])
        ip = get_first(row, ["ip", "IpAddress", "SourceIP"])
        status = get_first(row, ["status", "Status"])
        substatus = get_first(row, ["substatus", "SubStatus"])

        if str(event_id) == "4624":
            event_type = "RDP_SUCCESS_LOGON"
            severity = "medium"
            description = f"Başarılı RDP oturumu. User={user} IP={ip}"
        elif str(event_id) == "4625":
            event_type = "RDP_FAILED_LOGON"
            severity = "high"
            description = f"Başarısız RDP oturumu. User={user} IP={ip} Status={status} SubStatus={substatus}"
        else:
            event_type = "RDP_EVENT"
            severity = "info"
            description = f"RDP ilişkili event. ID={event_id} User={user} IP={ip}"

        events.append(
            normalize_event(
                timestamp=ts,
                source="RDP",
                event_type=event_type,
                description=description,
                artifact=ip,
                user=user,
                severity=severity,
                raw_ref=f"event_id={event_id}",
            )
        )

    print(f"[*] RDP -> timeline: {len(events)} | atlanan: {skipped}")
    return events


def load_prefetch_events() -> List[Dict]:
    file_path = os.path.join("output", "prefetch_timeline.csv")
    rows = safe_read_csv(file_path)
    events = []
    skipped = 0

    for row in rows:
        ts = parse_time(get_first(row, ["LastRun", "Last Run", "Last Run Time", "RunTime", "Timestamp"]))
        executable = get_first(
            row,
            ["Executable", "PrefetchFile", "Application", "Image", "FileName", "Name"]
        )
        suspicious = get_first(row, ["Suspicious", "IsSuspicious"], "").lower() == "true"

        if not executable:
            skipped += 1
            continue

        if not ts:
            skipped += 1
            continue

        severity = "medium" if suspicious else "info"
        description = f"Program çalıştırma izi. Executable={executable}"

        if suspicious:
            description += " (şüpheli/LOLBins listesinde olabilir)"

        events.append(
            normalize_event(
                timestamp=ts,
                source="Prefetch",
                event_type="PROGRAM_EXECUTION",
                description=description,
                artifact=executable,
                user="",
                severity=severity,
                raw_ref="prefetch",
            )
        )

    print(f"[*] Prefetch -> timeline: {len(events)} | atlanan: {skipped}")
    return events


def load_usb_events() -> List[Dict]:
    file_path = os.path.join("output", "usb_artifacts.csv")
    rows = safe_read_csv(file_path)
    events = []
    skipped = 0

    for row in rows:
        ts = parse_time(get_first(row, ["InstanceKeyLastWrite", "LastWrite", "Timestamp", "time"]))
        if not ts:
            skipped += 1
            continue

        device_key = get_first(row, ["DeviceKey", "device_key"])
        instance_id = get_first(row, ["InstanceID", "instance_id"])
        friendly_name = get_first(row, ["FriendlyName", "friendly_name"])
        device_desc = get_first(row, ["DeviceDesc", "device_desc"])

        artifact = friendly_name or device_desc or device_key or instance_id
        description = f"USB cihaz registry izi. DeviceKey={device_key} InstanceID={instance_id}"

        events.append(
            normalize_event(
                timestamp=ts,
                source="USBSTOR",
                event_type="USB_DEVICE_REGISTRY_ARTIFACT",
                description=description,
                artifact=artifact,
                user="",
                severity="medium",
                raw_ref=device_key,
            )
        )

    print(f"[*] USBSTOR -> timeline: {len(events)} | atlanan: {skipped}")
    return events


def load_mounted_devices_events() -> List[Dict]:
    file_path = os.path.join("output", "mounted_devices.csv")
    rows = safe_read_csv(file_path)
    events = []

    # Zaman yoksa timeline'a almıyoruz.
    print(f"[*] MountedDevices -> timeline: 0 | metadata-only kayıt: {len(rows)}")
    return events


def load_setupapi_events() -> List[Dict]:
    file_path = os.path.join("output", "setupapi_usb_events.csv")
    rows = safe_read_csv(file_path)
    events = []
    skipped = 0

    for row in rows:
        raw_ts = get_first(row, ["Timestamp", "time", "Date", "LogTime"])
        event_line = get_first(row, ["Event", "Message", "Line", "Description"])

        ts = parse_time(raw_ts)

        if not ts:
            skipped += 1
            continue

        if not event_line:
            event_line = "SetupAPI device event"

        events.append(
            normalize_event(
                timestamp=ts,
                source="SetupAPI",
                event_type="DEVICE_INSTALL",
                description=f"Cihaz kurulum/kayıt izi: {event_line}",
                artifact=event_line,
                user="",
                severity="medium",
                raw_ref="setupapi",
            )
        )

    print(f"[*] SetupAPI -> timeline: {len(events)} | atlanan: {skipped}")
    return events


def deduplicate_events(events: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []

    for event in events:
        key = (
            event["timestamp"].isoformat(),
            event["source"],
            event["event_type"],
            event["artifact"],
            event["user"],
        )
        if key not in seen:
            seen.add(key)
            unique.append(event)

    return unique


def sort_events(events: List[Dict]) -> List[Dict]:
    return sorted(events, key=lambda x: x["timestamp"])


def write_timeline(events: List[Dict], output_file: str) -> None:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "source",
            "event_type",
            "description",
            "artifact",
            "user",
            "severity",
            "raw_ref",
        ])

        for event in events:
            writer.writerow([
                event["timestamp"].isoformat(),
                event["source"],
                event["event_type"],
                event["description"],
                event["artifact"],
                event["user"],
                event["severity"],
                event["raw_ref"],
            ])


def print_summary(events: List[Dict]) -> None:
    print("[*] Timeline özeti")
    print(f"    Toplam olay sayısı : {len(events)}")

    by_source = {}
    by_severity = {}

    for event in events:
        by_source[event["source"]] = by_source.get(event["source"], 0) + 1
        by_severity[event["severity"]] = by_severity.get(event["severity"], 0) + 1

    print("    Kaynağa göre dağılım:")
    for source, count in sorted(by_source.items()):
        print(f"      - {source}: {count}")

    print("    Severity dağılımı:")
    for sev, count in sorted(by_severity.items()):
        print(f"      - {sev}: {count}")


def build_timeline() -> List[Dict]:
    events = []

    events.extend(load_rdp_events())
    events.extend(load_prefetch_events())
    events.extend(load_usb_events())
    events.extend(load_mounted_devices_events())
    events.extend(load_setupapi_events())

    before = len(events)
    events = deduplicate_events(events)
    after = len(events)

    print(f"[*] Dedupe sonrası: {after} | silinen tekrar: {before - after}")

    events = sort_events(events)
    return events


def main():
    events = build_timeline()
    write_timeline(events, OUTPUT_FILE)

    print(f"[+] Timeline oluşturuldu: {OUTPUT_FILE}")
    print_summary(events)


if __name__ == "__main__":
    main()