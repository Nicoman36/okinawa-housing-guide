# Extra pages for the generator: nearby + renter reports, shortlist/compare, checklist, costs, housing-office guide, glossary.
# This file is exec()'d by build_site.py, so it can use that module's helpers (T, url, page, esc, card, badge, ...).

# ------------------------------------------------------------------ listing sections
def nearby_section(r):
    if r["kind"] != "agency": return ""
    ns = near(r, 5)
    if not ns:
        return f'<h2 class="sec">{T("What is nearby","周辺の目印")}</h2><p class="sub">{T("Map position not confirmed yet, so we cannot show distances.","地図上の位置が未確認のため、距離を表示できません。")}</p>'
    rows = "".join(f'<tr><td>{esc(q["name_ja"] if LANG == "ja" else q["name_en"])}</td><td class="num">{km:.1f} km</td></tr>' for km, q in ns)
    pts = json.dumps([{"n": (q["name_ja"] if LANG == "ja" else q["name_en"]), "la": q["lat"], "lo": q["lon"], "k": q["kind"]} for _, q in ns], ensure_ascii=False)
    rough = T(" The pin is rounded to about 100 m.", "ピンは約100 mに丸めています。") if r.get("geo_precision") == "town" else ""
    return f'''<h2 class="sec">{T("What is nearby","周辺の目印")}</h2>
<div id="lmap" class="lmap" role="img" aria-label="{T("Map showing this agency and nearby bases","この会社と周辺の基地を示す地図")}" data-lat="{esc(r["lat"])}" data-lon="{esc(r["lon"])}" data-name="{esc(primary_name(r))}" data-pts='{esc(pts)}'></div>
<table class="data compact"><thead><tr><th>{T("Reference point","目印")}</th><th>{T("Straight-line distance","直線距離")}</th></tr></thead><tbody>{rows}</tbody></table>
<p class="sub" style="font-size:.85rem">{T("Straight-line distance from the agency’s office to a point inside each installation or landmark, not to a gate, and not driving time. Roads around the bases add a lot.","事務所から各基地・目印の中の一点までの直線距離で、ゲートまでの距離や運転時間ではありません。基地周辺は道路で遠回りになることが多いです。")}{rough}</p>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"><script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>'''

def exp_summary(xs):
    def tally(key, order):
        c = Counter(x[key] for x in xs); return [(o, c.get(o, 0)) for o in order]
    return [
        (T("Could they work in English?", "英語で対応できたか"), tally("english", ["Yes, easily", "Some, with effort", "No"])),
        (T("Were all fees explained before signing?", "署名前に費用の説明があったか"), tally("fees_clear", ["Yes", "Mostly", "No"])),
        (T("Did the final cost match the quote?", "最終費用は見積りどおりか"), tally("cost_matched", ["Yes", "Slightly higher", "Much higher"])),
        (T("Housing-office dealings", "住宅窓口の手続き"), tally("housing_office", ["Smooth", "Some trouble", "A lot of trouble", "Not applicable"])),
        (T("Would use again?", "また利用したいか"), tally("use_again", ["Yes", "Maybe", "No"])),
    ]

def reviews_section(r):
    if r["kind"] != "agency": return ""
    xs = EXP.get(r["id"], []); n = len(xs)
    link = url("/share-experience/?agency=" + r["id"])
    head = f'<h2 class="sec">{T("Renter reports","利用者の体験")}</h2>'
    if n < 3:
        msg = T(f"{n} renter report{'s' if n != 1 else ''} so far. We show a summary once three renters have reported, so nobody can be identified.", f"現在 {n} 件。個人が特定されないよう、3件集まった時点で集計を表示します。")
        return f'{head}<p>{msg}</p><p><a class="btn secondary" href="{link}">{T("Share your experience","体験を共有する")}</a></p>'
    rows = ""
    for q, vals in exp_summary(xs):
        tot = sum(v for _, v in vals) or 1
        segs = "".join(f'<span class="seg s{i}" style="flex:{max(v, 0)}" title="{esc(l)}: {v}"></span>' for i, (l, v) in enumerate(vals) if v)
        legend = " · ".join(f"{esc(l)} {v}" for l, v in vals)
        rows += f'<div class="xrow"><b>{q}</b><div class="xbar">{segs}</div><small>{legend}</small></div>'
    comments = "".join(f'<blockquote><p>{esc(x["comment"])}</p><small>{esc(x["move_in_month"])}</small></blockquote>' for x in xs if x["comment"])
    note = T(f"{n} renters reported. These are individual experiences, reviewed by a person before publishing, not a rating.", f"{n}件の報告。個々の体験談で、掲載前に人が確認しています。評価点ではありません。")
    return f'{head}<p class="sub">{note}</p><div class="xsum">{rows}</div>{comments}<p><a class="btn secondary" href="{link}">{T("Share your experience","体験を共有する")}</a></p>'

# ------------------------------------------------------------------ share-experience form
def build_share_experience():
    ags = sorted((r for r in ROWS if r["kind"] == "agency" and r["status"] != "closed"), key=lambda r: r["name_en"].lower())
    opts = "".join(f'<option value="{r["id"]}">{esc(r["name_en"])}{" — "+esc(r["name_ja"]) if r["name_ja"] else ""}</option>' for r in ags)
    def sel(id_, label, choices):
        o = "".join(f'<option value="{esc(v)}">{esc(l)}</option>' for v, l in choices)
        return f'<div><label for="{id_}">{label}</label><select id="{id_}" required><option value="">{T("Choose…","選択…")}</option>{o}</select></div>'
    form = f'''<form id="xp-form" class="xp" data-gh="{esc(CFG["github_repo"] if CFG.get("use_github", True) else "")}" data-mail="{esc(CFG["contact_email"])}" data-site="{esc(CFG["base_url"])}">
<div class="wide"><label for="xp-agency">{T("Which agency?","どの会社ですか？")}</label><select id="xp-agency" required><option value="">{T("Choose an agency…","会社を選択…")}</option>{opts}</select></div>
<div><label for="xp-month">{T("Month you signed or moved in","契約・入居した月")}</label><input id="xp-month" type="month" required></div>
{sel("xp-english", T("Could you get things done in English?","英語で用件を済ませられましたか"), [("Yes, easily",T("Yes, easily","問題なく")),("Some, with effort",T("Some, with effort","なんとか")),("No",T("No","できなかった"))])}
{sel("xp-fees", T("Were all fees explained before you signed?","署名前にすべての費用の説明がありましたか"), [("Yes",T("Yes","はい")),("Mostly",T("Mostly","ほぼ")),("No",T("No","いいえ"))])}
{sel("xp-cost", T("Did the final cost match the first quote?","最終費用は最初の見積りどおりでしたか"), [("Yes",T("Yes","はい")),("Slightly higher",T("Slightly higher","少し高かった")),("Much higher",T("Much higher","かなり高かった"))])}
{sel("xp-office", T("Housing office dealings (inspection, lease addendum)","住宅窓口の手続き（検査・特約）"), [("Not applicable",T("Not applicable","該当なし")),("Smooth",T("Smooth","スムーズ")),("Some trouble",T("Some trouble","少し問題あり")),("A lot of trouble",T("A lot of trouble","かなり問題あり"))])}
{sel("xp-again", T("Would you use this agency again?","この会社をまた利用したいですか"), [("Yes",T("Yes","はい")),("Maybe",T("Maybe","たぶん")),("No",T("No","いいえ"))])}
<div class="wide"><label for="xp-comment">{T("Anything else? (optional, 400 characters)","ほかにあれば（任意・400文字まで）")}</label><textarea id="xp-comment" maxlength="400" rows="4"></textarea></div>
<label class="wide chk"><input id="xp-ok" type="checkbox" required> {T("This is my own experience as a renter with this agency, and I included no names, unit numbers, phone numbers or other personal details.","これは私自身の体験で、氏名・部屋番号・電話番号などの個人情報は含めていません。")}</label>
<div class="wide"><button class="btn" type="submit">{T("Prepare my report","報告を作成")}</button> <span id="xp-msg" class="sub" style="margin:0"></span></div></form>'''
    how = T("When you press the button, your report opens as a draft on GitHub (or in your email app) so you can read it before sending. Nothing is published automatically: a person reads each report first.",
            "ボタンを押すと、報告の下書きがGitHub（またはメールアプリ）で開きます。送信前に内容を確認できます。自動で公開されることはなく、必ず人が確認します。")
    rules = [T("What we publish: your answers to the five questions, the month, and your comment if it is short, factual and about your own experience.","公開するもの：5つの質問への回答、月、そして短く事実に基づく自分の体験のコメント。"),
             T("What we remove: names of staff, phone numbers, unit numbers, guesses about motives, anything that is not about your own rental, and anything we cannot treat as fair.","削除するもの：担当者名、電話番号、部屋番号、動機の憶測、自分の賃貸と無関係な内容、公平とみなせない内容。"),
             T("Summaries appear only once an agency has three reports, so no single renter can be picked out. There is no star score.","要約は3件集まってから表示し、個人が特定されないようにします。星の点数はありません。"),
             T("Agencies can send a short, factual reply through the “For agencies” page, which we add under the reports. Anyone can ask us to remove their own report.","会社は「不動産会社の方へ」ページから短い事実の返信を送れます。報告の下に追記します。ご自身の報告の削除はいつでも依頼できます。"),
             T("These are personal experiences, not verified facts and not legal or financial advice.","これらは個人の体験であり、確認済みの事実でも法的・金銭的助言でもありません。")]
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › {T("Share your experience","体験を共有")}</div>
<h1>{T("Share your experience with an agency","不動産会社での体験を共有")}</h1><p class="sub">{T("Five quick questions help the next renter know what to expect. It takes about two minutes.","5つの簡単な質問が、次に探す人の助けになります。所要時間は約2分です。")}</p>
<div class="two"><div>{form}<p class="sub" style="font-size:.9rem">{how}</p></div><aside class="actions-card"><h2>{T("How reports are handled","報告の扱い")}</h2><ul class="plain tight">{"".join(f"<li>{x}</li>" for x in rules)}</ul></aside></div></div>'''
    page("/share-experience/", T("Share your experience with an agency — Okinawa Housing Agency Directory", "不動産会社での体験を共有"), T("Tell other renters how an Okinawa housing agency treated you, in five quick questions.", "沖縄の不動産会社での体験を5つの質問で共有。"), body, cur="share")

# ------------------------------------------------------------------ shortlist + compare shells
def _data_script():
    return f'<script src="{url("/assets/" + ("data_ja.js" if LANG == "ja" else "data.js"))}"></script>'

def build_shortlist():
    ref_opts = "".join(f'<option value="{q["id"]}">{esc(q["name_ja"] if LANG == "ja" else q["name_en"])}</option>' for q in REFS)
    body = f'''<div class="wrap pagehead" id="shortlist-app"><h1>{T("Your shortlist","候補リスト")}</h1>
