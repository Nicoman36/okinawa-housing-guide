"""Municipality + district dictionaries and kana->romaji (Hepburn, simplified)."""
import re

# ja prefix -> (slug, English, region)
MUNI = {
 "那覇市": ("naha","Naha","south"), "浦添市": ("urasoe","Urasoe","south"),
 "豊見城市": ("tomigusuku","Tomigusuku","south"), "糸満市": ("itoman","Itoman","south"),
 "南城市": ("nanjo","Nanjo","south"), "南風原町": ("haebaru","Haebaru","south"),
 "八重瀬町": ("yaese","Yaese","south"), "与那原町": ("yonabaru","Yonabaru","south"),
 "西原町": ("nishihara","Nishihara","central"), "宜野湾市": ("ginowan","Ginowan","central"),
 "北谷町": ("chatan","Chatan","central"), "北中城村": ("kitanakagusuku","Kitanakagusuku","central"),
 "中城村": ("nakagusuku","Nakagusuku","central"), "沖縄市": ("okinawa-city","Okinawa City (Koza)","central"),
 "読谷村": ("yomitan","Yomitan","central"), "嘉手納町": ("kadena","Kadena","central"),
 "うるま市": ("uruma","Uruma","central"), "金武町": ("kin","Kin","north"),
 "宜野座村": ("ginoza","Ginoza","north"), "恩納村": ("onna","Onna","north"),
 "名護市": ("nago","Nago","north"), "本部町": ("motobu","Motobu","north"),
 "今帰仁村": ("nakijin","Nakijin","north"), "国頭村": ("kunigami","Kunigami","north"),
 "久米島町": ("kumejima","Kumejima","islands"), "宮古島市": ("miyako","Miyakojima (Miyako Is.)","islands"),
 "多良間村": ("tarama","Tarama","islands"), "石垣市": ("ishigaki","Ishigaki (Yaeyama)","islands"),
}
REGIONS = [("south","South (Naha & south)"),("central","Central (Ginowan – Uruma)"),
           ("north","North (Yanbaru)"),("islands","Outer islands")]
MUNI_SLUGS = {v[0]: (k, v[1], v[2]) for k, v in MUNI.items()}

def muni_of(addr: str):
    a = re.sub(r"^(?:〒?\d{3}-?\d{4}\s*)?(?:沖縄県)?(?:中頭郡|島尻郡|国頭郡|宮古郡|八重山郡)?", "", addr.strip())
    for k in sorted(MUNI, key=len, reverse=True):
        if a.startswith(k):
            return k, a[len(k):]
    return None, a

