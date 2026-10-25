"""Service catalogue: slug -> display info. Used by the generator and the validator.

This file (plus data/locations.csv, data/sources.csv and config.json) is everything that makes this site
"about housing agencies". To reuse the template for another topic, replace the SERVICES list, the VERIF/KIND
wording and the long-form pages in build_site.py.
"""
SERVICES = [
 # slug, EN name, JA name, group, one-line, about, tip for newcomers
 ("rent-house", "Houses & duplexes", "一戸建て・デュプレックス", "Long-term rentals",
  "Stand-alone houses and duplexes — the most common choice for families.",
  "Detached houses and two-unit duplexes make up much of the rental stock used by families in Okinawa. They are usually "
  "smaller than U.S. homes, often come without central heating or cooling, and may have a carport rather than a garage. "
  "Agencies that handle these homes typically list them by nearest base and by number of bedrooms.",
  "Ask whether the unit is already inspected and registered with your housing office, what is included (appliances, lights, "
  "air-conditioners are often not), and how many parking spaces come with it."),
 ("rent-apartment", "Apartments & condos", "アパート・マンション", "Long-term rentals",
  "Apartment buildings and condominiums, from studios to family-size units.",
  "Apartments suit single members, couples and short assignments. Newer buildings often include a management or common-area "
  "fee in the monthly cost; older ones may not.",
  "Check the monthly management/common fee (管理費・共益費), parking, and whether pets are allowed before you travel to view."),
 ("short-stay", "Furnished & short-term stays", "家具付き・短期滞在", "Short stays",
  "Furnished weekly and monthly units, useful while you wait for a long-term home.",
  "Newly arrived families can wait weeks for a home. Furnished short-term units bridge that gap; some agencies quote "
  "military or temporary-lodging rates and allow pets.",
  "Ask what the rate covers (utilities, housekeeping, linens), the minimum stay, and whether the unit works with a temporary lodging allowance."),
 ("buy-sell", "Buying & selling", "売買仲介", "Buying & selling",
  "Agencies that also help you buy a house, condo or land.",
  "Some agencies broker purchases as well as rentals, including help for foreign residents with visas or military status. "
  "Buying in Japan has its own rules on financing, taxes and inspections.",
  "Use a licensed broker (see the licence number on each listing) and ask for the written explanation of important matters (重要事項説明) in English if you need it."),
 ("management", "Property management", "賃貸管理", "Services",
  "Agencies that manage rental homes for owners — useful if you also own and want to rent out.",
  "Management agencies collect rent, arrange repairs and handle tenant issues for property owners. If you are renting, the "
  "managing agency is often who you call about repairs.",
  "Ask who handles maintenance requests and how to reach them after hours or after a typhoon."),
 ("relocation", "Move-in & relocation help", "入居・引越しサポート", "Services",
  "Pick-up for viewings, utility set-up, bilingual contract support.",
  "Several agencies will drive you to view homes, help connect electricity, water and internet, or explain the contract in English.",
  "Ask exactly what is included and whether it costs extra; help with set-up is not the same as legal advice on your lease."),
 ("official", "Official housing offices & portals", "公的な住宅窓口・ポータル", "Official help",
  "Government housing referral offices and the portals that list homes for U.S. Forces families.",
  "Service members and DoD civilians are generally told to check in with their installation housing office before signing "
  "an off-base lease. These offices can answer rules questions that no agency can.",
  "Contact your housing referral office first. Their rules depend on your service, status and rank, and they change."),
]
SVC = {d[0]: dict(slug=d[0], en=d[1], ja=d[2], group=d[3], blurb=d[4], about=d[5], tip=d[6]) for d in SERVICES}
GROUPS = ["Long-term rentals", "Short stays", "Buying & selling", "Services", "Official help"]
VERIF = {
 "A": ("Checked Oct 2026", "Details confirmed against the agency's or office's own current web page."),
 "B": ("Listed — not independently confirmed", "Found on a directory, a news report or an older page; not yet confirmed against the agency's own current page."),
 "C": ("Older source — not re-verified", "Appears only in an older list. Details have not been re-checked."),
 "D": ("Lead — details unconfirmed", "An agency we know exists, but we could not confirm where it is or whether it is operating."),
}
STATUS = {"active": "Active", "unverified": "Unverified", "needs_check": "Needs check", "closed": "Closed", "moved": "Moved"}
KINDS = ["agency", "organization", "portal"]

