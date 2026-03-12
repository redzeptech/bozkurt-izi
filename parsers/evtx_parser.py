import sys
import json
import xml.etree.ElementTree as ET
from Evtx.Evtx import Evtx


def parse_evtx(evtx_path, output_json):

    results = []

    with Evtx(evtx_path) as log:
        for record in log.records():

            try:
                xml = record.xml()
                root = ET.fromstring(xml)

                system = root.find("System")
                event_id = int(system.find("EventID").text)
                time_created = system.find("TimeCreated").attrib["SystemTime"]

                data = {}
                for d in root.findall(".//EventData/Data"):
                    name = d.attrib.get("Name")
                    value = d.text
                    if name:
                        data[name] = value

                results.append({
                    "TimeCreated": time_created,
                    "EventID": event_id,
                    "LogonType": data.get("LogonType"),
                    "IpAddress": data.get("IpAddress"),
                    "TargetUserName": data.get("TargetUserName"),
                    "TargetDomainName": data.get("TargetDomainName"),
                    "WorkstationName": data.get("WorkstationName"),
                    "Status": data.get("Status"),
                    "SubStatus": data.get("SubStatus")
                })

            except Exception:
                continue

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[+] JSON üretildi: {output_json}")


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Kullanım:")
        print("python evtx_parser.py security.evtx output.json")
        sys.exit()

    evtx_file = sys.argv[1]
    output_file = sys.argv[2]

    parse_evtx(evtx_file, output_file)