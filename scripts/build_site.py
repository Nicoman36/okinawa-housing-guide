#!/usr/bin/env python3
"""Static site generator (stdlib only).  python3 scripts/build_site.py  ->  dist/"""
import csv, html, json, math, os, re, shutil, sys, urllib.parse, datetime
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import SVC, GROUPS, VERIF, STATUS, GROUPS_JA, REGIONS_JA, VERIF_JA, KIND_JA, FOCUS_JA, SVC_JA
from geo import MUNI_SLUGS, REGIONS

ROOT = Path(__file__).resolve().parent.parent
DIST = Path(os.environ.get("DIST_DIR", ROOT / "dist"))
CFG = json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
BASE = os.environ.get("BASE_PATH", CFG["base_path"]).rstrip("/")
TODAY = datetime.date.today().isoformat()
esc = lambda s: html.escape(str(s or ""), quote=True)

# ------------------------------------------------------------------ data
def load():
    rows = list(csv.DictReader(open(ROOT/"data/locations.csv", encoding="utf-8-sig")))
    for r in rows:
        r["svc"] = [s for s in r["services"].split(";") if s]
        r["srcs"] = [s for s in r["sources"].split(";") if s]
        r["is_org"] = r["kind"] != "agency"
        r["local"] = (r.get("segment") or "").strip() == "local"
        _el = r["english"].lower()
        r["eng_level"] = 1 if _el.startswith(("yes", "reported")) else (2 if _el.startswith("likely") else 0)
        _ml = r["military"].lower()
        r["mil_level"] = 1 if _ml.startswith("yes") else (2 if _ml.startswith(("reported", "likely")) else 0)
        _m = re.search(r"(?:Google rating|rated) (\d\.\d) \((\d+)(?: reviews?)?\)", r["notes"])
        r["rating"] = (_m.group(1), _m.group(2)) if _m else None
        if r["municipality"] in MUNI_SLUGS:
            r["m_ja"], r["m_en"], r["region"] = MUNI_SLUGS[r["municipality"]]
        else:
            r["m_ja"], r["m_en"] = "", "Location not listed"
    srcs = {s["id"]: s for s in csv.DictReader(open(ROOT/"data/sources.csv", encoding="utf-8-sig"))}
    return rows, srcs

ROWS, SRC = load()
PLACES = [r for r in ROWS if not r["is_org"] and not r["local"] and r["status"] != "closed"]   # international / SOFA-oriented agencies
LOCAL = [r for r in ROWS if r["local"] and r["status"] != "closed"]               # Japanese-run agencies (own page)
MUNIS = {r["municipality"] for r in ROWS if r["municipality"] and not r["local"] and r["status"] != "closed"}
def _hav(a, b, c, d):
    R, t = 6371.0, math.pi / 180
    dl, dn = (c - a) * t, (d - b) * t
    h = math.sin(dl / 2) ** 2 + math.cos(a * t) * math.cos(c * t) * math.sin(dn / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))
REFS = []
if (ROOT/"data/places.csv").exists():
    for _p in csv.DictReader(open(ROOT/"data/places.csv", encoding="utf-8-sig")):
        _p["lat"], _p["lon"] = float(_p["lat"]), float(_p["lon"]); REFS.append(_p)
def near(r, n=4, kind=None):
    """Nearest reference points (straight-line km). Returns [(km, ref)]."""
    if not r.get("lat") or not r.get("lon"): return []
    la, lo = float(r["lat"]), float(r["lon"])
    out = sorted(((_hav(la, lo, q["lat"], q["lon"]), q) for q in REFS if kind in (None, q["kind"])), key=lambda x: x[0])
    return out[:n]
EXP = {}
if (ROOT/"data/experiences.csv").exists():
    for _e in csv.DictReader(open(ROOT/"data/experiences.csv", encoding="utf-8-sig")):
        if (_e.get("status") or "").strip() == "approved": EXP.setdefault(_e["agency_id"], []).append(_e)
by_svc = defaultdict(list)
for r in ROWS:
    if r["status"] == "closed" or r["local"]: continue
    for d in r["svc"]: by_svc[d].append(r)
def n_places(d):
    """Agencies per service; the 'official' service counts offices and portals instead."""
    return len(by_svc[d]) if d == "official" else sum(1 for r in by_svc[d] if not r["is_org"])

# ------------------------------------------------------------------ helpers
LANG = "en"
def T(en, ja): return ja if LANG == "ja" else en
EN_ONLY = ("/checklist", "/costs", "/housing-office", "/glossary", "/guides")
LOCAL_PREFIXES = ("/shortlist", "/compare", "/share-experience", "/services", "/areas", "/find", "/guide", "/about-data", "/sources", "/suggest-edit", "/for-agencies", "/privacy", "/l/", "/map", "/local-agencies")
def url(p):
    if LANG == "ja" and (p == "/" or (p.startswith(LOCAL_PREFIXES) and not p.startswith(EN_ONLY))): p = "/ja" + (p if p != "/" else "/")
    return f"{BASE}{p}"
def vlabel(k): return (VERIF_JA if LANG == "ja" else VERIF)[k]
def dname(d): return SVC[d]["ja"] if LANG == "ja" else SVC[d]["en"]
def dtext(d, i):  # i: 0 blurb, 1 about, 2 tip
    if LANG == "ja": return SVC_JA[d][i]
    return (SVC[d]["blurb"], SVC[d]["about"], SVC[d]["tip"])[i]
def mname(slug): return MUNI_SLUGS[slug][0] if LANG == "ja" else MUNI_SLUGS[slug][1]
def write(path, content):
    f = DIST / path.lstrip("/"); f.parent.mkdir(parents=True, exist_ok=True); f.write_text(content, encoding="utf-8")

def issue_url(r, kind="report-listing.yml"):
    if not CFG.get("use_github", True): return mail_url(r)
    q = urllib.parse.urlencode({"template": kind, "title": f"[Edit] {r['name_en']}", "listing": r["id"]})
    return f"https://github.com/{CFG['github_repo']}/issues/new?{q}"
def mail_url(r):
    s = urllib.parse.quote(f"Correction: {r['name_en']} ({r['id']})")
    b = urllib.parse.quote(f"Listing: {CFG['base_url']}/l/{r['id']}/\n\nWhat is wrong / what changed:\n\nHow do you know (website, phone call, I work there):\n")
    return f"mailto:{CFG['contact_email']}?subject={s}&body={b}"

ANALYTICS = CFG.get("analytics_snippet", "")

def report_buttons(r):
    if CFG.get("use_github", True):
        return f'<a class="btn" href="{esc(issue_url(r))}" rel="noopener">{T("Report a problem","誤りを報告")}</a> <a class="btn secondary" href="{esc(mail_url(r))}">{T("Email instead","メールで連絡")}</a>'
    return f'<a class="btn" href="{esc(mail_url(r))}">{T("Report a problem","誤りを報告")}</a>'

LOGO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 6v14h14"/><path d="M5 6a14 14 0 0 1 14 14" stroke-width="1.7" stroke-dasharray="2.2 3"/></svg>'
def _ic(d): return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>'
ICONS = {
 "rent-house": _ic('<path d="M3 11.5L12 4l9 7.5M5.5 10v10h13V10M10 20v-5h4v5"/>'),
 "rent-apartment": _ic('<path d="M5 21V4h9v17M14 9h5v12M8 8h3M8 12h3M8 16h3M3 21h18"/>'),
 "short-stay": _ic('<path d="M3 19V6M3 15h18v4M21 15v-3a3 3 0 0 0-3-3h-7v6"/><circle cx="7" cy="11.5" r="1.6"/>'),
 "buy-sell": _ic('<path d="M3 12.5V4h8.5L21 13.5 13.5 21z"/><path d="M7.5 8h.01"/>'),
 "management": _ic('<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>'),
 "relocation": _ic('<path d="M3 7l9-4 9 4v10l-9 4-9-4zM3 7l9 4 9-4M12 11v10"/>'),
 "official": _ic('<path d="M3 10l9-6 9 6M5 10v8M10 10v8M14 10v8M19 10v8M3 20h18"/>'),
}
def header(cur="", alt=None):
    groups = []
    for g in GROUPS:
        items = "".join(f'<a href="{url("/services/"+d["slug"]+"/")}"><span>{esc(dname(d["slug"]))}</span><span class="n">{n_places(d["slug"])}</span></a>'
                        for d in SVC.values() if d["group"] == g)
        groups.append(f"<h3>{esc(T(g, GROUPS_JA[g]))}</h3>{items}")
    def a(href, label, key, cls=""): return f'<a href="{url(href)}"{" class="+cls if cls else ""}{" aria-current=page" if cur==key else ""}>{label}</a>'
    langlink = f'<a href="{BASE}{alt}" hreflang="{"en" if LANG=="ja" else "ja"}" lang="{"en" if LANG=="ja" else "ja"}">{"English" if LANG=="ja" else "日本語"}</a>' if alt else ""
    return f'''<a class="skip" href="#main">{T("Skip to content","本文へスキップ")}</a>
<header class="site"><div class="wrap">
<a class="brand" href="{url("/")}"><span class="mark" aria-hidden="true">{LOGO}</span><span>{esc(T(CFG["site_name"], CFG["site_name_ja"]))}<small lang="{T("ja","en")}">{esc(T(CFG["site_name_ja"], CFG["site_name"]))}</small></span></a>
<nav class="main" aria-label="{T("Main","メイン")}">
<details><summary>{T("Services ▾","サービス ▾")}</summary><div class="menu">{"".join(groups)}<a href="{url("/services/")}" style="grid-column:1/-1;margin-top:6px;font-weight:600">{T("All services","すべてのサービス")}</a></div></details>
<details><summary>{T("Find ▾","探す ▾")}</summary><div class="menu list"><a href="{url("/find/")}"><span>{T("Search all agencies","すべてを検索")}</span></a><a href="{url("/map/")}"><span>{T("Map","地図")}</span></a><a href="{url("/areas/")}"><span>{T("By area","地域別")}</span></a><a href="{url("/local-agencies/")}"><span>{T("Japanese agencies","日本の不動産会社")}</span></a></div></details>
<details><summary>{T("Renting ▾","賃貸の準備 ▾")}</summary><div class="menu list"><a href="{url("/checklist/")}"><span>{T("First-time renter checklist","初めての方のチェックリスト")}</span></a><a href="{url("/costs/")}"><span>{T("Up-front costs","初期費用")}</span></a><a href="{url("/housing-office/")}"><span>{T("Housing office guide","住宅窓口ガイド")}</span></a><a href="{url("/glossary/")}"><span>{T("Listing glossary","物件用語集")}</span></a><a href="{url("/guide/")}"><span>{T("Full renting guide","賃貸ガイド")}</span></a><a href="{url("/guides/")}"><span>{T("All guides (move-in, OHA, rent)","ガイド一覧（入居・OHA・家賃）")}</span></a></div></details>
<a href="{url("/shortlist/")}"{" aria-current=page" if cur=="shortlist" else ""}>{T("Shortlist","候補")} <span class="count" data-short-count></span></a>
{langlink}{a("/find/",T("Search","検索"),"find","nav-cta")}
</nav></div></header>'''

def footer():
    if LANG == "ja":
        return f'''<footer class="site"><div class="wrap"><div class="cols">
<div><h4>{esc(CFG["site_name_ja"])}</h4><p>沖縄で住まいを探す米軍関係者・外国人居住者のための、独立した有志運営のガイドです。掲載の不動産会社・米軍の住宅窓口・行政機関とは関係がなく、公式の案内ではありません。最終ビルド {TODAY}。※営業時間・備考など掲載詳細の一部は原文（英語）のままです。</p></div>
<div><h4>探す</h4><ul><li><a href="{url("/find/")}">すべてを検索</a></li><li><a href="{url("/areas/")}">地域から探す</a></li><li><a href="{url("/map/")}">地図</a></li><li><a href="{url("/guide/")}">賃貸ガイド</a></li><li><a href="{url("/local-agencies/")}">日本の不動産会社</a></li><li><a href="{url("/shortlist/")}">候補リスト</a></li><li><a href="{url("/share-experience/")}">体験を共有</a></li></ul></div>
<div><h4>信頼性・お問い合わせ</h4><ul><li><a href="{url("/about-data/")}">データについて</a></li><li><a href="{url("/sources/")}">情報源と帰属</a></li><li><a href="{url("/suggest-edit/")}">修正・追加の提案</a></li><li><a href="{url("/for-agencies/")}">不動産会社の方へ</a></li><li><a href="{url("/privacy/")}">プライバシーと削除依頼</a></li></ul></div>
</div></div></footer>'''
    return f'''<footer class="site"><div class="wrap"><div class="cols">
<div><h4>{esc(CFG["site_name"])}</h4><p>An independent, community-maintained guide to housing agencies in Okinawa for U.S. Forces members, other foreign residents and newcomers. Not affiliated with any agency, housing office or government body, and not official guidance. Last built {TODAY}.</p></div>
<div><h4>Explore</h4><ul><li><a href="{url("/find/")}">Search all agencies</a></li><li><a href="{url("/areas/")}">Browse by area</a></li><li><a href="{url("/map/")}">Map</a></li><li><a href="{url("/guide/")}">Renting guide</a></li><li><a href="{url("/local-agencies/")}">Japanese agencies</a></li><li><a href="{url("/guides/")}">Guides: move-in, rent, OHA</a></li><li><a href="{url("/checklist/")}">First-time renter checklist</a></li><li><a href="{url("/costs/")}">Up-front costs</a></li><li><a href="{url("/housing-office/")}">Housing office guide</a></li><li><a href="{url("/glossary/")}">Listing glossary</a></li><li><a href="{url("/shortlist/")}">Shortlist &amp; compare</a></li><li><a href="{url("/share-experience/")}">Share your experience</a></li><li><a href="{url("/services/")}">All services</a></li></ul></div>
<div><h4>Trust &amp; help</h4><ul><li><a href="{url("/about-data/")}">About this data</a></li><li><a href="{url("/sources/")}">Sources &amp; attribution</a></li><li><a href="{url("/suggest-edit/")}">Suggest an edit</a></li><li><a href="{url("/for-agencies/")}">For agencies</a></li><li><a href="{url("/privacy/")}">Privacy &amp; removal</a></li></ul></div>
</div></div></footer>'''

