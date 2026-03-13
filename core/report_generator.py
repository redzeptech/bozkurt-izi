import csv
import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional


TIMELINE_FILE = os.path.join("output", "timeline.csv")
ALERTS_FILE = os.path.join("output", "correlation_alerts.csv")
REPORT_FILE = os.path.join("output", "bozkurt_report.md")


def safe_read_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []

    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_time(value: str) -> Optional[datetime]:
    value = normalize_text(value)
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
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
    ]

    for fmt in fallback_formats:
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass

    return None


def detect_timestamp_field(rows: List[Dict[str, str]]) -> Optional[str]:
    if not rows:
        return None

    candidate_fields = [
        "timestamp",
        "time",
        "event_time",
        "created_at",
        "datetime",
    ]

    row_keys = set()
    for row in rows[:10]:
        row_keys.update(row.keys())

    for field in candidate_fields:
        if field in row_keys:
            return field

    return None


def sort_timeline_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    timestamp_field = detect_timestamp_field(rows)
    if not timestamp_field:
        return rows

    return sorted(
        rows,
        key=lambda r: parse_time(r.get(timestamp_field, "")) or datetime.min
    )


def count_by_field(rows: List[Dict[str, str]], field: str) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        value = normalize_text(row.get(field, ""))
        if value:
            counter[value] += 1
    return counter


def top_items(counter: Counter, limit: int = 5) -> List[str]:
    return [f"- {name}: {count}" for name, count in counter.most_common(limit)]


def timeline_time_range(rows: List[Dict[str, str]]) -> Dict[str, str]:
    timestamp_field = detect_timestamp_field(rows)
    if not timestamp_field:
        return {"start": "Bilinmiyor", "end": "Bilinmiyor"}

    parsed_times = []
    for row in rows:
        dt = parse_time(row.get(timestamp_field, ""))
        if dt:
            parsed_times.append(dt)

    if not parsed_times:
        return {"start": "Bilinmiyor", "end": "Bilinmiyor"}

    parsed_times.sort()
    return {
        "start": parsed_times[0].isoformat(sep=" ", timespec="seconds"),
        "end": parsed_times[-1].isoformat(sep=" ", timespec="seconds"),
    }


def severity_from_alert(alert: Dict[str, Any]) -> str:
    for key in ["severity", "level", "risk", "priority"]:
        value = normalize_text(alert.get(key))
        if value:
            return value
    return "unknown"


def title_from_alert(alert: Dict[str, Any]) -> str:
    for key in [
        "correlation_type",
        "title",
        "name",
        "rule",
        "alert",
        "description",
    ]:
        value = normalize_text(alert.get(key))
        if value:
            return value
    return "Untitled Alert"


def summary_from_alert(alert: Dict[str, Any]) -> str:
    for key in ["summary", "message", "details", "description"]:
        value = normalize_text(alert.get(key))
        if value:
            return value
    return "Detay bilgisi yok."


def sort_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    severity_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 4,
        "unknown": 5,
    }

    def alert_key(alert: Dict[str, Any]):
        sev = severity_from_alert(alert).lower()
        return severity_order.get(sev, 5), title_from_alert(alert).lower()

    return sorted(alerts, key=alert_key)


def build_executive_summary(
    timeline_rows: List[Dict[str, str]],
    alerts: List[Dict[str, Any]],
) -> str:
    total_events = len(timeline_rows)
    total_alerts = len(alerts)

    sev_counter = Counter(severity_from_alert(a).lower() for a in alerts)
    critical_high = sev_counter.get("critical", 0) + sev_counter.get("high", 0)

    if total_events == 0 and total_alerts == 0:
        return (
            "Bu analiz çalıştırılmış ancak raporlanacak veri üretilememiş. "
            "Pipeline girişleri, parser çıktıları ve output klasörü kontrol edilmelidir."
        )

    if total_alerts == 0:
        return (
            f"Toplam {total_events} zaman çizelgesi olayı işlendi. "
            "Korelasyon motoru tarafından alarm üretilmedi. "
            "Bu durum temiz sistem anlamına gelmez; yalnızca mevcut kuralların eşleşme üretmediğini gösterir."
        )

    if critical_high > 0:
        return (
            f"Analizde toplam {total_events} olay ve {total_alerts} korelasyon alarmı bulundu. "
            f"Bunların {critical_high} tanesi yüksek öncelikli görünüyor. "
            "Özellikle high ve critical bulgular manuel incelemeye alınmalıdır."
        )

    return (
        f"Analizde toplam {total_events} olay ve {total_alerts} korelasyon alarmı bulundu. "
        "Alarm üretimi mevcut olsa da ilk bakışta yüksek öncelikli yoğun bir tablo görünmüyor. "
        "Yine de bağlam analizi yapılmadan kesin hüküm verilmemelidir."
    )


