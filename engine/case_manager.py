import os
from datetime import datetime


BASE_CASE_DIR = "cases"


def create_case(case_name=None):
    if not os.path.exists(BASE_CASE_DIR):
        os.makedirs(BASE_CASE_DIR)

    if not case_name:
        case_name = datetime.now().strftime("CASE_%Y%m%d_%H%M%S")

    case_path = os.path.join(BASE_CASE_DIR, case_name)

    os.makedirs(case_path, exist_ok=True)
    os.makedirs(os.path.join(case_path, "artifacts"), exist_ok=True)
    os.makedirs(os.path.join(case_path, "timeline"), exist_ok=True)
    os.makedirs(os.path.join(case_path, "reports"), exist_ok=True)
    os.makedirs(os.path.join(case_path, "logs"), exist_ok=True)

    print(f"[+] Case oluşturuldu: {case_path}")
    return case_path