# ---------------------------------------------------------------- Japanese layer (needs a native-speaker review before launch)
GROUPS_JA = {"Long-term rentals": "賃貸（長期）", "Short stays": "短期滞在", "Buying & selling": "売買", "Services": "サービス", "Official help": "公的な窓口"}
REGIONS_JA = {"south": "南部（那覇・以南）", "central": "中部（宜野湾〜うるま）", "north": "北部（やんばる）", "islands": "離島", "": "所在地未掲載"}
VERIF_JA = {
 "A": ("2026年10月確認済み", "会社または窓口の最新の公式ページで内容を確認しています。"),
 "B": ("掲載あり・未確認", "ディレクトリ、報道、または古いページに基づく情報で、公式ページとの照合はまだです。"),
 "C": ("古い情報・未再確認", "古い一覧にのみ掲載されている情報で、再確認していません。"),
 "D": ("情報のみ・詳細未確認", "存在は把握していますが、所在地や営業状況を確認できていません。"),
}
KIND_JA = {"agency": "不動産会社", "organization": "公的窓口", "portal": "ポータル"}
FOCUS_JA = {"Military families": "米軍関係者向け", "General / foreign residents": "一般・外国人向け", "Military & civilians": "米軍関係者・一般", "Short stays": "短期滞在",
            "Sales & renovation": "売買・リノベーション", "Official office": "公的窓口", "Listing portal": "掲載ポータル", "Local & foreign residents": "地元・外国人向け"}
SVC_JA = {
 "rent-house": ("戸建て・デュプレックスの賃貸（家族向けに多い選択肢）。",
  "沖縄で家族が借りる住宅には、一戸建てや2戸1のデュプレックスが多く含まれます。米国の住宅より小さめで、セントラル冷暖房がないことも多く、ガレージではなくカーポートが一般的です。取り扱い会社は、最寄りの基地や寝室数で物件を紹介することが多いです。",
  "住宅局への登録・検査が済んでいるか、設備（家電・照明・エアコンは付かないことが多い）、駐車台数を確認しましょう。"),
 "rent-apartment": ("スタジオから家族向けまで、アパート・マンションの賃貸。",
  "アパートは単身者、夫婦、短期赴任に向いています。新しい建物は管理費・共益費が家賃に含まれることがあります。",
  "月々の管理費・共益費、駐車場、ペット可否を内見の前に確認しましょう。"),
 "short-stay": ("長期の住まいが決まるまでの、家具付き週単位・月単位の物件。",
  "到着したばかりの家族は住まいが決まるまで数週間待つことがあります。家具付きの短期物件はそのつなぎになり、軍関係者向けの料金やペット可の会社もあります。",
  "料金に含まれるもの（光熱費・清掃・リネン）、最短滞在期間、臨時宿泊手当の対象になるかを確認しましょう。"),
 "buy-sell": ("賃貸に加えて、住宅・マンション・土地の購入を支援する会社。",
  "賃貸に加え、売買の仲介も行う会社があります。ビザや軍籍のある外国人の購入相談を扱う会社もあります。日本の不動産購入には、融資・税金・調査に独自のルールがあります。",
  "免許番号を確認し、必要に応じて重要事項説明を英語で受けられるか尋ねましょう。"),
 "management": ("オーナーから賃貸住宅の管理を受託する会社。",
  "管理会社は家賃の集金、修繕の手配、入居者対応を行います。借りる側にとっては、修理の連絡先になることが多いです。",
  "修繕依頼の窓口と、夜間・台風後の連絡方法を確認しましょう。"),
 "relocation": ("内見の送迎、ライフラインの手続き、バイリンガルの契約サポート。",
  "内見の送迎、電気・水道・インターネットの手続き、契約内容の英語説明などを行う会社があります。",
  "含まれる内容と追加料金の有無を確認しましょう。手続き支援は、契約に関する法的助言とは異なります。"),
 "official": ("米軍関係者向けの公的な住宅窓口と、物件を掲載するポータル。",
  "軍人・軍属は、民間住宅の契約前に所属基地の住宅窓口に確認するよう案内されるのが一般的です。窓口は、不動産会社が答えられない規則の質問に答えられます。",
  "まず住宅窓口（Housing Referral Office）に連絡を。規則は所属・身分・階級により異なり、変更されることがあります。"),
}