def build_timeline_section(timeline_rows: List[Dict[str, str]]) -> str:
    if not timeline_rows:
        return "## Timeline Özeti\n\nTimeline verisi bulunamadı.\n"

    range_info = timeline_time_range(timeline_rows)
    source_counter = count_by_field(timeline_rows, "source")
    event_counter = count_by_field(timeline_rows, "event")
    artifact_counter = count_by_field(timeline_rows, "artifact")

    lines = [
        "## Timeline Özeti",
        "",
        f"- Toplam olay sayısı: **{len(timeline_rows)}**",
        f"- Başlangıç zamanı: **{range_info['start']}**",
        f"- Bitiş zamanı: **{range_info['end']}**",
        "",
        "### En Sık Kaynaklar",
    ]

    lines.extend(top_items(source_counter) if source_counter else ["- Veri yok"])

    lines.extend([
        "",
        "### En Sık Event Türleri",
    ])
    lines.extend(top_items(event_counter) if event_counter else ["- Veri yok"])

    lines.extend([
        "",
        "### En Sık Artifact Türleri",
    ])
    lines.extend(top_items(artifact_counter) if artifact_counter else ["- Veri yok"])
    lines.append("")

    return "\n".join(lines)


def build_alerts_section(alerts: List[Dict[str, Any]]) -> str:
    if not alerts:
        return "## Korelasyon Bulguları\n\nKorelasyon alarmı bulunamadı.\n"

    sev_counter = Counter(severity_from_alert(a).lower() for a in alerts)
    sorted_alerts = sort_alerts(alerts)

    lines = [
        "## Korelasyon Bulguları",
        "",
        f"- Toplam alarm sayısı: **{len(alerts)}**",
        f"- Critical: **{sev_counter.get('critical', 0)}**",
        f"- High: **{sev_counter.get('high', 0)}**",
        f"- Medium: **{sev_counter.get('medium', 0)}**",
        f"- Low: **{sev_counter.get('low', 0)}**",
        f"- Info: **{sev_counter.get('info', 0)}**",
        "",
        "### Alarm Detayları",
        "",
    ]

    for idx, alert in enumerate(sorted_alerts, start=1):
        title = title_from_alert(alert)
        severity = severity_from_alert(alert)
        summary = summary_from_alert(alert)

        lines.extend([
            f"#### {idx}. {title}",
            f"- Severity: **{severity}**",
            f"- Özet: {summary}",
        ])

        first_seen = normalize_text(alert.get("first_seen"))
        last_seen = normalize_text(alert.get("last_seen"))
        user = normalize_text(alert.get("user"))
        artifact_1 = normalize_text(alert.get("artifact_1"))
        artifact_2 = normalize_text(alert.get("artifact_2"))

        if first_seen:
            lines.append(f"- First Seen: **{first_seen}**")
        if last_seen:
            lines.append(f"- Last Seen: **{last_seen}**")
        if user:
            lines.append(f"- User: **{user}**")
        if artifact_1:
            lines.append(f"- Artifact 1: `{artifact_1}`")
        if artifact_2:
            lines.append(f"- Artifact 2: `{artifact_2}`")

        lines.append("")

    return "\n".join(lines)


def build_sample_events_section(
    timeline_rows: List[Dict[str, str]],
    limit: int = 10,
) -> str:
    if not timeline_rows:
        return "## Örnek Olaylar\n\nGösterilecek olay yok.\n"

    sorted_rows = sort_timeline_rows(timeline_rows)
    timestamp_field = detect_timestamp_field(sorted_rows) or "timestamp"

    lines = [
        "## Örnek Olaylar",
        "",
        "| Zaman | Kaynak | Event | Artifact | Detay |",
        "|---|---|---|---|---|",
    ]

    for row in sorted_rows[:limit]:
        ts = normalize_text(row.get(timestamp_field, ""))
        source = normalize_text(row.get("source", ""))
        event = normalize_text(row.get("event", ""))
        artifact = normalize_text(row.get("artifact", ""))
        detail = normalize_text(row.get("details", "")) or normalize_text(row.get("message", ""))

        source = source.replace("|", "/")
        event = event.replace("|", "/")
        artifact = artifact.replace("|", "/")
        detail = detail.replace("|", "/")

        if len(detail) > 120:
            detail = detail[:117] + "..."

        lines.append(f"| {ts} | {source} | {event} | {artifact} | {detail} |")

    lines.append("")
    return "\n".join(lines)


def generate_report() -> str:
    timeline_rows = safe_read_csv(TIMELINE_FILE)
    alerts = safe_read_csv(ALERTS_FILE)

    generated_at = datetime.now().isoformat(sep=" ", timespec="seconds")

    parts = [
        "# Bozkurt İzi Analiz Raporu",
        "",
        f"- Oluşturulma zamanı: **{generated_at}**",
        f"- Timeline dosyası: `{TIMELINE_FILE}`",
        f"- Alerts dosyası: `{ALERTS_FILE}`",
        "",
        "## Yönetici Özeti",
        "",
        build_executive_summary(timeline_rows, alerts),
        "",
        build_timeline_section(timeline_rows),
        build_alerts_section(alerts),
        build_sample_events_section(timeline_rows, limit=10),
        "## Sonuç",
        "",
        (
            "Bu rapor otomatik olarak üretilmiştir. Nihai adli değerlendirme için "
            "bulgular manuel doğrulama, olay bağlamı ve ek artefakt incelemesi ile desteklenmelidir."
        ),
        "",
    ]

    report = "\n".join(parts)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    return REPORT_FILE


if __name__ == "__main__":
    output_path = generate_report()
    print(f"[OK] Rapor üretildi: {output_path}")