def page(path, title, desc, body, cur="", noindex=False, jsonld=None, extra_head="", scripts=""):
    scripts = scripts + f'<script src="{url("/assets/tools.js")}" defer></script>'
    pf = "/ja" if LANG == "ja" else ""
    full_path = pf + path
    canon = f'{CFG["base_url"]}{full_path}'
    en_p = path; ja_p = "/ja" + path
    alt = en_p if LANG == "ja" else ja_p
    hl = f'<link rel="alternate" hreflang="en" href="{CFG["base_url"]}{en_p}"><link rel="alternate" hreflang="ja" href="{CFG["base_url"]}{ja_p}"><link rel="alternate" hreflang="x-default" href="{CFG["base_url"]}{en_p}">'
    if path.startswith(EN_ONLY):
        alt = "/ja/" if LANG == "en" else en_p
        hl = f'<link rel="alternate" hreflang="en" href="{CFG["base_url"]}{en_p}"><link rel="alternate" hreflang="x-default" href="{CFG["base_url"]}{en_p}">'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    full = f'''<!doctype html><html lang="{LANG}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canon)}">{hl}{robots}
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:locale" content="{"ja_JP" if LANG=="ja" else "en_US"}">
<meta name="color-scheme" content="light dark"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f4fe0'/%3E%3Cpath d='M10 9v14h13' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M10 9a14 14 0 0 1 13 14' fill='none' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-dasharray='2 3.5'/%3E%3C/svg%3E">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{url("/assets/fonts/bricolage-grotesque-latin-wght-normal.woff2")}"><link rel="preload" as="font" type="font/woff2" crossorigin href="{url("/assets/fonts/instrument-sans-latin-wght-normal.woff2")}">
<link rel="stylesheet" href="{url("/assets/style.css")}">{extra_head}{ld}{ANALYTICS}</head><body>{header(cur, alt)}<main id="main">{body}</main>{footer()}{scripts}<script src="{url("/assets/app.js")}" defer></script></body></html>'''
    write(full_path.rstrip("/") + "/index.html" if full_path != "/" else "index.html", full)

def badge(v): return f'<span class="badge {v}" title="{esc(vlabel(v)[1])}">{esc(vlabel(v)[0])}</span>'
def focus_txt(r): return FOCUS_JA.get(r["focus"], r["focus"]) if LANG == "ja" else r["focus"]
def kind_txt(r): return KIND_JA.get(r["kind"], r["kind"]) if LANG == "ja" else r["kind"].capitalize()

def primary_name(r):
    if LANG == "ja": return r["name_ja"] or r["name_en"]
    return r["name_en"]
def secondary_name(r):
    if LANG == "ja": return r["name_en"] if r["name_ja"] else ""
    return r["name_ja"]
def loc_text(r):
    if LANG == "ja": return r["address_ja"] or r["address_en"] or r["m_ja"] or "所在地未掲載"
    return r["address_en"] or r["m_en"]

def eng_chips(r):
    out = ""
    if r["eng_level"] == 1: out += f"<span class='chip eng'>{T('English','英語OK')}</span>"
    elif r["eng_level"] == 2: out += f"<span class='chip eng'>{T('English (likely)','英語可の可能性')}</span>"
    if r["mil_level"] == 1: out += f"<span class='chip mil'>{T('Military families','米軍関係者向け')}</span>"
    elif r["mil_level"] == 2: out += f"<span class='chip mil'>{T('Military (likely)','米軍関係者向けの可能性')}</span>"
    if r["rating"]: out += f"<span class='chip' title='{T('Google rating (number of reviews)','Googleの評価（口コミ件数）')}'><i class='ico star'></i>{r['rating'][0]} ({r['rating'][1]})</span>"
    return out

def monogram(r):
    if r["is_org"]: return ICONS["official"]
    if LANG == "ja" and r["name_ja"]:
        n = re.sub(r"^(株式会社|有限会社|（有）|\(有\))", "", r["name_ja"]).strip()
        return esc(n[:1])
    skip = {"the", "co", "ltd", "inc", "kk", "housing", "okinawa", "agency", "corp", "division"}
    words = [w for w in re.findall(r"[A-Za-z0-9]+", r["name_en"]) if w.lower() not in skip] or re.findall(r"[A-Za-z0-9]+", r["name_en"])
    if len(words) >= 2: return esc((words[0][0] + words[1][0]).upper())
    if not words: return "?"
    return esc(words[0][:2].upper())

def card(r):
    svcs = [d for d in r["svc"] if d in SVC]
    chips = "".join(f'<span class="chip">{esc(dname(d))}</span>' for d in svcs[:3]) + (f'<span class="chip">+{len(svcs)-3}</span>' if len(svcs) > 3 else "")
    tel_digits = "".join(c for c in r["phone"] if c.isdigit() or c == "+")
    phone = (f'<a href="tel:{esc(tel_digits)}"><i class="ico tel"></i>{esc(r["phone"])}</a>' if r["phone"] and r["phone"][0].isdigit()
             else (f'<span><i class="ico tel"></i>{esc(r["phone"])}</span>' if r["phone"] else ""))
    web = f'<a href="{esc(r["website"] if r["website"].startswith("http") else "https://"+r["website"])}" rel="noopener nofollow"><i class="ico web"></i>{T("Website","ウェブサイト")}</a>' if r["website"] else ""
    sec = secondary_name(r)
    jl = ' lang="ja"' if LANG == "en" else ""
    sec_html = f'<div class="ja"{jl}>{esc(sec)}</div>' if sec else ""
    org = f"<span class='chip org'>{esc(kind_txt(r))}</span>" if r["is_org"] else (f"<span class='chip jp'>{T('Japanese-run','日本の会社')}</span>" if r["local"] else "")
    hrs = f'<span><i class="ico clock"></i>{esc(r["hours"][:48] + ("…" if len(r["hours"]) > 48 else ""))}</span>' if r["hours"] else ""
    if r.get("open_hours") and r["status"] != "closed": hrs = f'<span class="open-badge" data-oh="{esc(r["open_hours"])}"></span>' + hrs
    nb = near(r, 1, "base")
    dist_html = f'<span><i class="ico dir"></i>{nb[0][0]:.1f} km {T("to","から")} {esc(T(nb[0][1]["name_en"], nb[0][1]["name_ja"]))}</span>' if nb and r["status"] != "closed" and r["kind"] == "agency" else ""
    star = f'<button type="button" class="star-btn" data-id="{r["id"]}" aria-pressed="false" aria-label="{T("Add to shortlist","候補に追加")}" title="{T("Add to shortlist","候補に追加")}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.5-9.2C1.2 8.6 3 5 6.4 5c2 0 3.6 1.1 4.6 2.6h2C14 6.1 15.600 5 17.600 5 21 5 22.800 8.600 21.500 11.800 19.500 16.400 12 21 12 21z"/></svg></button>'
    return f'''<article class="card v-{r["verification"]}"><span class="mono{" org" if r["is_org"] else ""}" aria-hidden="true">{monogram(r)}</span><div class="body">
<div class="top"><h3><a href="{url("/l/"+r["id"]+"/")}">{esc(primary_name(r))}</a></h3>{badge(r["verification"])}{star}</div>{sec_html}
<div class="chips">{org}{eng_chips(r)}{chips}</div>
<div class="meta"><span><i class="ico pin"></i>{esc(loc_text(r))}</span>{dist_html}{hrs}{phone}{web}</div></div></article>'''

def switcher(cur):
    opts = "".join(f'<option value="{url("/services/"+d["slug"]+"/")}"{" selected" if d["slug"]==cur else ""}>{esc(d["en"] if LANG=="en" else d["ja"])}{" — "+esc(d["ja"]) if LANG=="en" else ""} ({n_places(d["slug"])})</option>' for d in SVC.values())
    links = " · ".join(f'<a href="{url("/services/"+d["slug"]+"/")}">{esc(dname(d["slug"]))}</a>' for d in SVC.values())
    return f'''<div class="switcher"><label for="svc-switch"><b>{T("Switch service","サービスを切り替え")}</b></label>
<select id="svc-switch" data-nav aria-label="{T("Switch to another service","別のサービスへ移動")}">{opts}</select>
<noscript><p>{links}</p></noscript></div>'''

def grouped_cards(rs):
    out = []
    rs = sorted(rs, key=lambda r: (r["verification"], r["name_en"].lower()))
    for key, label in REGIONS + [("", "Location not listed")]:
        sub = [r for r in rs if (r.get("region") or "") == key] if key else [r for r in rs if not r.get("region")]
        if not sub: continue
        lab = REGIONS_JA[key] if LANG == "ja" else label
        out.append(f'<h2 class="region">{esc(lab)} <small style="font-weight:400;color:var(--muted)">· {len(sub)}</small></h2>')
        bym = defaultdict(list)
        for r in sub: bym[r["m_ja"] if LANG == "ja" else r["m_en"]].append(r)
        for m in sorted(bym):
            out.append(f'<h3 class="muni-head">{esc(m or T("Location not listed","所在地未掲載"))} <small style="color:var(--muted)">({len(bym[m])})</small></h3><div class="cards">{"".join(card(r) for r in bym[m])}</div>')
    return "".join(out)

def short_ja(n): return n[:-1] if n[-1] in "市町村" and len(n) > 2 else n

def tilemap(counts, link_prefix="/areas/", caption=None):
    caption = caption or T("agencies listed", "件掲載")
    pos = {"kunigami":(7,1),"nakijin":(5,2),"motobu":(5,3),"nago":(6,3),"ginoza":(7,3),"onna":(6,4),"kin":(7,4),
           "yomitan":(5,5),"uruma":(7,5),"kadena":(5,6),"okinawa-city":(6,6),"chatan":(4,7),"kitanakagusuku":(5,7),"nakagusuku":(6,7),
           "ginowan":(4,8),"nishihara":(5,8),"yonabaru":(6,8),"urasoe":(3,9),"naha":(4,9),"haebaru":(5,9),"nanjo":(6,9),
           "tomigusuku":(4,10),"yaese":(5,10),"itoman":(4,11)}
    mx = max([counts.get(s, 0) for s in pos] + [1])
    def lvl(n): return 0 if n == 0 else 1 if n <= mx*0.2 else 2 if n <= mx*0.45 else 3 if n <= mx*0.7 else 4
    def tile(slug, style=""):
        n = counts.get(slug, 0); ja, en, _ = MUNI_SLUGS[slug]
        name = short_ja(ja) if LANG == "ja" else en.split(" (")[0]
        inner = f"<span>{esc(name)}</span><b>{n}</b>"
        cls = f"tile l{lvl(n)}" + (" zero" if n == 0 else "")
        lab = f'aria-label="{esc(name)}: {n} {esc(caption)}"'
        if n: return f'<a class="{cls}" style="{style}" href="{url(link_prefix+slug+"/")}" {lab}>{inner}</a>'
        return f'<div class="{cls}" style="{style}" {lab}>{inner}</div>'
    tiles = "".join(tile(s, f"grid-column:{x};grid-row:{y}") for s, (x, y) in pos.items())
    isl = "".join(tile(s) for s in ("kumejima","miyako","tarama","ishigaki"))
    return f'''<div class="tilemap-wrap"><div class="tilemap" role="group" aria-label="{T("Okinawa main island, municipalities as tiles. North is up.","沖縄本島の市町村をタイルで表示（上が北）")}">{tiles}<span class="north-arrow" aria-hidden="true">↑ {T("North","北")}</span></div>
<div class="islands"><span class="label">{T("Outer islands →","離島 →")}</span>{isl}</div>
<div class="legend"><span>{T("Fewer","少")}</span><i style="background:var(--tile1)"></i><i style="background:var(--tile2)"></i><i style="background:var(--tile3)"></i><i style="background:var(--tile4)"></i><span>{T("More","多")} ({esc(caption)})</span><span>· {T("dashed tile = none listed yet (not “none exist”)","破線のタイル＝未掲載（「存在しない」ではありません）")}</span></div></div>'''

def svc_card(d):
    return f'<a class="svc" href="{url("/services/"+d["slug"]+"/")}"><span class="si">{ICONS[d["slug"]]}</span><span class="name">{esc(d["en"] if LANG=="en" else d["ja"])}</span><span class="cnt">{n_places(d["slug"])}</span><p>{esc(dtext(d["slug"],0))}</p></a>'