<p class="sub">{T("Star agencies anywhere on the site and they appear here. The list is stored in this browser only; nobody else can see it.","サイトのどこでも星（♡）を付けると、ここに表示されます。リストはこのブラウザにのみ保存され、他の人には見えません。")}</p>
<div class="switcher"><label for="sl-ref"><b>{T("Show distance to","距離を表示")}</b></label><select id="sl-ref"><option value="">{T("None","なし")}</option>{ref_opts}</select>
<button type="button" class="btn" id="sl-compare" disabled>{T("Compare selected","選択を比較")}</button><button type="button" class="btn secondary" id="sl-copy">{T("Copy contact sheet","連絡先をコピー")}</button><button type="button" class="btn ghost" id="sl-print">{T("Print","印刷")}</button><span id="sl-msg" class="sub" style="margin:0" aria-live="polite"></span></div>
<div id="sl-out" class="cards"></div><p id="sl-empty" class="empty" hidden>{T("Nothing here yet. Open any agency or search result and press the ♡ to save it.","まだありません。会社のページや検索結果で♡を押すと保存されます。")} <a href="{url("/find/")}">{T("Search agencies","会社を検索")}</a></p></div>'''
    page("/shortlist/", T("Your shortlist — Okinawa Housing Agency Directory","候補リスト"), T("Agencies you saved, with notes, distances and a printable contact sheet.","保存した会社を、メモ・距離・印刷用連絡先つきで確認。"), body, cur="shortlist", scripts=_data_script(), noindex=True)

def build_compare():
    ref_opts = "".join(f'<option value="{q["id"]}">{esc(q["name_ja"] if LANG == "ja" else q["name_en"])}</option>' for q in REFS)
    body = f'''<div class="wrap pagehead" id="compare-app"><div class="crumbs"><a href="{url("/shortlist/")}">{T("Shortlist","候補リスト")}</a> › {T("Compare","比較")}</div><h1>{T("Compare agencies","会社を比較")}</h1>
<p class="sub">{T("Up to three agencies side by side. Facts come from each agency’s own site unless the verification badge says otherwise.","最大3社を並べて比較します。確認バッジに別の記載がない限り、各社の公式サイトに基づきます。")}</p>
<div class="switcher"><label for="cp-ref"><b>{T("Distance to","距離")}</b></label><select id="cp-ref"><option value="">{T("None","なし")}</option>{ref_opts}</select><a class="btn ghost" href="{url("/shortlist/")}">{T("Back to shortlist","候補リストへ")}</a></div>
<div class="table-wrap"><table id="cp-table" class="data compare"></table></div><p id="cp-empty" class="empty" hidden>{T("Choose two or three agencies on your shortlist, then press “Compare selected”.","候補リストで2〜3社を選び、「選択を比較」を押してください。")}</p></div>'''
    page("/compare/", T("Compare agencies — Okinawa Housing Agency Directory","会社を比較"), T("Side-by-side comparison of up to three Okinawa housing agencies.","沖縄の不動産会社を最大3社まで並べて比較。"), body, cur="shortlist", scripts=_data_script(), noindex=True)

# ------------------------------------------------------------------ English-only guides
def _chk(i, text): return f'<li><label class="chk"><input type="checkbox" data-chk="{i}"> <span>{text}</span></label></li>'
def _sect(title, intro, items, pre):
    lis = "".join(_chk(f"{pre}{n}", t) for n, t in enumerate(items, 1))
    return f'<section class="cl"><h2>{title}</h2><p class="sub">{intro}</p><ul class="checks">{lis}</ul></section>'

def build_checklist():
    S = [
     ("1. Before you look", "Do these first; they save the most money and the most stress.", [
        "Check in with your housing office. Kadena’s page says accompanied active-duty personnel must report no later than 72 hours after arrival, and DoD personnel must check with the Housing Referral Office before committing to rent or lease off base. <a href='%s'>Housing office guide</a>" % url("/housing-office/"),
        "Ask the housing office what you are entitled to (allowances, temporary lodging) so your budget is based on real numbers.",
        "Set a monthly rent ceiling and a separate up-front budget. Up-front costs are often several months of rent: <a href='%s'>see the estimator</a>." % url("/costs/"),
        "Write your must-haves: bedrooms, number of cars (parking spaces), pets, school or base distance, air-conditioning, a washer hookup.",
        "Decide how you will cope in Japanese: ask the agency about English support, or bring a Japanese-speaking friend or colleague to key meetings."]),
     ("2. Choose and contact agencies", "Contact three, not one. Prices and attitudes vary.", [
        "Pick three agencies from the <a href='%s'>directory</a>. Include one Japanese-run agency if you can handle Japanese paperwork: <a href='%s'>Japanese agencies</a>." % (url("/find/"), url("/local-agencies/")),
        "Ask each: English support? Experience with U.S. housing-office lease addenda and inspections? How much total up front?",
        "Check the broker licence number on the listing against the MLIT register (it is linked on every listing page).",
        "Ask for homes near the base or gate you need; use <a href='%s'>search by base</a> to see who is close." % url("/find/"),
        "Expect weekday-only office hours. Many agencies close on Wednesdays or Sundays, so check hours on the listing."]),
     ("3. Viewing a home", "Okinawa has its own surprises. Look for these.", [
        "Mold and damp: check closets, bathroom, behind furniture, window frames. Okinawa is humid; ask about dehumidifiers and how the bathroom dries.",
        "Typhoon readiness: shutters or storm windows, balcony furniture, what the unit does in a strong storm.",
        "Air-conditioning: how many units, how old, and whether they are included in the rent. Older homes often have none.",
        "Hot water, water pressure, and the roof water tank if the building has one. Ask who maintains it.",
        "Parking: measure it against your vehicle. Ask about carport size and any extra parking fee.",
        "Noise: visit at different times. Aircraft, traffic and neighbours matter more than the photos.",
        "Power outlets, washer hookup, and where the kitchen appliances go. Ask what the housing office provides for eligible off-base residents.",
        "Take dated photos of every flaw you find, before you sign."]),
     ("4. Before you sign", "This is where fees and surprises appear. Slow down.", [
        "Get a written breakdown of every up-front fee (deposit, key money, agency fee, guarantor, insurance, key change).",
        "Ask for the explanation of important matters (重要事項説明) in English, or a trusted interpreter. A licensed agent reads it to you before signing.",
        "Ask whether you need a guarantor or a guarantee company, and what that costs.",
        "Check the early-termination clause for military transfer orders. Get it in writing and have your housing office review the lease.",
        "Ask who handles repairs, how to reach them after hours or after a typhoon, and who pays for what.",
        "Ask about pets, parking, renewal, notice period, and move-out cleaning or restoration charges.",
        "Never pay anything before you have seen the home and received a written fee list."]),
     ("5. Signing and moving in", "Keep every document, in both languages if you can.", [
        "Complete the housing-office lease review and inspection steps they tell you to do. Ask what is required before and after you sign.",
        "Pay fees by the method the agency gives in writing, and keep receipts.",
        "On move-in day, photograph every room and meter reading with the date, and send the list of defects to the agency.",
        "Set up electricity, water, gas and internet. Ask the agency which companies serve the building and whether they help.",
        "Learn the trash rules (days, sorting, bags). They are strict and vary by town.",
        "If you are not covered by SOFA (for example some retirees or contractors), ask city hall about registering your address within 14 days of moving."]),
     ("6. Moving out", "The deposit is easier to get back if you plan ahead.", [
        "Check the notice period in your lease (commonly one month) and give notice in writing.",
        "Clean thoroughly and take dated photos of the empty home.",
        "Ask for the restoration-cost estimate in writing and compare it against your move-in photos. Stars and Stripes reported that on 28 August 2026 the housing office stopped requiring re-inspection of approved off-base homes at each tenant move-out; ask what applies to you.",
        "Cancel utilities, return all keys, and keep the handover paper."])]
    body_sections = "".join(_sect(a, b, c, f"s{n}-") for n, (a, b, c) in enumerate(S, 1))
    total = sum(len(c) for _, _, c in S)
    body = f'''<div class="wrap pagehead" id="checklist-app" data-total="{total}"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › Checklist</div>