# districts I am confident of (prefix match after the municipality)
DISTRICT = {
 "naha": {"久米":"Kume","泉崎":"Izumizaki","首里":"Shuri","牧志":"Makishi","安里":"Asato","松山":"Matsuyama",
  "小禄":"Oroku","壺川":"Tsubogawa","若狭":"Wakasa","前島":"Maejima","繁多川":"Hantagawa","古島":"Kojima",
  "安謝":"Aja","銘苅":"Mekaru","おもろまち":"Omoromachi","真嘉比":"Makabi","国場":"Kokuba","識名":"Shikina",
  "垣花":"Kakinohana","三原":"Mihara","長田":"Osada","天久":"Amekubo","曙":"Akebono","宇栄原":"Uebaru",
  "田原":"Tabaru","金城":"Kinjo","具志":"Gushi","赤嶺":"Akamine","鏡水":"Kyomizu","奥武山町":"Onoyama-cho",
  "久茂地":"Kumoji","楚辺":"Sobe","寄宮":"Yoriyamiya","与儀":"Yogi","樋川":"Hikawa","古波蔵":"Kobagura",
  "壺屋":"Tsuboya","松川":"Matsukawa","仲井真":"Nakaigusuku","安次嶺":"Ashimine","大道":"Daido","字大道":"Daido",
  "上之屋":"Uenoya","港町":"Minatomachi","辻":"Tsuji","泊":"Tomari","松尾":"Matsuo","西":"Nishi","東町":"Higashimachi",
  "字安謝":"Aja","首里石嶺町":"Shuri-Ishimine","石嶺":"Ishimine","汀良":"Tera","当蔵":"Tougura","儀間":"Gima",
  "真和志":"Mawashi","宮城":"Miyagi","高良":"Takara","小禄":"Oroku","奥武山":"Onoyama","銘苅":"Mekaru"},
 "urasoe": {"牧港":"Makiminato","内間":"Uchima","仲間":"Nakama","宮城":"Miyagi","前田":"Maeda","港川":"Minatogawa",
  "安波茶":"Anbacha","勢理客":"Jiriki","城間":"Gusukuma","経塚":"Kyozuka","沢岻":"Takushi","屋富祖":"Yafuso",
  "当山":"Toyama","西原":"Nishihara","伊祖":"Iso","小湾":"Kowan","大平":"Ohira","田場":"Taba","港川":"Minatogawa"},
 "ginowan": {"大山":"Oyama","愛知":"Aichi","嘉数":"Kakazu","真栄原":"Maehara","宇地泊":"Uchitomari","我如古":"Gaja","上原":"Uehara",
  "普天間":"Futenma","大謝名":"Ojana","志真志":"Shimashi","長田":"Osada","伊佐":"Isa","赤道":"Akamichi","新城":"Shinjo","野嵩":"Notake","喜友名":"Kiyuna","真志喜":"Mashiki"},
 "okinawa-city": {"胡屋":"Goya","中央":"Chuo","松本":"Matsumoto","美里":"Misato","泡瀬":"Awase","山内":"Yamauchi","諸見里":"Moromizato","安慶田":"Agena","古謝":"Koja","知花":"Chibana","比屋根":"Hiyane","照屋":"Teruya","園田":"Sonda","越来":"Goeku","高原":"Takahara","上地":"Uechi","桃原":"Tobaru","大里":"Osato","白川":"Shirakawa","字":""},
 "chatan": {"北谷":"Chatan","北前":"Kitamae","宮城":"Miyagi","桑江":"Kuwae","砂辺":"Sunabe","美浜":"Mihama","謝苅":"Jakari","伊平":"Ihei","港":"Minato","浜川":"Hamagawa","玉代勢":"Tamayose","上勢頭":"Uwasedo"},
 "uruma": {"安慶名":"Agena","石川":"Ishikawa","具志川":"Gushikawa","勝連":"Katsuren","与那城":"Yonashiro","田場":"Taba","江洲":"Gesu","昆布":"Konbu","みどり町":"Midoricho","兼箇段":"Kanekadan","宮里":"Miyazato","川田":"Kawata","平良川":"Tairagawa"},
 "tomigusuku": {"瀬長":"Senaga","豊崎":"Toyosaki","真玉橋":"Matama","宜保":"Gibo","翁長":"Onaga","長堂":"Chodo","座安":"Zaan","保栄茂":"Bin","根差部":"Nezashi","與根":"Yone","上田":"Ueda","字":""},
 "itoman": {"西崎":"Nishizaki","潮崎町":"Shiozaki-cho","兼城":"Kanegusuku","糸満":"Itoman","西川町":"Nishikawa-cho","真栄里":"Maeza","大度":"Ufudo","摩文仁":"Mabuni","束里":"Tsukazan","喜屋武":"Kyan","字":""},
 "nanjo": {"大里":"Osato","佐敷":"Sashiki","玉城":"Tamagusuku","知念":"Chinen","馬天":"Batten","字":""},
 "haebaru": {"宮平":"Miyahira","津嘉山":"Tsukayama","兼城":"Kaneshiro","本部":"Motobu","新川":"Shinkawa","神里":"Kamisato","照屋":"Teruya","喜屋武":"Kyan","山川":"Yamakawa","宮城":"Miyagi"},
 "yomitan": {"座喜味":"Zakimi","古堅":"Furugen","渡慶次":"Tokeshi","比謝":"Hija","楚辺":"Soba","波平":"Namihira","長浜":"Nagahama","高志保":"Takashiho","都屋":"Toya","伊良皆":"Irage","瀬名波":"Senaha","喜名":"Kina","大湾":"Owan","宇座":"Uza","大木":"Oki"},
 "nishihara": {"西原":"Nishihara","小橋川":"Kobashigawa","翁長":"Onaga","嘉手苅":"Kategaru","幸地":"Koji","棚原":"Tanabaru","掛保久":"Kakeboku","我謝":"Gaja","小那覇":"Konaha","呉屋":"Goya","丸山":"Maruyama"},
 "yaese": {"字":"","具志頭":"Gushichan","東風平":"Kochinda","屋宜原":"Yagibaru","富盛":"Tomori","新城":"Shinjo","世名城":"Yonashiro","安里":"Asato"},
 "yonabaru": {"与那原":"Yonabaru","板良敷":"Itarashiki","東浜":"Higashihama","上与那原":"Kami-Yonabaru","字":""},
 "kitanakagusuku": {"ライカム":"Rycom","安谷屋":"Adaniya","島袋":"Shimabukuro","喜舎場":"Kishaba","大城":"Oshiro","荻道":"Ogido","渡口":"Toguchi","石平":"Ishihira"},
 "nakagusuku": {"南上原":"Minami-Uehara","和宇慶":"Wauke","当間":"Toma","伊舎堂":"Ishado","久場":"Kuba","新垣":"Aragaki","津覇":"Tsuha"},
 "nago": {"大南":"Dainan","為又":"Tamata","宇茂佐":"Umusa","世冨慶":"Yofuke","許田":"Kyoda","屋部":"Yabu","名護":"Nago","辺野古":"Henoko","宇茂佐の森":"Umusa-no-mori","字":""},
}