FLOORPLAN = '''<svg viewBox="0 0 560 440" role="presentation" focusable="false">
<rect class="fp-room" x="20" y="20" width="310" height="230"/>
<path class="fp-wall fp-draw" pathLength="1" d="M250 420H20V20H540V420H310"/>
<path class="fp-wall fp-draw d2" pathLength="1" d="M330 20V120M330 170V300M330 350V420M330 210H540M20 250H240M290 250H330M130 250V330M130 380V420M130 320H160M200 320H230M230 250V320"/>
<path class="fp-thin fp-draw d3" pathLength="1" d="M70 17H240M70 23H240M380 17H500M380 23H500M543 80V160M537 80V160M543 270V370M537 270V370M70 417H210M70 423H210"/>
<path class="fp-door fp-draw d3" pathLength="1" d="M330 120H380M380 120A50 50 0 0 1 330 170M240 250V200M240 200A50 50 0 0 1 290 250M330 300H380M380 300A50 50 0 0 1 330 350M130 330H180M180 330A50 50 0 0 1 130 380M160 320V280M160 280A40 40 0 0 1 200 320M250 420V360M250 360A60 60 0 0 1 310 420"/>
<path class="fp-thin fp-draw d3" pathLength="1" d="M34 34H176V62H34ZM150 150H240V205H150Z"/>
<text class="fp-label big" x="175" y="118" text-anchor="middle">LDK</text><text class="fp-label" x="175" y="138" text-anchor="middle">12畳</text>
<text class="fp-label big" x="435" y="110" text-anchor="middle">洋室</text><text class="fp-label" x="435" y="130" text-anchor="middle">6畳</text>
<text class="fp-label big" x="435" y="300" text-anchor="middle">和室</text><text class="fp-label" x="435" y="320" text-anchor="middle">6畳</text>
<text class="fp-label" x="75" y="340" text-anchor="middle">浴室</text><text class="fp-label" x="182" y="296" text-anchor="middle">WC</text><text class="fp-label" x="285" y="316" text-anchor="middle">玄関</text>
</svg>'''

PLAN = [("/checklist/","First-time renter checklist","初めてのチェックリスト","Tick off each step, search to move-out.","探す前から退去まで"),
 ("/costs/","Up-front costs","初期費用","Estimate deposit, key money and fees.","敷金・礼金・手数料の目安"),
 ("/housing-office/","Housing office guide","住宅窓口ガイド","Who must live on base, contacts, hours.","基地内居住・連絡先"),
 ("/guides/oha/","OHA guide","OHAガイド","Allowances, forms, May 2026 rates.","手当・書類・2026年5月の改定"),
 ("/guides/move-in/","Move-in day guide","入居日ガイド","Keys, photos, utilities, first week.","鍵・写真・公共料金"),
 ("/guides/rent-prices/","Rent and pricing","家賃と相場","Who sets rents, how to compare.","家賃を決める人と比べ方"),
 ("/guides/avoid-problems/","Avoid common problems","トラブルを避ける","Fees, deposits, mold, lease traps.","費用・敷金・カビ・契約"),
 ("/guides/living-in-okinawa/","Living in Okinawa","沖縄で暮らす","Typhoons, humidity, trash, driving.","台風・湿気・ごみ・運転")]

def build_home():
    muni_counts = Counter(r["municipality"] for r in PLACES if r["municipality"])
    svcs = "".join(svc_card(d) for d in SVC.values() if n_places(d["slug"]))
    area_opts = "".join(f'<option value="{s}">{esc(mname(s))}</option>' for s in sorted(muni_counts, key=lambda s: MUNI_SLUGS[s][1]))
    svc_opts = "".join(f'<option value="{d["slug"]}">{esc(dname(d["slug"]))}</option>' for d in SVC.values() if n_places(d["slug"]))
    vc = Counter(r["verification"] for r in PLACES)
    n = len(PLACES)
    if LANG == "ja":
        hero = f'''<h1>沖縄で、不動産会社を見つけよう。</h1><p class="lede">米軍関係者・外国人居住者・新しく来る方のために、{n}社の不動産会社と公的な住宅窓口を、地域とサービスで検索できます。各掲載に「いつ確認したか」を表示しています。</p>'''
    else:
        hero = f'''<h1>Find a housing agency in Okinawa.</h1><p class="lede">{n} agencies and the official housing offices, searchable by area, service and language. Every listing shows when it was last checked, and which agencies work with military families.</p>'''
    pins = f'''<span class="fp-tag ok p1"><i class="ico check"></i>{T("Checked Oct 2026","2026年10月確認済み")}</span><span class="fp-tag p2"><i class="ico lang"></i>{T("English","英語OK")}</span><span class="fp-tag p3"><i class="ico mil"></i>{T("Military families","米軍関係者向け")}</span>'''
    seg = "".join(f'<i class="m-{k}" style="flex:{vc[k]}" title="{esc(vlabel(k)[0])}: {vc[k]}"></i>' for k in "ABCD" if vc[k])
    key = "".join(f'<li><b class="{k}">{vc[k]}</b><div><strong>{esc(vlabel(k)[0])}</strong><span>{esc(vlabel(k)[1])}</span></div></li>' for k in "ABCD" if vc[k])
    body = f'''<section class="hero"><div class="wrap hero-grid"><div>{hero}
<form id="home-search" class="searchbox" action="{url("/find/")}" role="search"><div><label for="h-q">{T("Name, town or language","会社名・地名・言語")}</label><input id="h-q" name="q" type="search" placeholder="{T("Chatan, duplex…","北谷、デュプレックス…")}" autocomplete="off"></div>
<div><label for="h-svc">{T("Service","サービス")}</label><select id="h-svc" name="svc"><option value="">{T("Any service","すべて")}</option>{svc_opts}</select></div>
<div><label for="h-area">{T("Office area","事務所の地域")}</label><select id="h-area" name="area"><option value="">{T("Anywhere","沖縄全域")}</option>{area_opts}</select></div>
<button type="submit">{T("Search","検索")}</button></form></div>
<div class="hero-art" aria-hidden="true">{FLOORPLAN}{pins}</div></div></section>
<section class="block"><div class="wrap"><div class="sec-head"><div><h2>{T("Plan your move","引っ越しの準備")}</h2><p class="sub">{T("Guides for what comes after you find an agency. Each lists its sources and review date.","会社を見つけたあとの準備ガイドです（英語）。出典と確認日を記載しています。")}</p></div><a class="btn secondary" href="{url("/guides/")}">{T("All guides","ガイド一覧")}</a></div>
<div class="plan-grid">{"".join(f'<a class="plan" href="{url(pth)}"><b>{T(a,b)}</b><span>{T(c,d)}</span></a>' for pth,a,b,c,d in PLAN)}</div></div></section>
<section class="block tint"><div class="wrap"><h2>{T("How sure are we?","どのくらい確かか")}</h2><p class="sub">{T(f"Every listing shows how it was checked. Here is where the {n} agencies stand today.",f"すべての掲載に確認の状況を表示しています。現在の{n}社の内訳です。")} <a href="{url("/about-data/")}">{T("How we check","確認方法")}</a></p>
<div class="meter" role="img" aria-label="{T("Verification breakdown","確認状況の内訳")}">{seg}</div><ul class="ledger-key">{key}</ul></div></section>
<section class="block"><div class="wrap"><div class="sec-head"><div><h2>{T("Browse by service","サービスから探す")}</h2><p class="sub">{T("Use “Switch service” on any page to hop between them.","どのページでも「サービスを切り替え」から移動できます。")}</p></div></div><div class="svc-grid">{svcs}</div></div></section>
<section class="block"><div class="wrap promo"><div><h2>{T("Prefer a Japanese agency?","日本の不動産会社も選べます")}</h2><p>{T(f"Contractors, retirees and long-term residents often look at Japanese-run agencies, which can be cheaper than agencies built around U.S. clients. We list {len(LOCAL)} so far on their own page, with what to expect before you go.",f"請負業者・退職者・長期滞在の方は、米軍関係者向けの会社より費用を抑えられる日本の不動産会社も検討されます。現在{len(LOCAL)}社を専用ページに掲載し、事前に知っておくことも案内しています。")}</p></div><p><a class="btn" href="{url("/local-agencies/")}">{T("See Japanese agencies","日本の不動産会社を見る")}</a></p></div></section>
<section class="block tint"><div class="wrap"><h2>{T("Browse by area","地域から探す")}</h2><p class="sub">{T("Each tile is a municipality with agency offices, placed roughly where it sits on the island. Agencies often show homes island-wide, so check neighbouring tiles too.","各タイルは事務所のある市町村で、おおよその位置に並べています。会社は島全体の物件を扱うことが多いので、隣のタイルも見てください。")} <a href="{url("/map/")}">{T("Open the map","地図を開く")}</a></p>{tilemap(muni_counts)}</div></section>
<section class="block"><div class="wrap two"><div><h2>{T("New to renting here?","初めての賃貸の方へ")}</h2><p>{T("What to do before you sign, the Japanese contract terms you will meet, questions to ask an agency, and how to check a broker's licence.","署名の前にすること、契約書に出てくる日本語の用語、不動産会社に聞くこと、免許の確認方法。")}</p><p><a class="btn" href="{url("/guide/")}">{T("Read the renting guide","賃貸ガイドを読む")}</a> <a class="btn secondary" href="{url("/find/?mil=1")}">{T("Agencies for military families","米軍関係者向けの会社")}</a></p></div>
<div><h2>{T("Know something we don't?","情報をお持ちですか？")}</h2><p>{T("Agencies move, change numbers and close. Every listing has a “Report a problem” button, and agencies can update or remove their own entry.","会社の移転・電話番号の変更・閉業はよくあります。各掲載に「誤りを報告」ボタンがあり、会社ご本人は掲載の更新・削除もできます。")}</p><p><a class="btn secondary" href="{url("/suggest-edit/")}">{T("Suggest an edit","修正・追加を提案")}</a> <a class="btn ghost" href="{url("/sources/")}">{T("Our sources","情報源")}</a></p></div></div></section>'''
    page("/", T(f'{CFG["site_name"]} — rental and housing agencies for U.S. Forces and foreign residents', f'{CFG["site_name_ja"]} — 米軍関係者・外国人向けの住まい探し'),
         T(f'{n} housing and rental agencies in Okinawa, with official housing office contacts, searchable by area, service and language.', f'沖縄の不動産会社{n}社と公的な住宅窓口を、地域・サービス・言語で検索。'), body, cur="home",
         jsonld={"@context":"https://schema.org","@type":"WebSite","name":CFG["site_name"],"url":CFG["base_url"]})

def build_services_index():
    out = []
    for g in GROUPS:
        cards = "".join(svc_card(d) for d in SVC.values() if d["group"] == g)
        out.append(f'<h2 class="region">{esc(T(g, GROUPS_JA[g]))}</h2><div class="svc-grid">{cards}</div>')
    rows = "".join(f'<tr><td><a href="{url("/services/"+d["slug"]+"/")}">{esc(dname(d["slug"]))}</a></td><td lang="ja">{esc(d["ja"])}</td><td>{n_places(d["slug"])}</td></tr>' for d in SVC.values())
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › {T("Services","サービス")}</div><h1>{T("All services","すべてのサービス")}</h1>
<p class="sub">{T("An agency that offers several services is counted under each. The “Official” count is offices and portals, not agencies.","複数のサービスを提供する会社は、それぞれで数えます。「公的な窓口」の件数は、不動産会社ではなく窓口・ポータルの数です。")}</p>{switcher("")}{"".join(out)}
<h2 class="region">{T("Counts at a glance","件数一覧")}</h2><table class="data"><thead><tr><th>{T("Service","サービス")}</th><th>日本語</th><th>{T("Listed","掲載数")}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    page("/services/", T("Housing agency services in Okinawa","沖縄の不動産サービス一覧"), T("Every service we list for Okinawa housing agencies, with counts.","掲載している全サービスと件数。"), body, cur="services")

