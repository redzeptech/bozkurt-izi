# Bozkurt İzi

Bozkurt İzi, Türkçe odaklı bir **DFIR (Digital Forensics & Incident Response)** framework geliştirme projesidir.

Amaç; Windows sistemlerde olay analizi, artefact korelasyonu ve zaman çizelgesi üretimini modüler bir yapı ile gerçekleştirmektir.

## Hedef

Bu proje aşağıdaki alanlarda adım adım gelişecek şekilde tasarlanmaktadır:

- RDP brute force analizleri
- Event log timeline korelasyonu
- Prefetch artefact analizi
- USB artefact analizi
- Offline EVTX inceleme desteği
- Modüler DFIR analiz akışı

## Mevcut Bileşenler

### Collectors
Canlı sistemden veri toplama bileşenleri.

- `collectors/collect_rdp_events.ps1`

### Parsers
Ham artefact veya log verisini yapılandırılmış formata dönüştüren bileşenler.

- `parsers/evtx_parser.py`

### Engine
Normalize etme, korelasyon ve analiz motoru.

- `engine/analyze_rdp.py`

### Modules
Artefact bazlı analiz modülleri.

- `modules/prefetch_analysis.py`

## Mimari

```text
Collectors -> Parsers -> Engine -> Modules -> Output
