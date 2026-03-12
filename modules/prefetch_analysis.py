import os
import csv

PREFETCH_DIR = r"C:\Windows\Prefetch"
OUTPUT_FILE = r"output\prefetch_timeline.csv"


def analyze_prefetch():

    results = []

    if not os.path.exists(PREFETCH_DIR):
        print("Prefetch klasörü bulunamadı.")
        return

    for file in os.listdir(PREFETCH_DIR):

        if not file.endswith(".pf"):
            continue

        path = os.path.join(PREFETCH_DIR, file)

        results.append({
            "PrefetchFile": file,
            "Path": path
        })

    write_results(results)


def write_results(results):

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "PrefetchFile",
            "Path"
        ])

        for r in results:

            writer.writerow([
                r["PrefetchFile"],
                r["Path"]
            ])

    print(f"[+] Prefetch listesi oluşturuldu: {OUTPUT_FILE}")


if __name__ == "__main__":
    analyze_prefetch()