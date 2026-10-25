#!/usr/bin/env python3
"""Fill lat/lon in data/locations.csv using the free Geospatial Information Authority of Japan (GSI) address search.
    python3 scripts/geocode.py            # only rows without coordinates
    python3 scripts/geocode.py --redo     # everything
Needs internet (GSI: msearch.gsi.go.jp). ~1 request/second, so under a minute for ~30 rows. Safe to re-run; it resumes.

Rules: a match is accepted only if GSI's matched address starts with the row's prefecture+municipality (guards against wrong-city hits).
geo_precision = 'block' (matched down to the lot number) or 'town' (district only) or 'muni' (municipality centre — not stored, row skipped).
Roster-only (level C) rows are rounded to 3 decimals (~100 m) so private homes aren't pinpointed.
"""
import csv, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo import MUNI
ROOT = Path(__file__).resolve().parent.parent
F = ROOT/"data/locations.csv"
redo = "--redo" in sys.argv
rows = list(csv.DictReader(open(F, encoding="utf-8-sig")))
fields = list(rows[0].keys())
MUNI_REV = {}
for ja, v in MUNI.items(): MUNI_REV[v[0]] = ja

def clean(addr):
    a = unicodedata.normalize("NFKC", addr)
    a = re.sub(r"[（(].*?[）)]", "", a)                      # parentheticals
    a = re.sub(r"〒?\d{3}-?\d{4}", "", a)
    a = re.sub(r"\s+.*$", "", a.strip())                      # drop building / floor text after first space
    a = re.sub(r"(\d+)丁目", r"\1-", a).replace("番地", "").replace("番", "-").replace("号", "")
    a = re.sub(r"-+$", "", a)
    return a

def query(q):
    u = "https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(q)
    req = urllib.request.Request(u, headers={"User-Agent": "okinawa-housing-directory-geocode (volunteer project)"})
    return json.load(urllib.request.urlopen(req, timeout=20))

done = fail = 0
for r in rows:
    if r["lat"] and not redo: continue
    if not r["municipality"] or not r["address_ja"]: continue
    mja = MUNI_REV.get(r["municipality"])
    addr = clean(r["address_ja"])
    addr = re.sub(r"^沖縄県", "", addr)
    if mja and mja not in addr[:12]:
        addr = mja + addr          # venue-only / district-only addresses
    q = "沖縄県" + addr
    try:
        res = query(q)
    except Exception as e:
        print("ERR", r["id"], e); fail += 1; time.sleep(2); continue
    best = None
    for feat in res:
        title = feat.get("properties", {}).get("title", "")
        if mja and ("沖縄県" + mja) not in title and mja not in title: continue
        best = (feat, title); break
    if not best:
        print("no match", r["id"], q); fail += 1; time.sleep(1); continue
    feat, title = best
    lon, lat = feat["geometry"]["coordinates"]
    prec = "block" if re.search(r"\d", title) else "town"
    if r["verification"] == "C":
        lat, lon = round(lat, 3), round(lon, 3)
    else:
        lat, lon = round(lat, 5), round(lon, 5)
    r["lat"], r["lon"], r["geo_precision"] = str(lat), str(lon), prec
    done += 1
    if done % 25 == 0:
        with open(F, "w", newline="", encoding="utf-8-sig") as f: w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
        print("saved", done)
    time.sleep(1)
with open(F, "w", newline="", encoding="utf-8-sig") as f: w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
print(f"geocoded {done}, failed/no match {fail}. Spot-check a few on the map before publishing.")
