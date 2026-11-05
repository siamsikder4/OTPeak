# -*- coding: utf-8 -*-
"""
DXA Premium Number Bot  —  fixed + redesigned UI
- Render fix: tiny HTTP server binds to $PORT (no more "No open ports detected")
- Secrets are read from environment variables (BOT_TOKEN, ADMIN_ID, API_KEY)
"""
import os
import re
import json
import time
import html
import random
import sqlite3
import threading
import traceback
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# Configuration (set these in Render → Environment)
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8271633124"))
API_2OO9_BASE = os.environ.get("API_BASE", "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api")
API_2OO9_KEY_DEFAULT = os.environ.get("API_KEY", "M4DDE8HGFJ9")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
BOT_USERNAME = ""

BOT_DATA_FILE = "bot_data.json"
USERS_LIST_FILE = "users_list.json"
SESSION_TTL = 900  # number stays assigned to a user for 15 minutes

DIV = "━━━━━━━━━━━━━━━━━"
THIN = "— — — — — — — — — —"

# Reply-keyboard button labels (single source of truth)
BTN_GET = "𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥"
BTN_TRAFFIC = "𝗖𝗛𝗘𝗖𝗞 𝗧𝗥𝗔𝗙𝗙𝗜𝗖"
BTN_INVITE = "𝗜𝗡𝗩𝗜𝗧𝗘 𝗙𝗥𝗜𝗘𝗡𝗗"
BTN_BALANCE = "𝗕𝗔𝗟𝗔𝗡𝗖𝗘"
BTN_LEADER = "𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗"
BTN_OWNER = "𝗢𝗪𝗡𝗘𝗥 𝗣𝗔𝗡𝗘𝗟"
MENU_TEXTS = [BTN_GET, BTN_TRAFFIC, BTN_INVITE, BTN_BALANCE, BTN_LEADER, BTN_OWNER]

# ==========================================
# Global state
# ==========================================
current_db_mode = "sqlite"
db_firebase = None
user_states = {}
user_cache = {}
user_active_sessions = {}   # number -> {"uid": int, "ts": float}
user_cooldowns = {}

voltx_auto_mode = True
voltx_keys = [API_2OO9_KEY_DEFAULT]
force_join_status = False
force_join_channels = []

otp_forward_groups = []
otp_button_link = "https://t.me/your_default_bot"
recent_success_otps = OrderedDict()   # signature -> True (ordered, trimmed safely)

voltx_dynamic_data = {}
recent_traffic = []
daily_stats = {"date": "", "numbers": 0, "otps": 0}
daily_user_otps = {"date": "", "users": {}}

cached_services_kb = None
cached_countries_kb = {}
cached_leaderboard_text = ""

processed_withdraws = set()
state_lock = threading.Lock()
file_lock = threading.Lock()
http = requests.Session()

bot_settings = {
    "withdraw_on": True,
    "min_withdraw": 10.0,
    "support_link": "",
    "w_group": "",
    "refer_reward": 0.2,
    "cooldown": 5,
    "num_req": 1,
    "w_methods": ["bKash", "Nagad"],
    "otp_default_rate": 0.15,
    "otp_service_rates": {},
    "main_channel_link": "",
}

# ==========================================
# Emoji / service / country data
# ==========================================
GLOBAL_BODY_EMOJIS = {
    "➖": "5870818207383686839", "🚫": "5334807341109908955", "😒": "5334763399299506604",
    "🖥": "5334880948259427772", "🌐": "5334590977837403844", "🌟": "5337102391244263212",
    "🕓": "5336983442125001376", "⌛": "5337172996211648018", "💬": "5337302974806922068",
    "🔐": "5337255927735163754", "🍏": "5337132498965010628", "❔": "5336850036145823599",
    "⚠️": "5336944168944047463", "🔥": "5337267511261960341", "💸": "5429612421977253466",
    "🥚": "5348390922507817684", "👨‍⚖": "5334763399299506604", "🐁": "5348494358205207761",
    "🧻": "5348486915026884464", "⚗": "5346311574221000149", "🛴": "5348075478634766440",
    "📊": "5353032893096567467", "🔢": "5226929552319594190", "👤": "5352861489541714456",
    "📁": "5352721946054268944", "🚀": "5352597830089347330", "💎": "5352838545826420397",
    "📍": "5352922460897452503", "👋": "5353027129250453493", "✅": "5352694861990501856",
    "1️⃣": "5352651766288652742", "2️⃣": "5355186458418257716", "3️⃣": "5352867219028091093",
    "4️⃣": "5352566657216714037", "5️⃣": "5353086880835474989", "6️⃣": "5354859211975071385",
    "7️⃣": "5352859127309707652", "8️⃣": "5352957533600389988", "9️⃣": "5353060913463204207",
    "🔤": "5352727417842606016", "📣": "5352980533150259581", "📤": "5353001161878182134",
    "✨": "5352552689983067014", "🔹": "5352638632278660622", "🎙": "5355102594886833928",
    "💴": "5352985330628730418", "📅": "5352585194295564660", "📴": "5352974971167611327",
    "✏️": "5395444784611480792", "📱": "5337132498965010628", "🔗": "5420517437885943844",
    "❌": "5420130255174145507", "⚙️": "5420155432272438703", "🫂": "5420145051336485498",
    "➕": "5420323438508155202", "🗑": "5422557736330106570", "🎁": "5420396762189831222",
    "➤": "5420618897898381296", "🏢": "5420156334215565595", "💳": "5190899075968441286",
    "📝": "5192739271886282680", "🛡": "5190447043545438788", "🤝": "5192805934073685937",
    "💰": "5190576863226933563", "👀": "5190645917711114179", "🕹": "5193100774988617665",
    "🟢": "5192812028632274956", "🧪": "5190781475468915802", "🎨": "5190751148704833975",
    "📂": "5257969839313526622", "🌍": "5780471598922337683", "📌": "5318986077455795572",
    "📢": "5789428375261023681", "🆔": "5226929552319594190", "📈": "5352877703043258544",
    "🔔": "5352980533150259581", "🏦": "5429612421977253466", "🧾": "5192739271886282680",
    "👨‍⚖️": "5334763399299506604", "🔍": "5463352748751753567", "🔑": "5197288647275071607",
    "🏆": "5240021484516185513", "🚦": "5429571662737611814", "👥": "5420145051336485498",
    "🎯": "5352922460897452503", "📶": "5429353834881261942", "⏳": "5337172996211648018",
    "🔸": "5429576112323732785", "🎉": "5420396762189831222", "💵": "5429612421977253466",
    "👑": "5352838545826420397", "↳": "5420618897898381296",
    "🇺🇸": "5913463998522592692", "🇺🇦": "5911406692007941050", "🇵🇱": "5913550391789752571",
    "🇰🇿": "5913724621433082323", "🇨🇳": "5913779335021466780", "🇦🇿": "5911197578640233518",
    "🇪🇺": "5911106310585193018", "🇦🇲": "5913272455866093666", "🇷🇺": "5913274246867456342",
    "🇺🇿": "5911051846104912282", "🇩🇪": "5911096835887337583", "🇯🇵": "5913293711659241040",
    "🇹🇷": "5910995113881901195", "🇧🇾": "5911011185649521599", "🇬🇧": "5913443365499703513",
    "🇮🇳": "5913754823643107921", "🇧🇷": "5911148568768418614", "🇿🇲": "5913564754160389778",
    "🇾🇪": "5913346492512341993", "🏴󠁧󠁢󠁷󠁬󠁳󠁿": "5911297801702084799", "🇻🇳": "5913428887164949581",
    "🇻🇦": "5911211932420938860", "🇻🇺": "5913511535220625585", "🇺🇾": "5913623088406204470",
    "🇦🇪": "5913726554168365343", "🇺🇬": "5913488939397681980", "🇹🇲": "5913315521503170180",
    "🇹🇳": "5911332947419468671", "🇹🇹": "5911228635548750294", "🇹🇬": "5913423260757790970",
    "🇹🇭": "5913617968805187987", "🇹🇿": "5911418949844603556", "🇹🇯": "5911287639809463107",
    "🇨🇭": "5913271227505448072", "🇸🇪": "5911156510162949403", "🇸🇿": "5913374525763883286",
    "🇸🇷": "5913275539652611719", "🇸🇩": "5911387497799094470", "🇪🇸": "5911193287967904547",
    "🇱🇰": "5911293163137406640", "🇸🇸": "5911406262511211744", "🇿🇦": "5911203119148044594",
    "🇸🇴": "5911397852965244436", "🇸🇧": "5911482712929080608", "🇸🇮": "5913431983836368644",
    "🇸🇰": "5913751666842145020", "🇸🇬": "5911531460808051849", "🇸🇱": "5911210450657218661",
    "🇸🇨": "5911185183364616913", "🇷🇸": "5913592598433369871", "🇸🇳": "5910995302860461643",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿": "5911460091336331851", "🇸🇹": "5913574331937462345", "🇸🇲": "5913587968458625465",
    "🇼🇸": "5913325971158602854", "🇰🇳": "5913691898077253637", "🇻🇨": "5911318941531116255",
    "🇱🇨": "5911243659344351824", "🇵🇸": "5913684768431541668", "🇷🇼": "5911455229433352234",
    "🇷🇴": "5913460373570195273", "🇶🇦": "5911260864983339619", "🇵🇷": "5911504350974317480",
    "🇵🇹": "5911023653939581472", "🇵🇭": "5911268638874145162", "🇵🇪": "5911207993935925780",
    "🇵🇾": "5911014265141072316", "🇵🇬": "5911107251183030903", "🇵🇦": "5913428968769327174",
    "🇵🇼": "5911283903187915549", "🇵🇰": "5913705895375672082", "🇴🇲": "5913570801474343473",
    "🇳🇴": "5913617397574537046", "🇳🇬": "5911143844304393105", "🇳🇪": "5911270086278124251",
    "🇳🇿": "5913640044937089340", "🇳🇱": "5913367645226275100", "🇳🇵": "5913496520014958723",
    "🇳🇦": "5911108535378252443", "🇲🇿": "5911333419865871464", "🇲🇦": "5911482111633658301",
    "🇲🇪": "5913239436157522151", "🇲🇳": "5911041383564580038", "🇲🇨": "5911245347266500057",
    "🇲🇩": "5913456847402045950", "🇲🇻": "5913501399097806832", "🇲🇱": "5911305266355245916",
    "🇲🇹": "5911023714069123567", "🇧🇲": "5913680005312811090", "🇲🇶": "5911378005921370347",
    "🇲🇭": "5913235935759175692", "🇲🇺": "5913291113204027321", "🇲🇽": "5913687302462246518",
    "🇫🇲": "5911271104185373336", "🇲🇾": "5913654360063087453", "🇰🇪": "5911154710571651231",
    "🇲🇬": "5913766918271012920", "🇲🇰": "5913394029210374721", "🇱🇺": "5913390842344640293",
    "🇱🇹": "5911172315642597775", "🇱🇮": "5911166650580734660", "🇱🇾": "5911236989260140996",
    "🇱🇷": "5913324167272337727", "🇰🇮": "5911294443037660118", "🇽🇰": "5911433681582429010",
    "🇰🇼": "5913290705182134003", "🇰🇬": "5911202161370337549", "🇱🇦": "5913718526874489279",
    "🇱🇻": "5913738489882480243", "🇱🇧": "5911504273664905447", "🇱🇸": "5911059881988723711",
    "🇮🇩": "5913479361620611038", "🇮🇷": "5911308891307643032", "🇮🇶": "5911382442622587735",
    "🇮🇪": "5913440715504881532", "🇮🇱": "5911471936856134692", "🇮🇹": "5913688444923547525",
    "🇯🇲": "5913232280742006526", "🇯🇴": "5913234136167878475", "🇮🇸": "5911047899029967246",
    "🇭🇺": "5913767635530551104", "🇭🇳": "5911406889576436289", "🇭🇹": "5913459789454643194",
    "🇬🇾": "5913579412883771480", "🇬🇼": "5911398694778836149", "🇬🇳": "5913471858312744319",
    "🇬🇹": "5913324858762072330", "🇬🇩": "5913228063084121946", "🇬🇷": "5911210399117611448",
    "🇬🇭": "5913391155877252952", "🇬🇪": "5913434771270144023", "🇬🇲": "5913657267755945883",
    "🇬🇦": "5911037896051137264", "🇫🇷": "5913605586414473124", "🇫🇮": "5911041344909873378",
    "🇫🇯": "5911393832875856716", "🇪🇹": "5911078333168227043", "🇩🇴": "5911152099231536123",
    "🇹🇱": "5911141915864076479", "🇪🇨": "5911273865849347408", "🇪🇬": "5913694831539916769",
    "🇸🇻": "5913238624408703010", "🏴󠁧󠁢󠁥󠁮󠁧󠁿": "5913475719488344315", "🇪🇪": "5910986042910969906",
    "🇩🇲": "5911377121158107430", "🇩🇯": "5911407709915190157", "🇩🇰": "5911206009661034712",
    "🇨🇾": "5911023550860366409", "🇭🇷": "5913692684056269311", "🇨🇷": "5911261745451635030",
    "🇨🇬": "5911338788574990168", "🇨🇩": "5913770362834783827", "🇰🇲": "5911338582416560604",
    "🇰🇭": "5913699998385573485", "🇨🇲": "5911172109484167745", "🇨🇦": "5913623736946265914",
    "🇨🇻": "5913571501554012193", "🇨🇫": "5913443245240619222", "🇹🇩": "5913299849167507310",
    "🇨🇿": "5911198691036764307", "🇨🇱": "5911470957603592832", "🇨🇴": "5913773060074246009",
    "🇧🇮": "5913766441529642752", "🇧🇼": "5911513782722499475", "🇧🇦": "5913700002680541032",
    "🇧🇴": "5913638795101606133", "🇧🇹": "5913236734623093021", "🇧🇯": "5913735869952430547",
    "🇦🇷": "5913573356979884082", "🇦🇺": "5913632326880858455", "🇦🇹": "5911338831524664592",
    "🇧🇸": "5911451643135660214", "🇧🇭": "5913581663446634403", "🇧🇩": "5911365056594973179",
    "🇧🇧": "5911016996740272263", "🇧🇪": "5913529642802745141", "🇧🇿": "5913355005137522807",
    "🇦🇬": "5913389025573475085", "🇦🇴": "5913753316109586411", "🇦🇩": "5911314702398396902",
    "🇩🇿": "5913782968563800236", "🇦🇱": "5911357458797826163", "🇦🇫": "5913492040364068694",
    "🇿🇼": "5911092502265336396", "🇨🇺": "5431551436502611633", "🇰🇵": "5434142701941437163",
    "🇻🇪": "5434009132753499322", "🇸🇾": "5433910876786670092", "🇲🇲": "5433666360003540231",
    "🇳🇮": "5334807849418003620", "🇰🇷": "5913371673905598425", "🇬🇶": "5911306279967529251",
    "🇬🇱": "5292014752283774878", "🇫🇴": "5296469342039327674", "🇨🇮": "5222233374948602940",
    "🇧🇳": "5911336409163109113", "🇧🇬": "5294329219965272288", "🇧🇫": "5913407764515786948",
    "🇪🇷": "5433723401464198287", "🇲🇼": "5433968339154122439", "🇲🇷": "5433859405898594234",
    "🇳🇷": "5434131139889478358", "🇸🇦": "4985897134424328239", "🇹🇴": "5433640100573491806",
    "🇹🇻": "5433684690923961019", "🇹🇼": "5366187256937726720", "🇭🇰": "5292166459118606932",
    "🇲🇴": "6323557758096377611",
}