<h1>First-time renter checklist</h1><p class="sub">Renting in Okinawa for the first time? This is the order most people wish they had followed. Tick items as you go: your progress stays in this browser only.</p>
<div class="progress" role="status"><div class="bar"><i id="cl-bar" style="width:0%"></i></div><b id="cl-count">0 of {total} done</b><button class="btn ghost" type="button" id="cl-reset">Reset</button><button class="btn secondary" type="button" id="cl-print">Print</button></div>
<div class="callout info"><b>General information only.</b> Rules depend on your service, status and orders, and they change. Your housing office has the final say on what you must do. Typical Japanese rental practices described here are common, not guaranteed.</div>
{body_sections}
<p class="sub">Next: <a href="{url("/costs/")}">estimate your up-front costs</a> · <a href="{url("/glossary/")}">decode the listing</a> · <a href="{url("/housing-office/")}">housing office guide</a></p></div>'''
    page("/checklist/", "First-time renter checklist for Okinawa — Okinawa Housing Agency Directory", "A step-by-step checklist for first-time renters in Okinawa: before you look, viewing, signing, move-in and move-out.", body, cur="checklist")

def build_costs():
    rows = [
     ("Rent (first month)", "Paid at signing, usually prorated if you move in mid-month.", "typical"),
     ("Security deposit (敷金, shikikin)", "Held against damage and unpaid rent. Commonly 0–2 months. Refundable after restoration costs are deducted.", "typical"),
     ("Key money (礼金, reikin)", "A non-refundable “thank you” to the landlord. Commonly 0–2 months, and some listings advertise none.", "typical"),
     ("Agency fee (仲介手数料)", "Paid to the agency. By law the cap for a rental is one month of rent plus consumption tax, split between landlord and tenant by agreement.", "law"),
     ("Guarantor company (保証会社)", "Often required for foreign renters instead of a personal guarantor. Commonly a share of one month’s rent up front and a yearly renewal fee.", "typical"),
     ("Fire / renter’s insurance (火災保険)", "Usually required and paid for two years. Commonly around ¥15,000–20,000.", "typical"),
     ("Key exchange (鍵交換)", "Replacing the lock for you. Commonly about ¥10,000–25,000.", "typical"),
     ("Management / common fee (管理費・共益費)", "Paid every month with rent. Check whether it is included in the advertised rent.", "typical"),
     ("Last month’s rent", "Military OneSource says agencies commonly ask for first and last month’s rent at signing in addition to the deposit and an agency fee of about half a month. Ask if yours does.", "source")]
    tr = "".join(f'<tr><td><b>{a}</b></td><td>{b}</td></tr>' for a, b, _ in rows)
    body = f'''<div class="wrap pagehead" id="costs-app"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › Up-front costs</div>