def build_service(d):
    s = d["slug"]; rs = by_svc[s]
    places = [r for r in rs if not r["is_org"]]; orgs = [r for r in rs if r["is_org"]]
    mc = Counter(r["municipality"] for r in places if r["municipality"])
    chk = Counter(r["verification"] for r in places)
    focus = Counter(focus_txt(r) for r in places if r["focus"])
    top = "".join(f"<tr><td>{esc(k)}</td><td>{v}</td></tr>" for k, v in focus.most_common(10))
    orgs_html = f'<h2 class="region">{T("Offices & portals" if s=="official" else "Related offices & portals","窓口・ポータル" if s=="official" else "関連する窓口・ポータル")}</h2><div class="cards">{"".join(card(r) for r in sorted(orgs, key=lambda r: r["name_en"]))}</div>' if orgs else ""
    nm = dname(s)
    if s == "official":
        sub = T(f'{len(orgs)} offices and portals', f'窓口・ポータル {len(orgs)}件')
    else:
        sub = T(f'{len(places)} agenc{"ies" if len(places)!=1 else "y"} · {len(mc)} municipalit{"ies" if len(mc)!=1 else "y"} with an office · {chk["A"]} checked Oct 2026', f'{len(places)}社 · 事務所のある市町村 {len(mc)} · 2026年10月確認 {chk["A"]}件')
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › <a href="{url("/services/")}">{T("Services","サービス")}</a> › {esc(nm)}</div>
<span class="kanji" lang="ja">{esc(d["ja"])}</span><h1>{esc(T(d["en"]+" in Okinawa", "沖縄の"+d["ja"]))}</h1><p class="sub">{sub}</p>{switcher(s)}
<div class="two"><div class="prose"><p>{esc(dtext(s,1))}</p><div class="callout info"><b>{T("Tip:","ヒント：")}</b> {esc(dtext(s,2))}</div>
<p><a class="btn" href="{url("/find/?svc="+s)}">{T("Search & filter","検索・絞り込み")}</a> <a class="btn secondary" href="{url("/map/?svc="+s)}">{T("See on map","地図で見る")}</a></p></div>
<div>{tilemap(mc, caption=T("agencies","社")) if mc else ""}</div></div>
{('<h2 class="region">'+T("Who they focus on","主な対象")+'</h2><table class="data"><thead><tr><th>'+T("Focus","対象")+'</th><th>'+T("Agencies","件数")+'</th></tr></thead><tbody>'+top+'</tbody></table>') if len(focus)>1 else ""}
{grouped_cards(places)}{orgs_html}</div>'''
    page(f"/services/{s}/", T(f'{d["en"]} in Okinawa — {len(places) if s!="official" else len(orgs)} listed', f'沖縄の{d["ja"]} — {len(places) if s!="official" else len(orgs)}件'), dtext(s,0), body, cur="services")

def build_areas():
    muni_counts = Counter(r["municipality"] for r in PLACES if r["municipality"])
    unk = sum(1 for r in PLACES if not r["municipality"])
    lists = []
    for key, label in REGIONS:
        items = [(s, MUNI_SLUGS[s]) for s in muni_counts if MUNI_SLUGS[s][2] == key]
        if not items: continue
        lis = "".join(f'<tr><td><a href="{url("/areas/"+s+"/")}">{esc(v[0] if LANG=="ja" else v[1])}</a></td><td lang="ja">{esc(v[0])}</td><td>{muni_counts[s]}</td><td><div class="bar" style="width:{max(2,int(muni_counts[s]/max(muni_counts.values())*160))}px"></div></td></tr>' for s, v in sorted(items, key=lambda x: -muni_counts[x[0]]))
        lists.append(f'<h2 class="region">{esc(REGIONS_JA[key] if LANG=="ja" else label)}</h2><table class="data"><thead><tr><th>{T("Municipality","市町村")}</th><th>日本語</th><th>{T("Agencies","件数")}</th><th></th></tr></thead><tbody>{lis}</tbody></table>')
    unk_t = T(f'{unk} listing(s) have no office location we could confirm yet.', f'{unk}件は、事務所の所在地をまだ確認できていません。') if unk else ""
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › {T("Areas","地域")}</div><h1>{T("Browse by area","地域から探す")}</h1>
<p class="sub">{T("Counts are agencies we have listed with an office in that municipality — not every agency that exists, and not where their homes are. Most agencies show homes island-wide, and many offices cluster around the main bases (Chatan, Okinawa City and Kadena).","件数は、その市町村に事務所がある「掲載している会社」の数で、実在する全数でも、物件の所在地でもありません。多くの会社は島全体の物件を紹介し、事務所は主要な基地周辺（北谷・沖縄市・嘉手納）に集まります。")}</p>{tilemap(muni_counts)}
{"".join(lists)}{f'<p class="sub" style="margin-top:20px">{unk_t}</p>' if unk else ""}</div>'''
    page("/areas/", T("Housing agencies in Okinawa by area","沖縄の不動産会社（地域別）"), T("Browse housing agencies by the municipality of their office across Okinawa.","事務所のある市町村ごとに不動産会社を探せます。"), body, cur="areas")

def build_area(slug):
    ja, en, region = MUNI_SLUGS[slug]
    rs = [r for r in ROWS if r["municipality"] == slug and r["status"] != "closed" and not r["local"]]
    places = [r for r in rs if not r["is_org"]]
    dc = Counter(d for r in places for d in r["svc"])
    pills = " ".join(f'<a class="chip" href="{url("/find/?area="+slug+"&svc="+d)}">{esc(dname(d))} · {n}</a>' for d, n in dc.most_common() if d in SVC)
    ordered = sorted(rs, key=lambda r: (r["verification"], r["name_en"].lower()))
    nm = ja if LANG == "ja" else en
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › <a href="{url("/areas/")}">{T("Areas","地域")}</a> › {esc(nm)}</div>
<span class="kanji" lang="ja">{esc(ja)}</span><h1>{esc(T("Housing agencies in "+en, ja+"の不動産会社"))}</h1><p class="sub">{T(f'{len(places)} agenc{"ies" if len(places)!=1 else "y"} with an office here · {len(dc)} service{"s" if len(dc)!=1 else ""}', f'事務所のある会社 {len(places)}社 · {len(dc)}サービス')}</p>
<div class="pill-row" style="margin:10px 0 18px">{pills}</div><div class="cards">{"".join(card(r) for r in ordered)}</div></div>'''
    page(f"/areas/{slug}/", T(f"Housing agencies in {en}, Okinawa — {len(places)} listings", f"{ja}の不動産会社 — {len(places)}件"), T(f"Rental and housing agencies with an office in {en} ({ja}), Okinawa.", f"{ja}に事務所のある不動産会社。"), body, cur="areas")

def row(k, v, raw=False):
    return f"<dt>{esc(k)}</dt><dd>{v if raw else esc(v)}</dd>" if v else ""

def not_stated(txt):
    """'unknown — x' -> 'Not stated — x' (data convention: free text starting with 'unknown' means the source doesn't say)."""
    if txt.lower().startswith("unknown"):
        rest = txt[7:].lstrip(" —-")
        return T("Not stated", "記載なし") + ((" — " + rest) if rest else "") + T(" · ask when you contact them", "（問い合わせ時に確認）")
    return txt

def build_listing(r):
    chips = "".join(f'<a class="chip" href="{url("/services/"+d+"/")}">{esc(dname(d))}</a>' for d in r["svc"] if d in SVC)
    web = r["website"] if r["website"].startswith("http") or not r["website"] else "https://" + r["website"]
    has_ll = bool(r["lat"] and r["lon"])
    gq = f'{r["lat"]},{r["lon"]}' if has_ll else (r["address_ja"] if r["municipality"] and r["address_ja"] else ((r["name_ja"] or r["name_en"]) + " 沖縄"))
    gmaps = ("https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(gq)) if (r["kind"] == "agency" and (has_ll or r["address_ja"] or r["municipality"])) else ""
    tel = f'<a href="tel:{esc("".join(c for c in r["phone"] if c.isdigit() or c=="+"))}">{esc(r["phone"])}</a>' if r["phone"] and r["phone"][0].isdigit() else r["phone"]
    eng = not_stated(r["english"]) if r["english"] else T("Not known — ask when you contact them", "不明（問い合わせ時に確認）")
    facts = "".join([
        row(T("Japanese name","日本語名"), r["name_ja"]) if LANG == "en" else row("名称（英語）", r["name_en"]),
        row(T("Focus","対象"), focus_txt(r)), row(T("Type","種別"), kind_txt(r)),
        row(T("Broker licence","宅建免許番号"), r["license"]) if r["license"] else (row(T("Broker licence","宅建免許番号"), T("Not published on its website — ask, and check it on the MLIT register","公式サイトに記載なし — 確認を依頼し、国交省の検索で照合"), ) if r["kind"] == "agency" else ""),
        row(T("Address (Japanese)","住所"), r["address_ja"]), row(T("Where (English)","所在地（英語）") if LANG=="en" else "所在地", r["address_en"] if LANG=="en" else (r["m_ja"] if not r["address_ja"] else "")),
        row(T("Phone","電話"), tel, raw=True),
        row(T("Website","ウェブサイト"), f'<a href="{esc(web)}" rel="noopener nofollow">{esc(r["website"])}</a>' if web else "", raw=True),
        row("SNS" if LANG=="ja" else "Social", f'<a href="{esc(r["social"])}" rel="noopener nofollow">{esc(r["social"])}</a>' if r["social"].startswith("http") else r["social"], raw=True),
        row(T("Email","メール"), f'<a href="mailto:{esc(r["email"])}">{esc(r["email"])}</a>' if r["email"] else "", raw=True),
        row(T("Office hours","営業時間"), (f'<span class="open-badge" data-oh="{esc(r["open_hours"])}"></span> ' if r.get("open_hours") else "") + esc(r["hours"]), raw=True) if r["hours"] else "", row(T("Contact person","担当者"), r["contact"]), row(T("Viewings & pick-up","内見・送迎"), r["viewings"]),
        row(T("English","英語対応"), eng), row(T("Military / SOFA","米軍関係・SOFA"), r["military"]), row(T("Also known as","別名"), r["aliases"]),
    ])
    srcs = ", ".join(f'<a href="{url("/sources/")}#{esc(s)}">{esc(SRC[s]["title"].split(" — ")[0][:60])}</a>' for s in r["srcs"] if s in SRC)
    verif_txt = ""
    if r["status"] == "needs_check": verif_txt += T('<div class="callout"><b>Needs a check.</b> We could not fully confirm this listing — call or look at the agency\'s own page before relying on it.</div>','<div class="callout"><b>要確認。</b>この掲載は十分に確認できていません。ご利用前に電話か会社の公式ページでご確認ください。</div>')
    if r["verification"] == "D": verif_txt += T('<div class="callout"><b>Heads up:</b> this is a lead — we know the name but could not confirm where it is or whether it operates. If you know, please <a href="'+esc(issue_url(r))+'">tell us</a>.</div>','<div class="callout"><b>ご注意：</b>これは「情報のみ」の掲載で、所在地や営業状況を確認できていません。ご存じでしたら<a href="'+esc(issue_url(r))+'">お知らせください</a>。</div>')
    if r["kind"] == "agency" and r["mil_level"]: verif_txt += T('<div class="callout info"><b>Military claims:</b> statements such as “approved” or “military-friendly” are the agency\'s own. We found no public official list of approved agencies — confirm with your housing office before signing.</div>','<div class="callout info"><b>米軍関係の表記について：</b>「承認済み」「米軍向け」などは会社自身の表記です。公開されている公式の承認会社リストは確認できませんでした。署名の前に所属の住宅窓口へご確認ください。</div>')
    ld = None
    if r["verification"] in ("A", "B") and r["kind"] == "agency":
        ld = {"@context":"https://schema.org","@type":"RealEstateAgent","name":r["name_en"],"alternateName":r["name_ja"] or None,"url":web or None,
              "telephone":r["phone"] or None,"address":{"@type":"PostalAddress","addressCountry":"JP","addressRegion":"Okinawa","addressLocality":r["m_en"],"streetAddress":r["address_ja"] or None}}
        if has_ll: ld["geo"] = {"@type":"GeoCoordinates","latitude":float(r["lat"]),"longitude":float(r["lon"])}
        ld = {k: v for k, v in ld.items() if v}
        ld["address"] = {k: v for k, v in ld["address"].items() if v}
    first = r["svc"][0] if r["svc"] and r["svc"][0] in SVC else None
    sec = secondary_name(r)
    nt = f'<p style="max-width:68ch;margin-top:18px">{esc(r["notes"])}</p>' if r["notes"] else ""
    lvl = lambda n: (T("Yes","あり") if n == 1 else T("Likely","可能性あり") if n == 2 else T("Not stated","記載なし"))
    glance = ""
    if r["kind"] == "agency":
        lv = r["last_verified"] if r["last_verified"] else T("Not yet checked","未確認")
        glance = f'''<div class="glance"><div><small>{T("Last checked","最終確認")}</small><b class="{r["verification"] if r["verification"] in "AD" else ""}">{esc(lv)}</b></div><div><small>{T("English","英語対応")}</small><b>{lvl(r["eng_level"])}</b></div><div><small>{T("Military families","米軍関係者")}</small><b>{lvl(r["mil_level"])}</b></div><div><small>{T("Broker licence","宅建免許")}</small><b>{esc(r["license"]) if r["license"] else T("Not published","記載なし")}</b></div></div>'''
    btns = ""
    if r["phone"] and r["phone"][0].isdigit():
        btns += f'<a class="btn block" href="tel:{esc("".join(c for c in r["phone"] if c.isdigit() or c=="+"))}"><i class="ico tel"></i>{T("Call","電話")} {esc(r["phone"])}</a>'
    if web: btns += f'<a class="btn secondary block" href="{esc(web)}" rel="noopener nofollow"><i class="ico web"></i>{T("Open website","ウェブサイトを開く")}</a>'
    if r["email"]: btns += f'<a class="btn secondary block" href="mailto:{esc(r["email"])}">{T("Email","メール")} {esc(r["email"])}</a>'
    if gmaps: btns += f'<a class="btn secondary block" href="{esc(gmaps)}" rel="noopener nofollow"><i class="ico dir"></i>{T("Directions in Google Maps","Googleマップで道順")}</a>'
    btns += f'<button type="button" class="btn secondary block star-btn-wide" data-id="{r["id"]}" aria-pressed="false">{T("♡ Add to shortlist","♡ 候補に追加")}</button>'
    if r["kind"] == "agency": btns += f'<a class="btn secondary block" href="{url("/share-experience/?agency="+r["id"])}">{T("Share your experience","体験を共有する")}</a>'
    if has_ll: btns += f'<a class="btn ghost block" href="{url("/map/?id="+r["id"])}"><i class="ico map"></i>{T("Show on our map","このサイトの地図で見る")}</a>'
    qb = []
    if r["phone"] and r["phone"][0].isdigit(): qb.append(f'<a class="btn" href="tel:{esc("".join(c for c in r["phone"] if c.isdigit() or c=="+"))}"><i class="ico tel"></i>{T("Call","電話")}</a>')
    if web: qb.append(f'<a class="btn secondary" href="{esc(web)}" rel="noopener nofollow"><i class="ico web"></i>{T("Website","サイト")}</a>')
    if gmaps: qb.append(f'<a class="btn secondary" href="{esc(gmaps)}" rel="noopener nofollow"><i class="ico dir"></i>{T("Directions","道順")}</a>')
    elif r["email"]: qb.append(f'<a class="btn secondary" href="mailto:{esc(r["email"])}">{T("Email","メール")}</a>')
    qb.append(f'<button type="button" class="btn secondary star-btn-wide short" data-id="{r["id"]}" aria-pressed="false">{T("♡ Save","♡ 保存")}</button>')
    quick = f'<div class="quickbar" aria-label="{T("Quick actions","すぐに連絡")}">{"".join(qb)}</div>'
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › {(f'<a href="{url("/local-agencies/")}">{T("Japanese agencies","日本の不動産会社")}</a>' if r["local"] else (f'<a href="{url("/services/"+first+"/")}">{esc(dname(first))}</a>' if first else ""))} › {esc(primary_name(r))}</div>
<div class="lh"><span class="mono lg{" org" if r["is_org"] else ""}" aria-hidden="true">{monogram(r)}</span><div><h1>{esc(primary_name(r))}</h1>{f'<div lang="{T("ja","en")}" style="font-family:var(--jp);color:var(--muted);font-size:1.1rem;margin-bottom:8px">{esc(sec)}</div>' if sec else ""}
<div class="pill-row">{badge(r["verification"])}{"<span class='chip org'>"+esc(kind_txt(r))+"</span>" if r["is_org"] else ""}{eng_chips(r)}{chips}</div></div></div>
<p class="sub" style="margin:12px 0 0">{esc(vlabel(r["verification"])[1])}</p>{verif_txt}{quick}{glance}
<div class="listing-grid"><div><dl class="facts">{facts}</dl>{nt}{nearby_section(r)}{reviews_section(r)}
<p class="sub" style="font-size:.85rem;margin-top:18px">{T("Sources","情報源")}: {srcs or "—"} · {T("Source date","情報の時点")}: {esc(r["source_date"] or "—")} · {T("Last verified","最終確認")}: {esc(r["last_verified"] or T("not yet","未確認"))}{(" · "+esc(r["privacy_note"])) if r["privacy_note"] else ""}</p></div>
<aside class="actions-card" aria-label="{T("Contact and corrections","連絡と訂正")}">{btns}{"<hr>" if btns else ""}<h2>{T("Something wrong or changed?","誤りや変更がありますか？")}</h2><p>{T("Agencies move, change numbers and close. Two minutes of your time keeps this useful for the next person.","会社は移転・番号変更・閉業があります。数分のご協力が、次に探す人の助けになります。")}</p>{report_buttons(r)}
<p>{T("Work here?","この会社の方は")} <a href="{url("/for-agencies/")}">{T("Update or remove your listing","掲載の更新・削除")}</a>.</p>
<p>{T("We don't embed Google Maps or copy map-service data. Pins show the agency's office, not its properties.","Googleマップの埋め込みや地図データの複製は行いません。位置は物件ではなく事務所です。")}</p></aside></div></div>'''
    noindex = (r["verification"] in ("C", "D") and not CFG["index_unverified_pages"])
    page(f'/l/{r["id"]}/', T(f'{r["name_en"]} — {r["m_en"]}, Okinawa', f'{primary_name(r)} — {r["m_ja"] or "沖縄"}'),
         T(f'{r["name_en"]} ({r["focus"] or kind_txt(r)}) in {r["m_en"]}, Okinawa. {VERIF[r["verification"]][0]}.', f'{primary_name(r)}（{focus_txt(r) or kind_txt(r)}）。{r["m_ja"]}。{VERIF_JA[r["verification"]][0]}。'), body, cur="", noindex=noindex, jsonld=ld)

