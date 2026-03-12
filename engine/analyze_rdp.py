import json
import csv
import os
import argparse
from collections import defaultdict
from datetime import datetime, timedelta

BRUTE_FORCE_THRESHOLD = 5
SPRAY_USER_THRESHOLD = 3
WINDOW_MINUTES = 5
SUCCESS_WINDOW_MINUTES = 10


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="rdp_events.json tam yolu")
    parser.add_argument("--output-dir", required=True, help="çıktı klasörü")
    return parser.parse_args()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_events(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Girdi dosyası bulunamadı: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    if not raw:
        return []

    data = json.loads(raw)

    if isinstance(data, dict):
        data = [data]

    cleaned = []
    for item in data:
        try:
            cleaned.append({
                "time": parse_time(item.get("TimeCreated")),
                "event_id": int(item.get("EventID")),
                "record_id": item.get("RecordId"),
                "computer": item.get("Computer"),
                "logon_type": item.get("LogonType"),
                "ip": item.get("IpAddress"),
                "user": item.get("TargetUserName"),
                "domain": item.get("TargetDomainName"),
                "workstation": item.get("WorkstationName"),
                "status": item.get("Status"),
                "substatus": item.get("SubStatus"),
            })
        except Exception:
            continue

    return sorted(cleaned, key=lambda x: x["time"])


def normalize_events(events):
    filtered = []
    bad_users = {"ANONYMOUS LOGON", "DWM-1", "UMFD-0", "LOCAL SERVICE", "NETWORK SERVICE", "SYSTEM"}
    bad_ips = {"-", "", None, "127.0.0.1", "::1"}

    for e in events:
        user = (e["user"] or "").strip()
        ip = e["ip"]

        if ip in bad_ips:
            continue
        if not user or user.upper() in bad_users:
            continue
        if str(e["logon_type"]) != "10":
            continue

        filtered.append(e)

    return filtered


def write_timeline(events, path: str):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time", "event_id", "ip", "user", "domain", "logon_type",
            "workstation", "status", "substatus", "record_id", "computer"
        ])

        for e in events:
            writer.writerow([
                e["time"].isoformat(),
                e["event_id"],
                e["ip"],
                e["user"],
                e["domain"],
                e["logon_type"],
                e["workstation"],
                e["status"],
                e["substatus"],
                e["record_id"],
                e["computer"],
            ])


def find_success_after(fail_time, ip, user, success_events, minutes):
    max_time = fail_time + timedelta(minutes=minutes)
    for s in success_events:
        if s["ip"] == ip and s["user"] == user and fail_time <= s["time"] <= max_time:
            return s
    return None


def score_severity(failed_count, distinct_users, has_success, technique):
    if technique == "PASSWORD_SPRAY":
        if has_success:
            return "critical"
        if distinct_users >= 10:
            return "high"
        return "medium"

    if technique == "BRUTE_FORCE":
        if has_success and failed_count >= 10:
            return "critical"
        if has_success:
            return "high"
        if failed_count >= 10:
            return "high"
        return "medium"

    return "low"


def analyze_bruteforce(events):
    failed_by_key = defaultdict(list)
    success_events = []

    for e in events:
        if e["event_id"] == 4625:
            failed_by_key[(e["ip"], e["user"])].append(e)
        elif e["event_id"] == 4624:
            success_events.append(e)

    alerts = []

    for (ip, user), failed_list in failed_by_key.items():
        failed_list = sorted(failed_list, key=lambda x: x["time"])

        start = 0
        for end in range(len(failed_list)):
            while failed_list[end]["time"] - failed_list[start]["time"] > timedelta(minutes=WINDOW_MINUTES):
                start += 1

            window = failed_list[start:end + 1]

            if len(window) >= BRUTE_FORCE_THRESHOLD:
                first_fail = window[0]["time"]
                last_fail = window[-1]["time"]
                success = find_success_after(last_fail, ip, user, success_events, SUCCESS_WINDOW_MINUTES)

                alerts.append({
                    "technique": "BRUTE_FORCE",
                    "ip": ip,
                    "user": user,
                    "failed_count": len(window),
                    "distinct_users": 1,
                    "first_seen": first_fail.isoformat(),
                    "last_seen": last_fail.isoformat(),
                    "success_time": success["time"].isoformat() if success else "",
                    "status": "SUCCESS_AFTER_ATTACK" if success else "FAILED_ATTACK_ATTEMPT",
                    "severity": score_severity(len(window), 1, bool(success), "BRUTE_FORCE")
                })
                break

    return alerts


