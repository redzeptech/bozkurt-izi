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

    # Olası formatlar
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

    # Bazı basit fallback formatlar
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
    return rows


def load_rdp_events() -> List[Dict]:
    file_path = os.path.join("output", "rdp_timeline.csv")
    rows = safe_read_csv(file_path)
    events = []

    for row in rows:
        ts = parse_time(row.get("time", ""))
        if not ts:
            continue

        event_id = row.get("event_id", "")
        user = row.get("user", "")
        ip = row.get("ip", "")
        status = row.get("status", "")
        substatus = row.get("substatus", "")

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

    return events


def load_prefetch_events() -> List[Dict]:
    file_path = os.path.join("output", "prefetch_timeline.csv")
    rows = safe_read_csv(file_path)
    events = []

    for row in rows:
        # Basit sürümlerde LastRun, daha basit sürümlerde sadece PrefetchFile olabilir
        ts = parse_time(row.get("LastRun", ""))
        executable = row.get("Executable", "") or row.get("PrefetchFile", "")
        suspicious = str(row.get("Suspicious", "")).strip().lower() == "true"

        if not executable:
            continue

        if not ts:
            # Zaman yoksa timeline’a koymuyoruz; istersen ileride "undated events" diye ayrı raporlanır
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

    return events


def load_usb_events() -> List[Dict]:
    file_path = os.path.join("output", "usb_artifacts.csv")
    rows = safe_read_csv(file_path)
    events = []

    for row in rows:
        ts = parse_time(row.get("InstanceKeyLastWrite", ""))
        if not ts:
            continue

        device_key = row.get("DeviceKey", "")
        instance_id = row.get("InstanceID", "")
        friendly_name = row.get("FriendlyName", "")
        device_desc = row.get("DeviceDesc", "")

        artifact = friendly_name or device_desc or device_key or instance_id
        description = (
            f"USB cihaz registry izi. DeviceKey={device_key} "
            f"InstanceID={instance_id}"
        )

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

    return events


def load_mounted_devices_events() -> List[Dict]:
    file_path = os.path.join("output", "mounted_devices.csv")
    rows = safe_read_csv(file_path)
    events = []

    # MountedDevices verisinde zaman yoksa doğrudan timeline’a almak analitik olarak zayıf.
    # O yüzden bu sürümde zaman yoksa dahil etmiyoruz.
    # İleride korelasyon amacıyla ayrı metadata tablosu olarak da kullanılabilir.
    for row in rows:
        drive = row.get("DriveLetter", "")
        reg_name = row.get("RegistryName", "")

        # Şimdilik timeline'a eklemiyoruz; zaman yok.
        # Ama ileride correlation map olarak kullanılabilir.
        _ = drive, reg_name

    return events


def load_setupapi_events() -> List[Dict]:
    file_path = os.path.join("output", "setupapi_usb_events.csv")
    rows = safe_read_csv(file_path)
    events = []

    for row in rows:
        raw_ts = row.get("Timestamp", "")
        event_line = row.get("Event", "")

        # SetupAPI satırları her zaman parse edilebilir net timestamp taşımayabilir.
        # İlk sürümde parse edilebilenleri alıyoruz.
        ts = parse_time(raw_ts)

        if not ts:
            continue

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

    events = deduplicate_events(events)
    events = sort_events(events)

    return events


def main():
    events = build_timeline()
    write_timeline(events, OUTPUT_FILE)

    print(f"[+] Timeline oluşturuldu: {OUTPUT_FILE}")
    print_summary(events)


if __name__ == "__main__":
    main()