def data_blob():
    ui = T({"places":"listings","place":"listing","none":"No matches. Try removing a filter — some agencies are listed in Japanese only, so a Japanese place name (e.g. 北谷) can help.","more":"Show more","website":"Website ↗","noloc":"Location not listed","km":"km","org":"Office / portal","nocoord":"Distance needs coordinates — only listings with a map position are ranked.","locating":"Finding your location…","denied":"Couldn’t get your location (permission denied or unavailable)."},
           {"places":"件","place":"件","none":"該当なし。絞り込みを外してみてください。日本語表記のみの会社もあるため、地名（例：北谷）で探すと見つかる場合があります。","more":"さらに表示","website":"ウェブサイト ↗","noloc":"所在地未掲載","km":"km","org":"窓口・ポータル","nocoord":"距離順は、地図上の位置が分かる掲載のみが対象です。","locating":"現在地を取得中…","denied":"現在地を取得できませんでした（許可がない、または利用できません）。"})
    ui = dict(ui); ui.update(T({"jp":"Japanese-run","hrs":"Hours","note":"Straight-line distance","eng":"English","engl":"English (likely)","mil":"Military families","mill":"Military (likely)"},{"jp":"日本の会社","eng":"英語OK","engl":"英語可の可能性","mil":"米軍関係者向け","mill":"米軍関係者向けの可能性"}))
    locs = []
    for r in ROWS:
        if r["status"] == "closed": continue
        locs.append({"id": r["id"], "n": primary_name(r), "j": secondary_name(r), "a": loc_text(r), "aj": r["address_ja"], "m": r["municipality"], "m_en": r["m_en"] if LANG=="en" else r["m_ja"],
                     "d": r["svc"], "k": r["kind"], "v": r["verification"], "p": r["phone"], "w": (r["website"] if r["website"].startswith("http") or not r["website"] else "https://"+r["website"]),
                     "c": r["contact"], "s": focus_txt(r), "al": r["aliases"], "e": r["eng_level"], "mi": r["mil_level"], "r": list(r["rating"]) if r["rating"] else None,
                     "g": 1 if r["local"] else 0, "h": r["hours"], "em": r["email"], "lic": r["license"], "et": r["english"], "mt": r["military"], "ae": r["address_en"], "rv": len(EXP.get(r["id"], [])), "oh": r.get("open_hours", ""), "la": float(r["lat"]) if r["lat"] else None, "lo": float(r["lon"]) if r["lon"] else None, "ne": r["name_en"] if LANG=="ja" else r["name_ja"]})
    return {"base": BASE, "pfx": "/ja" if LANG == "ja" else "", "disc": {k: dname(k) for k in SVC}, "verif": {k: list(vlabel(k)) for k in "ABCD"}, "ui": ui, "locations": locs, "refs": [{"id": q["id"], "n": (q["name_ja"] if LANG == "ja" else q["name_en"]), "la": q["lat"], "lo": q["lon"], "k": q["kind"]} for q in REFS]}

def build_find():
    svc_opts = "".join(f'<option value="{d["slug"]}">{esc(dname(d["slug"]))} ({n_places(d["slug"])})</option>' for d in SVC.values() if by_svc[d["slug"]])
    mc = Counter(r["municipality"] for r in ROWS if r["municipality"] and r["status"] != "closed")
    area_opts = "".join(f'<option value="{s}">{esc(mname(s))} ({mc[s]})</option>' for s in sorted(mc, key=lambda s: MUNI_SLUGS[s][1]))
    ver_opts = "".join(f'<option value="{k}">{esc(vlabel(k)[0])}</option>' for k in "ABCD") + f'<option value="AB">{T("Checked or listed (A + B)","確認済み＋掲載あり（A・B）")}</option>'
    ref_opts = "".join(f'<option value="{q["id"]}">{esc(q["name_ja"] if LANG=="ja" else q["name_en"])}</option>' for q in REFS)
    fn = "data_ja.js" if LANG == "ja" else "data.js"
    write("assets/" + fn, "window.DIR=" + json.dumps(data_blob(), ensure_ascii=False, separators=(",", ":")) + ";")
    body = f'''<div class="wrap pagehead" id="find-app"><h1>{T("Search all agencies","すべての会社を検索")}</h1><p class="sub">{T("Filter by service, area, language, military focus and how recently we checked. Japanese or English words both work.","サービス・地域・英語対応・米軍関係・確認の新しさで絞り込めます。日本語でも英語でも検索できます。")}</p>
<div class="find-grid"><form class="filters" onsubmit="return false" role="search"><div class="wide"><label for="f-q">{T("Search","検索")}</label><input id="f-q" type="search" placeholder="{T("Name, town, phone, service…","会社名・地名・電話・サービス…")}" autocomplete="off"></div>
<div><label for="f-svc">{T("Service","サービス")}</label><select id="f-svc"><option value="">{T("Any service","すべて")}</option>{svc_opts}</select></div>
<div><label for="f-area">{T("Area (office)","地域（事務所）")}</label><select id="f-area"><option value="">{T("Anywhere","すべて")}</option>{area_opts}</select></div>
<div><label for="f-ver">{T("Verification","確認状況")}</label><select id="f-ver"><option value="">{T("Any","すべて")}</option>{ver_opts}</select></div>
<div><label for="f-ref">{T("Near (base or landmark)","基地・目印の近く")}</label><select id="f-ref"><option value="">{T("Any","指定なし")}</option>{ref_opts}</select></div>
<div><label for="f-rad">{T("Within","範囲")}</label><select id="f-rad"><option value="">{T("Any distance","指定なし")}</option><option value="2">2 km</option><option value="5">5 km</option><option value="10">10 km</option><option value="20">20 km</option></select></div>
<div class="toggles wide"><label><input type="checkbox" id="f-eng"> {T("English-friendly","英語対応")}</label><label><input type="checkbox" id="f-mil"> {T("Works with military families","米軍関係者向け")}</label><label><input type="checkbox" id="f-org"> {T("Include offices & portals","窓口・ポータルを含む")}</label><label><input type="checkbox" id="f-loc"> {T("Include Japanese-run agencies","日本の不動産会社を含む")}</label></div>
<div class="actions wide"><button type="button" id="f-near" class="btn secondary"><i class="ico pin"></i>{T("Nearest to me","現在地から近い順")}</button><button type="button" id="f-reset" class="btn ghost">{T("Reset","リセット")}</button></div></form>
<div class="results"><div class="results-bar"><b id="f-count" aria-live="polite"></b><span id="f-msg" class="sub" style="margin:0"></span></div><div id="f-out" class="cards"><noscript><p>{T("Search needs JavaScript. You can still browse by service or by area.","検索にはJavaScriptが必要です。サービス別・地域別のページからも探せます。")}</p></noscript></div>
<p style="text-align:center"><button type="button" id="f-more" class="btn secondary" hidden>{T("Show more","さらに表示")}</button></p></div></div></div>'''
    page("/find/", T("Search housing agencies in Okinawa","沖縄の不動産会社を検索"), T("Search rental and housing agencies in Okinawa by name, service, area, language and military focus.","会社名・サービス・地域・言語・米軍関係で、沖縄の不動産会社を検索。"), body, cur="find", scripts=f'<script src="{url("/assets/"+fn)}"></script>')

def build_map():
    n = sum(1 for r in ROWS if r["lat"] and r["lon"] and r["status"] != "closed")
    fn = "data_ja.js" if LANG == "ja" else "data.js"
    svc_opts = "".join(f'<option value="{d["slug"]}">{esc(dname(d["slug"]))}</option>' for d in SVC.values() if n_places(d["slug"]) and d["slug"] != "official")
    empty = "" if n else f'<div class="callout"><b>{T("Map positions are being added.","地図上の位置は順次追加中です。")}</b> {T("Until then, use search or browse by area.","それまでは検索や地域別ページをご利用ください。")}</div>'
    body = f'''<div class="wrap pagehead"><h1>{T("Map","地図")}</h1><p class="sub">{T(f"{n} listings with a map position. Pins show each agency's office, not its properties. Offices on military installations are not pinned.",f"地図上の位置がある掲載：{n}件。位置は各社の事務所で、物件ではありません。基地内の窓口は表示していません。")}</p>{empty}
<div class="switcher"><label for="m-svc"><b>{T("Service","サービス")}</b></label><select id="m-svc"><option value="">{T("All services","すべて")}</option>{svc_opts}</select>
<button type="button" id="m-near" class="btn secondary">{T("📍 Near me","📍 現在地")}</button><span id="m-count" class="sub" style="margin:0"></span></div>
<div id="map" role="region" aria-label="{T("Map of listings","掲載地図")}" style="height:min(70vh,640px);border-radius:12px;border:1px solid var(--line)"></div>
<p class="sub" style="font-size:.8rem">{T("Map © OpenStreetMap contributors.","地図 © OpenStreetMap contributors")}</p></div>'''
    leaf_css = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">'
    scripts = f'<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script><script src="{url("/assets/"+fn)}"></script><script src="{url("/assets/map.js")}"></script>'
    page("/map/", T("Map of housing agencies in Okinawa","沖縄の不動産会社 地図"), T("See housing agency offices on a map of Okinawa and find the nearest to you.","沖縄の不動産会社の事務所を地図で確認し、近くの会社を探せます。"), body, cur="map", extra_head=leaf_css, scripts=scripts)

# ---------------------------------------------------------------- long-form pages (EN + JA)
def guide_wrap(body, toc):
    """Turn the long-form guide into [sticky step list | article]. toc = [(id, label, numbered)]."""
    for hid, label, _ in toc:
        pat = re.compile(r"<h2>(?:\d\. )?" + re.escape(label) + r"</h2>")
        m = pat.search(body)
        assert m, "guide heading missing: " + label
        body = body[:m.start()] + m.group(0).replace("<h2>", f'<h2 id="{hid}">') + body[m.end():]
    lis = "".join(f'<li class="{"n" if num else ""}"><a href="#{hid}">{label}</a></li>' for hid, label, num in toc)
    body = body.replace('<div class="wrap pagehead prose">', '<div class="wrap pagehead">', 1)
    i = body.index("</p>", body.index('<p class="sub">')) + 4
    head, rest = body[:i], body[i:]
    assert rest.endswith("</div>")
    return head + f'<div class="guide-grid"><nav class="toc" aria-label="{T("On this page","このページの内容")}"><ol>{lis}</ol></nav><div class="prose">' + rest[:-6] + '</div></div></div>'

