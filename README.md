# Bozkurt İzi

**Türkçe odaklı dijital adli bilişim iz sürme ve analiz projesi**

## Proje Amacı

Bozkurt İzi, dijital sistemlerde bırakılan izleri toplamak, sınıflandırmak, ilişkilendirmek ve anlamlandırmak amacıyla geliştirilen açık kaynak bir adli bilişim projesidir.

Bu proje özellikle Windows artefact analizi, olay zaman çizelgesi oluşturma ve vaka özetleme süreçlerine odaklanacaktır.

## Hedefler

- Windows odaklı artefact toplama
- Olay zaman çizelgesi üretme
- RDP ve kullanıcı etkinliği analizi
- Türkçe açıklamalı bulgu üretimi
- Eğitim ve uygulama odaklı DFIR yaklaşımı

## Klasör Yapısı

- `docs/` → proje dokümantasyonu
- `araclar/powershell/` → veri toplama scriptleri
- `araclar/python/` → analiz ve raporlama araçları
- `ornek-veri/` → test verileri
- `ciktilar/` → üretilen çıktılar
- `raporlar/` → vaka özetleri
- `kurallar/` → tespit ve öncelik kuralları

## İlk Hedef

İlk sürümde Windows kullanıcı etkinliği ve RDP odaklı temel artefact korelasyonu geliştirilecektir.
## Mevcut Modüller

### RDP Analiz
Başarısız oturum açma denemelerini IP bazlı analiz eder.

### Event Timeline
Security log olaylarını zaman sırasına göre çıkarır ve raporlar.
# Bozkurt İzi

Türkçe Dijital Adli Bilişim (DFIR) analiz framework.

## Özellikler

- RDP brute force analizi
- Event Log korelasyonu
- EVTX parser
- Prefetch artefact analizi

## Mimari

Collectors → Parsers → Engine → Modules → Output

## Amaç

Türkçe açık kaynak DFIR araç geliştirmek.
