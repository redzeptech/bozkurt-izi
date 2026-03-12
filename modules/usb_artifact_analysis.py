import os
import csv
import winreg
from datetime import datetime, timezone

OUTPUT_FILE = os.path.join("output", "usb_artifacts.csv")


def filetime_to_dt(filetime_100ns: int) -> str:
    """
    Windows FILETIME (1601 epoch, 100ns) -> ISO8601 string
    """
    try:
        unix_time = (filetime_100ns - 116444736000000000) / 10000000
        dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def get_key_last_write_time(key) -> str:
    """
    Python winreg.QueryInfoKey -> (subkeys, values, last_write_time)
    last_write_time is returned as 100ns intervals since Jan 1, 1601 UTC.
    """
    try:
        info = winreg.QueryInfoKey(key)
        last_write = info[2]
        return filetime_to_dt(last_write)
    except Exception:
        return ""


def safe_query_value(key, value_name):
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return value
    except FileNotFoundError:
        return ""
    except OSError:
        return ""


def enumerate_usbstor():
    results = []

    root_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"

    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root_path)
    except FileNotFoundError:
        print("[!] USBSTOR anahtarı bulunamadı.")
        return results
    except PermissionError:
        print("[!] Registry erişim hatası. PowerShell/Terminal'i yönetici olarak aç.")
        return results

    try:
        vendor_count = winreg.QueryInfoKey(root)[0]

        for i in range(vendor_count):
            vendor_key_name = winreg.EnumKey(root, i)

            try:
                vendor_key = winreg.OpenKey(root, vendor_key_name)
            except OSError:
                continue

            vendor_lastwrite = get_key_last_write_time(vendor_key)

            try:
                instance_count = winreg.QueryInfoKey(vendor_key)[0]

                for j in range(instance_count):
                    instance_key_name = winreg.EnumKey(vendor_key, j)

                    try:
                        instance_key = winreg.OpenKey(vendor_key, instance_key_name)
                    except OSError:
                        continue

                    instance_lastwrite = get_key_last_write_time(instance_key)

                    results.append({
                        "DeviceKey": vendor_key_name,
                        "InstanceID": instance_key_name,
                        "FriendlyName": safe_query_value(instance_key, "FriendlyName"),
                        "DeviceDesc": safe_query_value(instance_key, "DeviceDesc"),
                        "Mfg": safe_query_value(instance_key, "Mfg"),
                        "Service": safe_query_value(instance_key, "Service"),
                        "Class": safe_query_value(instance_key, "Class"),
                        "ClassGUID": safe_query_value(instance_key, "ClassGUID"),
                        "VendorKeyLastWrite": vendor_lastwrite,
                        "InstanceKeyLastWrite": instance_lastwrite,
                    })

            finally:
                winreg.CloseKey(vendor_key)

    finally:
        winreg.CloseKey(root)

    return results


def write_csv(rows, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "DeviceKey",
                "InstanceID",
                "FriendlyName",
                "DeviceDesc",
                "Mfg",
                "Service",
                "Class",
                "ClassGUID",
                "VendorKeyLastWrite",
                "InstanceKeyLastWrite",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = enumerate_usbstor()
    write_csv(rows, OUTPUT_FILE)

    print(f"[+] USB artefact çıktısı: {OUTPUT_FILE}")
    print(f"[+] Toplam kayıt sayısı: {len(rows)}")


if __name__ == "__main__":
    main()