# longest keys first so multi-codepoint emojis are replaced before their parts
_EMOJI_ITEMS = sorted(GLOBAL_BODY_EMOJIS.items(), key=lambda kv: len(kv[0]), reverse=True)


def apply_emojis(text):
    hidden = []

    def hide(m):
        hidden.append(m.group(0))
        return f"__TG_EMOJI_{len(hidden) - 1}__"

    text = re.sub(r'<tg-emoji[^>]*>.*?</tg-emoji>', hide, text)
    for char, eid in _EMOJI_ITEMS:
        if char in text:
            text = text.replace(char, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>')
    for i, h in enumerate(hidden):
        text = text.replace(f"__TG_EMOJI_{i}__", h)
    return text


PREMIUM_APPS = {
    "Facebook": {"emoji": "📘", "id": "5429172110520003976"},
    "WhatsApp": {"emoji": "💬", "id": "5429612632430654504"},
    "Telegram": {"emoji": "✈️", "id": "5429136513831057777"},
    "Instagram": {"emoji": "📸", "id": "5429478178479447442"},
    "Google": {"emoji": "🔍", "id": "5429558795015593080"},
    "Microsoft": {"emoji": "🪟", "id": "5979047775470358891"},
    "TikTok": {"emoji": "🎵", "id": "5429132656950419591"},
    "Bkash": {"emoji": "🏦", "id": "5431552076452766597"},
    "Binance": {"emoji": "💱", "id": "5429438106434575354"},
    "Snapchat": {"emoji": "👻", "id": "5429398137468919845"},
    "Uber": {"emoji": "🚗", "id": "5298715455316303708"},
    "Discord": {"emoji": "🎬", "id": "5429594374524676604"},
    "Amazon": {"emoji": "🌟", "id": "5431358656895568355"},
    "Viber": {"emoji": "💜", "id": "5429470576387335368"},
    "Twitter": {"emoji": "🐦", "id": "5431899135580087595"},
    "Netflix": {"emoji": "🎥", "id": "5431641055290235797"},
    "Spotify": {"emoji": "🎵", "id": "5429235839244739644"},
    "Foodpanda": {"emoji": "🐼", "id": "5336879280578138635"},
    "Pathao": {"emoji": "🛵", "id": "5336879280578138635"},
    "ChatGPT": {"emoji": "🤖", "id": "5429503209548847635"},
    "Imo": {"emoji": "💭", "id": "5431378937731129128"},
    "Other": {"emoji": "📶", "id": "5429353834881261942"},
}

SERVICE_SMS_KEYWORDS = {
    "Facebook": ["facebook", "fb code", "fb", "meta"],
    "WhatsApp": ["whats", "whatsapp", "whatsapp code"],
    "Telegram": ["telegram", "tg code"],
    "Instagram": ["instagram", "ig code"],
    "Google": ["google", "googl"],
    "Microsoft": ["microsoft", "micro", "microsof", "xbox"],
    "TikTok": ["tiktok", "tik tok"],
    "Bkash": ["bkash"],
    "Binance": ["binance", "bnb"],
    "Snapchat": ["snapchat", "snap"],
    "Uber": ["uber"],
    "Discord": ["discord"],
    "Amazon": ["amazon", "aws"],
    "Viber": ["viber"],
    "Twitter": ["twitter", "x.com"],
    "Netflix": ["netflix"],
    "Spotify": ["spotify"],
    "Foodpanda": ["foodpanda", "panda"],
    "Pathao": ["pathao"],
    "ChatGPT": ["openai", "chatgpt"],
    "Imo": ["imo code", "imo"],
}

COUNTRY_CODES = {
    "1": "🇺🇸 USA/Canada", "380": "🇺🇦 Ukraine", "48": "🇵🇱 Poland", "7": "🇰🇿 Kazakhstan",
    "86": "🇨🇳 China", "994": "🇦🇿 Azerbaijan", "374": "🇦🇲 Armenia", "79": "🇷🇺 Russia",
    "998": "🇺🇿 Uzbekistan", "49": "🇩🇪 Germany", "81": "🇯🇵 Japan", "90": "🇹🇷 Turkey",
    "375": "🇧🇾 Belarus", "44": "🇬🇧 United Kingdom", "91": "🇮🇳 India", "55": "🇧🇷 Brazil",
    "260": "🇿🇲 Zambia", "967": "🇾🇪 Yemen", "84": "🇻🇳 Vietnam", "379": "🇻🇦 Vatican City",
    "678": "🇻🇺 Vanuatu", "598": "🇺🇾 Uruguay", "971": "🇦🇪 UAE", "256": "🇺🇬 Uganda",
    "993": "🇹🇲 Turkmenistan", "216": "🇹🇳 Tunisia", "228": "🇹🇬 Togo", "66": "🇹🇭 Thailand",
    "255": "🇹🇿 Tanzania", "992": "🇹🇯 Tajikistan", "41": "🇨🇭 Switzerland", "46": "🇸🇪 Sweden",
    "268": "🇸🇿 Eswatini", "597": "🇸🇷 Suriname", "249": "🇸🇩 Sudan", "34": "🇪🇸 Spain",
    "94": "🇱🇰 Sri Lanka", "211": "🇸🇸 South Sudan", "27": "🇿🇦 South Africa", "252": "🇸🇴 Somalia",
    "677": "🇸🇧 Solomon Islands", "386": "🇸🇮 Slovenia", "421": "🇸🇰 Slovakia", "65": "🇸🇬 Singapore",
    "232": "🇸🇱 Sierra Leone", "248": "🇸🇨 Seychelles", "381": "🇷🇸 Serbia", "221": "🇸🇳 Senegal",
    "239": "🇸🇹 Sao Tome", "378": "🇸🇲 San Marino", "685": "🇼🇸 Samoa", "970": "🇵🇸 Palestine",
    "250": "🇷🇼 Rwanda", "40": "🇷🇴 Romania", "974": "🇶🇦 Qatar", "351": "🇵🇹 Portugal",
    "63": "🇵🇭 Philippines", "51": "🇵🇪 Peru", "595": "🇵🇾 Paraguay", "675": "🇵🇬 Papua New Guinea",
    "507": "🇵🇦 Panama", "680": "🇵🇼 Palau", "92": "🇵🇰 Pakistan", "968": "🇴🇲 Oman",
    "47": "🇳🇴 Norway", "234": "🇳🇬 Nigeria", "227": "🇳🇪 Niger", "64": "🇳🇿 New Zealand",
    "31": "🇳🇱 Netherlands", "977": "🇳🇵 Nepal", "264": "🇳🇦 Namibia", "258": "🇲🇿 Mozambique",
    "212": "🇲🇦 Morocco", "382": "🇲🇪 Montenegro", "976": "🇲🇳 Mongolia", "377": "🇲🇨 Monaco",
    "373": "🇲🇩 Moldova", "960": "🇲🇻 Maldives", "223": "🇲🇱 Mali", "356": "🇲🇹 Malta",
    "596": "🇲🇶 Martinique", "692": "🇲🇭 Marshall Islands", "230": "🇲🇺 Mauritius", "52": "🇲🇽 Mexico",
    "691": "🇫🇲 Micronesia", "60": "🇲🇾 Malaysia", "254": "🇰🇪 Kenya", "261": "🇲🇬 Madagascar",
    "389": "🇲🇰 North Macedonia", "352": "🇱🇺 Luxembourg", "370": "🇱🇹 Lithuania", "423": "🇱🇮 Liechtenstein",
    "218": "🇱🇾 Libya", "231": "🇱🇷 Liberia", "686": "🇰🇮 Kiribati", "383": "🇽🇰 Kosovo",
    "965": "🇰🇼 Kuwait", "996": "🇰🇬 Kyrgyzstan", "856": "🇱🇦 Laos", "371": "🇱🇻 Latvia",
    "961": "🇱🇧 Lebanon", "266": "🇱🇸 Lesotho", "62": "🇮🇩 Indonesia", "98": "🇮🇷 Iran",
    "964": "🇮🇶 Iraq", "353": "🇮🇪 Ireland", "972": "🇮🇱 Israel", "39": "🇮🇹 Italy",
    "962": "🇯🇴 Jordan", "354": "🇮🇸 Iceland", "36": "🇭🇺 Hungary", "504": "🇭🇳 Honduras",
    "509": "🇭🇹 Haiti", "592": "🇬🇾 Guyana", "245": "🇬🇼 Guinea-Bissau", "224": "🇬🇳 Guinea",
    "502": "🇬🇹 Guatemala", "30": "🇬🇷 Greece", "233": "🇬🇭 Ghana", "995": "🇬🇪 Georgia",
    "220": "🇬🇲 Gambia", "241": "🇬🇦 Gabon", "33": "🇫🇷 France", "358": "🇫🇮 Finland",
    "679": "🇫🇯 Fiji", "251": "🇪🇹 Ethiopia", "670": "🇹🇱 Timor-Leste", "593": "🇪🇨 Ecuador",
    "20": "🇪🇬 Egypt", "503": "🇸🇻 El Salvador", "372": "🇪🇪 Estonia", "253": "🇩🇯 Djibouti",
    "45": "🇩🇰 Denmark", "357": "🇨🇾 Cyprus", "385": "🇭🇷 Croatia", "506": "🇨🇷 Costa Rica",
    "242": "🇨🇬 Congo", "243": "🇨🇩 DR Congo", "269": "🇰🇲 Comoros", "855": "🇰🇭 Cambodia",
    "237": "🇨🇲 Cameroon", "238": "🇨🇻 Cape Verde", "236": "🇨🇫 CAR", "235": "🇹🇩 Chad",
    "420": "🇨🇿 Czechia", "56": "🇨🇱 Chile", "57": "🇨🇴 Colombia", "257": "🇧🇮 Burundi",
    "267": "🇧🇼 Botswana", "387": "🇧🇦 Bosnia", "591": "🇧🇴 Bolivia", "975": "🇧🇹 Bhutan",
    "229": "🇧🇯 Benin", "54": "🇦🇷 Argentina", "61": "🇦🇺 Australia", "43": "🇦🇹 Austria",
    "973": "🇧🇭 Bahrain", "880": "🇧🇩 Bangladesh", "32": "🇧🇪 Belgium", "501": "🇧🇿 Belize",
    "244": "🇦🇴 Angola", "376": "🇦🇩 Andorra", "213": "🇩🇿 Algeria", "355": "🇦🇱 Albania",
    "93": "🇦🇫 Afghanistan", "263": "🇿🇼 Zimbabwe", "53": "🇨🇺 Cuba", "850": "🇰🇵 North Korea",
    "58": "🇻🇪 Venezuela", "963": "🇸🇾 Syria", "95": "🇲🇲 Myanmar", "505": "🇳🇮 Nicaragua",
    "82": "🇰🇷 South Korea", "240": "🇬🇶 Equatorial Guinea", "299": "🇬🇱 Greenland", "298": "🇫🇴 Faroe Islands",
    "225": "🇨🇮 Ivory Coast", "673": "🇧🇳 Brunei", "359": "🇧🇬 Bulgaria", "226": "🇧🇫 Burkina Faso",
    "291": "🇪🇷 Eritrea", "265": "🇲🇼 Malawi", "222": "🇲🇷 Mauritania", "674": "🇳🇷 Nauru",
    "966": "🇸🇦 Saudi Arabia", "676": "🇹🇴 Tonga", "688": "🇹🇻 Tuvalu", "886": "🇹🇼 Taiwan",
    "852": "🇭🇰 Hong Kong", "853": "🇲🇴 Macau", "297": "🇦🇼 Aruba", "599": "🇨🇼 Curacao",
    "500": "🇫🇰 Falkland Islands", "594": "🇬🇫 French Guiana", "590": "🇬🇵 Guadeloupe", "262": "🇷🇪 Reunion",
    "687": "🇳🇨 New Caledonia", "683": "🇳🇺 Niue", "672": "🇳🇫 Norfolk Island", "681": "🇼🇫 Wallis and Futuna",
    "682": "🇨🇰 Cook Islands", "689": "🇵🇫 French Polynesia", "350": "🇬🇮 Gibraltar", "508": "🇵🇲 Saint Pierre",
}
_COUNTRY_SORTED = sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True)


