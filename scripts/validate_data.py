#!/usr/bin/env python3
"""CI gate: python3 scripts/validate_data.py  (exit 1 on any error)"""
import csv, re, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import SVC, VERIF, STATUS, KINDS
from geo import MUNI_SLUGS
ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT/"data/locations.csv", encoding="utf-8-sig")))
src = {s["id"] for s in csv.DictReader(open(ROOT/"data/sources.csv", encoding="utf-8-sig"))}
errs, warns, seen = [], [], set()
for r in rows:
    i = r["id"]
    if not re.fullmatch(r"[a-z0-9-]+", i): errs.append(f"{i}: bad id")
    if i in seen: errs.append(f"{i}: duplicate id")
    seen.add(i)
    if not r["name_en"]: errs.append(f"{i}: missing name_en")
    if r["kind"] not in KINDS: errs.append(f"{i}: bad kind {r['kind']!r}")
    for d in r["services"].split(";"):
        if d not in SVC: errs.append(f"{i}: unknown service {d!r}")
    if not r["services"]: errs.append(f"{i}: no service")
    if r["municipality"] and r["municipality"] not in MUNI_SLUGS: errs.append(f"{i}: unknown municipality {r['municipality']!r}")
    if r["verification"] not in VERIF: errs.append(f"{i}: bad verification")
    if r["status"] not in STATUS: errs.append(f"{i}: bad status")
    for s in filter(None, r["sources"].split(";")):
        if s not in src: errs.append(f"{i}: unknown source {s!r}")
    if r["last_verified"]:
        try: datetime.date.fromisoformat(r["last_verified"])
        except ValueError: errs.append(f"{i}: last_verified must be YYYY-MM-DD")
    if r["verification"] == "A" and not r["last_verified"]: errs.append(f"{i}: verification A needs last_verified")
    if r.get("lat") or r.get("lon"):
        try:
            la, lo = float(r["lat"]), float(r["lon"])
            if not (23.5 < la < 28.6 and 122.5 < lo < 131.5): errs.append(f"{i}: coordinates outside Okinawa")
        except ValueError: errs.append(f"{i}: bad lat/lon")
    if r.get("open_hours"):
        for part in r["open_hours"].split(";"):
            if not re.fullmatch(r"\s*(mon|tue|wed|thu|fri|sat|sun)(-(mon|tue|wed|thu|fri|sat|sun))? \d\d:\d\d-\d\d:\d\d\s*", part): errs.append(f"{i}: open_hours part {part!r} must look like 'mon-fri 09:00-17:00'")
    if r["phone"] and not re.search(r"\d", r["phone"]): warns.append(f"{i}: phone has no digits")
    if r["website"] and not re.match(r"(https?://|[\w.-]+\.\w+)", r["website"]): warns.append(f"{i}: odd website")
    if r["kind"] == "agency" and r["verification"] in ("A", "B") and not r["license"]: warns.append(f"{i}: no licence number recorded")
    if re.match(r"\s*0[789]0-?\d{4}-?\d{4}\s*$", r["phone"] or ""): warns.append(f"{i}: phone looks like a personal mobile — check privacy policy before publishing")
    if r["military"] and not re.match(r"(yes|reported|likely|unknown|no)\b", r["military"], re.I): warns.append(f"{i}: military column should start with Yes / Reported / Likely / Unknown / No (or be empty)")

ids = {r["id"] for r in rows}
if rows and any(r.get("segment") not in ("", "local", None) for r in rows): errs.append("segment must be blank or 'local'")
try:
    for j, q in enumerate(csv.DictReader(open(ROOT/"data/places.csv", encoding="utf-8-sig")), 2):
        try:
            la, lo = float(q["lat"]), float(q["lon"])
            if not (23.5 < la < 28.6 and 122.5 < lo < 131.5): errs.append(f"places row {j}: outside Okinawa")
        except ValueError: errs.append(f"places row {j}: bad lat/lon")
    for j, q in enumerate(csv.DictReader(open(ROOT/"data/experiences.csv", encoding="utf-8-sig")), 2):
        if q.get("agency_id") not in ids: errs.append(f"experiences row {j}: unknown agency_id")
        if len(q.get("comment", "")) > 400: errs.append(f"experiences row {j}: comment over 400 chars")
        if re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", q.get("comment", "")): errs.append(f"experiences row {j}: comment contains a phone number")
except FileNotFoundError as e: errs.append(f"missing file {e.filename}")
print(f"{len(rows)} rows, {len(errs)} errors, {len(warns)} warnings")
for e in errs: print("ERROR", e)
for w in warns[:40]: print("warn", w)
sys.exit(1 if errs else 0)