# --- kana -> romaji ---
_B = {"ア":"a","イ":"i","ウ":"u","エ":"e","オ":"o","カ":"ka","キ":"ki","ク":"ku","ケ":"ke","コ":"ko","サ":"sa","シ":"shi","ス":"su","セ":"se","ソ":"so",
 "タ":"ta","チ":"chi","ツ":"tsu","テ":"te","ト":"to","ナ":"na","ニ":"ni","ヌ":"nu","ネ":"ne","ノ":"no","ハ":"ha","ヒ":"hi","フ":"fu","ヘ":"he","ホ":"ho",
 "マ":"ma","ミ":"mi","ム":"mu","メ":"me","モ":"mo","ヤ":"ya","ユ":"yu","ヨ":"yo","ラ":"ra","リ":"ri","ル":"ru","レ":"re","ロ":"ro","ワ":"wa","ヲ":"o","ン":"n",
 "ガ":"ga","ギ":"gi","グ":"gu","ゲ":"ge","ゴ":"go","ザ":"za","ジ":"ji","ズ":"zu","ゼ":"ze","ゾ":"zo","ダ":"da","ヂ":"ji","ヅ":"zu","デ":"de","ド":"do",
 "バ":"ba","ビ":"bi","ブ":"bu","ベ":"be","ボ":"bo","パ":"pa","ピ":"pi","プ":"pu","ペ":"pe","ポ":"po","ヴ":"vu"}
_C = {"キャ":"kya","キュ":"kyu","キョ":"kyo","シャ":"sha","シュ":"shu","ショ":"sho","チャ":"cha","チュ":"chu","チョ":"cho","ニャ":"nya","ニュ":"nyu","ニョ":"nyo",
 "ヒャ":"hya","ヒュ":"hyu","ヒョ":"hyo","ミャ":"mya","ミュ":"myu","ミョ":"myo","リャ":"rya","リュ":"ryu","リョ":"ryo","ギャ":"gya","ギュ":"gyu","ギョ":"gyo",
 "ジャ":"ja","ジュ":"ju","ジョ":"jo","ビャ":"bya","ビュ":"byu","ビョ":"byo","ピャ":"pya","ピュ":"pyu","ピョ":"pyo","ティ":"ti","ディ":"di","ファ":"fa","フィ":"fi","フェ":"fe","フォ":"fo","ウィ":"wi","ウェ":"we","ウォ":"wo"}

def kana_to_romaji(s: str) -> str:
    out, i = [], 0
    s = re.sub(r"[\s　・]", "", s)
    while i < len(s):
        ch = s[i]
        if s[i:i+2] in _C:
            out.append(_C[s[i:i+2]]); i += 2; continue
        if ch == "ッ":
            nxt = _B.get(s[i+1:i+2], "") if i+1 < len(s) else ""
            if s[i+1:i+3] in _C: nxt = _C[s[i+1:i+3]]
            out.append(nxt[0] if nxt else ""); i += 1; continue
        if ch == "ー":
            i += 1; continue
        out.append(_B.get(ch, "")); i += 1
    r = "".join(out)
    r = r.replace("oo", "o").replace("ou", "o").replace("uu", "u")
    return r.capitalize()

def en_address(muni_ja: str, rest: str):
    """'Naha City — Kume 2-20-21' when the district is in the dictionary; else just the city."""
    slug, en, _ = MUNI[muni_ja]
    city = en.split(" (")[0]
    import unicodedata
    rest = unicodedata.normalize("NFKC", rest)
    suffix = "" if city.endswith("City") else ("City" if muni_ja.endswith("市") else ("Town" if muni_ja.endswith("町") else "Village"))
    d = DISTRICT.get(slug, {})
    rest = re.sub(r"^字", "", rest.strip())
    for k in sorted(d, key=len, reverse=True):
        if k and rest.startswith(k):
            tail = rest[len(k):].strip()
            nums = re.match(r"[\d０-９\-－ー丁目番地号]+", tail)
            n = nums.group(0).replace("丁目", "-").replace("番地", "-").replace("番", "-").replace("号", "").strip("-") if nums else ""
            return f"{d[k]}{(' ' + n) if n else ''}, {(city + ' ' + suffix).strip()}"
    return (city + " " + suffix).strip()
