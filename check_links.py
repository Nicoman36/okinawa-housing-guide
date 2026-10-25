#!/usr/bin/env python3
"""Checks every website in data/locations.csv and writes data/work/link_report.md. stdlib only; polite (1 req/s, HEAD then GET)."""
import csv, time, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT/"data/locations.csv", encoding="utf-8-sig")))
bad = []
for r in rows:
    w = r["website"].strip()
    if not w: continue
    u = w if w.startswith("http") else "https://" + w
    status = None
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers={"User-Agent": "okinawa-housing-directory-linkcheck (+volunteer project)"})
            status = urllib.request.urlopen(req, timeout=15).status; break
        except urllib.error.HTTPError as e: status = e.code
        except Exception as e: status = type(e).__name__
    if status != 200 and not (isinstance(status, int) and 300 <= status < 400): bad.append((r["id"], u, status))
    time.sleep(1)
lines = ["# Link report", "", f"{len(bad)} links need a look (a 403/405 can be a bot block, not a dead site).", ""] + [f"- `{i}` {u} → {s}" for i, u, s in bad]
(ROOT/"data/work").mkdir(parents=True, exist_ok=True)
(ROOT/"data/work/link_report.md").write_text("\n".join(lines), encoding="utf-8"); print("\n".join(lines))