GUIDE_TOC_EN = [("s1", "Start with your housing office", True), ("s2", "Know the market (as of October 2026)", True), ("s3", "Budget for up-front costs", True), ("terms", "Contract terms you will meet", False), ("s4", "Questions to ask an agency", True), ("s5", "Check the agency", True), ("phrases", "Useful phrases", False)]
GUIDE_TOC_JA = [("s1", "まず住宅窓口へ", True), ("s2", "市場の状況（2026年10月時点）", True), ("s3", "初期費用に備える", True), ("terms", "契約書に出てくる用語", False), ("s4", "不動産会社に聞くこと", True), ("s5", "会社を確認する", True), ("phrases", "使える表現", False)]

def build_guide():
    off1, off2, hm = url("/l/okinawa-family-housing-office/"), url("/l/mcipac-camp-foster-housing/"), url("/l/homes-mil/")
    stripes = f'{url("/sources/")}#stripes-2026-09'; stripes2 = f'{url("/sources/")}#stripes-2026-05'; mlit = f'{url("/sources/")}#mlit-takken'
    if LANG == "ja":
        terms = [("敷金","しききん","保証金（退去時に原状回復費用などを引いて返金されるのが一般的）"),("礼金","れいきん","大家さんへの謝礼で返金されない。かからない物件もある"),("仲介手数料","ちゅうかいてすうりょう","不動産会社に払う手数料"),("管理費・共益費","かんりひ・きょうえきひ","毎月の共用部分の管理費"),("更新料","こうしんりょう","契約更新時にかかる費用"),("保証会社","ほしょうがいしゃ","連帯保証人の代わりになる保証会社"),("原状回復","げんじょうかいふく","退去時に元の状態に戻すこと・その費用"),("特約","とくやく","契約書に追加される特別な取り決め"),("解約","かいやく","契約を途中で終えること"),("重要事項説明","じゅうようじこうせつめい","契約前に宅建士が行う、物件・条件の説明")]
        tr = "".join(f'<tr><td lang="ja"><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>' for a, b, c in terms)
        ph = [("賃貸の家を探しています。","賃貸を探していると伝える"),("敷金・礼金はありますか？","初期費用を尋ねる"),("契約時に、いくら必要ですか？内訳を教えてください。","署名時の費用の内訳を尋ねる"),("転勤命令で、途中解約できますか？","異動時の途中解約を尋ねる"),("ペットは飼えますか？","ペット可否を尋ねる"),("エアコンや冷蔵庫は付いていますか？","設備を尋ねる"),("内見をお願いします。","内見を頼む"),("英語の契約書はありますか？","英文契約書の有無を尋ねる")]
        phr = "".join(f'<div class="phrase"><div class="j" lang="ja">{a}</div><div class="e">{b}</div></div>' for a, b in ph)
        body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">ホーム</a> › 賃貸ガイド</div><h1>沖縄で家を借りる：初めての方へ</h1>
<p class="sub">米軍関係者・軍属・外国人居住者・新しく来る方のための一般的な案内です。法律上の助言や公式の案内ではありません。何が適用されるかは、所属の住宅窓口が判断します。</p>
<h2>1. まず住宅窓口へ</h2><p>嘉手納の住宅窓口のページによると、同伴者のいる現役隊員は到着後72時間以内に軍住宅事務所へ報告する必要があり、民間住宅を借りる・買う契約をする前に住宅紹介窓口（Housing Referral Office）に確認するとされています。規則は所属・身分・命令により異なります。沖縄の米軍関係者は全軍共通で、<a href="{off1}">嘉手納の沖縄ファミリーハウジング</a>が窓口です（キャンプ・フォスター、キンザー、コートニーに出張窓口があります）。物件検索は<a href="{hm}">Homes.mil</a>。</p>
<h2>2. 市場の状況（2026年10月時点）</h2><p>スターズ・アンド・ストライプスは、2026年8月の米軍向け賃貸約8,400件のうち空室は317件（空室率4%未満）と報じ、順番待ちの会社もあるとしています（<a href="{stripes}">記事</a>）。複数の会社に同時に連絡し、待機リストへの登録や条件の緩和（通勤時間など）を検討しましょう。沖縄の海外住宅手当（OHA）は2026年5月16日から引き上げられました（<a href="{stripes2}">記事</a>）。家賃は不動産会社とオーナーが決め、住宅窓口は賃料の承認ではなく契約内容の確認を行うとされています。現在の手当額は所属の経理窓口で確認してください。</p>
<h2>3. 初期費用に備える</h2><p>Military OneSourceは、不動産会社の手数料が家賃の半月分程度、さらに敷金と初月・最終月の家賃を契約時に支払うことが多いと説明しています。水道・下水・ごみの費用は別になる場合があります。立替の後に精算される費用や、給与の前払いを使う隊員もいます。</p>
<h2>契約書に出てくる用語</h2><div style="overflow-x:auto"><table class="data"><thead><tr><th>用語</th><th>読み</th><th>意味</th></tr></thead><tbody>{tr}</tbody></table></div>
<h2>4. 不動産会社に聞くこと</h2><ul><li>契約時の費用の内訳（家賃・敷金・礼金・仲介手数料・管理費・保険）。</li><li>物件が住宅窓口に登録・検査済みか。</li><li>転勤・異動命令での途中解約条項があるか（書面で）。契約書は住宅窓口に確認してもらいましょう。</li><li>設備（エアコン・家電・照明が付くか）、駐車台数。</li><li>ペット可否と敷金。</li><li>修理の連絡先、夜間・台風後の対応。カビ対策。</li><li>退去時の清掃・原状回復の範囲。</li><li>契約書・重要事項説明を英語で受けられるか。</li></ul>
<h2>5. 会社を確認する</h2><p>日本で賃貸・売買を仲介するには宅地建物取引業の免許が必要です。番号は「沖縄県知事（2）第5027号」のように表示されます。<a href="{mlit}">国土交通省の宅建業者検索</a>で照合できます。このサイトは、会社が公開している場合に免許番号を表示しますが、まだ多くの会社で未記載です。「承認済み」という表記は会社自身のもので、公開された公式リストは確認できていません。</p>
<h2>使える表現</h2><div>{phr}</div>
<div class="callout info">掲載されていない会社をご存じですか？<a href="{url("/suggest-edit/")}">教えてください</a>。</div></div>'''
        body = guide_wrap(body, GUIDE_TOC_JA)
        page("/guide/", "沖縄で家を借りる — 賃貸ガイド", "住宅窓口、初期費用、契約用語、不動産会社に聞くこと、免許の確認方法。", body, cur="guide"); return
    terms = [("敷金","shikikin","Security deposit; normally refundable after restoration costs are deducted."),("礼金","reikin","“Key money”: a non-refundable payment to the landlord. Not charged on every home."),("仲介手数料","chūkai tesūryō","Brokerage fee paid to the agency."),("管理費・共益費","kanrihi / kyōekihi","Monthly fee for management or shared areas."),("更新料","kōshinryō","Renewal fee when the lease is extended."),("保証会社","hoshō gaisha","Guarantor company, used instead of a personal guarantor."),("原状回復","genjō kaifuku","Restoring the home to its original state at move-out — and the cost of doing so."),("特約","tokuyaku","Special clause or addendum added to the contract."),("解約","kaiyaku","Cancelling the lease early."),("重要事項説明","jūyō jikō setsumei","The explanation of key terms a licensed broker must give before you sign.")]
    tr = "".join(f'<tr><td lang="ja"><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>' for a, b, c in terms)
    ph = [("賃貸の家を探しています。","Chintai no ie o sagashite imasu.","I'm looking for a rental home."),
          ("敷金・礼金はありますか？","Shikikin, reikin wa arimasu ka?","Is there a deposit or key money?"),
          ("契約時にいくら必要ですか？内訳を教えてください。","Keiyaku-ji ni ikura hitsuyō desu ka? Uchiwake o oshiete kudasai.","How much is due at signing? Please break it down."),
          ("転勤命令で、途中解約できますか？","Tenkin meirei de, tochū kaiyaku dekimasu ka?","Can I end the lease early if I get transfer orders?"),
          ("ペットは飼えますか？","Petto wa kaemasu ka?","Are pets allowed?"),
          ("エアコンや冷蔵庫は付いていますか？","Eakon ya reizōko wa tsuite imasu ka?","Do air-conditioners or a fridge come with it?"),
          ("内見をお願いします。","Naiken o onegai shimasu.","I'd like to view the home."),
          ("英語の契約書はありますか？","Eigo no keiyakusho wa arimasu ka?","Is there an English contract?")]
    phr = "".join(f'<div class="phrase"><div class="j" lang="ja">{a}</div><div class="r">{b}</div><div class="e">{c}</div></div>' for a, b, c in ph)
    body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">Home</a> › Renting guide</div><h1>Renting in Okinawa: a guide for newcomers</h1>
<p class="sub">For U.S. Forces members, DoD civilians, contractors and other foreign residents. General information only — not legal advice and not official guidance. Your housing office decides what applies to you.</p>
<h2>1. Start with your housing office</h2><p>Kadena’s housing page says accompanied active-duty personnel must report to the Military Housing Office no later than 72 hours after arrival, and DoD pages say personnel must check with the Housing Referral Office before committing to rent, lease or buy off base. Rules depend on your service, status and orders. Every SOFA member on Okinawa uses one office: the <a href="{off1}">Okinawa Family Housing Office at Kadena</a>, which has satellite counters at Camp Foster, Kinser and Courtney. Search inventory on <a href="{hm}">Homes.mil</a>.</p>
<h2>2. Know the market (as of October 2026)</h2><p>Stars and Stripes reported that only 317 of about 8,400 rentals available to U.S. military families were vacant in August 2026 (under 4%), with some agencies holding waiting lists (<a href="{stripes}">article</a>). Contact several agencies at once, ask to join waiting lists, and consider loosening requirements such as commute time. The Overseas Housing Allowance on Okinawa rose from 16 May 2026 (<a href="{stripes2}">article</a>); rents are set by agencies and owners, and the housing office reviews leases for consistency rather than approving rent. Confirm current allowance rates with your pay office.</p>
<h2>3. Budget for up-front costs</h2><p>Military OneSource says agencies commonly charge about half a month's rent, plus a security deposit and first and last month's rent at signing. Water, sewage and trash fees may be separate. Some members pay up front and are reimbursed later, or take a pay advance.</p>
<h2>Contract terms you will meet</h2><div style="overflow-x:auto"><table class="data"><thead><tr><th>Japanese</th><th>Reading</th><th>Meaning</th></tr></thead><tbody>{tr}</tbody></table></div>
<h2>4. Questions to ask an agency</h2><ul><li>An itemised list of what is due at signing (rent, deposit, key money, brokerage fee, management fee, insurance).</li><li>Is the home already inspected and registered with the housing office?</li><li>Does the lease let you end it early on transfer or reassignment orders? Get it in writing, and have your housing office review the lease.</li><li>What is included — air-conditioners, appliances, lights — and how many parking spaces?</li><li>Pets: allowed, and what deposit?</li><li>Who handles repairs, and how do you reach them after hours or after a typhoon? What about mould in the humid months?</li><li>What move-out cleaning or restoration charges apply?</li><li>Can you get the contract and the explanation of key terms (重要事項説明) in English?</li></ul>
<h2>5. Check the agency</h2><p>Real estate brokers in Japan must be licensed. A licence number looks like “Okinawa Prefectural Governor (2) No. 5027”, and you can look it up in the <a href="{mlit}">MLIT licensed-broker search</a>. This directory shows a licence number when the agency publishes one — most do not yet. “Approved” and “military-friendly” are the agency's own words: we found no public official list of approved agencies, so ask your housing office.</p>
<h2>Useful phrases</h2><div>{phr}</div><p class="sub">Romanization is simplified. A native speaker or a translation app can help you check a message before you send it.</p>
<div class="callout info">Know an agency that isn't listed? <a href="{url("/suggest-edit/")}">Tell us</a>.</div></div>'''
    body = guide_wrap(body, GUIDE_TOC_EN)
    page("/guide/", "Renting in Okinawa — a guide for newcomers and U.S. Forces members", "Housing office first, up-front costs, Japanese contract terms, questions to ask an agency and how to check a broker's licence.", body, cur="guide")

def build_about():
    vc = Counter(r["verification"] for r in ROWS if not r["is_org"]); tot = sum(vc.values())
    rowsv = "".join(f'<tr><td>{badge(k)}</td><td>{esc(vlabel(k)[1])}</td><td>{vc[k]}</td></tr>' for k in "ABCD")
    pstat = Counter(r["status"] for r in ROWS)
    nmap = sum(1 for r in ROWS if r["lat"])
    nlic = sum(1 for r in ROWS if r["license"])
    if LANG == "ja":
        body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">ホーム</a> › データについて</div><h1>データについて</h1>
