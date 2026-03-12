import os
import csv
import re

SETUPAPI_LOG = r"C:\Windows\INF\setupapi.dev.log"
OUTPUT_FILE = "output/setupapi_usb_events.csv"

USB_PATTERN = re.compile(r"USBSTOR|USB\\VID", re.IGNORECASE)

def parse_setupapi():

    results = []

    if not os.path.exists(SETUPAPI_LOG):
        print("[!] setupapi.dev.log bulunamadı.")
        return

    with open(SETUPAPI_LOG, encoding="utf-8", errors="ignore") as f:

        lines = f.readlines()

    current_time = None

    for line in lines:

        if ">>>  [Device Install" in line:
            current_time = line.strip()

        if USB_PATTERN.search(line):

            results.append({
                "Timestamp": current_time,
                "EventLine": line.strip()
            })

    write_results(results)

def write_results(results):

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "Timestamp",
            "Event"
        ])

        for r in results:

            writer.writerow([
                r["Timestamp"],
                r["EventLine"]
            ])

    print(f"[+] SetupAPI USB events yazıldı: {OUTPUT_FILE}")
    print(f"[+] Toplam event: {len(results)}")


if __name__ == "__main__":
    parse_setupapi()