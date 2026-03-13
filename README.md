# Bozkurt İzi

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-informational)
![DFIR](https://img.shields.io/badge/DFIR-Digital%20Forensics-orange)
![License](https://img.shields.io/github/license/redzeptech/bozkurt-izi)
![Last Commit](https://img.shields.io/github/last-commit/redzeptech/bozkurt-izi)
![Repo Size](https://img.shields.io/github/repo-size/redzeptech/bozkurt-izi)
![Issues](https://img.shields.io/github/issues/redzeptech/bozkurt-izi)

**Bozkurt İzi**, Windows sistemleri üzerinde dijital adli bilişim (DFIR) analizi yapmak için geliştirilen açık kaynaklı bir Türkçe analiz framework’üdür.

Framework; artefakt analizi, zaman çizelgesi üretimi, olay korelasyonu ve analiz raporu oluşturma süreçlerini otomatikleştirmeyi amaçlar.

---

# Özellikler

- USB artefakt analizi
- MountedDevices registry analizi
- SetupAPI cihaz geçmişi analizi
- Prefetch çalıştırma geçmişi analizi
- Timeline üretimi
- Korelasyon motoru
- Markdown analiz raporu üretimi

---

## Mimari Akış

```mermaid
flowchart LR
A[Windows Artifacts] --> B[Analysis Modules]

B --> B1[USB Artifact Analysis]
B --> B2[MountedDevices Analysis]
B --> B3[SetupAPI Parser]
B --> B4[Prefetch Analysis]

B1 --> C[Timeline Engine]
B2 --> C
B3 --> C
B4 --> C

C --> D[timeline.csv]

D --> E[Correlation Engine]
E --> F[correlation_alerts.csv]

D --> G[Report Generator]
F --> G

G --> H[bozkurt_report.md]


Bozkurt İzi, Windows artefaktlarını modüler analiz katmanlarından geçirerek zaman çizelgesi, korelasyon çıktıları ve okunabilir analiz raporu üretmeyi hedefler.

## Proje Yapısı

bozkurt-izi
│
├─ bozkurt.py
│
├─ engine
│ ├─ timeline_engine.py
│ ├─ correlation_engine.py
│ └─ case_manager.py
│
├─ modules
│ ├─ prefetch_analysis.py
│ ├─ usb_artifact_analysis.py
│ ├─ mounted_devices_analysis.py
│ └─ setupapi_parser.py
│
├─ core
│ └─ report_generator.py
│
├─ collectors
│ └─ collect_rdp_events.ps1
│
├─ output
│ └─ (analiz çıktıları)
│
├─ cases
│ └─ (case klasörleri)
│
└─ docs

---

## Kurulum

Projeyi klonlayın:

```bash
git clone https://github.com/redzeptech/bozkurt-izi.git
cd bozkurt-izi
Python 3.10+ önerilir.

## Kullanım
Yeni analiz vakası oluştur
python bozkurt.py case

Prefetch analizi
python bozkurt.py prefetch

USB artefakt analizi
python bozkurt.py usb

MountedDevices analizi
python bozkurt.py mounted

SetupAPI cihaz geçmişi
python bozkurt.py setupapi

Timeline oluşturma
python bozkurt.py timeline

Korelasyon analizi
python bozkurt.py correlate

Analiz raporu üretme
python bozkurt.py report

Tüm pipeline'ı çalıştırma
python bozkurt.py full

Üretilen Çıktılar

Analiz sonucunda output klasöründe aşağıdaki dosyalar oluşur:
output/
├─ timeline.csv
├─ correlation_alerts.csv
├─ usb_artifacts.csv
├─ prefetch_timeline.csv
└─ bozkurt_report.md
## Amaç

Bozkurt İzi'nin amacı:

Türkçe DFIR araç ekosistemine katkı sağlamak

Windows artefakt analizini kolaylaştırmak

Açık kaynaklı DFIR araç geliştirme kültürünü desteklemek

## Yol Haritası

Planlanan geliştirmeler:

HTML rapor üretimi

JSON rapor çıktısı

Gelişmiş korelasyon kuralları

Ek Windows artefakt modülleri

SIEM entegrasyonu

## Lisans

Bu proje MIT License altında lisanslanmıştır.

## Example Report

Example output:


