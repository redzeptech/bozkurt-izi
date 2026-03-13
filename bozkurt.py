import argparse
import os
import sys
import traceback

# Engine
import engine.timeline_engine as timeline_engine
import engine.correlation_engine as correlation_engine
from engine.case_manager import create_case

# Modules
from modules.prefetch_analysis import analyze_prefetch
from modules.usb_artifact_analysis import (
    enumerate_usbstor,
    write_csv as write_usb_csv,
)
from modules.mounted_devices_analysis import analyze_mounted_devices
from modules.setupapi_parser import parse_setupapi

# Official report generator
from core.report_generator import generate_report


def banner() -> None:
    print("=" * 60)
    print("Bozkurt İzi - Türkçe DFIR Framework")
    print("=" * 60)


def ensure_output() -> None:
    os.makedirs("output", exist_ok=True)


def run_prefetch() -> None:
    print("[*] Prefetch modülü çalışıyor...")
    analyze_prefetch()
    print("[+] Prefetch modülü tamamlandı.")


def run_usb() -> None:
    print("[*] USBSTOR modülü çalışıyor...")
    rows = enumerate_usbstor()
    write_usb_csv(rows, os.path.join("output", "usb_artifacts.csv"))
    print(f"[+] USBSTOR modülü tamamlandı. Kayıt sayısı: {len(rows)}")


def run_mounted() -> None:
    print("[*] MountedDevices modülü çalışıyor...")
    analyze_mounted_devices()
    print("[+] MountedDevices modülü tamamlandı.")


def run_setupapi() -> None:
    print("[*] SetupAPI modülü çalışıyor...")
    parse_setupapi()
    print("[+] SetupAPI modülü tamamlandı.")


def run_timeline() -> None:
    print("[*] Timeline engine çalışıyor...")
    timeline_engine.main()
    print("[+] Timeline engine tamamlandı.")


def run_correlate() -> None:
    print("[*] Correlation engine çalışıyor...")
    correlation_engine.main()
    print("[+] Correlation engine tamamlandı.")


def run_report() -> None:
    print("[*] Report generator çalışıyor...")
    report_path = generate_report()
    print(f"[OK] Report generated: {report_path}")


def run_case() -> None:
    print("[*] Yeni DFIR case oluşturuluyor...")
    create_case()
    print("[+] Case hazır.")


def run_full() -> None:
    print("[*] Full analysis pipeline başlatılıyor...")

    run_prefetch()
    run_usb()
    run_mounted()
    run_setupapi()
    run_timeline()
    run_correlate()
    run_report()

    print("[+] Full analysis pipeline tamamlandı.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bozkurt İzi - Türkçe DFIR Framework"
    )
    parser.add_argument(
        "command",
        help="Çalıştırılacak analiz modülü",
        choices=[
            "case",
            "prefetch",
            "usb",
            "mounted",
            "setupapi",
            "timeline",
            "correlate",
            "report",
            "full",
        ],
    )
    return parser.parse_args()


def main() -> None:
    banner()
    ensure_output()
    args = parse_args()

    try:
        if args.command == "case":
            run_case()
        elif args.command == "prefetch":
            run_prefetch()
        elif args.command == "usb":
            run_usb()
        elif args.command == "mounted":
            run_mounted()
        elif args.command == "setupapi":
            run_setupapi()
        elif args.command == "timeline":
            run_timeline()
        elif args.command == "correlate":
            run_correlate()
        elif args.command == "report":
            run_report()
        elif args.command == "full":
            run_full()
        else:
            print("[!] Bilinmeyen komut.")
            sys.exit(1)

    except Exception as e:
        print(f"[!] Hata oluştu: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
