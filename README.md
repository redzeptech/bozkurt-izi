# Bozkurt İzi

**Bozkurt İzi**, Windows sistemleri üzerinde dijital adli bilişim (DFIR) analizi yapmak için geliştirilen açık kaynaklı bir Türkçe analiz framework’üdür.

Framework; artefakt toplama, zaman çizelgesi oluşturma, olay korelasyonu ve analiz raporu üretimi gibi temel DFIR süreçlerini otomatikleştirmeyi amaçlar.

---

## Özellikler

- USB artefakt analizi
- MountedDevices analizi
- SetupAPI cihaz geçmişi analizi
- Prefetch çalıştırma geçmişi analizi
- Timeline (zaman çizelgesi) üretimi
- Korelasyon motoru
- Markdown formatında analiz raporu üretimi

---

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