def get_country_info(range_str):
    clean = str(range_str or "").replace("X", "").lstrip("+")
    for code, name in _COUNTRY_SORTED:
        if clean.startswith(code):
            return code, name
    return clean[:3], f"🏳️ Other (+{clean[:3]})"


# ==========================================
# Helpers
# ==========================================
def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def get_api_key():
    return random.choice(voltx_keys) if voltx_keys else API_2OO9_KEY_DEFAULT


def get_otp_reward(service_name):
    rates = bot_settings.get("otp_service_rates", {})
    val = rates.get(service_name, bot_settings.get("otp_default_rate", 0.15))
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.15


def update_daily_stat(key, amount=1):
    global daily_stats
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date") != today:
        daily_stats = {"date": today, "numbers": 0, "otps": 0}
    daily_stats[key] = daily_stats.get(key, 0) + amount


def cooldown_left(user_id):
    last = user_cooldowns.get(user_id, 0)
    left = bot_settings.get("cooldown", 0) - (time.time() - last)
    return int(left) + 1 if left > 0 else 0


def clean_sessions():
    now = time.time()
    for num in [n for n, s in list(user_active_sessions.items()) if now - s.get("ts", 0) > SESSION_TTL]:
        user_active_sessions.pop(num, None)


# ==========================================
# Local storage
# ==========================================
def load_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels
    global voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps
    global user_active_sessions, daily_stats, daily_user_otps
    if not os.path.exists(BOT_DATA_FILE):
        return
    try:
        with open(BOT_DATA_FILE, "r") as f:
            data = json.load(f)
        recent_traffic = data.get("recent_traffic", [])
        voltx_dynamic_data = data.get("voltx_dynamic_data", {})
        voltx_keys = data.get("voltx_keys") or [API_2OO9_KEY_DEFAULT]
        force_join_status = data.get("force_join_status", False)
        force_join_channels = data.get("force_join_channels", [])
        voltx_auto_mode = data.get("voltx_auto_mode", True)
        otp_forward_groups = data.get("otp_forward_groups", [])
        otp_button_link = data.get("otp_button_link", otp_button_link)
        recent_success_otps = OrderedDict((s, True) for s in data.get("recent_success_otps", []))
        for k, v in data.get("bot_settings", {}).items():
            bot_settings[k] = v
        daily_stats = data.get("daily_stats", daily_stats)
        daily_user_otps = data.get("daily_user_otps", daily_user_otps)
        sessions = {}
        for num, val in data.get("user_active_sessions", {}).items():
            if isinstance(val, dict):
                sessions[num] = val
            else:  # old format: number -> user_id
                sessions[num] = {"uid": int(val), "ts": time.time()}
        user_active_sessions = sessions
    except Exception as e:
        log("Error loading local data:", e)


def save_local_data(sync_cloud=True):
    with file_lock:
        try:
            tmp = BOT_DATA_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump({
                    "recent_traffic": recent_traffic,
                    "voltx_dynamic_data": voltx_dynamic_data,
                    "voltx_keys": voltx_keys,
                    "force_join_status": force_join_status,
                    "force_join_channels": force_join_channels,
                    "voltx_auto_mode": voltx_auto_mode,
                    "otp_forward_groups": otp_forward_groups,
                    "otp_button_link": otp_button_link,
                    "recent_success_otps": list(recent_success_otps.keys()),
                    "bot_settings": bot_settings,
                    "user_active_sessions": user_active_sessions,
                    "daily_stats": daily_stats,
                    "daily_user_otps": daily_user_otps,
                }, f)
            os.replace(tmp, BOT_DATA_FILE)
        except Exception as e:
            log("Error saving local data:", e)

    if sync_cloud and current_db_mode == "firebase" and db_firebase:
        try:
            db_firebase.collection('settings').document('bot_config').set({
                "bot_settings": bot_settings,
                "force_join_status": force_join_status,
                "force_join_channels": force_join_channels,
                "otp_forward_groups": otp_forward_groups,
                "otp_button_link": otp_button_link,
                "voltx_keys": voltx_keys,
                "voltx_auto_mode": voltx_auto_mode,
            }, merge=True)
        except Exception as e:
            log("Firebase config sync error:", e)


cached_user_list = set()


def add_to_broadcast_list(user_id):
    global cached_user_list
    if not cached_user_list and os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                cached_user_list = set(json.load(f))
        except Exception:
            pass
    if user_id not in cached_user_list:
        cached_user_list.add(user_id)
        try:
            with open(USERS_LIST_FILE, "w") as f:
                json.dump(list(cached_user_list), f)
        except Exception:
            pass


def get_all_user_ids():
    users = set(int(u) for u in user_cache.keys())
    if os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                users.update(int(u) for u in json.load(f))
        except Exception:
            pass
    return list(users)


# ==========================================
# Telegram API helpers
# ==========================================
def tg(method, payload=None, timeout=15):
    """POST to Telegram with automatic 429 retry."""
    for _ in range(3):
        try:
            r = http.post(BASE_URL + method, json=payload or {}, timeout=timeout)
            data = r.json()
            if not data.get("ok") and data.get("error_code") == 429:
                time.sleep(data.get("parameters", {}).get("retry_after", 1) + 0.5)
                continue
            return data
        except Exception:
            time.sleep(1)
    return None


def get_bot_info():
    res = tg("getMe")
    if res and res.get("ok"):
        return res["result"]["username"]
    return ""


def set_bot_commands():
    tg("setMyCommands", {"commands": [{"command": "start", "description": "Start the bot / refresh menu"}]})


def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": apply_emojis(text), "parse_mode": parse_mode,
               "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendMessage", payload)


def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": apply_emojis(text),
               "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("editMessageText", payload)