def analyze_password_spray(events):
    failed_by_ip = defaultdict(list)
    success_events = []

    for e in events:
        if e["event_id"] == 4625:
            failed_by_ip[e["ip"]].append(e)
        elif e["event_id"] == 4624:
            success_events.append(e)

    alerts = []

    for ip, failed_list in failed_by_ip.items():
        failed_list = sorted(failed_list, key=lambda x: x["time"])

        start = 0
        for end in range(len(failed_list)):
            while failed_list[end]["time"] - failed_list[start]["time"] > timedelta(minutes=WINDOW_MINUTES):
                start += 1

            window = failed_list[start:end + 1]
            users = sorted(set(x["user"] for x in window if x["user"]))

            if len(users) >= SPRAY_USER_THRESHOLD:
                first_seen = window[0]["time"]
                last_seen = window[-1]["time"]

                success = None
                max_time = last_seen + timedelta(minutes=SUCCESS_WINDOW_MINUTES)
                for s in success_events:
                    if s["ip"] == ip and s["user"] in users and last_seen <= s["time"] <= max_time:
                        success = s
                        break

                alerts.append({
                    "technique": "PASSWORD_SPRAY",
                    "ip": ip,
                    "user": "|".join(users),
                    "failed_count": len(window),
                    "distinct_users": len(users),
                    "first_seen": first_seen.isoformat(),
                    "last_seen": last_seen.isoformat(),
                    "success_time": success["time"].isoformat() if success else "",
                    "status": "SUCCESS_AFTER_ATTACK" if success else "FAILED_ATTACK_ATTEMPT",
                    "severity": score_severity(len(window), len(users), bool(success), "PASSWORD_SPRAY")
                })
                break

    return alerts


def deduplicate_alerts(alerts):
    seen = set()
    unique = []

    for a in alerts:
        key = (
            a["technique"],
            a["ip"],
            a["user"],
            a["first_seen"],
            a["last_seen"],
            a["status"]
        )
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique


def write_alerts(alerts, path: str):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "technique", "ip", "user", "failed_count", "distinct_users",
            "first_seen", "last_seen", "success_time", "status", "severity"
        ])

        for a in alerts:
            writer.writerow([
                a["technique"],
                a["ip"],
                a["user"],
                a["failed_count"],
                a["distinct_users"],
                a["first_seen"],
                a["last_seen"],
                a["success_time"],
                a["status"],
                a["severity"],
            ])


def print_summary(alerts):
    brute_count = sum(1 for x in alerts if x["technique"] == "BRUTE_FORCE")
    spray_count = sum(1 for x in alerts if x["technique"] == "PASSWORD_SPRAY")
    critical_count = sum(1 for x in alerts if x["severity"] == "critical")
    high_count = sum(1 for x in alerts if x["severity"] == "high")

    print("[*] Analiz özeti")
    print(f"    Brute force alert sayısı   : {brute_count}")
    print(f"    Password spray alert sayısı: {spray_count}")
    print(f"    Critical alert sayısı      : {critical_count}")
    print(f"    High alert sayısı          : {high_count}")


def main():
    args = parse_args()

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    timeline_file = os.path.join(output_dir, "rdp_timeline.csv")
    alerts_file = os.path.join(output_dir, "rdp_alerts.csv")

    events = load_events(args.input)
    events = normalize_events(events)

    write_timeline(events, timeline_file)

    brute_alerts = analyze_bruteforce(events)
    spray_alerts = analyze_password_spray(events)

    all_alerts = deduplicate_alerts(brute_alerts + spray_alerts)
    write_alerts(all_alerts, alerts_file)

    print(f"[+] Timeline üretildi: {timeline_file}")
    print(f"[+] Alert dosyası üretildi: {alerts_file}")
    print(f"[+] Normalize event sayısı: {len(events)}")
    print(f"[+] Toplam alert sayısı: {len(all_alerts)}")
    print_summary(all_alerts)


if __name__ == "__main__":
    main()