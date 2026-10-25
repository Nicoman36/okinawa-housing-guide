#!/usr/bin/env python3
"""Writes data/work/verification_queue.md — entries past their re-check window (see config.json stale_days),
plus all needs_check / lead rows. Used by the monthly GitHub Action; also run it by hand."""
import csv, datetime, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
today = datetime.date.today()
rows = list(csv.DictReader(open(ROOT/"data/locations.csv", encoding="utf-8-sig")))
due = []
for r in rows:
    if r["status"] == "closed": continue
    lim = cfg["stale_days"][r["verification"]]
    if r["last_verified"]:
        age = (today - datetime.date.fromisoformat(r["last_verified"])).days
        if age > lim: due.append((r, f"last verified {age} days ago (limit {lim})"))
    elif r["verification"] in ("A","B"):
        due.append((r, "never verified"))
    elif r["status"] == "needs_check":
        due.append((r, "flagged needs_check"))
pri = {"D":0,"B":1,"A":2,"C":3}
due.sort(key=lambda x: (x[0]["status"] != "needs_check", pri[x[0]["verification"]], x[0]["name_en"]))
out = [f"# Verification queue — {today}", "", f"{len(due)} of {len(rows)} entries need attention. Work top-down; roster-only (C) rows are last.", ""]
for r, why in due[:150]:
    out.append(f"- [ ] **{r['name_en']}** (`{r['id']}`, {r['municipality'] or 'no area'}, level {r['verification']}) — {why}. Phone: {r['phone'] or '—'} · Web: {r['website'] or '—'}")
if len(due) > 150: out.append(f"\n…and {len(due)-150} more (see data/locations.csv).")
p = ROOT/"data/work/verification_queue.md"; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("\n".join(out), encoding="utf-8")
print(f"{len(due)} due -> {p}")
