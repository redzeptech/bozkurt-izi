import pandas as pd
from pathlib import Path

girdi = Path("ciktilar/rdp_loglari.csv")
cikti = Path("raporlar/rdp_bruteforce_analiz.csv")

df = pd.read_csv(girdi)

sonuc = (
    df.groupby("IPAddress")
    .size()
    .reset_index(name="fail_count")
    .sort_values("fail_count", ascending=False)
)

sonuc.to_csv(cikti, index=False)

print("Analiz tamamlandı.")
print(sonuc.head())