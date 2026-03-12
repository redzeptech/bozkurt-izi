import argparse
import os
import sys
import traceback
import engine.correlation_engine as correlation_engine
from modules import report_engine

# Modules
from modules.prefetch_analysis import analyze_prefetch
from modules.usb_artifact_analysis import enumerate_usbstor, write_csv as write_usb_csv
from modules.mounted_devices_analysis import analyze_mounted_devices
from modules.setupapi_parser import parse_setupapi

# Engine
import engine.timeline_engine as timeline_engine


def banner():
    print("=" * 60)
    print("Bozkurt İzi - Türkçe DFIR Framework")
    print("=" * 60)


def ensure_output():
    os.makedirs("output", exist_ok=True)


def run_prefetch():
    print("[*] Prefetch modülü çalışıyor...")
    analyze_prefetch()
    print("[+] Prefetch modülü tamamlandı.")


def run_usb():
    print("[*] USBSTOR modülü çalışıyor...")
    rows = enumerate_usbstor()
    write_usb_csv(rows, os.path.join("output", "usb_artifacts.csv"))
    print(f"[+] USBSTOR modülü tamamlandı. Kayıt sayısı: {len(rows)}")


def run_mounted():
    print("[*] MountedDevices modülü çalışıyor...")
    analyze_mounted_devices()
    print("[+] MountedDevices modülü tamamlandı.")


def run_setupapi():
    print("[*] SetupAPI modülü çalışıyor...")
    parse_setupapi()
    print("[+] SetupAPI modülü tamamlandı.")


def run_timeline():
    print("[*] Timeline engine çalışıyor...")
    timeline_engine.main()
    print("[+] Timeline engine tamamlandı.")


def run_full():
    print("[*] Full analysis pipeline başlatılıyor...")
    run_prefetch()
    run_usb()
    run_mounted()
    run_setupapi()
    run_timeline()
    run_correlate()
    run_report()
    print("[+] Full analysis pipeline tamamlandı.")
    
            
def run_correlate():
    print("[*] Correlation engine çalışıyor...")
    correlation_engine.main()
    print("[+] Correlation engine tamamlandı.")
    
def run_report():
    print("[*] Report engine çalışıyor...")
    report_engine.main()
    print("[+] Report engine tamamlandı.")   
    
    
def parse_args():

    parser = argparse.ArgumentParser(
        description="Bozkurt İzi - Türkçe DFIR Framework"
    )

    parser.add_argument("command", choices=["prefetch","usb","mounted","setupapi","timeline","correlate","report","full"])

    return parser.parse_args()


def main():
    banner()
    ensure_output()
    args = parse_args()

    try:
        if args.command == "prefetch":
            run_prefetch()
        elif args.command == "usb":
            run_usb()
        elif args.command == "mounted":
            run_mounted()
        elif args.command == "setupapi":
            run_setupapi()
        elif args.command == "timeline":
            run_timeline()
        elif args.command == "full":
            run_full()
        elif args.command == "correlate":
            run_correlate()    
        elif args.command == "report":
            run_report()    
        else:
            print("[!] Bilinmeyen komut.")
            sys.exit(1)

    except Exception as e:
        print("[!] Hata oluştu:", str(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()