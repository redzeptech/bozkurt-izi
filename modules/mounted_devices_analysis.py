import winreg
import csv
import os

OUTPUT_FILE = "output/mounted_devices.csv"

def analyze_mounted_devices():

    results = []

    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\MountedDevices"
        )
    except Exception as e:
        print("[!] MountedDevices okunamadı:", e)
        return

    i = 0

    while True:
        try:
            name, value, _ = winreg.EnumValue(key, i)

            if name.startswith("\\DosDevices\\"):
                drive_letter = name.replace("\\DosDevices\\", "")

                results.append({
                    "DriveLetter": drive_letter,
                    "BinaryLength": len(value),
                    "RegistryName": name
                })

            i += 1

        except OSError:
            break

    write_results(results)

def write_results(results):

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "DriveLetter",
            "BinaryLength",
            "RegistryName"
        ])

        for r in results:

            writer.writerow([
                r["DriveLetter"],
                r["BinaryLength"],
                r["RegistryName"]
            ])

    print(f"[+] MountedDevices çıktısı oluşturuldu: {OUTPUT_FILE}")
    print(f"[+] Toplam kayıt: {len(results)}")


if __name__ == "__main__":
    analyze_mounted_devices()