<h1>Up-front costs: what you pay before you get the keys</h1>
<p class="sub">In Japan the first payment is far bigger than one month’s rent. Use the estimator to see a realistic total, then ask each agency for its own written breakdown.</p>
<div class="callout"><b>These are typical ranges, not quotes.</b> Every agency and landlord sets its own fees, and Okinawa agencies differ. The agency’s written fee list is the only number that counts. Ask your pay office whether any of these costs are reimbursed or advanced.</div>
<div class="two"><form id="cost-calc" class="calc" aria-label="Up-front cost estimator">
<div><label for="c-rent">Monthly rent (¥)</label><input id="c-rent" type="number" min="0" step="1000" value="100000" inputmode="numeric"></div>
<div><label for="c-adv">Rent paid in advance (months)</label><input id="c-adv" type="number" min="0" step="0.5" value="1"></div>
<div><label for="c-dep">Deposit / shikikin (months)</label><input id="c-dep" type="number" min="0" step="0.5" value="1"></div>
<div><label for="c-key">Key money / reikin (months)</label><input id="c-key" type="number" min="0" step="0.5" value="0"></div>
<div><label for="c-fee">Agency fee (months, before tax)</label><input id="c-fee" type="number" min="0" max="1" step="0.5" value="0.5"></div>
<div><label for="c-gua">Guarantor company (% of one month’s rent)</label><input id="c-gua" type="number" min="0" step="10" value="50"></div>
<div><label for="c-ins">Fire insurance (¥)</label><input id="c-ins" type="number" min="0" step="1000" value="15000"></div>
<div><label for="c-kex">Key exchange (¥)</label><input id="c-kex" type="number" min="0" step="1000" value="15000"></div>
<div><label for="c-rate">Yen per US dollar (example, edit it)</label><input id="c-rate" type="number" min="1" step="1" value="150"></div>
</form>
<aside class="actions-card" aria-live="polite"><h2>Your estimate</h2><div id="c-out" class="calc-out"></div><p class="sub" style="font-size:.85rem">Includes 10% consumption tax on the agency fee. Utilities, moving costs, furniture and the monthly management fee are not included. The yen-per-dollar figure is only an example: check today’s rate.</p></aside></div>
<h2>What each line means</h2><table class="data"><thead><tr><th>Cost</th><th>What it is</th></tr></thead><tbody>{tr}</tbody></table>
<h2>Ways to keep it down</h2><ul class="plain"><li><b>Look for “no deposit / no key money” listings.</b> They exist, but check the monthly rent and the exit fees.</li><li><b>Ask what is negotiable.</b> The agency fee is capped by law; other items often are not fixed.</li><li><b>Compare total cost over the whole stay</b>, not just monthly rent: a cheaper rent with high exit charges can cost more.</li><li><b>Ask the housing office</b> which costs are reimbursed or advanced before you pay anything.</li></ul>
<p class="sub">Next: <a href="{url("/checklist/")}">first-time renter checklist</a> · <a href="{url("/glossary/")}">listing glossary</a></p></div>'''
    page("/costs/", "Up-front costs of renting in Okinawa — estimator and fee guide", "Estimate deposit, key money, agency fee, guarantor and insurance costs for an Okinawa rental, with plain-language explanations.", body, cur="costs")

def build_housing_office():
    off = [r for r in ROWS if r["id"] in ("okinawa-family-housing-office", "homes-mil")]
    cards = "".join(card(r) for r in off)
    M = lambda e: f'<a href="mailto:{e}">{e}</a>'
    def tb(head, rows): return _tbl(head, rows)
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › Housing office guide</div>
<h1>Housing office guide: Okinawa military family housing</h1>
<p class="sub">Everything the Kadena housing office page tells newcomers, in one place: who must live on base, how to apply, who to call, and what the office does for people who rent off base. Read from <a href="https://www.kadena.af.mil/Agencies/Okinawa-Family-Housing/" rel="noopener nofollow">the Okinawa Family Housing page</a> on 25 October 2026. It shows no update date, so confirm by phone.</p>
<div class="callout info"><b>One office for every service.</b> Kadena’s housing office handles Marines, Sailors, Soldiers and Airmen, whatever base you are assigned to. Camp Foster, Kinser and Courtney have satellite counters of the same office, not separate offices.</div>
<div class="callout info"><b>Rules depend on your service, status and orders, and change.</b> This is a plain-language summary, not official guidance. The official page also hosts forms, policies, floor plans and the waiting-list file, which we do not copy.</div>
<nav class="toc" aria-label="On this page"><a href="#assign">Who lives on base</a> · <a href="#apply">Applying</a> · <a href="#offbase">If you live off base</a> · <a href="#perks">Appliances and furniture</a> · <a href="#pets">Pets</a> · <a href="#mold">Mold tips</a> · <a href="#contacts">Contacts</a> · <a href="#maint">Maintenance</a> · <a href="#tmo">Moving offices</a></nav>
<h2 id="assign">Who must live on base</h2><ul class="plain">
<li><b>Mandatory assignment.</b> Accompanied active-duty personnel must live in government family housing if adequate units are available. The office manages more than 6,928 on-base homes across seven bases and camps, centralized for Marines, Sailors, Soldiers and Airmen regardless of base assignment.</li>
<li><b>Check in within 72 hours.</b> Accompanied active-duty personnel must report to the Military Housing Office no later than 72 hours after arrival. The first available home goes to the first eligible family on the waiting list with complete paperwork. Reserve lodging in case a home is not ready.</li>
<li><b>“Live Where You Work.”</b> Housing is assigned by two locations, based on the duty location on your orders.</li>
<li><b>Eligible for government housing:</b> military members with authorized dependents, military-married-to-military couples assigned to the same or adjacent base and living together, and Key and Essential Personnel.</li>
<li><b>No home on arrival?</b> Stay on the waiting list in the “Lease Bypass” category. After 12 months you are contacted when a home matches your grade and entitlement. Declining that home removes you from the list.</li>
<li><b>Moving off post after 12 months.</b> Occupancy in grade and entitlement must be at or above 90% in both your primary and secondary assignment locations, your command must concur, and it is a convenience move that is not funded.</li>
<li><b>DoD civilians</b> live off post. On-post homes are not currently offered to them, except for the Key and Essential Personnel List, controlled by the 18th Wing with input from MCIPAC, USN and USAG-Okinawa. Key and Essential positions are designated by senior island leaders as critical in emergencies, and the policy is available at the housing office.</li>
<li><b>Unaccompanied personnel:</b> each service houses its own members. Ask your unit, sponsor or family readiness officer.</li></ul>
<h2 id="apply">Applying for government housing</h2><ul class="plain">
<li>Email <b>DD Form 1746</b> (advance application) with a complete copy of your PCS orders to {M("Kadenahousing.customerservice@us.af.mil")}. Sponsors should send it as one package.</li>
<li><b>Your waiting-list date:</b> advance application: the date you leave your prior installation (including TDY or leave en route), or the date you are ordered to active duty. Walk-in within 30 days of arrival: the date you left your previous installation. Walk-in after 30 days: the walk-in date. Port To Home application before arrival: your arrival date.</li>
<li>Staff need 2 to 3 business days to review documents. Include proof of any pending promotion or gain of dependents so you are placed on the correct list.</li>
<li>A school verification letter can be replaced by a Housing Assignment letter (on base) or a lease agreement (off base).</li>
<li>The office posts the latest occupancy and waiting-list file on its page. If it looks old, clear your browser cache.</li></ul>
<h2 id="offbase">If you rent off base</h2><ul class="plain">
<li><b>Check with the Housing Referral Office before you commit.</b> Off-base correspondence: {M("718ces.cehmf.housingreferral@us.af.mil")}. Pre-final inspections: {M("718ces.cehc@us.af.mil")}.</li>
<li><b>Lease review.</b> Stars and Stripes reports the office reviews leases for consistency, and does not approve rents, which agencies and owners set.</li>
<li><b>Inspections.</b> Stars and Stripes reported that on 28 August 2026 the office stopped requiring re-inspection of approved off-base homes at each tenant move-out. Ask what applies to you.</li>
<li><b>Pets are not considered in assignments.</b> You may be placed off post, and about 1 in 3 families live off post.</li>
<li>For allowances while renting, see the <a href="{url("/guides/oha/")}">OHA guide</a>. To end an on- or off-base housing arrangement, use the “Terminate On/Off Base Housing” form on the official page.</li></ul>
<h2 id="perks">Appliances, furniture and yards</h2><ul class="plain">
<li><b>Major appliances</b> are provided for the whole tour to eligible personnel on and off base: stove, refrigerator, washer and dryer. A dishwasher comes with on-base homes only. Furnishings questions: {M("718ces.fms@us.af.mil")}.</li>
<li><b>Loaner furniture:</b> 90 days for inbound personnel only, and 60 days for eligible PCS personnel.</li>
<li><b>Yards:</b> on-base residents must mow if a yard is present. Fences are not provided.</li></ul>
<h2 id="pets">Pets</h2><ul class="plain">
<li>Japan’s quarantine for dogs is at least six months (180 days), so start the process immediately. A dog may serve it before arrival only under very strict conditions, or on an installation if the owner is in military family housing and the pet stays in an on-post unit.</li>
<li>Pets are not considered in housing assignments, and quarantined animals are not allowed in off-post homes.</li>
<li>Kennels on post cost at least $25 a day and can run much higher. Aggressive or potentially aggressive breeds are not allowed on the installation.</li>
<li>Limit: no more than two dogs and/or cats in non-tower units and in designated towers on floors 1 to 3.</li>
<li>A pet-friendly home is not guaranteed on arrival. If you wait for one, your temporary lodging allowance may end. See the Local Pet Policy on the official page.</li></ul>
<h2 id="mold">Mold and humidity: the office’s tips</h2><p>The office says mold is prevalent in Okinawa’s humid, subtropical climate, and dehumidifiers are not provided.</p><ul class="plain">
<li>Do not block HVAC ducts or fan coil units, and keep filters clean: every 30 days, or every 15 with pets.</li>
<li>Keep indoor temperature at 76 to 80°F in cooling season and 65 to 74°F in heating season.</li>
<li>Clean regularly with environmentally safe cleaners and a HEPA vacuum.</li>
<li>Use bathroom and kitchen exhaust fans during and after use, but not continuously.</li>
<li>Clean dryer lint filters after each use, report vent damage, wipe closet condensation daily and dry damp clothing quickly.</li>
<li>Limit houseplants, blot carpet spills dry, avoid overcrowding closets, and do not store items in the A/C mechanical room.</li>
<li>Open windows in moderate spring and fall weather when the A/C is off.</li></ul>
<h2 id="contacts">Contacts and hours</h2>
{tb(["Office","Phone / email","Hours (JST)"],[
 ["<b>Customer service</b>","634-0582 on base. From a Japan cell: 098-938-1111, then 634-0582. From a U.S. cell: 011-81-98-938-1111, then 634-0582. DSN 315-634-0582.<br>"+M("Kadenahousing.customerservice@us.af.mil"),"Mon to Fri 08:00 to 15:30; closes 12:00 Wednesdays"],
 ["<b>Facility inquiries</b>","634-1427<br>"+M("718CES.CEHMF.Facilities@us.af.mil"),"—"],
 ["<b>Furnishings</b>",M("718ces.fms@us.af.mil"),"—"],
 ["<b>Dorms (unaccompanied housing)</b>","634-0173<br>"+M("Kadena.unaccompaniedhousing@us.af.mil"),"—"],
 ["<b>Off-base correspondence</b>",M("718ces.cehmf.housingreferral@us.af.mil"),"—"],
 ["<b>On-base correspondence</b>",M("718ces.cehma.housing@us.af.mil"),"—"],
 ["<b>Pre-final inspections</b>",M("718ces.cehc@us.af.mil"),"—"],
 ["<b>Facebook Messenger</b>","Okinawa Military Family Housing (@OkinawaMFH)","—"],
 ["<b>Camp Foster satellite</b><br>Bldg 1670, Sada Tower, multipurpose room","645-6234","08:00 to 09:00 and 15:00 to 16:00, except Wednesday"],
 ["<b>Camp Kinser satellite</b><br>Bldg 107, Room 118","637-3736","14:30 to 15:30; closed Wednesday"],
 ["<b>Camp Courtney satellite</b><br>Bldg 4118","622-7317","14:30 to 15:30; closed Wednesday"]])}
<p class="sub">The page lists no street address for the main office. Satellite hours are narrow, so call first.</p>
<h2 id="maint">Maintenance</h2><ul class="plain">
<li><b>Emergency and phone requests: 634-HOME (4663).</b> From a cell, dial 098-938-1111, wait for the dial tone, then 634-4663.</li>
<li>Quick options: 1 emergency power or water outage, 2 scheduled outage, 3 pests (rodents, insects, dead animals), 4 appliance maintenance (on and off base), 5 service clerks, 24/7.</li>
<li>Service requests by email: {M("718ces.servicecall@us.af.mil")}. There is also an online Housing Maintenance Request form on the official page.</li></ul>
<h2 id="tmo">Household goods offices (TMO/DMO)</h2>
{tb(["Who","Where","Phone"],[["Air Force and Navy at Kadena or White Beach","Kadena Bldg 756","DSN 632-0068"],["Army","Torii Station Bldg 236, Rm 133","DSN 644-4753"],["USMC and Navy at a USMC base","Foster Bldg 495","DSN 645-0922"],["","Courtney Bldg 4311","DSN 622-5802"],["","Hansen Bldg 2137","DSN 623-7029"]])}
<h2>On-base communities</h2><p>The official page has photos and floor plans for: <b>Kadena</b> (Chibana, Clark Vista, Jennings, Sebille Manor, Stearley Heights, Washington Heights), <b>Foster</b> (Futenma, North Foster Tower, Plaza), <b>Courtney</b> (Camp Courtney Tower, Camp McTureous) and <b>Kinser</b> (Kinser Tower, Kinser Heights). Schools are DoDEA Pacific South. Feedback goes through ICE on the official page.</p>
<h2>What the office does not do</h2><ul class="plain"><li><b>No approved-agency list that we could find.</b> When an agency says it is “approved” or “military-friendly”, that is the agency’s own claim.</li><li><b>It cannot negotiate your rent</b> or give you a Japanese lease in English.</li></ul>
<h2>Questions to bring</h2><ul class="plain"><li>What must I submit before and after signing a lease?</li><li>What is the early-termination wording I need for PCS or transfer orders?</li><li>Which up-front costs can be reimbursed or advanced?</li><li>Am I eligible for issued appliances and loaner furniture?</li><li>What is my waiting-list date and category?</li></ul>
<h2>Official offices and portals in our directory</h2><div class="cards">{cards}</div>
<p class="sub" style="margin-top:20px">Next: <a href="{url("/checklist/")}">first-time renter checklist</a> · <a href="{url("/costs/")}">up-front costs</a> · <a href="{url("/guides/")}">all guides</a></p></div>'''
    page("/housing-office/", "Housing office guide for Okinawa military family housing", "Who must live on base, how to apply, contacts and hours, pets, mold tips and maintenance numbers from the Okinawa housing office.", body, cur="housing-office")

