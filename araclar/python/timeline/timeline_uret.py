from pathlib import Path
import pandas as pd

GIRDI = Path("ciktilar/event_timeline.csv")
CIKTI_CSV = Path("raporlar/zaman_cizelgesi.csv")
CIKTI_MD = Path("raporlar/zaman_cizelgesi.md")

EVENT_MAP = {
    4624: "Başarılı oturum açma",
    4625: "Başarısız oturum açma",
    4634: "Oturum kapatma",
    4648: "Açık kimlik bilgisi ile giriş denemesi",
    4672: "Özel ayrıcalık atandı",
}

def guvenli_deger(v):
    if pd.isna(v):
        return ""
    return str(v).strip()

def main():
    if not GIRDI.exists():
        print(f"Girdi dosyası bulunamadı: {GIRDI}")
        return

    df = pd.read_csv(GIRDI)

    if df.empty:
        print("Girdi dosyası boş.")
        return

    df["TimeCreated"] = pd.to_datetime(df["TimeCreated"], errors="coerce")
    df = df.sort_values("TimeCreated").copy()

    df["OlayAciklamasi"] = df["EventID"].map(EVENT_MAP).fillna("Bilinmeyen olay")
    df["Ozet"] = df.apply(
        lambda row: (
            f"{row['OlayAciklamasi']} | "
            f"Kullanıcı: {guvenli_deger(row.get('TargetUser', ''))} | "
            f"IP: {guvenli_deger(row.get('IpAddress', ''))} | "
            f"İşİstasyonu: {guvenli_deger(row.get('Workstation', ''))}"
        ),
        axis=1,
    )

    rapor_df = df[
        [
            "TimeCreated",
            "EventID",
            "OlayAciklamasi",
            "TargetUser",
            "IpAddress",
            "Workstation",
            "ProcessName",
            "Ozet",
        ]
    ].copy()

    CIKTI_CSV.parent.mkdir(parents=True, exist_ok=True)
    rapor_df.to_csv(CIKTI_CSV, index=False, encoding="utf-8")

    with CIKTI_MD.open("w", encoding="utf-8") as f:
        f.write("# Zaman Çizelgesi Raporu\n\n")
        f.write(f"Toplam olay sayısı: **{len(rapor_df)}**\n\n")

        for _, row in rapor_df.iterrows():
            zaman = row["TimeCreated"]
            olay = guvenli_deger(row["OlayAciklamasi"])
            ozet = guvenli_deger(row["Ozet"])

            f.write(f"- **{zaman}** — {olay}\n")
            f.write(f"  - {ozet}\n")

    print(f"CSV raporu oluşturuldu: {CIKTI_CSV}")
    print(f"Markdown raporu oluşturuldu: {CIKTI_MD}")

if __name__ == "__main__":
    main()