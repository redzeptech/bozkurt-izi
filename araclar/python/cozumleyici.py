from pathlib import Path
from datetime import datetime

CIKTI_KLASORU = Path("ciktilar")
RAPOR_DOSYASI = CIKTI_KLASORU / "python_durum_raporu.txt"

def main() -> None:
    CIKTI_KLASORU.mkdir(parents=True, exist_ok=True)

    icerik = [
        "Bozkurt İzi Python çözümleyici başlatıldı.",
        f"Tarih: {datetime.now()}",
        "Durum: Hazır",
        "Açıklama: Bu dosya Python analiz katmanının çalıştığını doğrulamak için üretildi."
    ]

    RAPOR_DOSYASI.write_text("\n".join(icerik), encoding="utf-8")
    print(f"Rapor oluşturuldu: {RAPOR_DOSYASI}")

if __name__ == "__main__":
    main()