GLOSS = [
 ("Floor plans: the alphabet soup", [
  ("1R / ワンルーム", "wan-rūmu", "One room that does everything: sleep, cook, stare at the wall.", "Studio. The kitchen is “a section of wall with ambitions”."),
  ("1K", "wan-kē", "One room plus a separate kitchen (K).", "A door exists between you and the stove. Marriages have survived on less."),
  ("1DK / 2DK", "wan-dī-kē", "Bedroom(s) plus a dining-kitchen (DK): the kitchen has room for a table.", "A table. Be honest, it will hold mail."),
  ("1LDK / 2LDK / 3LDK", "wan-eru-dī-kē", "Living-dining-kitchen (LDK) plus the number of bedrooms.", "Labelling rules set minimum sizes for an “LDK” (about 8 jō with one bedroom, about 10 with two or more), so the L cannot be pure fiction. Close, though."),
  ("S / サービスルーム / 納戸", "sābisu rūmu / nando", "A room that does not meet the legal definition of a bedroom, often because it has no window.", "Storage with a hint of hope. Fine for bikes and a sad treadmill."),
  ("和室 / 洋室", "washitsu / yōshitsu", "Japanese-style room (tatami) / Western-style room (flooring).", "One lets you sit on the floor; the other makes you feel less guilty about sitting on the floor."),
  ("ロフト", "rofuto", "A sleeping or storage loft above the main room.", "Great for storage. Bring a short friend, or a short temper."),
 ]),
 ("Size and location", [
  ("畳 (jō)", "jō", "One tatami mat. Listing rules treat 1 jō as 1.62 m² (about 17.4 sq ft), so 6 jō is about 9.7 m² (105 sq ft).", "Japan’s favourite unit of measurement, because feet are for the floor."),
  ("㎡ / 坪 (tsubo)", "heibei / tsubo", "Square metres / an old unit of 3.3 m² (two tatami).", "Land is often sold in tsubo, which is why the real-estate agent speaks in a unit nobody else uses."),
  ("専有面積", "sen’yū menseki", "The floor area that is actually yours, not counting balcony or shared areas.", "The honest number. The brochure may use a more optimistic one."),
  ("築年数", "chiku nensū", "Age of the building. Anything built after mid-1981 follows the newer earthquake rules.", "Older is not automatically worse. But ask about the A/C and the bathroom."),
  ("駅徒歩", "eki toho", "Walking minutes to the nearest station, calculated at 80 metres a minute.", "In Okinawa this mostly matters near the Naha monorail. Elsewhere: ask about the car."),
  ("角部屋", "kado-beya", "A corner unit with windows on two sides.", "More light, fewer neighbours, same rent if you ask nicely."),
  ("南向き", "minami-muki", "Faces south for sunshine.", "In Okinawa, “sunshine” and “air-conditioning bill” are close relatives."),
 ]),
 ("Money words", [
  ("家賃 / 賃料", "yachin / chinryō", "Monthly rent.", "The only line that is every month. The rest is a one-time tour of your wallet."),
  ("管理費・共益費", "kanrihi / kyōekihi", "A monthly fee for building upkeep and shared areas.", "Rent’s sidekick. Always ask whether it is inside the number you saw."),
  ("敷金", "shikikin", "A security deposit, refundable after restoration costs.", "Refundable, in theory and in good weather."),
  ("礼金", "reikin", "“Key money”: a non-refundable thank-you to the landlord.", "A tip you pay before the service. Some listings offer “礼金なし” (none), and you may clap."),
  ("仲介手数料", "chūkai tesūryō", "The agency fee. By law, capped at one month of rent plus tax for a rental.", "Ask early, and ask politely, whether it is the full month."),
  ("保証会社", "hoshō gaisha", "A guarantee company that stands in for a personal guarantor.", "A stranger that agrees to vouch for you. Strangely common, usually fee-based."),
  ("火災保険", "kasai hoken", "Fire / renter’s insurance, usually required.", "Covers fire, water and the time you drop a pot on the neighbour’s ceiling."),
  ("鍵交換", "kagi kōkan", "Changing the lock before you move in.", "A new lock for a new you."),
  ("更新料", "kōshinryō", "A fee some leases charge to renew.", "Surprise renewal! Check the lease before you fall in love."),
  ("フリーレント", "furī rento", "Some months of free rent as a move-in offer.", "Free, with fine print. Read the fine print."),
  ("初期費用", "shoki hiyō", "Total up-front costs.", "The number the monthly rent has been hiding. Our <a href='%s'>estimator</a> shows it." % url("/costs/")),
 ]),
 ("Contract and paperwork", [
  ("重要事項説明", "jūyō jikō setsumei", "The explanation of key terms that a licensed agent reads to you before you sign. It is required.", "A very formal, very long reading. Ask for it in English, or bring a friend and snacks."),
  ("賃貸借契約書", "chintai-shaku keiyaku-sho", "The lease contract.", "Keep a copy. Photograph every page."),
  ("特約", "tokuyaku", "A special clause added to the lease.", "The place where move-out cleaning charges like to hide. Read these twice."),
  ("原状回復", "genjō kaifuku", "Restoring the home to its condition at move-in, within what the rules allow.", "Your move-in photos are the star witness."),
  ("解約予告", "kaiyaku yokoku", "Advance notice to end the lease, often one month.", "Mark the date. Do not trust your memory in packing season."),
  ("中途解約", "chūto kaiyaku", "Ending the lease early.", "For PCS or transfer orders, get the exit wording in writing."),
  ("入居審査", "nyūkyo shinsa", "Screening before the lease is approved.", "A polite interview with paperwork. Be calm and honest."),
  ("内見", "naiken", "Viewing the home.", "Go look. Photos have a flattering lens."),
  ("即入居可", "soku nyūkyo ka", "Ready to move in right away.", "A unicorn. Then check the details."),
  ("外国人可", "gaikokujin ka", "Foreign tenants are welcome.", "The best three words on a listing. Ask what they mean in practice."),
 ]),
 ("Features and Okinawa surprises", [
  ("外人住宅", "gaijin jūtaku", "“Foreigner housing”: detached houses first built for U.S. residents, often concrete, roomy, with a carport.", "A classic Okinawa home with charm. Check age, A/C, and maintenance."),
  ("RC造 / 木造", "āru-shī-zukuri / mokuzō", "Reinforced concrete / wood construction.", "Concrete suits typhoons and does not argue with them."),
  ("雨戸 / シャッター", "amado / shattā", "Storm shutters.", "Very good friends in typhoon season. Ask if they work."),
  ("カビ", "kabi", "Mold.", "Okinawa humidity’s favourite hobby. Open closets before you sign, not after."),
  ("塩害", "enGai", "Salt damage near the coast.", "The reason the balcony rail looks aged. Ask about it near the sea."),
  ("受水槽 / 高架水槽", "jusuisō / kōka suisō", "A water tank on the roof or ground that supplies the building.", "Water pressure has a story. Ask who cleans the tank."),
  ("カースペース / 駐車場", "kā supēsu / chūshajō", "Parking space / lot.", "Measure it. Some American trucks think “space” is a suggestion."),
  ("オートロック", "ōto rokku", "An auto-locking entry door.", "Makes you feel safe and forget your keys."),
  ("追い焚き", "oidaki", "A bath that can reheat itself.", "The luxury you did not know you needed."),
  ("浴室乾燥", "yokushitsu kansō", "A bathroom dryer.", "A humidity weapon. Moldy towels will thank you."),
  ("ペット可 / 不可", "petto ka / fuka", "Pets allowed / not allowed.", "Always ask in writing, including breed, size and number."),
 ])]