def answer_callback_query(callback_query_id, text="", show_alert=False):
    tg("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert})


def delete_message(chat_id, message_id):
    tg("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def copy_message(chat_id, from_chat_id, message_id):
    return tg("copyMessage", {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id})


def get_chat_details(chat_identifier):
    chat_identifier = str(chat_identifier).strip()
    if chat_identifier.startswith("https://t.me/"):
        chat_identifier = "@" + chat_identifier.split("/")[-1]
    elif not chat_identifier.startswith("@") and not chat_identifier.startswith("-100"):
        chat_identifier = "@" + chat_identifier
    res = tg("getChat", {"chat_id": chat_identifier})
    if res and res.get("ok"):
        chat = res["result"]
        chat_data = {
            "id": chat["id"],
            "username": "@" + chat["username"] if "username" in chat else "",
            "title": chat.get("title", "Private Channel"),
            "invite_link": chat.get("invite_link", ""),
        }
        if not chat_data["invite_link"]:
            inv = tg("exportChatInviteLink", {"chat_id": chat["id"]})
            if inv and inv.get("ok"):
                chat_data["invite_link"] = inv["result"]
        return chat_data
    return None


def is_user_joined(user_id):
    if not force_join_status or not force_join_channels:
        return True
    if user_id == ADMIN_ID:
        return True
    for ch in force_join_channels:
        res = tg("getChatMember", {"chat_id": ch["id"], "user_id": user_id})
        if not res or not res.get("ok"):
            return False
        if res["result"]["status"] in ("left", "kicked"):
            return False
    return True


# ==========================================
# Service detection / OTP formatting
# ==========================================
def detect_service(message_text, raw_sid=""):
    msg_lower = str(message_text).lower()
    sid_lower = str(raw_sid).lower()
    for service, keywords in SERVICE_SMS_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return service
    for service in PREMIUM_APPS.keys():
        if service.lower() in sid_lower:
            return service
    return "Other"


def get_service_info_html(service_name):
    app_info = PREMIUM_APPS.get(service_name, PREMIUM_APPS["Other"])
    short = service_name.upper()
    short = {"FACEBOOK": "FB", "WHATSAPP": "WS", "INSTAGRAM": "IG"}.get(short, short)
    return f'<tg-emoji emoji-id="{app_info["id"]}">{app_info["emoji"]}</tg-emoji> <b>{html.escape(short)}</b>', app_info["id"]


def extract_otp_code(message_text):
    m = re.search(r'\b(\d{3}[\s-]?\d{3,4}|\d{4,8})\b', str(message_text))
    return m.group(1) if m else "COPY"


def deliver_to_inbox(user_id, service_name, raw_number, msg_text, current_balance, reward):
    _, c_name = get_country_info(raw_number)
    flag = c_name.split(" ", 1)[0]
    service_html, srv_eid = get_service_info_html(service_name)
    clean_number = str(raw_number).lstrip('+')
    text = (
        f"{THIN}\n"
        f"<blockquote>🎉 <b>OTP RECEIVED</b></blockquote>\n"
        f"<blockquote>{service_html} ➜ {flag} <code>+{clean_number}</code></blockquote>\n"
        f"<blockquote>➕ <b>ADDED</b> ➜ <b>{reward:.2f} TK</b></blockquote>\n"
        f"<blockquote>💳 <b>BALANCE</b> ➜ <b>{current_balance:.2f} TK</b></blockquote>\n"
        f"{THIN}"
    )
    otp = extract_otp_code(msg_text)
    markup = {"inline_keyboard": [[{"text": otp, "icon_custom_emoji_id": srv_eid,
                                    "copy_text": {"text": otp}, "style": "success"}]]}
    send_message(user_id, text, reply_markup=markup)


def generate_otp_display(service_name, raw_number, message_text):
    _, c_name = get_country_info(raw_number)
    country_emoji = c_name.split(" ", 1)[0]
    masked = f"{raw_number[:3]}DXA{raw_number[-3:]}" if len(raw_number) > 6 else raw_number
    service_html, srv_eid = get_service_info_html(service_name)

    text = (
        f"{DIV}\n"
        f"{service_html} ➜ {country_emoji} <code>{html.escape(masked)}</code>\n"
        f"{DIV}"
    )
    otp = extract_otp_code(message_text)
    clean_range = str(raw_number)[:5] if len(str(raw_number)) >= 5 else str(raw_number)
    deep_link = f"https://t.me/{BOT_USERNAME}?start=alloc_{clean_range}_{service_name.lower()}"

    markup = {"inline_keyboard": []}
    row1 = []
    mcl = bot_settings.get("main_channel_link", "")
    if mcl:
        row1.append({"text": "𝗖𝗛𝗔𝗡𝗡𝗘𝗟", "url": mcl, "icon_custom_emoji_id": "5429353834881261942", "style": "primary"})
    row1.append({"text": otp, "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"})
    markup["inline_keyboard"].append(row1)
    markup["inline_keyboard"].append([
        {"text": "GET NUMBER", "url": deep_link, "icon_custom_emoji_id": "5429167978761461870", "style": "danger"}
    ])
    return text, markup


def send_otp_to_groups(text, markup):
    sent_any = False
    for gid in list(otp_forward_groups):
        resp = send_message(gid, text, reply_markup=markup)
        if resp and resp.get("ok"):
            sent_any = True
        time.sleep(1)
    return sent_any


# ==========================================
# 2oo9 API + background workers
# ==========================================
def fetch_live_access():
    try:
        res = http.get(f"{API_2OO9_BASE}/liveaccess", headers={"mauthapi": get_api_key()}, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200:
            return data.get("data", {}).get("services", [])
    except Exception:
        pass
    return []


def fetch_live_number(rid):
    headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
    try:
        res = http.post(f"{API_2OO9_BASE}/getnum", headers=headers, json={"rid": str(rid)}, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200:
            return data.get("data", {})
    except Exception:
        pass
    return None


def voltx_console_listener():
    global recent_traffic, voltx_dynamic_data
    cycle = 0
    while True:
        try:
            res = http.get(f"{API_2OO9_BASE}/console", headers={"mauthapi": get_api_key()}, timeout=10)
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                hits = data.get("data", {}).get("hits", [])
                new_traffic, seen = [], set()
                now = int(time.time())

                for h in hits:
                    sig = f"{h.get('time', 0)}_{h.get('range', '')}"
                    if sig in seen:
                        continue
                    h['local_receive_time'] = now
                    new_traffic.append(h)
                    seen.add(sig)

                    raw_sid = h.get("sid") or "Unknown"
                    raw_msg = h.get("message") or ""
                    raw_range = str(h.get("range", "")).replace("X", "")
                    if raw_range:
                        sid = detect_service(raw_msg, raw_sid)
                        app = PREMIUM_APPS.get(sid, PREMIUM_APPS["Other"])
                        entry = voltx_dynamic_data.setdefault(
                            sid, {"emoji_id": app["id"], "normal_emoji": app["emoji"], "ranges": {}})
                        r_entry = entry["ranges"].setdefault(raw_range, {"last_seen": now, "hits": 0})
                        r_entry["last_seen"] = now
                        r_entry["hits"] += 1

                cutoff = now - 900
                for h in recent_traffic:
                    if h.get('local_receive_time', 0) >= cutoff:
                        sig = f"{h.get('time', 0)}_{h.get('range', '')}"
                        if sig not in seen:
                            new_traffic.append(h)
                            seen.add(sig)
                new_traffic.sort(key=lambda x: x.get('local_receive_time', 0), reverse=True)
                recent_traffic = new_traffic

                for sid in list(voltx_dynamic_data.keys()):
                    s_data = voltx_dynamic_data[sid]
                    for r in [r for r, d in s_data["ranges"].items() if now - d["last_seen"] > 300]:
                        del s_data["ranges"][r]
                    if not s_data["ranges"]:
                        del voltx_dynamic_data[sid]

                cycle += 1
                if cycle % 3 == 0:
                    save_local_data(sync_cloud=False)
        except Exception:
            pass
        time.sleep(10)


def _extract_otp_list(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            return inner.get("otps") or inner.get("hits") or []
        return data.get("otps") or data.get("hits") or []
    return []


def voltx_sms_listener():
    global recent_success_otps
    group_sent = OrderedDict()
    while True:
        try:
            clean_sessions()
            headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
            res = http.get(f"{API_2OO9_BASE}/success-otp", headers=headers, timeout=15)
            if res.status_code == 200:
                otps = _extract_otp_list(res.json())
                for od in reversed(otps):
                    msg_text = str(od.get("message", od.get("sms", od.get("code", ""))))
                    raw_number = str(od.get("number", od.get("phone", "")))
                    raw_service = str(od.get("sid", od.get("service", "Unknown")))
                    if not msg_text or not raw_number:
                        continue

                    sig = f"{raw_number}_{msg_text}"
                    service = detect_service(msg_text, raw_service)

                    if sig not in group_sent:
                        group_sent[sig] = True
                        if otp_forward_groups:
                            text, markup = generate_otp_display(service, raw_number, msg_text)
                            send_otp_to_groups(text, markup)

                    if sig not in recent_success_otps:
                        recent_success_otps[sig] = True
                        owner_id = None
                        tail = raw_number[-8:] if len(raw_number) > 8 else raw_number
                        for num, sess in list(user_active_sessions.items()):
                            if num.endswith(tail):
                                owner_id = sess["uid"]
                                user_active_sessions.pop(num, None)
                                break

                        if owner_id:
                            reward = get_otp_reward(service)
                            update_user_stats(owner_id, reward, 0, 1)
                            bal = (get_user(owner_id) or {}).get("balance", 0.0)
                            deliver_to_inbox(owner_id, service, raw_number, msg_text, bal, reward)

                            today = time.strftime("%Y-%m-%d")
                            if daily_user_otps.get("date") != today:
                                daily_user_otps["date"] = today
                                daily_user_otps["users"] = {}
                            k = str(owner_id)
                            daily_user_otps["users"][k] = daily_user_otps["users"].get(k, 0) + 1

                        update_daily_stat("otps", 1)
                        save_local_data(sync_cloud=False)
                        time.sleep(1)

            while len(recent_success_otps) > 2000:
                recent_success_otps.popitem(last=False)
            while len(group_sent) > 2000:
                group_sent.popitem(last=False)
        except Exception:
            pass
        time.sleep(10)


# ==========================================
# Database layer (SQLite + Firebase)
# ==========================================
def init_sqlite():
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT DEFAULT 'User', "
              "balance REAL DEFAULT 0.0, total_invites INTEGER DEFAULT 0)")
    for ddl in ("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT 'User'",
                "ALTER TABLE users ADD COLUMN total_otps INTEGER DEFAULT 0"):
        try:
            c.execute(ddl)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def migrate_sqlite_to_firebase():
    if not db_firebase:
        return
    try:
        conn = sqlite3.connect("bot_database.db")
        c = conn.cursor()
        c.execute("SELECT user_id, first_name, balance, total_invites, COALESCE(total_otps,0) FROM users")
        rows = c.fetchall()
        if not rows:
            conn.close()
            return
        batch = db_firebase.batch()
        count = 0
        for uid, fname, bal, inv, otps in rows:
            ref = db_firebase.collection('users').document(str(uid))
            batch.set(ref, {"user_id": uid, "first_name": fname,
                            "balance": firestore.Increment(bal),
                            "total_invites": firestore.Increment(inv),
                            "total_otps": firestore.Increment(otps)}, merge=True)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db_firebase.batch()
        if count % 400 != 0:
            batch.commit()
        c.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        user_cache.clear()
    except Exception as e:
        log("Migration Error:", e)


def _apply_cloud_config(data):
    global force_join_status, force_join_channels, otp_forward_groups, otp_button_link, voltx_keys, voltx_auto_mode
    if "bot_settings" in data:
        bot_settings.update(data["bot_settings"])
    if "force_join_status" in data:
        force_join_status = data["force_join_status"]
    if "force_join_channels" in data:
        force_join_channels = data["force_join_channels"]
    if "otp_forward_groups" in data:
        otp_forward_groups = data["otp_forward_groups"]
    if "otp_button_link" in data:
        otp_button_link = data["otp_button_link"]
    if "voltx_keys" in data and data["voltx_keys"]:
        voltx_keys = data["voltx_keys"]
    if "voltx_auto_mode" in data:
        voltx_auto_mode = data["voltx_auto_mode"]


def _sync_users_from_firebase():
    try:
        local = set()
        if os.path.exists(USERS_LIST_FILE):
            with open(USERS_LIST_FILE, "r") as f:
                local = set(json.load(f))
        docs = db_firebase.collection('users').select([]).stream()
        fb = set(int(d.id) for d in docs)
        combined = local.union(fb)
        if len(combined) > len(local):
            with open(USERS_LIST_FILE, "w") as f:
                json.dump(list(combined), f)
            log(f"✅ Synced {len(fb)} users from Firebase")
    except Exception as e:
        log("User sync error:", e)


def init_firebase_from_file():
    global current_db_mode, db_firebase
    if not os.path.exists("temp_firebase.json"):
        return
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
        db_firebase = firestore.client()
        current_db_mode = "firebase"
        log("✅ Firebase auto-connected")
        doc = db_firebase.collection('settings').document('bot_config').get()
        if doc.exists:
            _apply_cloud_config(doc.to_dict())
            log("✅ Settings synced from Firebase")
        _sync_users_from_firebase()
    except Exception as e:
        log("❌ Firebase auto-connect error:", e)


def get_user(user_id):
    if user_id in user_cache:
        return user_cache[user_id]
    if current_db_mode == "firebase" and db_firebase:
        try:
            doc = db_firebase.collection('users').document(str(user_id)).get()
            if doc.exists:
                d = doc.to_dict()
                d.setdefault("total_otps", 0)
                d.setdefault("total_invites", 0)
                d.setdefault("balance", 0.0)
                user_cache[user_id] = d
                return d
        except Exception as e:
            log("get_user firebase error:", e)
        return None
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT first_name, balance, total_invites, COALESCE(total_otps,0) FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        d = {"user_id": user_id, "first_name": row[0], "balance": row[1],
             "total_invites": row[2], "total_otps": row[3]}
        user_cache[user_id] = d
        return d
    return None


def add_user(user_id, first_name="User"):
    add_to_broadcast_list(user_id)
    if user_id in user_cache and user_cache[user_id].get("first_name") == first_name:
        return
    if current_db_mode == "firebase" and db_firebase:
        ref = db_firebase.collection('users').document(str(user_id))
        if not ref.get().exists:
            new = {"user_id": user_id, "first_name": first_name, "balance": 0.0, "total_invites": 0, "total_otps": 0}
            ref.set(new)
            user_cache[user_id] = new
        else:
            ref.update({"first_name": first_name})
            if user_id in user_cache:
                user_cache[user_id]["first_name"] = first_name
    else:
        conn = sqlite3.connect("bot_database.db")
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, first_name, balance, total_invites, total_otps) "
                  "VALUES (?, ?, 0.0, 0, 0)", (user_id, first_name))
        c.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
        conn.commit()
        conn.close()
        if user_id not in user_cache:
            user_cache[user_id] = {"user_id": user_id, "first_name": first_name,
                                   "balance": 0.0, "total_invites": 0, "total_otps": 0}
        else:
            user_cache[user_id]["first_name"] = first_name


def update_user_stats(user_id, balance_add, invite_add, otp_add=0):
    bal_add, inv_add, otp_add = float(balance_add), int(invite_add), int(otp_add)
    if user_id not in user_cache:
        get_user(user_id)
    if user_id in user_cache:
        u = user_cache[user_id]
        u["balance"] = round(u.get("balance", 0) + bal_add, 2)
        u["total_invites"] = u.get("total_invites", 0) + inv_add
        u["total_otps"] = u.get("total_otps", 0) + otp_add

    if current_db_mode == "firebase" and db_firebase:
        try:
            db_firebase.collection('users').document(str(user_id)).set({
                "balance": firestore.Increment(bal_add),
                "total_invites": firestore.Increment(inv_add),
                "total_otps": firestore.Increment(otp_add),
            }, merge=True)
        except Exception as e:
            log("update_user_stats firebase error:", e)
    else:
        conn = sqlite3.connect("bot_database.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ?, total_invites = total_invites + ?, "
                  "total_otps = COALESCE(total_otps,0) + ? WHERE user_id = ?",
                  (bal_add, inv_add, otp_add, user_id))
        conn.commit()
        conn.close()


def get_total_users():
    return len(get_all_user_ids())


# ==========================================
# Background cache (menus + leaderboard)
# ==========================================
def auto_cache_menu_thread():
    global cached_services_kb, cached_countries_kb, cached_leaderboard_text
    while True:
        try:
            if voltx_auto_mode and voltx_dynamic_data:
                service_hits = [(sid, d, sum(r["hits"] for r in d["ranges"].values()))
                                for sid, d in list(voltx_dynamic_data.items())]
                top = sorted(service_hits, key=lambda x: x[2], reverse=True)[:15]

                srv_kb = {"inline_keyboard": []}
                row, styles, i = [], ["primary", "success", "danger"], 0
                for sid, data, hits in top:
                    safe = html.escape(str(sid))
                    row.append({"text": safe, "callback_data": f"srv_{safe[:15]}",
                                "style": styles[i % 3], "icon_custom_emoji_id": data["emoji_id"]})
                    i += 1
                    if len(row) == 2:
                        srv_kb["inline_keyboard"].append(row)
                        row = []
                if row:
                    srv_kb["inline_keyboard"].append(row)
                srv_kb["inline_keyboard"].append([{"text": "CLOSE", "callback_data": "close_panel",
                                                   "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}])
                cached_services_kb = srv_kb

                new_cnt = {}
                for sid, data, hits in top:
                    short = html.escape(str(sid))[:15]
                    cmap = {}
                    for r, rd in data["ranges"].items():
                        cr = str(r).replace("X", "")
                        if not re.match(r'^\d+$', cr):
                            continue
                        code, name = get_country_info(cr)
                        cmap.setdefault(code, {"name": name, "hits": 0})["hits"] += rd["hits"]
                    top_c = sorted(cmap.items(), key=lambda x: x[1]["hits"], reverse=True)[:15]

                    kb = {"inline_keyboard": []}
                    rate = get_otp_reward(detect_service("", sid))
                    styles_c, j = ["primary", "success", "danger"], 0
                    for code, cd in top_c:
                        parts = cd["name"].split(" ", 1)
                        emoji_char = parts[0]
                        clean = parts[1] if len(parts) > 1 else cd["name"]
                        label = (f"Other (+{code}) - {rate} TK" if "Other" in clean
                                 else f"{clean} (+{code}) - {rate} TK")
                        btn = {"text": label, "callback_data": f"cc_{short}_{code}", "style": styles_c[j % 3]}
                        if emoji_char in GLOBAL_BODY_EMOJIS:
                            btn["icon_custom_emoji_id"] = GLOBAL_BODY_EMOJIS[emoji_char]
                        kb["inline_keyboard"].append([btn])
                        j += 1
                    kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "back_to_services",
                                                   "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}])
                    new_cnt[short] = kb
                cached_countries_kb = new_cnt

            today = time.strftime("%Y-%m-%d")
            if daily_user_otps.get("date") != today:
                daily_user_otps["date"] = today
                daily_user_otps["users"] = {}

            top_users = sorted(daily_user_otps["users"].items(), key=lambda x: x[1], reverse=True)[:5]
            lb = (f"<blockquote>🏆 <b>𝗧𝗢𝗣 𝟱 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗</b> <i>(today)</i></blockquote>\n{DIV}\n")
            medals = [("1️⃣", "5238176680098440792"), ("2️⃣", "5237806896299157399"),
                      ("3️⃣", "5239965456667812809"), ("4️⃣", "5237911487342751418"),
                      ("5️⃣", "5240278297790686165")]
            if not top_users:
                lb += "<i>No OTPs received today. Be the first! 🚀</i>\n"
            else:
                for idx, (uid_str, cnt) in enumerate(top_users):
                    u = get_user(int(uid_str))
                    fname = u["first_name"] if u else "User"
                    ch, eid = medals[idx]
                    lb += (f"<blockquote><tg-emoji emoji-id=\"{eid}\">{ch}</tg-emoji> "
                           f"<a href='tg://user?id={uid_str}'>{html.escape(str(fname))}</a> "
                           f"➜ <b>{cnt}</b> OTP</blockquote>\n")
            lb += DIV
            cached_leaderboard_text = lb
        except Exception:
            pass
        time.sleep(5)


# ==========================================
# Keyboards
# ==========================================
def ibtn(text, cb, icon=None, style=None):
    b = {"text": text, "callback_data": cb}
    if icon:
        b["icon_custom_emoji_id"] = icon
    if style:
        b["style"] = style
    return b


BACK_ICON = "5267490665117275176"
CLOSE_ICON = "5438541186539232243"


def get_main_keyboard(user_id):
    layout = [
        [{"text": BTN_GET, "icon_custom_emoji_id": "5429167978761461870", "style": "success"},
         {"text": BTN_TRAFFIC, "icon_custom_emoji_id": "5429571662737611814", "style": "danger"}],
        [{"text": BTN_INVITE, "icon_custom_emoji_id": "5850323366476519158", "style": "danger"},
         {"text": BTN_BALANCE, "icon_custom_emoji_id": "5429105001655999635", "style": "success"}],
        [{"text": BTN_LEADER, "icon_custom_emoji_id": "5240021484516185513", "style": "primary"}],
    ]
    if user_id == ADMIN_ID:
        layout.append([{"text": BTN_OWNER, "icon_custom_emoji_id": "5429427051188756948", "style": "success"}])
    return {"keyboard": layout, "resize_keyboard": True, "input_field_placeholder": "Choose an option 👇"}


def get_admin_inline_keyboard():
    db_status = "SQLITE ACTIVE" if current_db_mode == "sqlite" else "FIREBASE ACTIVE"
    return {"inline_keyboard": [
        [ibtn("STEX SETTINGS", "manage_voltx", "5877466056548691003", "danger")],
        [ibtn("BROADCAST", "broadcast_menu", "5296633779157243809", "primary"),
         ibtn("FORCE JOIN", "manage_fj", "5429353834881261942", "success")],
        [ibtn("OTP GROUP", "manage_otp_group", "5429208347159077664", "danger"),
         ibtn("USER CONTROL", "user_control", "5429274992166609833", "primary")],
        [ibtn("DXA CONTROL", "dxa_control", "5240451569656308978", "danger")],
        [ibtn("UPLOAD FIREBASE", "upload_firebase", "5429362935916962442", "primary")],
        [ibtn(db_status, "db_status", "5429591316507963112", "success")],
        [ibtn("CLOSE", "close_panel", CLOSE_ICON, "danger")],
    ]}


def get_otp_group_keyboard():
    kb = {"inline_keyboard": []}
    ld = otp_button_link or "Not Set"
    if len(ld) > 25:
        ld = ld[:25] + "..."
    kb["inline_keyboard"].append([ibtn(f"Link: {ld}", "edit_otp_link", "5420517437885943844", "primary")])
    mc = bot_settings.get("main_channel_link", "") or "Not Set"
    if len(mc) > 25:
        mc = mc[:25] + "..."
    kb["inline_keyboard"].append([ibtn(f"Main Channel: {mc}", "edit_main_channel", "5429353834881261942", "primary")])
    if otp_forward_groups:
        kb["inline_keyboard"].append([ibtn(f"Delete Group: {otp_forward_groups[0]}", "del_otp_group_0",
                                           "5422557736330106570", "danger")])
    kb["inline_keyboard"].append([ibtn("Set Forward Group", "add_otp_group", "5429501315468270290", "success")])
    kb["inline_keyboard"].append([ibtn("BACK", "back_to_admin", BACK_ICON, "danger")])
    return kb


def get_force_join_keyboard():
    kb = {"inline_keyboard": []}
    on = force_join_status
    kb["inline_keyboard"].append([ibtn("STATUS: ON" if on else "STATUS: OFF", "toggle_fj",
                                       "5352694861990501856" if on else "5420130255174145507",
                                       "primary" if on else "danger")])
    for idx, ch in enumerate(force_join_channels):
        name = ch.get("username") or ch.get("title", f"Channel {idx}")
        kb["inline_keyboard"].append([ibtn(f"Delete: {name}", f"del_fj_{idx}", "5438178416421544431", "danger")])
    kb["inline_keyboard"].append([ibtn("Add Channel", "add_fj", "5429501315468270290", "success")])
    kb["inline_keyboard"].append([ibtn("Back", "back_to_admin", CLOSE_ICON, "primary")])
    return kb


def get_force_join_alert_keyboard():
    kb = {"inline_keyboard": []}
    for ch in force_join_channels:
        name = ch.get("title") or ch.get("username", "Our Channel")
        url = ch.get("invite_link", "")
        if not url and ch.get("username"):
            url = f"https://t.me/{ch['username'].replace('@', '')}"
        if url:
            kb["inline_keyboard"].append([{"text": f"JOIN {name}", "url": url,
                                           "icon_custom_emoji_id": "5420517437885943844", "style": "danger"}])
    kb["inline_keyboard"].append([ibtn("VERIFY", "check_fj_joined", "5352694861990501856", "success")])
    return kb


def get_voltx_keys_keyboard():
    kb = {"inline_keyboard": []}
    on = voltx_auto_mode
    kb["inline_keyboard"].append([ibtn("PANEL AUTO: ON" if on else "PANEL AUTO: OFF", "toggle_vk",
                                       "5352694861990501856" if on else "5420130255174145507",
                                       "primary" if on else "danger")])
    for idx, key in enumerate(voltx_keys):
        masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else key
        kb["inline_keyboard"].append([ibtn(f"Delete: {masked}", f"del_vk_{idx}", "5438178416421544431", "danger")])
    kb["inline_keyboard"].append([ibtn("Add Panel Key", "add_vk", "5429501315468270290", "success")])
    kb["inline_keyboard"].append([ibtn("Back", "back_to_admin", CLOSE_ICON, "primary")])
    return kb


def dxa_control_keyboard():
    grp = bot_settings.get("w_group", "") or "NOT SET"
    return {"inline_keyboard": [
        [ibtn(f"MIN WITHDRAW: {bot_settings['min_withdraw']}", "dxa_min_w", "5352877703043258544", "success"),
         ibtn("OTP CONTROL", "dxa_otp_control", "5190576863226933563", "primary")],
        [ibtn(f"REFER REWARD: {bot_settings.get('refer_reward', 0.2)}", "dxa_ref_r", "5420396762189831222", "success"),
         ibtn(f"COOLDOWN: {bot_settings['cooldown']}s", "dxa_cool", "5337172996211648018", "primary")],
        [ibtn(f"NUM/REQ: {bot_settings['num_req']}", "dxa_num_req", "5337132498965010628", "success"),
         ibtn("W. METHODS", "manage_w_methods", "5190899075968441286", "primary")],
        [ibtn(f"W. GROUP: {grp}", "dxa_w_group", "5420517437885943844", "success")],
        [ibtn("BACK", "back_to_admin", BACK_ICON, "danger")],
    ]}


def dxa_otp_control_keyboard():
    kb = {"inline_keyboard": [
        [ibtn(f"Default Rate: {bot_settings['otp_default_rate']}", "dxa_def_rate", "5352877703043258544", "primary")],
        [ibtn("Set Service Rate", "dxa_srv_rate", "5395444784611480792", "success")],
    ]}
    for name, rate in bot_settings.get("otp_service_rates", {}).items():
        app = PREMIUM_APPS.get(name, PREMIUM_APPS["Other"])
        kb["inline_keyboard"].append([ibtn(f"Delete: {name} ({rate})", f"del_srv_rate_{name}", app["id"], "danger")])
    kb["inline_keyboard"].append([ibtn("BACK", "dxa_control", BACK_ICON, "danger")])
    return kb


def dxa_manage_w_methods_keyboard():
    kb = {"inline_keyboard": []}
    for idx, m in enumerate(bot_settings.get("w_methods", [])):
        kb["inline_keyboard"].append([ibtn(f"Delete: {m}", f"del_w_method_{idx}", None, "danger")])
    kb["inline_keyboard"].append([ibtn("Add Method", "add_w_method", None, "success")])
    kb["inline_keyboard"].append([ibtn("BACK", "dxa_control", None, "primary")])
    return kb


def get_user_control_keyboard():
    return {"inline_keyboard": [
        [ibtn("USER PROFILE", "uc_profile", "5352861489541714456", "primary")],
        [ibtn("BACK", "back_to_admin", BACK_ICON, "danger")],
    ]}


def get_user_profile_keyboard(uid):
    return {"inline_keyboard": [
        [ibtn("BALANCE", f"uc_balance_{uid}", "5429612421977253466", "success")],
        [ibtn("BACK", "user_control", BACK_ICON, "danger")],
    ]}


def get_upload_firebase_keyboard():
    return {"inline_keyboard": [[ibtn("CANCEL", "back_to_admin", "5420130255174145507", "danger")]]}


def get_back_only_keyboard():
    return {"inline_keyboard": [[ibtn("BACK", "user_cancel", CLOSE_ICON, "danger")]]}


def get_leaderboard_keyboard():
    return {"inline_keyboard": [[ibtn("REFRESH", "refresh_leaderboard", "5229111790842952353", "success")]]}


# ==========================================
# Screens / content builders
# ==========================================
def get_owner_panel_text():
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date") != today:
        daily_stats.update({"date": today, "numbers": 0, "otps": 0})
    grp = "✅ Connected" if otp_forward_groups else "❌ Not set"
    return (
        f"<b>📊 OWNER ZONE</b>\n{DIV}\n"
        f"<b>DATABASE OVERVIEW</b>\n{THIN}\n"
        f"<blockquote>👤 <b>TOTAL USERS</b> ➜ <b>{get_total_users()}</b></blockquote>\n"
        f"<blockquote>📱 <b>TODAY NUMBERS</b> ➜ <b>{daily_stats['numbers']}</b></blockquote>\n"
        f"<blockquote>💬 <b>TODAY OTP</b> ➜ <b>{daily_stats['otps']}</b></blockquote>\n"
        f"<blockquote>⏳ <b>ACTIVE SESSIONS</b> ➜ <b>{len(user_active_sessions)}</b></blockquote>\n"
        f"{THIN}\n"
        f"🛡 <b>OTP Group:</b> {grp}\n"
        f"🌐 <b>Database:</b> {current_db_mode.upper()}\n{DIV}"
    )


def get_leaderboard_text():
    return cached_leaderboard_text or "⏳ <b>Loading leaderboard, please wait...</b>"


def get_live_traffic_content():
    markup = {"inline_keyboard": [[ibtn("REFRESH", "refresh_traffic", "5229111790842952353", "primary")]]}
    header = f"<blockquote>📈 <b>15M LIVE TRAFFIC</b></blockquote>\n{DIV}\n"
    if not recent_traffic:
        return header + "<i>No traffic data available right now.</i>\n" + DIV, markup

    counts = {}
    for h in recent_traffic:
        sid = detect_service(h.get("message") or "", h.get("sid") or "Unknown")
        app = PREMIUM_APPS.get(sid, PREMIUM_APPS["Other"])
        counts.setdefault(sid, {"count": 0, "id": app["id"], "emoji": app["emoji"]})["count"] += 1

    ranked = sorted(counts.items(), key=lambda it: it[1]["count"], reverse=True)[:8]
    msg = header
    for i, (sid, d) in enumerate(ranked):
        msg += (f"<tg-emoji emoji-id=\"{d['id']}\">{d['emoji']}</tg-emoji> <b>{html.escape(str(sid))}</b> "
                f"➜ 🔥 <b>{d['count']}</b> OTP\n")
        if i < len(ranked) - 1:
            msg += THIN + "\n"
    msg += DIV + f"\n<i>Updated {time.strftime('%H:%M:%S')}</i>"
    return msg, markup


def get_services_content():
    if cached_services_kb:
        return f"📱 <b>SELECT SERVICE</b>\n{THIN}\n<i>Top live services right now 👇</i>", cached_services_kb
    return "⏳ <b>Loading services, please try again in a few seconds...</b>", None


def get_countries_content(sid_short):
    if sid_short in cached_countries_kb:
        return f"🌍 <b>SELECT COUNTRY</b>\n{THIN}\n<i>Reward shown on each button 👇</i>", cached_countries_kb[sid_short], None
    return None, None, "❌ No active countries for this service (Out of Stock)"


def get_number_allocation_content(sid_short, c_code, user_id=None):
    target = []
    full_sid = sid_short

    if voltx_auto_mode:
        for sid, data in list(voltx_dynamic_data.items()):
            if sid.lower().startswith(sid_short.lower()):
                full_sid = sid
                for r, rd in data["ranges"].items():
                    if c_code.startswith(r) or r.startswith(c_code):
                        target.append((r, rd["hits"]))
                break
        target.sort(key=lambda x: x[1], reverse=True)
        best = [x[0] for x in target[:3]]
    else:
        best = []
        for s in fetch_live_access():
            sv = s.get('sid') or ""
            if sv.lower().startswith(sid_short.lower()):
                full_sid = sv
                for r in s.get('ranges', []):
                    cr = str(r).replace("X", "")
                    if (c_code.startswith(cr) or cr.startswith(c_code)) and cr not in best:
                        best.append(cr)
                break
        best = best[:3]

    if not best:
        best = [c_code]

    fetched = []
    for _ in range(max(1, int(bot_settings.get("num_req", 1)))):
        nd = fetch_live_number(random.choice(best))
        if nd:
            full_number = str(nd.get("full_number", ""))
            operator = html.escape(str(nd.get("operator", "Unknown")))
            if full_number:
                fetched.append((html.escape(full_number), operator))
                if user_id:
                    user_active_sessions[full_number] = {"uid": user_id, "ts": time.time()}

    back_kb = {"inline_keyboard": [[ibtn("BACK", f"srv_{sid_short}", CLOSE_ICON, "danger")]]}
    if not fetched:
        return "❌ <b>Out of stock in these ranges.</b>\n<i>Please try again in a moment.</i>", back_kb

    update_daily_stat("numbers", len(fetched))
    save_local_data(sync_cloud=False)

    service_html, _ = get_service_info_html(full_sid)
    _, country = get_country_info(c_code)
    reward = get_otp_reward(detect_service("", full_sid))

    msg = (
        f"{DIV}\n"
        f"⌛ <b>ACTIVE NUMBER</b> <i>• 15 min</i>\n"
        f"{THIN}\n"
        f"{service_html} ➜ {country}\n"
        f"<blockquote>📡 <b>Operator:</b> {fetched[0][1]}\n"
        f"💰 <b>Reward:</b> {reward:.2f} TK / OTP</blockquote>\n"
        f"🕓 <i>Waiting for OTP… it will arrive here automatically.</i>\n"
        f"{DIV}"
    )
    kb = {"inline_keyboard": []}
    for num, _op in fetched:
        n = num.lstrip('+')
        kb["inline_keyboard"].append([{"text": f"+{n}", "icon_custom_emoji_id": "5226929552319594190",
                                       "copy_text": {"text": f"+{n}"}, "style": "primary"}])
    kb["inline_keyboard"].append([
        ibtn("Change Number", f"cc_{sid_short}_{c_code}", "5429386648431405093", "danger"),
        {"text": "OTP Group", "icon_custom_emoji_id": "5314366268898300483", "url": otp_button_link, "style": "success"},
    ])
    kb["inline_keyboard"].append([ibtn("BACK", f"srv_{sid_short}", CLOSE_ICON, "danger")])
    return msg, kb


def welcome_text(first_name, u):
    return (
        f"<blockquote>🔥 <b>PREMIUM NUMBER BOT</b></blockquote>\n{DIV}\n"
        f"👋 Welcome, <b>{html.escape(str(first_name))}</b>!\n"
        f"<i>Get virtual numbers, receive OTPs instantly and earn BDT.</i>\n{THIN}\n"
        f"<blockquote>💰 <b>Balance</b> ➜ {u.get('balance', 0):.2f} BDT\n"
        f"💬 <b>Total OTP</b> ➜ {u.get('total_otps', 0)}\n"
        f"👥 <b>Invites</b> ➜ {u.get('total_invites', 0)}</blockquote>\n{DIV}\n"
        f"👇 <b>Pick an option from the menu below.</b>"
    )


# ==========================================
# Broadcast
# ==========================================
def broadcast_worker(from_chat_id, message_id, target_msg_id):
    users = get_all_user_ids()
    ok = 0
    for uid in users:
        try:
            res = copy_message(uid, from_chat_id, message_id)
            if res and res.get("ok"):
                ok += 1
        except Exception:
            pass
        time.sleep(0.05)
    send_message(from_chat_id, f"✅ <b>Broadcast Completed!</b>\n{THIN}\nDelivered to <b>{ok}</b> / {len(users)} users.")
    if target_msg_id:
        edit_message(from_chat_id, target_msg_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())


# ==========================================
# Message handler
# ==========================================
def _set_state(user_id, state, msg_id=None):
    user_states[user_id] = {"state": state, "msg_id": msg_id}


def _clear_state(user_id):
    user_states.pop(user_id, None)


def handle_message(message):
    global current_db_mode, db_firebase, otp_button_link

    if message.get("chat", {}).get("type") != "private":
        return

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "") or ""
    message_id = message["message_id"]
    first_name = message["from"].get("first_name", "User")

    if text == "🔙 BACK" and user_id == ADMIN_ID:
        _clear_state(user_id)
        send_message(chat_id, "❌ <b>Action Cancelled!</b>", reply_markup=get_main_keyboard(user_id))
        send_message(chat_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        return

    # ---- Native chat picker result ----
    if "chat_shared" in message:
        shared = message["chat_shared"]["chat_id"]
        sd = user_states.get(user_id)
        if user_id == ADMIN_ID and sd:
            state, tmid = sd.get("state"), sd.get("msg_id")
            send_message(chat_id, "✅ <b>Successfully Selected!</b>", reply_markup=get_main_keyboard(user_id))
            if state == "waiting_otp_group":
                otp_forward_groups.clear()
                otp_forward_groups.append(str(shared))
                inv = tg("exportChatInviteLink", {"chat_id": shared})
                if inv and inv.get("ok"):
                    otp_button_link = inv["result"]
                save_local_data()
                if tmid:
                    edit_message(chat_id, tmid, f"🛡 <b>OTP GROUP MANAGEMENT</b>\n{THIN}\nManage settings below:",
                                 reply_markup=get_otp_group_keyboard())
            elif state == "waiting_dxa_w_group":
                bot_settings["w_group"] = str(shared)
                save_local_data()
                if tmid:
                    edit_message(chat_id, tmid, f"⚙️ <b>DXA CONTROL PANEL</b>\n{THIN}\nManage core settings:",
                                 reply_markup=dxa_control_keyboard())
            elif state == "waiting_fj_channel":
                details = get_chat_details(str(shared))
                if details:
                    force_join_channels.append(details)
                    save_local_data()
                    if tmid:
                        edit_message(chat_id, tmid, f"🔗 <b>FORCE JOIN SYSTEM</b>\n{THIN}\nManage channels below:",
                                     reply_markup=get_force_join_keyboard())
                elif tmid:
                    edit_message(chat_id, tmid, "❌ <b>Failed to verify channel! Make sure the bot is admin.</b>",
                                 reply_markup=get_back_only_keyboard())
            _clear_state(user_id)
        return

    # ---- Force join gate ----
    if not is_user_joined(user_id):
        fj = (
            f"<b>════《 🔥 ACCESS REQUIRED 》════</b>\n\n"
            f"<blockquote>🔗 <b>Join all channels below to use this bot.</b></blockquote>\n"
            f"<blockquote>✅ <b>After joining, tap VERIFY.</b></blockquote>"
        )
        send_message(chat_id, fj, reply_markup=get_force_join_alert_keyboard())
        return

    # ---- Input states ----
    sd = user_states.get(user_id)
    if sd and (text in MENU_TEXTS or text.startswith("/start")):
        _clear_state(user_id)
        sd = None

    if sd:
        state, tmid = sd.get("state"), sd.get("msg_id")

        def back_to(title, kb):
            if tmid:
                edit_message(chat_id, tmid, title, reply_markup=kb)

        def done():
            _clear_state(user_id)
            delete_message(chat_id, message_id)

        if state == "waiting_vk_key":
            voltx_keys.append(text.strip())
            save_local_data()
            back_to(f"🔑 <b>PANEL KEY SYSTEM</b>\n{THIN}\nManage API keys below:", get_voltx_keys_keyboard())
            return done()

        if state == "waiting_otp_link":
            if text.startswith("http"):
                otp_button_link = text.strip()
                save_local_data()
                back_to(f"🛡 <b>OTP GROUP MANAGEMENT</b>\n{THIN}\nManage settings below:", get_otp_group_keyboard())
            else:
                back_to("❌ <b>Invalid URL. Must start with http/https.</b>", get_back_only_keyboard())
            return done()

        if state == "waiting_main_channel_link":
            if text.startswith("http"):
                bot_settings["main_channel_link"] = text.strip()
                save_local_data()
                back_to(f"🛡 <b>OTP GROUP MANAGEMENT</b>\n{THIN}\nManage settings below:", get_otp_group_keyboard())
            else:
                back_to("❌ <b>Invalid URL. Must start with http/https.</b>", get_back_only_keyboard())
            return done()

        if state == "waiting_broadcast":
            back_to("⏳ <b>Broadcasting message to all users...</b>", None)
            threading.Thread(target=broadcast_worker, args=(chat_id, message_id, tmid), daemon=True).start()
            _clear_state(user_id)
            return

        if state == "waiting_firebase":
            try:
                if "document" in message:
                    fid = message["document"]["file_id"]
                    fi = tg("getFile", {"file_id": fid})
                    fpath = fi["result"]["file_path"]
                    text = http.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fpath}", timeout=20).text
                text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
                cred = json.loads(text)
                with open("temp_firebase.json", "w") as f:
                    json.dump(cred, f)
                try:
                    if not firebase_admin._apps:
                        firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
                    db_firebase = firestore.client()
                    current_db_mode = "firebase"
                    _sync_users_from_firebase()
                    try:
                        ref = db_firebase.collection('settings').document('bot_config')
                        doc = ref.get()
                        if not doc.exists:
                            ref.set({"bot_settings": bot_settings, "force_join_status": force_join_status,
                                     "force_join_channels": force_join_channels,
                                     "otp_forward_groups": otp_forward_groups, "otp_button_link": otp_button_link,
                                     "voltx_keys": voltx_keys, "voltx_auto_mode": voltx_auto_mode})
                        else:
                            _apply_cloud_config(doc.to_dict())
                            save_local_data(sync_cloud=False)
                    except Exception as e:
                        log("config sync error:", e)
                    back_to("⏳ <b>Syncing SQLite data to Firebase... Please wait.</b>", None)
                    migrate_sqlite_to_firebase()
                    back_to(get_owner_panel_text(), get_admin_inline_keyboard())
                    send_message(chat_id, "✅ <b>Firebase connected & synced!</b>")
                except Exception as e:
                    back_to(f"❌ <b>Failed to connect to Firebase:</b>\n<code>{html.escape(str(e))}</code>",
                            get_back_only_keyboard())
            except Exception:
                back_to("⚠️ <b>Invalid JSON. Please upload the .json file directly.</b>", get_back_only_keyboard())
            return done()

        if isinstance(state, str) and state.startswith("waiting_withdraw_amount_"):
            method = state[len("waiting_withdraw_amount_"):]
            u = get_user(user_id) or {}
            bal = u.get("balance", 0)
            min_w = bot_settings.get("min_withdraw", 10.0)
            try:
                amount = float(text.strip())
                if amount < min_w:
                    back_to(f"❌ <b>Minimum withdraw is {min_w} BDT.</b>\nTry again:", get_back_only_keyboard())
                elif amount > bal:
                    back_to(f"❌ <b>Insufficient balance!</b> You have {bal:.2f} BDT.\nTry again:",
                            get_back_only_keyboard())
                else:
                    _set_state(user_id, f"waiting_withdraw_number_{amount}_{method}", tmid)
                    back_to(f"✅ <b>Amount set: {amount:.2f} BDT</b>\n{THIN}\n💳 <b>Method:</b> {html.escape(method)}\n"
                            f"💬 <b>Now send your {html.escape(method)} account number:</b>", get_back_only_keyboard())
                    delete_message(chat_id, message_id)
                    return
            except ValueError:
                back_to("❌ <b>Invalid amount. Send numbers only.</b>\nTry again:", get_back_only_keyboard())
            return done()

        if isinstance(state, str) and state.startswith("waiting_withdraw_number_"):
            rest = state[len("waiting_withdraw_number_"):]
            amount_s, method = rest.split("_", 1)
            amount = float(amount_s)
            u = get_user(user_id) or {}
            if u.get("balance", 0) < amount:
                back_to("❌ <b>Insufficient balance!</b>", None)
            else:
                acc = text.strip()
                update_user_stats(user_id, -amount, 0)
                w_group = bot_settings.get("w_group", "")
                if w_group:
                    w_msg = (
                        f"🎁 <b>NEW WITHDRAW REQUEST</b>\n{DIV}\n"
                        f"👤 <b>User:</b> <a href='tg://user?id={user_id}'>{html.escape(first_name)}</a>\n{THIN}\n"
                        f"🆔 <b>ID:</b> <code>{user_id}</code>\n{THIN}\n"
                        f"💵 <b>Amount:</b> <b>{amount:.2f} BDT</b>\n{THIN}\n"
                        f"💳 <b>Method:</b> {html.escape(method)}\n{THIN}\n"
                        f"📱 <b>Number:</b> <code>{html.escape(acc)}</code>\n{DIV}"
                    )
                    w_markup = {"inline_keyboard": [[
                        ibtn("APPROVE", f"admin_w_approve_{user_id}_{amount}_{acc}", "5352694861990501856", "success"),
                        ibtn("REJECT", f"admin_w_reject_{user_id}_{amount}_{acc}", "5420130255174145507", "danger"),
                    ]]}
                    send_message(w_group, w_msg, reply_markup=w_markup)
                ok_msg = (
                    f"{DIV}\n✅ <b>WITHDRAW REQUEST SENT</b>\n{THIN}\n"
                    f"💵 <b>Amount:</b> {amount:.2f} BDT\n"
                    f"💳 <b>Method:</b> {html.escape(method)}\n"
                    f"📱 <b>Number:</b> <code>{html.escape(acc)}</code>\n{THIN}\n"
                    f"<i>⏳ Waiting for admin approval…</i>\n{DIV}"
                )
                if tmid:
                    delete_message(chat_id, tmid)
                send_message(chat_id, ok_msg, reply_markup=get_main_keyboard(user_id))
            return done()

        simple_float = {
            "waiting_dxa_ref_r": ("refer_reward", float, "dxa"),
            "waiting_dxa_min_w": ("min_withdraw", float, "dxa"),
            "waiting_dxa_cool": ("cooldown", int, "dxa"),
            "waiting_dxa_num_req": ("num_req", int, "dxa"),
            "waiting_dxa_def_rate": ("otp_default_rate", float, "otp"),
        }
        if state in simple_float:
            key, caster, target = simple_float[state]
            try:
                bot_settings[key] = caster(text.strip())
                save_local_data()
                if target == "dxa":
                    back_to(f"⚙️ <b>DXA CONTROL PANEL</b>\n{THIN}\nManage core settings:", dxa_control_keyboard())
                else:
                    back_to(f"💰 <b>OTP REWARD CONTROL</b>\n{THIN}\nManage rates below:", dxa_otp_control_keyboard())
            except ValueError:
                pass
            return done()

        if state == "waiting_w_method":
            bot_settings["w_methods"].append(text.strip())
            save_local_data()
            back_to(f"💳 <b>WITHDRAW METHODS</b>\n{THIN}\nManage methods below:", dxa_manage_w_methods_keyboard())
            return done()

        if state == "waiting_dxa_srv_rate":
            try:
                name, rate = text.split("-", 1)
                bot_settings["otp_service_rates"][name.strip()] = float(rate.strip())
                save_local_data()
                back_to(f"💰 <b>OTP REWARD CONTROL</b>\n{THIN}\nManage rates below:", dxa_otp_control_keyboard())
            except Exception:
                send_message(chat_id, "❌ Invalid format. Use: ServiceName - Rate (e.g. Telegram - 5.0)")
            return done()

        if isinstance(state, str) and state.startswith("waiting_rate_value_"):
            srv = state[len("waiting_rate_value_"):]
            try:
                bot_settings["otp_service_rates"][srv] = float(text.strip())
                save_local_data()
                back_to(f"💰 <b>OTP REWARD CONTROL</b>\n{THIN}\nManage rates below:", dxa_otp_control_keyboard())
            except ValueError:
                back_to(f"❌ <b>Invalid rate! Use numbers (e.g. 2.5).</b>", get_back_only_keyboard())
            return done()

        if state == "waiting_uc_id":
            try:
                tuid = int(text.strip())
                td = get_user(tuid)
                if td:
                    msg = (
                        f"👤 <b>USER PROFILE</b>\n{DIV}\n"
                        f"<b>Name:</b> {html.escape(str(td.get('first_name', 'User')))}\n"
                        f"<b>ID:</b> <code>{tuid}</code>\n"
                        f"<b>Balance:</b> {td.get('balance', 0):.2f} BDT\n"
                        f"<b>Total OTPs:</b> {td.get('total_otps', 0)}\n"
                        f"<b>Total Invites:</b> {td.get('total_invites', 0)}\n{DIV}"
                    )
                    back_to(msg, get_user_profile_keyboard(tuid))
                else:
                    back_to("❌ <b>User not found in database!</b>", get_user_control_keyboard())
            except ValueError:
                back_to("❌ <b>Invalid User ID format!</b>", get_user_control_keyboard())
            return done()

        if isinstance(state, str) and state.startswith("waiting_uc_balance_"):
            tuid = int(state[len("waiting_uc_balance_"):])
            try:
                update_user_stats(tuid, float(text.strip()), 0)
                td = get_user(tuid) or {}
                msg = (f"✅ <b>Balance updated!</b>\n{THIN}\n"
                       f"👤 <b>Name:</b> {html.escape(str(td.get('first_name', 'User')))}\n"
                       f"💵 <b>New Balance:</b> {td.get('balance', 0):.2f} BDT")
                back_to(msg, get_user_profile_keyboard(tuid))
            except ValueError:
                back_to("❌ <b>Invalid amount! Use numbers (e.g. 50 or -10).</b>", get_user_profile_keyboard(tuid))
            return done()

    # ---- Normal commands ----
    is_new_user = get_user(user_id) is None
    add_user(user_id, first_name)
    u = get_user(user_id) or {"balance": 0, "total_invites": 0, "total_otps": 0}

    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1:
            param = parts[1]
            if param.startswith("alloc_"):
                try:
                    _, req_range, req_sid = param.split("_", 2)
                    left = cooldown_left(user_id)
                    if left:
                        send_message(chat_id, f"⌛ <b>Please wait {left}s before requesting again.</b>")
                        return
                    user_cooldowns[user_id] = time.time()
                    wait = send_message(chat_id, f"⏳ <b>Fetching number for {html.escape(req_sid.title().replace('_', ' '))}…</b>")
                    msg, markup = get_number_allocation_content(req_sid, req_range, user_id=user_id)
                    if wait and "result" in wait:
                        edit_message(chat_id, wait["result"]["message_id"], msg, reply_markup=markup)
                    else:
                        send_message(chat_id, msg, reply_markup=markup)
                    return
                except Exception:
                    pass
            else:
                try:
                    inviter = int(param)
                    if is_new_user and inviter != user_id and get_user(inviter):
                        amt = bot_settings.get("refer_reward", 0.2)
                        update_user_stats(inviter, amt, 1)
                        send_message(inviter, f"🎉 <b>New Referral!</b>\n{THIN}\nSomeone joined with your link.\n"
                                              f"💰 You earned <b>{amt} BDT</b>.")
                except ValueError:
                    pass
        send_message(chat_id, welcome_text(first_name, u), reply_markup=get_main_keyboard(user_id))

    elif text == BTN_GET:
        msg, markup = get_services_content()
        send_message(chat_id, msg, reply_markup=markup)

    elif text == BTN_TRAFFIC:
        msg, markup = get_live_traffic_content()
        send_message(chat_id, msg, reply_markup=markup)

    elif text == BTN_INVITE:
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        rr = bot_settings.get("refer_reward", 0.2)
        msg = (
            f"{DIV}\n👥 <b>REFERRAL PROGRAM</b>\n{DIV}\n"
            f"🔗 <b>Your invite link:</b>\n<code>{link}</code>\n{THIN}\n"
            f"<blockquote>🎁 <b>PER INVITE</b> ➜ <b>{rr} TK</b>\n"
            f"📊 <b>TOTAL INVITES</b> ➜ <b>{u.get('total_invites', 0)}</b></blockquote>\n{DIV}"
        )
        send_message(chat_id, msg, reply_markup={"inline_keyboard": [[
            {"text": "COPY LINK", "icon_custom_emoji_id": "5379889727325350343",
             "copy_text": {"text": link}, "style": "success"}]]})

    elif text == BTN_BALANCE:
        w = (
            f"💰 <b>YOUR WALLET</b>\n{DIV}\n"
            f"👤 <b>NAME :</b> {html.escape(str(first_name))}\n{THIN}\n"
            f"🆔 <b>ID :</b> <code>{user_id}</code>\n{THIN}\n"
            f"<blockquote>💵 <b>BALANCE</b> ➜ <b>{u.get('balance', 0):.2f} BDT</b>\n"
            f"💬 <b>TOTAL OTP</b> ➜ {u.get('total_otps', 0)}\n"
            f"👥 <b>INVITES</b> ➜ {u.get('total_invites', 0)}</blockquote>\n{THIN}\n"
            f"📉 <b>Min withdraw:</b> {bot_settings.get('min_withdraw', 10.0)} BDT\n"
            f"💳 <b>SELECT WITHDRAW METHOD 👇</b>"
        )
        kb = {"inline_keyboard": []}
        for m in bot_settings.get("w_methods", []):
            kb["inline_keyboard"].append([ibtn(m, f"user_withdraw_{m}", "5431783519355444455", "primary")])
        send_message(chat_id, w, reply_markup=kb)

    elif text == BTN_LEADER:
        send_message(chat_id, get_leaderboard_text(), reply_markup=get_leaderboard_keyboard())

    elif text == BTN_OWNER:
        if user_id == ADMIN_ID:
            send_message(chat_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        else:
            send_message(chat_id, "⚠️ <b>Access Denied!</b>\nThis menu is restricted to the admin.")


# ==========================================
# Callback handler
# ==========================================
def handle_callback(cq):
    global voltx_auto_mode, force_join_status
    qid = cq["id"]
    user_id = cq["from"]["id"]
    data = cq.get("data", "")
    chat_id = cq["message"]["chat"]["id"]
    mid = cq["message"]["message_id"]

    if data == "ignore_action":
        answer_callback_query(qid)
        return

    if data == "check_fj_joined":
        if is_user_joined(user_id):
            delete_message(chat_id, mid)
            send_message(chat_id, "✅ <b>Thank you for joining! You can now use the bot.</b>",
                         reply_markup=get_main_keyboard(user_id))
        else:
            answer_callback_query(qid, "❌ You haven't joined all channels!", show_alert=True)
        return

    if not is_user_joined(user_id):
        answer_callback_query(qid, "Join channels first!", show_alert=True)
        return

    if data == "refresh_traffic":
        msg, markup = get_live_traffic_content()
        edit_message(chat_id, mid, msg, reply_markup=markup)
        answer_callback_query(qid, "Traffic refreshed!")
        return

    if data == "back_to_services":
        msg, markup = get_services_content()
        edit_message(chat_id, mid, msg, reply_markup=markup)
        answer_callback_query(qid)
        return

    if data.startswith("srv_"):
        msg, markup, err = get_countries_content(data[4:])
        if err:
            answer_callback_query(qid, err, show_alert=True)
        else:
            edit_message(chat_id, mid, msg, reply_markup=markup)
            answer_callback_query(qid)
        return

    if data.startswith("cc_"):
        parts = data.split("_", 2)
        if len(parts) < 3:
            answer_callback_query(qid)
            return
        sid_short, c_code = parts[1], parts[2]
        left = cooldown_left(user_id)
        if left:
            answer_callback_query(qid, f"Please wait {left} seconds.", show_alert=True)
            return
        user_cooldowns[user_id] = time.time()
        answer_callback_query(qid, "Allocating number...")
        edit_message(chat_id, mid, f"⏳ <b>Fetching best range and allocating your number…</b>")
        msg, markup = get_number_allocation_content(sid_short, c_code, user_id=user_id)
        edit_message(chat_id, mid, msg, reply_markup=markup)
        return

    if data == "refresh_leaderboard":
        edit_message(chat_id, mid, get_leaderboard_text(), reply_markup=get_leaderboard_keyboard())
        answer_callback_query(qid, "Leaderboard refreshed!")
        return

    if data.startswith("user_withdraw_"):
        method = data[len("user_withdraw_"):]
        bal = (get_user(user_id) or {}).get("balance", 0)
        min_w = bot_settings.get("min_withdraw", 10.0)
        if bal < min_w:
            answer_callback_query(qid, f"❌ Minimum withdraw is {min_w} BDT. You have {bal:.2f} BDT.", show_alert=True)
            return
        _set_state(user_id, f"waiting_withdraw_amount_{method}", mid)
        edit_message(chat_id, mid,
                     f"💳 <b>WITHDRAW via {html.escape(method)}</b>\n{THIN}\n"
                     f"💵 <b>Your balance:</b> {bal:.2f} BDT\n"
                     f"💬 <b>Enter the amount you want to withdraw:</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
        return

    if data == "user_cancel":
        _clear_state(user_id)
        delete_message(chat_id, mid)
        send_message(chat_id, "❌ Action cancelled.", reply_markup=get_main_keyboard(user_id))
        answer_callback_query(qid)
        return

    # ---------- Admin only ----------
    if user_id != ADMIN_ID:
        answer_callback_query(qid, "Access Denied!", show_alert=True)
        return

    if data.startswith("admin_w_approve_") or data.startswith("admin_w_reject_"):
        key = (chat_id, mid)
        with state_lock:
            if key in processed_withdraws:
                answer_callback_query(qid, "Already processed.", show_alert=True)
                return
            processed_withdraws.add(key)

        parts = data.split("_", 5)
        action, req_uid, amount, acc = parts[2], int(parts[3]), float(parts[4]), parts[5]
        masked = f"{acc[:3]}DXA{acc[-3:]}" if len(acc) >= 6 else acc

        text = cq.get("message", {}).get("text", "")
        m1 = re.search(r"User:\s*(.+)", text)
        m2 = re.search(r"Method:\s*(.+)", text)
        req_name = m1.group(1).strip() if m1 else "User"
        req_method = m2.group(1).strip() if m2 else "Unknown"

        if action == "approve":
            btn_text, style, icon = "APPROVED BY ADMIN", "success", "5352694861990501856"
            send_message(req_uid, f"🎉 <b>Withdrawal Approved!</b>\n{THIN}\n"
                                  f"💵 <b>{amount:.2f} BDT</b> has been sent to <code>{html.escape(masked)}</code>.")
        else:
            btn_text, style, icon = "REJECTED BY ADMIN", "danger", "5420130255174145507"
            update_user_stats(req_uid, amount, 0)
            send_message(req_uid, f"⚠️ <b>Withdrawal Rejected!</b>\n{THIN}\n"
                                  f"Your request of <b>{amount:.2f} BDT</b> to <code>{html.escape(masked)}</code> "
                                  f"was rejected and refunded.")

        updated = (
            f"🎁 <b>WITHDRAW REQUEST PROCESSED</b>\n{DIV}\n"
            f"👤 <b>User:</b> <a href='tg://user?id={req_uid}'>{html.escape(req_name)}</a>\n{THIN}\n"
            f"🆔 <b>ID:</b> <code>{req_uid}</code>\n{THIN}\n"
            f"💵 <b>Amount:</b> <b>{amount:.2f} BDT</b>\n{THIN}\n"
            f"💳 <b>Method:</b> {html.escape(req_method)}\n{THIN}\n"
            f"📱 <b>Number:</b> <code>{html.escape(masked)}</code>\n{DIV}"
        )
        edit_message(chat_id, mid, updated, reply_markup={"inline_keyboard": [[
            ibtn(btn_text, "ignore_action", icon, style)]]})
        answer_callback_query(qid, f"Request {action}d!")
        return

    # ----- Panel key manager -----
    if data == "manage_voltx":
        edit_message(chat_id, mid, f"🔑 <b>PANEL KEY SYSTEM</b>\n{THIN}\nManage API keys below:",
                     reply_markup=get_voltx_keys_keyboard())
        answer_callback_query(qid)
    elif data == "toggle_vk":
        voltx_auto_mode = not voltx_auto_mode
        save_local_data()
        edit_message(chat_id, mid, f"🔑 <b>PANEL KEY SYSTEM</b>\n{THIN}\nManage API keys below:",
                     reply_markup=get_voltx_keys_keyboard())
        answer_callback_query(qid, f"Panel mode: {'ON' if voltx_auto_mode else 'OFF'}")
    elif data == "add_vk":
        _set_state(user_id, "waiting_vk_key", mid)
        edit_message(chat_id, mid, "🔑 <b>Send the new Panel API key.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data.startswith("del_vk_"):
        idx = int(data[7:])
        if idx < len(voltx_keys):
            if len(voltx_keys) > 1:
                voltx_keys.pop(idx)
                save_local_data()
                edit_message(chat_id, mid, f"🔑 <b>PANEL KEY SYSTEM</b>\n{THIN}\nManage API keys below:",
                             reply_markup=get_voltx_keys_keyboard())
                answer_callback_query(qid, "Key deleted!")
            else:
                answer_callback_query(qid, "Cannot delete the only key!", show_alert=True)

    # ----- Force join -----
    elif data == "manage_fj":
        edit_message(chat_id, mid, f"🔗 <b>FORCE JOIN SYSTEM</b>\n{THIN}\nManage channels below:",
                     reply_markup=get_force_join_keyboard())
        answer_callback_query(qid)
    elif data == "toggle_fj":
        force_join_status = not force_join_status
        save_local_data()
        edit_message(chat_id, mid, f"🔗 <b>FORCE JOIN SYSTEM</b>\n{THIN}\nManage channels below:",
                     reply_markup=get_force_join_keyboard())
        answer_callback_query(qid, f"Force Join: {'ON' if force_join_status else 'OFF'}")
    elif data == "add_fj":
        _set_state(user_id, "waiting_fj_channel", mid)
        kb = {"keyboard": [[{"text": "Select Force Join Channel", "request_chat": {"request_id": 3, "chat_is_channel": True}}],
                           [{"text": "🔙 BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "👇 <b>Select channel below:</b>\n<i>(Make sure the bot is admin there)</i>", reply_markup=kb)
        answer_callback_query(qid)
    elif data.startswith("del_fj_"):
        idx = int(data[7:])
        if idx < len(force_join_channels):
            force_join_channels.pop(idx)
        save_local_data()
        edit_message(chat_id, mid, f"🔗 <b>FORCE JOIN SYSTEM</b>\n{THIN}\nManage channels below:",
                     reply_markup=get_force_join_keyboard())
        answer_callback_query(qid, "Channel deleted!")

    # ----- OTP group -----
    elif data == "manage_otp_group":
        edit_message(chat_id, mid, f"🛡 <b>OTP GROUP MANAGEMENT</b>\n{THIN}\nManage settings below:",
                     reply_markup=get_otp_group_keyboard())
        answer_callback_query(qid)
    elif data == "add_otp_group":
        _set_state(user_id, "waiting_otp_group", mid)
        kb = {"keyboard": [[{"text": "Select OTP Group", "request_chat": {"request_id": 1, "chat_is_channel": False}}],
                           [{"text": "🔙 BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "👇 <b>Select OTP group below:</b>", reply_markup=kb)
        answer_callback_query(qid)
    elif data.startswith("del_otp_group_"):
        idx = int(data[14:])
        if idx < len(otp_forward_groups):
            otp_forward_groups.pop(idx)
        save_local_data()
        edit_message(chat_id, mid, f"🛡 <b>OTP GROUP MANAGEMENT</b>\n{THIN}\nManage settings below:",
                     reply_markup=get_otp_group_keyboard())
        answer_callback_query(qid, "Group deleted!")
    elif data == "edit_otp_link":
        _set_state(user_id, "waiting_otp_link", mid)
        edit_message(chat_id, mid, "🔗 <b>Send the new URL for the button under forwarded OTPs.</b>",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data == "edit_main_channel":
        _set_state(user_id, "waiting_main_channel_link", mid)
        edit_message(chat_id, mid, "🔗 <b>Send the URL for the MAIN CHANNEL button.</b>",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)

    # ----- DXA control -----
    elif data == "dxa_control":
        edit_message(chat_id, mid, f"⚙️ <b>DXA CONTROL PANEL</b>\n{THIN}\nManage core settings:",
                     reply_markup=dxa_control_keyboard())
        answer_callback_query(qid)
    elif data in ("dxa_min_w", "dxa_ref_r", "dxa_def_rate", "dxa_cool", "dxa_num_req"):
        cfg = {
            "dxa_min_w": ("waiting_dxa_min_w", "💸 <b>Enter new minimum withdraw (e.g. 50):</b>"),
            "dxa_ref_r": ("waiting_dxa_ref_r", "🎁 <b>Enter new referral reward (e.g. 5.0):</b>"),
            "dxa_def_rate": ("waiting_dxa_def_rate", "💰 <b>Enter new default OTP rate (e.g. 0.5):</b>"),
            "dxa_cool": ("waiting_dxa_cool", "⏳ <b>Enter new cooldown in seconds (e.g. 10):</b>"),
            "dxa_num_req": ("waiting_dxa_num_req", "📱 <b>Numbers per request (e.g. 3):</b>"),
        }[data]
        _set_state(user_id, cfg[0], mid)
        edit_message(chat_id, mid, cfg[1], reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data == "dxa_otp_control":
        edit_message(chat_id, mid, f"💰 <b>OTP REWARD CONTROL</b>\n{THIN}\nManage rates below:",
                     reply_markup=dxa_otp_control_keyboard())
        answer_callback_query(qid)
    elif data.startswith("del_srv_rate_"):
        name = data[len("del_srv_rate_"):]
        bot_settings["otp_service_rates"].pop(name, None)
        save_local_data()
        edit_message(chat_id, mid, f"💰 <b>OTP REWARD CONTROL</b>\n{THIN}\nManage rates below:",
                     reply_markup=dxa_otp_control_keyboard())
        answer_callback_query(qid, f"Rate for {name} deleted!")
    elif data == "dxa_srv_rate":
        kb = {"inline_keyboard": []}
        row = []
        for sid, sd in list(voltx_dynamic_data.items()):
            safe = html.escape(str(sid))
            row.append(ibtn(safe, f"s_rt_{safe[:15]}", sd["emoji_id"], "primary"))
            if len(row) == 2:
                kb["inline_keyboard"].append(row)
                row = []
        if row:
            kb["inline_keyboard"].append(row)
        kb["inline_keyboard"].append([ibtn("Manual Entry", "dxa_srv_rate_manual", None, "success")])
        kb["inline_keyboard"].append([ibtn("BACK", "dxa_otp_control", BACK_ICON, "danger")])
        edit_message(chat_id, mid, "💰 <b>Select a service to set its rate:</b>", reply_markup=kb)
        answer_callback_query(qid)
    elif data == "dxa_srv_rate_manual":
        _set_state(user_id, "waiting_dxa_srv_rate", mid)
        edit_message(chat_id, mid, "💰 <b>Enter service rate.</b>\nFormat: <code>ServiceName - Rate</code>\n"
                                   "Example: <code>Telegram - 2.5</code>", reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data.startswith("s_rt_"):
        short = data[5:]
        full = short
        for sid in voltx_dynamic_data:
            if str(sid).startswith(short):
                full = str(sid)
                break
        _set_state(user_id, f"waiting_rate_value_{full}", mid)
        edit_message(chat_id, mid, f"💰 <b>Enter reward rate for {html.escape(full)}:</b>\n(e.g. 2.5)",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data == "manage_w_methods":
        edit_message(chat_id, mid, f"💳 <b>WITHDRAW METHODS</b>\n{THIN}\nManage methods below:",
                     reply_markup=dxa_manage_w_methods_keyboard())
        answer_callback_query(qid)
    elif data == "add_w_method":
        _set_state(user_id, "waiting_w_method", mid)
        edit_message(chat_id, mid, "💳 <b>Enter new withdraw method name (e.g. bKash):</b>",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data.startswith("del_w_method_"):
        idx = int(data[13:])
        if idx < len(bot_settings["w_methods"]):
            bot_settings["w_methods"].pop(idx)
        save_local_data()
        edit_message(chat_id, mid, f"💳 <b>WITHDRAW METHODS</b>\n{THIN}\nManage methods below:",
                     reply_markup=dxa_manage_w_methods_keyboard())
        answer_callback_query(qid, "Method deleted!")
    elif data == "dxa_w_group":
        _set_state(user_id, "waiting_dxa_w_group", mid)
        kb = {"keyboard": [[{"text": "Select Withdraw Group", "request_chat": {"request_id": 2, "chat_is_channel": False}}],
                           [{"text": "🔙 BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "👇 <b>Select withdraw group below:</b>", reply_markup=kb)
        answer_callback_query(qid)

    # ----- Broadcast / Firebase / Users -----
    elif data == "broadcast_menu":
        _set_state(user_id, "waiting_broadcast", mid)
        edit_message(chat_id, mid, f"📣 <b>BROADCAST SYSTEM</b>\n{THIN}\n"
                                   f"Send any text, photo, video or audio to broadcast to all users.",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data == "upload_firebase":
        _set_state(user_id, "waiting_firebase", mid)
        edit_message(chat_id, mid, f"🔥 <b>FIREBASE SETUP</b>\n{THIN}\n"
                                   f"Upload the Service Account <b>.json file</b> (or paste its full content).",
                     reply_markup=get_upload_firebase_keyboard())
        answer_callback_query(qid, "Send JSON now")
    elif data == "user_control":
        edit_message(chat_id, mid, f"👥 <b>USER CONTROL</b>\n{DIV}\n📊 <b>Total users:</b> {get_total_users()}\n\n👇 Manage users below:",
                     reply_markup=get_user_control_keyboard())
        answer_callback_query(qid)
    elif data == "uc_profile":
        _set_state(user_id, "waiting_uc_id", mid)
        edit_message(chat_id, mid, "🆔 <b>Send the Telegram user ID to view profile:</b>",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data.startswith("uc_balance_"):
        tuid = int(data[len("uc_balance_"):])
        _set_state(user_id, f"waiting_uc_balance_{tuid}", mid)
        edit_message(chat_id, mid, "💵 <b>Send the amount to add or subtract.</b>\n<i>(e.g. 50 to add, -10 to deduct)</i>",
                     reply_markup=get_back_only_keyboard())
        answer_callback_query(qid)
    elif data == "back_to_admin":
        _clear_state(user_id)
        edit_message(chat_id, mid, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        answer_callback_query(qid)
    elif data == "db_status":
        answer_callback_query(qid, f"Current DB: {current_db_mode.upper()}", show_alert=True)
    elif data == "close_panel":
        answer_callback_query(qid, "Closed")
        delete_message(chat_id, mid)
    else:
        answer_callback_query(qid)


# ==========================================
# Render keep-alive web server (fixes "No open ports detected")
# ==========================================
class _HealthHandler(BaseHTTPRequestHandler):
    def _ok(self, body=True):
        payload = b"OK - bot is running"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def do_GET(self):
        self._ok(True)

    def do_HEAD(self):
        self._ok(False)

    def log_message(self, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        log(f"🌐 Health server listening on port {port}")
    except Exception as e:
        log("Health server error:", e)


# ==========================================
# Main
# ==========================================
def safe_run(fn, arg):
    try:
        fn(arg)
    except Exception:
        traceback.print_exc()


def main():
    global BOT_USERNAME

    start_health_server()   # bind the port FIRST so Render detects it immediately

    if not BOT_TOKEN:
        log("❌ BOT_TOKEN env var is missing! Add it in Render → Environment.")
        while True:
            time.sleep(60)

    load_local_data()
    init_sqlite()
    init_firebase_from_file()

    BOT_USERNAME = get_bot_info()
    set_bot_commands()
    tg("deleteWebhook", {"drop_pending_updates": False})

    threading.Thread(target=voltx_console_listener, daemon=True).start()
    threading.Thread(target=voltx_sms_listener, daemon=True).start()
    threading.Thread(target=auto_cache_menu_thread, daemon=True).start()

    log(f"🚀 Bot @{BOT_USERNAME} is running")

    offset = None
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
            if offset:
                params["offset"] = offset
            res = http.post(BASE_URL + "getUpdates", json=params, timeout=45).json()
            if res.get("ok"):
                for upd in res["result"]:
                    offset = upd["update_id"] + 1
                    if "message" in upd:
                        threading.Thread(target=safe_run, args=(handle_message, upd["message"]), daemon=True).start()
                    elif "callback_query" in upd:
                        threading.Thread(target=safe_run, args=(handle_callback, upd["callback_query"]), daemon=True).start()
            else:
                log("getUpdates error:", res.get("description"))
                time.sleep(3)
        except Exception as e:
            log("Polling error:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()