<p class="sub">何が載っているか、どう集めたか、どれくらい確かか、どう最新に保つか。</p>
<div class="callout"><b>最初にお読みください。</b>これは最善を尽くした案内であり、公式の登録簿でも、掲載会社の推奨でもありません。{tot}社のうち{vc["A"]}社は2026年10月に公式ページで確認しましたが、{vc["B"]+vc["C"]+vc["D"]}社は未確認・情報のみです。契約の前に、必ず会社と所属の住宅窓口にご確認ください。</div>
<h2>確認ラベル</h2><table class="data"><thead><tr><th>ラベル</th><th>意味</th><th>件数</th></tr></thead><tbody>{rowsv}</tbody></table>
<h2>私たちが行っていること</h2><ol class="steps"><li><b>収集。</b>公式の住宅窓口と各社の公式サイトから始め、ディレクトリ（手がかりとしてのみ）、報道、利用者からの情報で追加します。</li>
<li><b>確認。</b>会社の最新の公式ページと照合し、可能なら電話等で確認し、日付を記録します。</li>
<li><b>表示。</b>すべての掲載に確認レベルと最終確認日を表示します。未確認の情報を黙って格上げすることはありません。</li>
<li><b>定期的な再確認。</b>毎月、再確認期限（確認済み6か月、その他12か月、情報のみ3か月）を過ぎた掲載とリンク切れの一覧を自動作成します。</li>
<li><b>迅速な修正。</b>利用者・会社からの報告は公開の一覧に入ります。閉業した会社は「閉鎖」として1年間保持します。</li></ol>
<h2>会社の自己申告について</h2><p>「承認済み」「米軍向け」などの表記は、会社自身の申告として表示し、その旨を明記しています。公開されている公式の承認会社リストは確認できていません。宅建免許番号は{nlic}社分のみ記録しており、その他は公式サイトに記載がありません。</p>
<h2>件数の意味</h2><p>件数は「掲載している数」で、全数調査ではありません。地域別の件数は事務所の所在地であり、物件の所在地ではありません。複数のサービスを提供する会社は、サービスごとに数えるため、サービス別の合計は会社の総数より多くなります。</p>
<h2>名称・翻訳・住所</h2><ul><li>日本語は公表されているとおりに表示します。一部の日本語住所は、公式サイトの英語住所から書き起こしたもので、その旨を各掲載の備考に記しています。</li><li>地図の座標（{nmap}件）は公的な住所検索（国土地理院）で付与します。Googleマップは埋め込まず、リンクのみです。</li><li>個人の携帯電話番号は掲載しません。基地内の窓口は地図に表示しません。</li></ul>
<h2>既知の不足</h2><ul><li>多くの会社で免許番号・営業時間・対応言語が未記載です。</li><li>一部の会社の電話番号は、公式サイトに記載がないためディレクトリに基づきます。</li><li>自動アクセスを禁じるサイトは取得していません。</li><li>日本語ページは、公開前にネイティブによる確認が必要です。</li><li>掲載の「ディレクトリ」であるTotal Okinawaは、掲載会社の一部のサイトと関係があるため、独立した情報源ではありません。</li></ul>
<h2>データの再利用</h2><p>全データは<a href="{url("/data/locations.csv")}">locations.csv</a>で公開しています（{esc(CFG["data_license"])}）。出典としてこのサイトを明記し、「最終確認」列を保持してください。</p>
<h2>運営について</h2><p>有志による独立した運営で、掲載は無料、有料の掲載順位はありません。<a href="{url("/suggest-edit/")}">修正の提案</a>・<a href="{url("/for-agencies/")}">不動産会社の方へ</a>をご覧ください。</p></div>'''
        page("/about-data/", "データについて — 方法と確認", "沖縄の不動産会社ディレクトリの作成・確認・更新の方法。", body, cur="about"); return
    body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">Home</a> › About this data</div><h1>About this data</h1>
<p class="sub">What is here, how it was gathered, how confident we are, and how it stays current.</p>
<div class="callout"><b>Read this first.</b> This is a best-effort directory, not an official register and not an endorsement of any agency. {vc["A"]} of {tot} agencies were checked against their own current page in October 2026; {vc["B"]+vc["C"]+vc["D"]} are listed from directories or news reports and not yet confirmed. Always confirm with the agency, and with your housing office, before you sign anything.</div>
<h2>How we rate every listing</h2><table class="data"><thead><tr><th>Label</th><th>Meaning</th><th>Agencies now</th></tr></thead><tbody>{rowsv}</tbody></table>
<h2>What we do</h2><ol class="steps"><li><b>Collect.</b> Start from official housing-office pages and agencies' own websites, then add others found through directories (as leads only), news reports and community reports.</li>
<li><b>Verify.</b> Compare each listing with the agency's own current page. Where possible, confirm with a call or message. Record the date.</li>
<li><b>Label.</b> Every listing shows its verification level and last-checked date. Unconfirmed items are labelled, never silently promoted.</li>
<li><b>Re-check on a schedule.</b> A monthly automated report lists entries older than their re-check window (checked: 6 months; others: 12 months; leads: 3 months) and dead website links.</li>
<li><b>Fix quickly.</b> Reports from visitors and agencies go into a public queue. Closed agencies are marked closed and kept for a year so people searching old names find the answer.</li></ol>
<h2>Claims agencies make about themselves</h2><p>Words like “approved” or “military-friendly” are shown as the agency's own claim and labelled that way. We found no public official list of approved agencies. A broker licence number is recorded for {nlic} agenc{"y" if nlic==1 else "ies"} so far — the rest do not publish one on their websites.</p>
<h2>Counts and what they mean</h2><p>Counts are numbers of <em>listed</em> agencies, not a census. Area counts show where an agency has its office, not where its homes are — most agencies show homes island-wide. An agency that offers several services is counted under each, so service totals add up to more than the number of agencies.</p>
<h2>Names, translations, addresses and map positions</h2><ul><li>Japanese is shown as published. Where a Japanese address was transcribed from the English address on an agency's site, the listing's note says so.</li><li>Map positions ({nmap} listings so far) come from the Japanese government's public address-search service (GSI). We link out to Google Maps rather than embedding it.</li><li>We do not publish personal mobile numbers, and offices on military installations are not pinned on the map.</li></ul>
<h2>Known gaps</h2><ul><li>Most agencies do not publish a licence number, office hours or the languages their staff speak.</li><li>Some phone numbers come from a directory because the agency's own site shows none.</li><li>Sites that forbid automated access were not read; those agencies are listed from other sources and labelled.</li><li>The Japanese pages need a native-speaker review before launch.</li><li>Total Okinawa, the directory we used to discover agencies, is commercial and several listed agencies' sites credit it in their footers, so it is not an independent source.</li></ul>
<h2>Data you can reuse</h2><p>The full list is in <a href="{url("/data/locations.csv")}">locations.csv</a> ({esc(CFG["data_license"])}). Please credit this site and keep the “last verified” column.</p>
<h2>Who maintains this</h2><p>This is an independent volunteer project. Listing is free and there is no paid placement. See <a href="{url("/suggest-edit/")}">Suggest an edit</a> or <a href="{url("/for-agencies/")}">For agencies</a>. Status of all rows: {", ".join(f"{STATUS.get(k,k)} {v}" for k, v in pstat.most_common())}.</p></div>'''
    page("/about-data/", "About this data — methodology and verification", "How the Okinawa housing agency directory is compiled, verified and kept up to date.", body, cur="about")

def build_sources():
    rows = []
    for s in SRC.values():
        link = f'<a href="{esc(s["url"])}" rel="noopener nofollow">{esc(s["url"])}</a>' if s["url"] else "—"
        rows.append(f'<tr id="{esc(s["id"])}"><td><b>{esc(s["title"])}</b><br>{link}</td><td>{esc(s["type"])}</td><td>{esc(s["how_used"])}</td><td>{esc(s["policy"])}</td></tr>')
    if LANG == "ja":
        body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">ホーム</a> › 情報源</div><h1>情報源と帰属</h1>
<div class="prose"><p class="sub">情報の出どころと、他者の掲載情報の扱い方。</p>
<h2>方針</h2><ul><li><b>内容ではなく事実のみ。</b>名称・住所・電話番号・営業時間といった事実を記録し、会社へリンクします。説明文・写真・評価・口コミ・物件情報・ページ構成は複製しません。</li>
<li><b>ディレクトリは「手がかり」。</b>民間ディレクトリ（Total Okinawaなど）は、会社の存在を知るためにだけ使い、会社の公式サイトで確認します。確認できないものはその旨を表示します。</li>
<li><b>robots.txtと利用規約を尊重。</b>自動アクセスを禁じるサイトは取得していません。</li>
<li><b>報道は文脈のみ。</b>報道記事は文脈と会社名の把握にのみ使い、本文は複製しません。</li>
<li><b>地図。</b>地図サービスのデータは複製・埋め込みをしません。座標は国土地理院の公開住所検索を使い、地図表示はOpenStreetMapです。</li>
<li><b>削除。</b>会社はいつでも修正・削除を依頼できます（<a href="{url("/for-agencies/")}">不動産会社の方へ</a>）。</li></ul></div>
<h2>使用した情報源</h2><div style="overflow-x:auto"><table class="data"><thead><tr><th>情報源</th><th>種類</th><th>用途</th><th>扱い</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>'''
        page("/sources/", "情報源と帰属", "沖縄の不動産会社ディレクトリの情報源と他者の掲載情報の扱い。", body, cur="about"); return
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">Home</a> › Sources</div><h1>Sources &amp; attribution</h1>
<div class="prose"><p class="sub">Where the information comes from, and how we treat other people's listings.</p>
<h2>Our policy</h2><ul><li><b>Facts, not content.</b> We record facts (a name, an address, a phone number, office hours) and link to the agency. We do not copy descriptions, photographs, ratings, reviews, property listings or page layouts.</li>
<li><b>Directories are leads, not sources of record.</b> Commercial directories (for example Total Okinawa) are used only to discover that an agency exists. We then check it against the agency's own site, and label it if we couldn't.</li>
<li><b>We respect robots.txt and site terms.</b> Sites that disallow automated access were not read; those agencies are listed from other sources and labelled accordingly.</li>
<li><b>News is context only.</b> News reports are used for context and to learn agency names; their text is not reproduced.</li>
<li><b>Maps.</b> No map-service data is copied or embedded. The “Open in Google Maps” links simply open a search in your own map app. Coordinates come from the Geospatial Information Authority of Japan's public address search; the map tiles are © OpenStreetMap contributors.</li>
<li><b>Removal.</b> Agencies can ask for correction or removal at any time — see <a href="{url("/for-agencies/")}">For agencies</a>.</li></ul></div>
<h2>Sources used</h2><div style="overflow-x:auto"><table class="data"><thead><tr><th>Source</th><th>Type</th><th>Used for</th><th>Policy</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>'''
    page("/sources/", "Sources & attribution", "Where the Okinawa housing agency directory's information comes from and how other listings are treated.", body, cur="about")

def build_suggest():
    repo = CFG["github_repo"]
    def iu(t): return f"https://github.com/{repo}/issues/new?template={t}" if CFG.get("use_github", True) else f"mailto:{CFG['contact_email']}?subject=" + urllib.parse.quote("Add an agency")
    if LANG == "ja":
        body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">ホーム</a> › 修正・追加の提案</div><h1>修正・追加の提案</h1>
<p class="sub">会社の方でなくても構いません。番号がつながらない、移転した、掲載にない会社をご存じ——そんなときはお知らせください。</p>
<div class="cards"><div class="card"><h3>誤りを報告</h3><p>各掲載ページの「誤りを報告」ボタンから、掲載内容があらかじめ入力された状態で送れます。まず<a href="{url("/find/")}">掲載を探して</a>ください。</p></div>
<div class="card"><h3>未掲載の会社を追加</h3><p>会社名・事務所の地域・連絡先・情報の出どころを教えてください。ウェブサイトやSNSのリンクがあれば最適です。</p><p><a class="btn" href="{esc(iu("add-listing.yml"))}" rel="noopener">会社を追加</a></p></div>
<div class="card"><h3>メールで送る</h3><p><a href="mailto:{esc(CFG["contact_email"])}">{esc(CFG["contact_email"])}</a> に、掲載名と修正内容をお送りください。代わりに入力します。</p></div></div>
<h2>特に助かる情報</h2><ul><li>最後に訪問・電話した日付。</li><li>現在つながる電話番号・営業時間。</li><li>宅建免許番号（契約書や店頭に表示されています）。</li><li>英語対応・米軍関係者の取り扱い。</li></ul></div>'''
        page("/suggest-edit/", "修正・追加の提案", "沖縄の不動産会社ディレクトリへの修正報告・追加の提案。", body); return
    body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">Home</a> › Suggest an edit</div><h1>Suggest an edit</h1>
<p class="sub">You don't need to work for an agency. If a number is dead, an office has moved, or you know an agency we've missed, tell us.</p>
<div class="cards"><div class="card"><h3>Report incorrect info</h3><p>Every listing has a “Report a problem” button that pre-fills the listing. Or <a href="{url("/find/")}">find the listing</a> first.</p></div>
<div class="card"><h3>Add a missing agency</h3><p>Name, where the office is, how to reach them, and how you know. A website or social link is perfect.</p><p><a class="btn" href="{esc(iu("add-listing.yml"))}" rel="noopener">Add an agency</a></p></div>
<div class="card"><h3>Prefer email?</h3><p>Email <a href="mailto:{esc(CFG["contact_email"])}">{esc(CFG["contact_email"])}</a> with the listing name and what to change.</p></div></div>
<h2>What helps most</h2><ul><li>The date you last visited or called.</li><li>A phone number and office hours that are currently working.</li><li>The broker licence number (it appears on contracts and in the shop).</li><li>Whether English is spoken and whether the agency handles military families.</li></ul>
<p>We review reports and update the data regularly. See <a href="{url("/about-data/")}">About this data</a>.</p></div>'''
    page("/suggest-edit/", "Suggest an edit or add an agency", "Report incorrect information or add a missing housing agency in Okinawa.", body)