def build_glossary():
    secs = ""
    for title, terms in GLOSS:
        items = "".join(f'<div class="gloss" data-t="{esc((a + " " + b + " " + c + " " + d).lower())}"><div class="g-term" lang="ja">{a}</div><div class="g-read">{b}</div><p class="g-mean">{c}</p><p class="g-joke">{d}</p></div>' for a, b, c, d in terms)
        secs += f'<section><h2>{title}</h2><div class="gloss-grid">{items}</div></section>'
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">{T("Home","ホーム")}</a> › Glossary</div>
<h1>The listing glossary: reading a Japanese rental ad without panic</h1>
<p class="sub">Japanese listings are dense, abbreviated and occasionally funny. Here is what the words mean, plus a bit of humour to take the edge off. The facts are meant to be accurate; the jokes are free. Confirm anything money-related with your agency.</p>
<div class="switcher"><label for="gloss-q"><b>Find a term</b></label><input id="gloss-q" type="search" placeholder="Type: reikin, 1LDK, 畳 …" autocomplete="off"><span id="gloss-count" class="sub" style="margin:0" aria-live="polite"></span></div>
{secs}<p id="gloss-none" class="empty" hidden>No match. Try the Japanese term, or a plain word like “deposit”.</p>
<p class="sub">Related: <a href="{url("/costs/")}">up-front costs</a> · <a href="{url("/checklist/")}">first-time renter checklist</a> · <a href="{url("/guide/")}">full renting guide</a>. Spot a mistake? <a href="{url("/suggest-edit/")}">Tell us</a>.</p></div>'''
    page("/glossary/", "Listing glossary: reading Japanese rental ads in Okinawa", "Plain-English meanings (with a little humour) of floor plans, fees, contract terms and Okinawa-specific features in Japanese rental listings.", body, cur="glossary")

def build_extra():
    build_share_experience(); build_shortlist(); build_compare()
    if LANG == "en":
        build_checklist(); build_costs(); build_housing_office(); build_glossary(); build_guides()

# ------------------------------------------------------------------ guides hub + five guides (EN only)
GUIDES = [
 ("move-in", "Move-in day guide", "Keys, photos, meters, utilities and your first week, in order."),
 ("rent-prices", "Rent and pricing guide", "What Okinawa rents look like, who sets them, and how to compare a quote."),
 ("avoid-problems", "Avoiding common problems", "Fee surprises, deposit disputes, mold, typhoon damage and lease traps, and how to prevent each."),
 ("living-in-okinawa", "Living in Okinawa basics", "Typhoons, humidity, trash, power, water and driving paperwork."),
 ("oha", "Overseas Housing Allowance (OHA) guide", "What OHA pays, the move-in allowance, the forms, and Okinawa’s May 2026 increase."),
]

def _src(items):
    li = "".join(f'<li><a href="{u}" rel="noopener nofollow">{t}</a>{(" — " + n) if n else ""}</li>' for t, u, n in items)
    return f'<h2>Sources</h2><ul class="plain tight">{li}</ul>'

def _guide(slug, title, desc, lede, inner, srcs, note="", related=()):
    rel = " · ".join(f'<a href="{url("/guides/" + s + "/")}">{t}</a>' for s, t, _ in GUIDES if s != slug and s in related) if related else ""
    body = f'''<div class="wrap pagehead prose"><div class="crumbs"><a href="{url("/")}">Home</a> › <a href="{url("/guides/")}">Guides</a> › {title}</div>
<h1>{title}</h1><p class="sub">{lede}</p>
<div class="callout info"><b>General information, reviewed 25 October 2026.</b> Rules depend on your service, status and orders, and they change. {note}Your housing office and finance office have the final say. This is not legal or financial advice.</div>
{inner}{_src(srcs)}
<p class="sub" style="margin-top:22px">Related: {rel} · <a href="{url("/checklist/")}">checklist</a> · <a href="{url("/costs/")}">up-front costs</a> · <a href="{url("/glossary/")}">glossary</a></p></div>'''
    page(f"/guides/{slug}/", f"{title} — Okinawa housing", desc, body, cur="guides")

def _tbl(head, rows):
    h = "".join(f"<th>{x}</th>" for x in head)
    r = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table class="data"><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>'

def _ul(items): return '<ul class="plain">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"

S_STRIPES_OHA = ("Stars and Stripes, 11 May 2026: Okinawa housing allowance increase", "https://www.stripes.com/theaters/asia_pacific/2026-05-11/oha-okinawa-kadena-air-force-kadena-21636999.html", "rates, increase, agency rent ranges")
S_KADENA_HS = ("Kadena: Housing shortage, what you should know", "https://www.kadena.af.mil/News/Display/Article/3948579/housing-shortage-what-you-should-know/", "")
S_KADENA_OFH = ("Okinawa Family Housing (Kadena)", "https://www.kadena.af.mil/Agencies/Okinawa-Family-Housing/", "")
S_OIST = ("OIST: Living in a Japanese house/apartment", "https://groups.oist.jp/node/6224", "mold, odor, move-out, power and water")
S_TYPHOON = ("Kadena Typhoon Guide (2020 edition)", "https://www.kadena.af.mil/Portals/40/documents/Typhoon%20Guide%20Vol%202.2020.pdf", "TCCOR levels and supply list")
S_OHA = ("My Air Force Benefits: Overseas Housing Allowance", "https://myairforcebenefits.us.af.mil/Benefit-Library/Federal-Benefits/Overseas-Housing-Allowance-(OHA)?serv=23", "")
S_TRASH = ("Stars and Stripes Okinawa: How to properly sort trash", "https://okinawa.stripes.com/travel/living-off-base-in-japan-how-to-properly-sort-trash.html", "")
S_VEH = ("Kadena: Vehicle documentation 101", "https://www.kadena.af.mil/News/Display/Article/770436/vehicle-documentation-101-what-you-need-to-drive-in-okinawa/", "undated and uses 2014–2015 examples; confirm current rules")
S_MOLD = ("Stars and Stripes: Mold complaints in Okinawa housing (c. 2003)", "https://www.stripes.com/living/mold-complaints-in-okinawa-housing-slowly-prompting-changes-1.10883", "old article, undated; used only for general lessons")

def g_move_in():
    inner = f'''<h2>The day before</h2>{_ul([
 "<b>Get the final fee list in writing</b> and pay only by the method it names. Keep every receipt. See <a href='%s'>up-front costs</a>." % url("/costs/"),
 "<b>Confirm the exact handover time and who meets you</b> (agent, landlord or both), and whether you need an interpreter.",
 "<b>Ask for the key count</b> and for any spare, mailbox, gate and carport keys or remotes.",
 "<b>Tell your housing office you are moving</b> and ask what lease paperwork and inspections they still need from you. <a href='%s'>Housing office guide</a>." % url("/housing-office/")])}
<h2>Move-in day, in order</h2>{_ul([
 "<b>Walk every room before you unpack.</b> Photograph walls, floors, ceilings, closets, bathroom, balcony and any stain, crack or smell, with the date visible. Open the closets: this is where mold shows first.",
 "<b>Test everything:</b> every A/C unit (cool and dry modes), hot water, shower pressure, toilet, drains, stove, lights, door locks, window latches and storm shutters.",
 "<b>Photograph the meters</b> (electricity, water, gas if any) so you are billed only from your start date.",
 "<b>Write a defect list</b> and send it to the agency by email the same day, with your photos. A written, dated list is your record when you move out. Japanese leases generally make the tenant responsible for returning the home to its move-in condition, so what you document now matters later (see the <a href='%s'>problem-avoidance guide</a>)." % url("/guides/avoid-problems/"),
 "<b>Ask who to call</b> for repairs, including after hours and after a typhoon, and save the number in your phone.",
 "<b>Keep the handover paper</b> and a signed copy of the lease in one folder, with photos of every page."])}
