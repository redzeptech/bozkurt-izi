# Bozkurt İzi

Türkçe DFIR framework for artifact parsing, timeline generation, correlation, and reporting.

## Özellikler
- USB artifact analizi
- MountedDevices analizi
- SetupAPI parse
- Prefetch analizi
- Timeline üretimi
- Correlation engine
- Markdown rapor üretimi

## Proje Yapısı
- bozkurt.py
- engine/
- modules/
- core/
- output/
- cases/

## Kullanım
python bozkurt.py case
python bozkurt.py prefetch
python bozkurt.py usb
python bozkurt.py mounted
python bozkurt.py setupapi
python bozkurt.py timeline
python bozkurt.py correlate
python bozkurt.py report
python bozkurt.py full

## Üretilen Çıktılar
- output/timeline.csv
- output/correlation_alerts.csv
- output/bozkurt_report.md

## Yol Haritası
- HTML rapor
- JSON rapor
- Kural tabanı genişletme
- Ek Windows artifact modülleri