def build_local():
    chk = Counter(r["verification"] for r in LOCAL)
    n = len(LOCAL)
    mc = Counter(r["municipality"] for r in LOCAL if r["municipality"])
    if LANG == "ja":
        title = "日本の不動産会社 — 沖縄の賃貸"
        intro = f"日本の会社が運営する賃貸仲介{n}社です。米軍関係者向けの会社ほど英語や軍関係の手続きに慣れていないことがありますが、広告上の家賃や初期費用が低いことがあるため、請負業者・退職者・長期滞在の方に選ばれることがあります（価格は当サイトでは比較していません）。"
        why = [("向いている人", "日本語が使える（または日本語が話せる人に同行してもらえる）方、長期で借りる予定の方、費用を抑えたい方。"),
               ("費用", "一般に敷金・礼金・仲介手数料・保証会社の利用料などが発生します。会社によっては「敷金礼金なし」「初期費用0円」を掲げています。契約前に総額の内訳を書面で確認してください。"),
               ("保証人・保証会社", "外国人は連帯保証人または保証会社の利用を求められるのが一般的です。可否は会社と物件によって違います。"),
               ("言語", "契約書と重要事項説明は日本語が基本です。英語対応が分からない会社は、問い合わせ時に確認しましょう。"),
               ("米軍関係者の方", "民間住宅の契約前に所属基地の住宅窓口に確認してください。規則（検査・契約条項など）は身分や所属で異なります。")]
        h_why, h_list, h_more = "選ぶ前に知っておくこと", "掲載している会社", "さらに探すには"
        more = f'<p>日本全国の宅建業者は<a href="https://etsuran2.mlit.go.jp/" rel="noopener nofollow">国土交通省の業者検索</a>で確認できます。沖縄県内には2026年3月末時点で約2,143の宅建業者がありますが、賃貸を扱い外国人に対応する会社は一部です。ここに載っていない会社をご存じの場合は<a href="{url("/suggest-edit/")}">追加の提案</a>をお願いします。</p>'
        note = "「確認済み」は、会社自身のサイトで住所・電話などを確認した状態です。英語対応・外国人入居の可否・免許番号は、サイトに記載がない場合「記載なし」と表示します。"
    else:
        title = "Japanese-run agencies in Okinawa — rentals"
        intro = f"{n} Japanese-run rental agencies. They may be less used to English paperwork and military housing rules than the agencies on the main directory, but advertised rents and fees can be lower, which is why some contractors, retirees and long-term residents use them. We have not compared prices, so check the full cost yourself."
        why = [("Who it suits", "People who speak Japanese (or can bring someone who does), plan to stay a while, or want to keep costs down."),
               ("Costs", "Expect the usual Japanese up-front costs: deposit (shikikin), key money (reikin), the agency fee and often a guarantor-company fee. Some agencies advertise no deposit or key money, or zero up-front cost. Get the full total in writing before you sign."),
               ("Guarantors", "Foreign renters are usually asked for a co-signer or a guarantee company. Whether it is possible depends on the agency and the property."),
               ("Language", "Contracts and the explanation of key terms (重要事項説明) are normally in Japanese. If a listing says English support is not stated, ask before you travel."),
               ("If you are a service member", "Check with your housing office before signing any off-base lease. Their rules on inspection and lease clauses depend on your status, so do not rely on an agency to know them.")]
        h_why, h_list, h_more = "Before you choose", "Agencies we list", "Finding more"
        more = f'<p>Any licensed broker can be checked on the <a href="https://etsuran2.mlit.go.jp/" rel="noopener nofollow">MLIT broker search</a>. About 2,143 licensed brokers were headquartered in Okinawa at the end of March 2026, but only some handle rentals for foreign residents. If you know one we are missing, please <a href="{url("/suggest-edit/")}">suggest an addition</a>.</p>'
        note = "“Checked” means address and phone were confirmed on the agency’s own site. English support, foreign-tenant policy and licence number show “Not stated” when the site does not say."
    items = "".join(f"<li><b>{esc(a)}.</b> {esc(b)}</li>" for a, b in why)
    sub_ = T(f"{n} listed · {chk['A']} checked against their own sites · {mc and len(mc)} municipalities", f"{n}社掲載 · 公式サイトで確認 {chk['A']}社 · {len(mc)}市町村")
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › {T("Japanese agencies","日本の不動産会社")}</div>
<span class="kanji" lang="ja">日本の不動産会社</span><h1>{esc(title)}</h1><p class="sub">{esc(intro)}</p><p class="sub">{sub_}. {esc(note)}</p>
<div class="two"><div class="prose"><h2>{h_why}</h2><ul class="plain">{items}</ul></div><div>{tilemap(mc, link_prefix="/local-agencies/#", caption=T("agencies","社")) if False else ""}</div></div>
<h2 class="region">{h_list}</h2>{grouped_cards(LOCAL)}<div class="prose" style="margin-top:28px"><h2>{h_more}</h2>{more}</div></div>'''
    page("/local-agencies/", title, T("Japanese-run rental agencies in Okinawa for contractors, retirees and long-term residents, with costs, guarantor and language notes.", "請負業者・退職者・長期滞在の方向けの、日本の不動産会社の一覧と注意点。"), body, cur="local")

def build_agencies():
    repo = CFG["github_repo"]
    OWNER_LINK = f"https://github.com/{repo}/issues/new?template=owner-update.yml" if CFG.get("use_github", True) else f"mailto:{CFG['contact_email']}?subject=" + urllib.parse.quote("Agency update")
    if LANG == "ja":
        body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">ホーム</a> › 不動産会社の方へ</div><h1>不動産会社の方へ</h1>
<p class="sub">掲載内容の修正・追加・削除は、いつでもお申し込みいただけます。掲載は無料で、有料の掲載順位はありません。</p>
<h2>掲載の更新・確認</h2><p>掲載ページの「誤りを報告」から「この会社の者です」を選び、変更内容と、ご本人であることの確認方法（公式サイトやSNSで十分です）をお知らせください。電話番号・営業時間・宅建免許番号・対応言語・米軍関係者の取り扱いを教えていただけると、利用者の助けになります。</p>
<p><a class="btn" href="{OWNER_LINK}" rel="noopener">会社用フォーム</a> <a class="btn secondary" href="mailto:{esc(CFG["contact_email"])}">メールで連絡</a></p>
<h2>掲載の削除</h2><p>ご希望があれば、速やかに削除または縮小します。理由は不要です。上記フォームまたはメールでご連絡ください。</p>
<h2>表示している内容</h2><p>会社名・サービス・事務所の地域・住所・電話・ウェブサイト／SNS・営業時間・対応言語・米軍関係者の取り扱い・免許番号。物件情報・写真・口コミは掲載しません。</p></div>'''
        page("/for-agencies/", "不動産会社の方へ — 掲載の更新・削除", "会社が掲載を修正・確認・削除する方法。", body); return
    body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">Home</a> › For agencies</div><h1>For agencies</h1>
<p class="sub">不動産会社の方へ — You can correct, complete or remove your listing at any time. Listing is free and there is no paid placement.</p>
<h2>Update or claim your listing</h2><p>Find your listing, press “Report a problem”, and choose “I work here”. Give us the changes and a way to confirm it's you (your official website or social page is enough). The details that help renters most are your phone number, office hours, broker licence number, the languages your staff speak, and whether you handle military families.</p>
<p><a class="btn" href="{OWNER_LINK}" rel="noopener">Agency update form</a> <a class="btn secondary" href="mailto:{esc(CFG["contact_email"])}">Email us</a></p>
<h2>Remove your listing</h2><p>Ask us and we will remove or trim it promptly. No reason needed. Use the form or email.</p>
<h2>日本語でのご連絡</h2><p lang="ja">掲載内容の修正・追加・削除のご希望は、上記のメールまたはフォームからご連絡ください。電話番号・営業時間・宅建免許番号・対応言語・米軍関係者の取り扱いをお知らせいただけると、利用者の役に立ちます。掲載の削除も、理由なくお受けします。</p>
<h2>What we show</h2><p>Name, services, office area, address, phone, website/social, hours, languages, military focus and licence number. We do not show property listings, photographs or reviews.</p></div>'''
    page("/for-agencies/", "For agencies — update or remove your listing", "How agencies can correct, claim or remove a listing in the Okinawa housing agency directory.", body)

def build_privacy():
    an_en = "This site uses privacy-friendly, cookie-free analytics (page views only, no personal profiles)." if ANALYTICS else "This site has no accounts, no ads and sets no tracking cookies."
    an_ja = "このサイトはCookieを使わないプライバシー配慮型のアクセス解析（ページ閲覧数のみ・個人の特定なし）を使用しています。" if ANALYTICS else "このサイトにはアカウント・広告・追跡用Cookieはありません。"
    if LANG == "ja":
        body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">ホーム</a> › プライバシー</div><h1>プライバシーと削除依頼</h1>
<ul><li>{an_ja}</li><li>「現在地から近い順」「現在地」は、お使いのブラウザ内でのみ位置を使います。位置情報は当サイトのサーバーに送信・保存されません。</li><li>掲載は、各社・各窓口が公開している事業上の情報です。個人の携帯電話番号は掲載しません。基地内の窓口は地図に表示しません。</li><li>掲載された会社・方は、いつでも修正・削除を依頼できます（<a href="{url("/for-agencies/")}">不動産会社の方へ</a>）。</li><li>「誤りを報告」を押すとGitHub（またはメールアプリ）に移動し、そちらのプライバシーポリシーが適用されます。地図はOpenStreetMapのタイルを読み込みます。</li></ul></div>'''
        page("/privacy/", "プライバシーと削除依頼", "個人情報の扱いと削除依頼の方法。", body); return
    body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">Home</a> › Privacy</div><h1>Privacy &amp; removal</h1>
<ul><li>{an_en}</li><li>“Nearest to me” and “Near me” use your location only inside your browser; it is never sent to or stored on our servers.</li><li>Listings contain business details that agencies and offices publish themselves. We do not publish personal mobile numbers, and offices on military installations are not shown on the map.</li><li>Anyone named on this site can ask for correction or removal at any time — see <a href="{url("/for-agencies/")}">For agencies</a>.</li><li>When you press “Report a problem”, you leave this site for GitHub (or open your email app) and its own privacy policy applies. The map page loads tiles from OpenStreetMap.</li></ul></div>'''
    page("/privacy/", "Privacy & removal requests", "How personal information is handled and how to request removal.", body)

def build_404():
    write("404.html", f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found</title><link rel="stylesheet" href="{url("/assets/style.css")}"></head><body><main class="wrap pagehead"><h1>Page not found / ページが見つかりません</h1><p>Try <a href="{url("/find/")}">searching</a> or go <a href="{url("/")}">home</a>. · <a href="{BASE}/ja/">日本語トップへ</a></p></main></body></html>''')

def build_static():
    shutil.copytree(ROOT/"templates/assets", DIST/"assets", dirs_exist_ok=True)
    (DIST/"data").mkdir(exist_ok=True)
    shutil.copy(ROOT/"data/locations.csv", DIST/"data/locations.csv")
    (DIST/".nojekyll").write_text("")

SVCS_WITH = [d for d in SVC if n_places(d)]

def sitemap():
    pages = ["/", "/services/", "/areas/", "/find/", "/map/", "/guide/", "/guides/", "/guides/move-in/", "/guides/rent-prices/", "/guides/avoid-problems/", "/guides/living-in-okinawa/", "/guides/oha/", "/local-agencies/", "/checklist/", "/costs/", "/housing-office/", "/glossary/", "/shortlist/", "/compare/", "/share-experience/", "/about-data/", "/sources/", "/suggest-edit/", "/for-agencies/", "/privacy/"]
    pages += [f"/services/{d}/" for d in SVC if by_svc[d]] + [f"/areas/{s}/" for s in MUNIS]
    pages += [f'/l/{r["id"]}/' for r in ROWS if not (r["verification"] in ("C", "D") and not CFG["index_unverified_pages"])]
    pages = [p for p in pages if p not in ("/shortlist/", "/compare/")]
    allp = sorted(pages) + sorted("/ja" + p for p in pages if not p.startswith(EN_ONLY))
    sm = "".join(f'<url><loc>{CFG["base_url"]}{p}</loc><lastmod>{TODAY}</lastmod></url>' for p in allp)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {CFG['base_url']}/sitemap.xml\n")

def build_language():
    build_home(); build_services_index(); build_areas(); build_find(); build_map(); build_guide(); build_local(); build_extra(); build_about(); build_sources(); build_suggest(); build_agencies(); build_privacy()
    for d in SVC.values():
        if by_svc[d["slug"]]: build_service(d)
    for s in MUNIS: build_area(s)
    for r in ROWS: build_listing(r)

exec(compile((Path(__file__).resolve().parent / "extra_pages.py").read_text(encoding="utf-8"), "extra_pages.py", "exec"), globals())

def main():
    global LANG
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    build_static(); build_404(); sitemap()
    for LANG in ("en", "ja"):
        build_language()
    print("pages:", sum(1 for _ in DIST.rglob("index.html")), "agencies:", len(PLACES), "services:", len(SVCS_WITH))

if __name__ == "__main__":
    main()
