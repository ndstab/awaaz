#!/usr/bin/env python3
"""
Poll an Awaaz feed URL and print active incidents.
Usage: python scripts/feed_consumer.py [BASE_URL] [feed_path]

Examples:
  python scripts/feed_consumer.py
  python scripts/feed_consumer.py http://localhost:8000 /api/v1/feed/all/
  python scripts/feed_consumer.py http://localhost:8000 /api/v1/feed/city/bangalore/
"""

import sys
import time
import urllib.request
import xml.etree.ElementTree as ET


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    path = sys.argv[2] if len(sys.argv) > 2 else "/api/v1/feed/all/"
    url = base.rstrip("/") + path

    print(f"Polling {url} every 30s (Ctrl+C to stop)\n")

    while True:
        try:
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/xml")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode()
        except Exception as e:
            print(f"Error: {e}")
        else:
            try:
                root = ET.fromstring(body)
                incidents = root.findall("incident")
                if not incidents:
                    print("No incidents.")
                else:
                    for inc in incidents:
                        inc_id = inc.get("id", "?")
                        inc_type = inc.find("type")
                        inc_type = inc_type.text if inc_type is not None else "?"
                        loc = inc.find("location/polyline")
                        loc = loc.text if loc is not None else "?"
                        print(f"  {inc_id} | {inc_type} | {loc}")
                    print(f"Total: {len(incidents)}")
            except ET.ParseError:
                print(body[:500])
        print()
        time.sleep(30)


if __name__ == "__main__":
    main()