<h2>Your first week</h2>{_ul([
 "<b>Utilities:</b> ask the agency which companies serve the building and whether they will help you start electricity, water, gas and internet. Do not assume anything is already on in your name.",
 "<b>Trash:</b> learn your town’s categories and collection days before the first bag goes out. See <a href='%s'>living in Okinawa</a>." % url("/guides/living-in-okinawa/"),
 "<b>Mold prevention starts now:</b> ventilate, run the A/C dry mode, and use dehumidifiers in closets and bathrooms. Mold damage is charged at move-out (OIST).",
 "<b>Typhoon season prep:</b> if you move in between June and November, set up a three-day water and food kit and check the shutters. Okinawa sits in TCCOR 4 from 1 June to 30 November every year.",
 "<b>Allowances:</b> ask your finance office about the Move-In Housing Allowance and what receipts to keep. <a href='%s'>OHA guide</a>." % url("/guides/oha/"),
 "<b>Neighbors:</b> introduce yourself and learn the building rules. Walls absorb odors and sound; ventilate when cooking strongly and avoid smoking indoors (OIST)."])}
<h2>Your move-in kit</h2><p>Camera or phone with space, a notebook, a tape measure (for the carport and furniture), a power strip and an A-to-B adapter for older two-prong outlets (Japan uses 100 V), dehumidifier packs, and the agency’s emergency number.</p>'''
    _guide("move-in", "Move-in day guide", "A step-by-step move-in guide for renters in Okinawa: handover, inspection photos, utilities, trash and the first week.", "From handover to your first week: what to do, in order, so your deposit and your sanity survive.", inner, [S_OIST, S_TYPHOON, S_OHA], related=("avoid-problems", "living-in-okinawa", "oha"))

def g_rent():
    inner = f'''<p>There is no official, public rent index for Okinawa, so this page sticks to what we can source and tells you how to check the rest. We would rather leave a gap than invent a number.</p>
<h2>Who sets the rent</h2>{_ul([
 "<b>Agencies and owners set rents.</b> The Kadena housing commander said rents are set by agencies and property owners, not approved by the housing office, which reviews leases for consistency with housing policies (Stars and Stripes, May 2026).",
 "<b>Rents track the allowance.</b> The 18th Wing commander said landlords were matching the higher local civilian housing allowance, and that service members had been paying about $300 a month out of pocket on average before the May 2026 increase.",
 "<b>Owners can raise rents between tenants.</b> One agency quoted by Stripes said it may raise rents after tenants move out, citing rising maintenance and property tax costs."])}
<h2>What we can source</h2>{_tbl(["Item","Reported figure","Source and date"],[
 ["2–3 bedroom units at Ishiken Housing (about 150 military families)","$1,150 to $1,785 a month","Stars and Stripes, 11 May 2026"],
 ["Seaside Housing (about 650 military families) and Joy Housing (about 600)","Rents set by market prices, unit size and owner wishes; no range published","Stars and Stripes, 11 May 2026"],
 ["Rental allowance, E-1 to E-4 with dependents","$1,403.46","Stars and Stripes, as of 1 May 2026"],
 ["Rental allowance, E-5, O-1, O-2 with dependents","$1,439.44","same"],
 ["Rental allowance, E-6 to E-8, O-3 with dependents","$1,655.36","same"]])}
<p class="sub">Allowances are what the government pays, not what homes cost. Allowances change, and an increase was announced from 16 May 2026. Use the <a href="{url("/guides/oha/")}">OHA guide</a> and the official calculator for your own numbers.</p>
<h2>What moves the price</h2>{_ul([
 "<b>Distance to your gate.</b> Use the <a href='%s'>base-distance search</a> to see who is close. Closer often costs more." % url("/find/"),
 "<b>Age and condition.</b> Older concrete homes can be roomy and charming, with older A/C and plumbing.",
 "<b>Bedrooms and parking.</b> Check the carport against your vehicle and ask about extra parking fees.",
 "<b>Management fee.</b> Ask whether the monthly management or common fee is inside the advertised rent.",
 "<b>Furnishing and appliances.</b> Eligible off-base residents may receive issued major appliances; ask the housing office before you buy any (<a href='%s'>housing office guide</a>)." % url("/housing-office/")])}
<h2>How to compare two quotes</h2>{_ul([
 "<b>Ask for the monthly total</b> (rent + management fee + parking) and the <b>up-front total</b> (<a href='%s'>use the estimator</a>)." % url("/costs/"),
 "<b>Compare the whole stay, not just the monthly figure.</b> A lower rent with high exit charges, or a renewal fee, can cost more.",
 "<b>Convert at today’s rate and re-check.</b> Rent is in yen; allowances are adjusted for exchange rates, so your out-of-pocket changes when the yen moves.",
 "<b>Get three quotes</b> from agencies in the <a href='%s'>directory</a>, including one <a href='%s'>Japanese-run</a> agency if you can manage the paperwork." % (url("/find/"), url("/local-agencies/"))])}
<h2>Gaps we are filling</h2><p>We do not yet publish rent ranges by town or home type. If you have a recent lease or quote you are willing to share without personal details, <a href="{url("/suggest-edit/")}">tell us</a> and we will consider adding anonymous ranges once there are enough to avoid identifying anyone.</p>'''
    _guide("rent-prices", "Rent and pricing guide", "Who sets rents in Okinawa, what figures are published, and how to compare a rental quote.", "What Okinawa rents look like, who sets them, and how to compare a quote without being surprised later.", inner, [S_STRIPES_OHA, S_KADENA_OFH], note="Figures are as reported by Stars and Stripes on 11 May 2026 and may be out of date. ", related=("oha", "avoid-problems"))

def g_avoid():
    rows = [
     ("Surprise up-front fees","Fees are listed late, or in Japanese only.","Get a written breakdown of every fee before you pay anything. The agency fee for a rental is capped by law at one month of rent plus tax. <a href='%s'>Estimator</a>." % url("/costs/")),
     ("Deposit taken for “cleaning” or damage","Tenants are generally expected to return the home to its move-in condition, and mold and odor can be charged (OIST).","Document the home on move-in with dated photos and a written defect list. Ventilate, clean, and photograph at move-out."),
     ("Mold in closets, bathroom and walls","Okinawa is humid all year, and mold spreads fast in summer.","Ventilate daily, run A/C dry mode, use dehumidifiers, keep furniture off walls, clean the bathroom often. Report persistent moisture to the agency in writing."),
     ("Mold in the A/C","Heavy year-round A/C use can grow mold inside units; an older Stripes report traced Kadena cases to insulation and drip pans.","Ask when the A/C was last cleaned. Do not run a unit you suspect is contaminated; tell the agency and your housing office."),
     ("Typhoon damage and gaps in who pays","Storm damage and outages, with unclear responsibility.","Ask in writing who handles repairs after a storm and how to reach them. Test shutters on move-in. Keep renter’s insurance."),
     ("“Approved” or “military-friendly” claims","These are the agency’s own words. We found no public official list of approved agencies.","Confirm with the housing office, and check the broker licence on the MLIT register (linked on every listing)."),
     ("Lease has no military exit clause","PCS and transfer orders can end a stay early.","Get the early-termination wording in writing and have the housing office review the lease before you sign."),
     ("Rent raised or fee added at renewal","Owners can raise rents between tenants, and some leases charge a renewal fee.","Read the renewal and notice terms before signing. Ask what the renewal fee is."),
     ("Paying before seeing the home","Pressure to pay a holding fee for a home you have not viewed.","Never pay before you have viewed the home and received the written fee list."),
     ("Language gap in the contract","You sign something you do not understand.","Ask for the key-terms explanation (重要事項説明) in English or with an interpreter, and ask for the English summary in writing."),
     ("Parking that does not fit","Carports can be tight for large vehicles.","Measure before signing and ask about extra parking fees."),
     ("Neighbor friction over noise or odor","Walls absorb odor and carry sound.","Ventilate when cooking, avoid smoking indoors, learn trash rules, introduce yourself to neighbors.")]
    inner = f'''<p>These are the pitfalls we think are worth planning for. Each entry says why it happens and how to avoid it. Where a claim comes from a source it is linked below; the rest is general good practice, not a statistic about any agency.</p>
{_tbl(["Problem","Why it happens","How to avoid it"],[list(r) for r in rows])}
<h2>If something goes wrong</h2>{_ul([
 "<b>Write it down.</b> Email the agency with dated photos. A written record is worth more than a phone call.",
 "<b>Call the housing office early,</b> especially for health concerns or unresolved repairs. For on-base homes, damage goes to 634-HOME (4663). See the <a href='%s'>housing office guide</a>." % url("/housing-office/"),
 "<b>Ask for a Japanese-speaking helper</b> from your command or a local community group. Many disputes are misunderstandings.",
 "<b>For an agency problem,</b> note the broker licence number and use the MLIT register linked on the listing. You can also <a href='%s'>share your experience</a>, and we publish only moderated, factual summaries." % url("/share-experience/")])}'''
    _guide("avoid-problems", "Avoiding common problems", "How to avoid fee surprises, deposit disputes, mold, typhoon damage and lease traps when renting in Okinawa.", "Fee surprises, deposit disputes, mold, storm damage and lease traps: why they happen and how to avoid each.", inner, [S_OIST, S_MOLD, S_KADENA_HS, S_STRIPES_OHA], related=("move-in", "living-in-okinawa", "rent-prices"))

def g_living():
    inner = f'''<h2>Typhoons and storm season</h2>{_ul([
 "<b>Okinawa is in TCCOR 4 every year from 1 June to 30 November.</b> Have 72 hours of food and water on hand.",
 "<b>As a storm approaches,</b> the Kadena typhoon guide says to secure balcony and outdoor items, fill the car’s gas tank, keep documents accessible, clear gutters and drains, and sandbag door sills. Near landfall: move things away from windows, fill the bathtub, and set the fridge and freezer colder.",
 "<b>Supplies:</b> one gallon of water per person per day for at least three days, food, a battery radio, flashlight, first aid kit, medications, and pet supplies.",
 "<b>After a storm:</b> wait for the all-clear before cleaning up debris.",
 "<b>Water quality:</b> typhoons can lower tap-water quality. When reports are issued, boil water or use bottled water (OIST)."])}
<h2>Humidity and mold</h2><p>Okinawa is humid all year. Ventilate often, use dehumidifiers or the A/C dry mode, and keep leather, clothes and books where air moves. Wipe the bathroom and open closets. Mold damage can be charged at move-out.</p>
<h2>Power, water and plumbing</h2>{_ul([
 "<b>Power:</b> Japan uses 100 V. Most outlets take two-prong A-type plugs, and some older buildings do not accept three-prong plugs. A-to-B adapters are sold at electronics stores.",
 "<b>Tap water</b> is safe to drink, though it may taste different.",
 "<b>Drains:</b> do not pour cooking oil or chemicals down sinks or toilets."])}
<h2>Trash</h2><p>Rules differ by town and change, so get your town’s English or Japanese guide on day one. Common categories are combustible, non-burnable, hazardous, recyclables and bulk trash.</p>{_ul([
 "Rinse recyclable bottles and remove caps and labels; tie paper with string.",
 "Wrap broken glass and dishes in newspaper where the town requires it.",
 "Bulk items such as furniture and bicycles usually need advance registration and a fee.",
 "Do not assume your last town’s rules apply."])}
<h2>Driving and your car</h2><p>SOFA-status drivers need current documents in the vehicle, and mistakes carry points and impoundment. The Kadena article lists: SOFA license, Japanese car title, military registration, government of Japan inspection decal, compulsory insurance (JCI) papers, property damage insurance papers, and the road-tax receipt and decal. Expired items add license points, and some add impoundment and suspension. The article is undated, so confirm current requirements with your vehicle registration office.</p>
<h2>Living in a Japanese-style home</h2>{_ul([
 "<b>Noise and smell travel.</b> Ventilate after strong cooking, avoid indoor smoking, and keep late-night noise low.",
 "<b>Introduce yourself</b> to neighbors and learn building rules, including carport and bicycle rules.",
 "<b>Keep the lease terms handy:</b> notice periods, renewal, and who to call for repairs."])}
<p class="sub">Not covered yet: healthcare, schools, utilities providers, internet and phone plans, and local customs in more depth. We add pages once we can source them.</p>'''
    _guide("living-in-okinawa", "Living in Okinawa basics", "What to know about typhoons, humidity, trash, power, water and driving paperwork when living in Okinawa.", "The everyday things nobody tells you about until the first typhoon: weather, humidity, power, trash and car paperwork.", inner, [S_TYPHOON, S_OIST, S_TRASH, S_VEH], related=("move-in", "avoid-problems"))

def g_oha():
    inner = f'''<h2>What OHA is</h2><p>The Overseas Housing Allowance helps service members who rent on the local economy overseas when on-base or government housing is not provided. It has several parts.</p>
{_tbl(["Part","What it is"],[
 ["<b>Rental allowance</b>","A monthly payment toward rent. The Air Force benefits page says rates are designed so that 80% of members with dependents have their rent fully reimbursed."],
 ["<b>Utility / recurring maintenance allowance</b>","A monthly payment for members who pay utilities and minor recurring repairs. Rates come from an annual survey of prior-year spending."],
 ["<b>Move-In Housing Allowance (MIHA)</b>","One-time payments: <i>Miscellaneous</i> (average move-in costs such as appliances and utility hookups), <i>Rent</i> (dollar-for-dollar reimbursement of realtor fees), and, only at authorized locations, <i>Security</i> and <i>Infectious Disease</i> upgrades."]])}
<h2>Okinawa rates, as reported in May 2026</h2>{_tbl(["Rank group","Rental allowance (with dependents)","Reported increase from 16 May 2026"],[
 ["E-1 to E-4","$1,403.46","about $396 for E-4 and below"],
 ["E-5, O-1, O-2","$1,439.44","about $504"],
 ["E-6 to E-8, O-3","$1,655.36","about $450"]])}
<p>Utility and maintenance allowance for all ranks: $661.56 with dependents, $496.17 without. Without dependents the rental allowance is lower (about $140 less for E-1 to E-4, about $1,300 for E-5/O-1/O-2 and about $1,500 for E-6 to E-8/O-3, as reported).</p>
<p class="sub">These come from a Stars and Stripes article dated 11 May 2026. The increase applies to active-duty members on Okinawa; U.S. Forces Japan said it had nothing to announce about elsewhere in Japan. Rates change, so confirm your exact amount with the DTMO OHA calculator and your finance office.</p>
<h2>The paperwork</h2>{_ul([
 "<b>DD Form 2367</b> (Individual OHA Report), with a copy of your lease, goes to your approving official. File a new one whenever your housing information changes.",
 "<b>DD Form 2556</b> (Move-In Housing Allowance Claim) is for MIHA Rent, Security and Infectious Disease claims.",
 "Keep every receipt and the lease. Accurate expense records and survey participation affect utility and move-in amounts."])}
<h2>How to get the most from it</h2>{_ul([
 "<b>Check your numbers before you sign.</b> Ask your finance office what your allowance will be for the home you are considering.",
 "<b>Ask which up-front costs MIHA covers</b>, such as the agency fee, before you pay it.",
 "<b>Keep records.</b> Photos of receipts and the lease help if something is questioned.",
 "<b>Tell your housing office</b> if your lease or rent changes."])}
<h2>What we could not confirm</h2><p>We could not verify how your payment changes when rent is above or below your allowance, or the current official rate tables, because the sources we could reach do not say. Use the official DTMO calculator and your finance office for those.</p>'''
    _guide("oha", "Overseas Housing Allowance (OHA) guide", "How the Overseas Housing Allowance works in Okinawa: rental and utility allowance, move-in allowance, forms and the May 2026 increase.", "What OHA pays, what the move-in allowance covers, which forms to file, and what changed in Okinawa in May 2026.", inner, [S_OHA, S_STRIPES_OHA, S_KADENA_HS], note="OHA applies to eligible service members, not to every renter. ", related=("rent-prices", "move-in"))

def build_guides():
    g_move_in(); g_rent(); g_avoid(); g_living(); g_oha()
    cards = "".join(f'<div class="gloss"><div class="g-term"><a href="{url("/guides/" + s + "/")}">{t}</a></div><p class="g-mean">{d}</p></div>' for s, t, d in GUIDES)
    more = "".join(f'<div class="gloss"><div class="g-term"><a href="{url(p)}">{t}</a></div><p class="g-mean">{d}</p></div>' for p, t, d in [
        ("/checklist/", "First-time renter checklist", "A tick-as-you-go list from search to move-out."),
        ("/costs/", "Up-front costs", "An estimator for deposit, key money, fees and insurance."),
        ("/housing-office/", "Housing office guide", "What the office does, contacts, hours and questions to bring."),
        ("/glossary/", "Listing glossary", "Floor plans, fees and contract terms, decoded with a little humour."),
        ("/guide/", "Renting guide", "The market, contract terms and questions to ask an agency.")])
    body = f'''<div class="wrap pagehead"><div class="crumbs"><a href="{url("/")}">Home</a> › Guides</div><h1>Guides for renters in Okinawa</h1>
<p class="sub">Plain-language guides for the part after you find an agency: what things cost, what to do on move-in day, what to watch for, and how Okinawa living differs. Each page lists its sources and review date.</p>
<h2>New guides</h2><div class="gloss-grid">{cards}</div><h2>Also useful</h2><div class="gloss-grid">{more}</div></div>'''
    page("/guides/", "Okinawa housing guides — move-in, rent, OHA, problems, living", "Guides for renters in Okinawa: move-in day, rent and pricing, OHA, avoiding common problems and everyday living.", body, cur="guides")
