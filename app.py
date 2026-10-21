import html
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import random
import re
import sqlite3
import threading
import time
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# ==========================================
# Configuration
# ==========================================
BOT_TOKEN = "8762662830:AAEDhKXAMVnaUZIPedJ7ksDKi6jnFEziSmg"
ADMIN_ID = 8271633124
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
BOT_USERNAME = ""

# 2oo9 API Configuration
API_2OO9_BASE = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
API_2OO9_KEY_DEFAULT = "M4DDE8HGFJ9"

# Global states
current_db_mode = "sqlite"
db_firebase = None
waiting_for_firebase = False
user_states = {}

# User & Cooldown States
user_cache = {}
user_active_sessions = {}  # format: {"number": user_id}
user_cooldowns = {}

# Voltx Auto System States
voltx_auto_mode = True
voltx_keys = [API_2OO9_KEY_DEFAULT]
force_join_status = False
force_join_channels = []

# OTP Forwarding States
otp_forward_groups = []
otp_button_link = "https://t.me/your_default_bot"
recent_success_otps = set()

voltx_dynamic_data = {}
recent_traffic = []
daily_stats = {"date": "", "numbers": 0, "otps": 0}  # 🌟 Daily Stats Tracker
daily_user_otps = {"date": "", "users": {}}

# 🌟 Caching Variables for Rocket Speed!
cached_services_kb = None
cached_countries_kb = {}
cached_leaderboard_text = ""

# ==========================================
# Global Emojis Map & Premium Apps Setup
# ==========================================
DEFAULT_GLOBAL_BODY_EMOJIS = {
    # System & Interface Icons
    "➖": "5870818207383686839",
    "🚫": "5334807341109908955",
    "😒": "5334763399299506604",
    "🖥": "5334880948259427772",
    "🌐": "5334590977837403844",
    "🌟": "5337102391244263212",
    "🕓": "5336983442125001376",
    "⌛": "5337172996211648018",
    "💬": "5337302974806922068",
    "🔐": "5337255927735163754",
    "🍏": "5337132498965010628",
    "❔": "5336850036145823599",
    "⚠️": "5336944168944047463",
    "🔥": "5337267511261960341",
    "💸": "5429612421977253466",
    "🥚": "5348390922507817684",
    "👨‍⚖": "5334763399299506604",
    "🐁": "5348494358205207761",
    "🧻": "5348486915026884464",
    "⚗": "5346311574221000149",
    "🛴": "5348075478634766440",
    "📊": "5353032893096567467",
    "🔢": "5226929552319594190",
    "👤": "5352861489541714456",
    "📁": "5352721946054268944",
    "🚀": "5352597830089347330",
    "💎": "5352838545826420397",
    "📍": "5352922460897452503",
    "👋": "5353027129250453493",
    "✅": "5352694861990501856",
    "1️⃣": "5352651766288652742",
    "2️⃣": "5355186458418257716",
    "3️⃣": "5352867219028091093",
    "4️⃣": "5352566657216714037",
    "5️⃣": "5353086880835474989",
    "6️⃣": "5354859211975071385",
    "7️⃣": "5352859127309707652",
    "8️⃣": "5352957533600389988",
    "9️⃣": "5353060913463204207",
    "🔤": "5352727417842606016",
    "📣": "5352980533150259581",
    "📤": "5353001161878182134",
    "✨": "5352552689983067014",
    "🔹": "5352638632278660622",
    "🎙": "5355102594886833928",
    "💴": "5352985330628730418",
    "📅": "5352585194295564660",
    "📴": "5352974971167611327",
    "✏️": "5395444784611480792",
    "📱": "5337132498965010628",
    "🔗": "5420517437885943844",
    "❌": "5420130255174145507",
    "⚙️": "5420155432272438703",
    "🫂": "5420145051336485498",
    "➕": "5420323438508155202",
    "🗑": "5422557736330106570",
    "🎁": "5420396762189831222",
    "➤": "5420618897898381296",
    "🏢": "5420156334215565595",
    "💳": "5190899075968441286",
    "📝": "5192739271886282680",
    "🛡": "5190447043545438788",
    "🤝": "5192805934073685937",
    "💰": "5190576863226933563",
    "👀": "5190645917711114179",
    "🕹": "5193100774988617665",
    "🟢": "5192812028632274956",
    "🧪": "5190781475468915802",
    "🎨": "5190751148704833975",
    "📂": "5257969839313526622",
    "🌍": "5780471598922337683",
    "📌": "5318986077455795572",
    "📢": "5789428375261023681",
    "🆔": "5226929552319594190",
    "📈": "5352877703043258544",
    "🔔": "5352980533150259581",
    "🏦": "5429612421977253466",
    "🧾": "5192739271886282680",
    "👨‍⚖️": "5334763399299506604",
    "🔍": "5463352748751753567",
    "🔑": "5197288647275071607",
    "🏆": "5240021484516185513",
    "🚦": "5429571662737611814",
    "👥": "5420145051336485498",
    "🎯": "5352922460897452503",
    "📶": "5429353834881261942",
    "⏳": "5337172996211648018",
    "🔸": "5429576112323732785",
    "🎉": "5420396762189831222",
    "💵": "5429612421977253466",
    "👑": "5352838545826420397",
    "↳": "5420618897898381296",
    # 🌟 Real Custom Emoji IDs from Screen Captures
    "🇦🇪": "5294314831824835370",
    "🇦🇫": "5291937511591925566",
    "🇦🇬": "5294005972136647964",
    "🇦🇱": "5294202819077756005",
    "🇦🇲": "5291978717508164018",
    "🇦🇴": "5294516785482062829",
    "🇦🇷": "5292208210495689627",
    "🇦🇸": "5291994273879709721",
    "🇦🇹": "5291975174160145850",
    "🇦🇺": "5294444247779399477",
    "🇦🇼": "5294007002928798927",
    "🇦🇿": "5294323533428579078",
    "🇧🇦": "5292063805105263554",
    "🇧🇧": "5294526187165471742",
    "🇧🇩": "5291824687096027834",
    "🇧🇪": "5291774466043435275",
    "🇧🇫": "5294153164960848949",
    "🇧🇬": "5294308947719640437",
    "🇧🇭": "5294108398516720753",
    "🇧🇮": "5294051631933967760",
    "🇧🇯": "5293984969746566866",
    "🇧🇲": "5294189019347833274",
    "🇧🇳": "5292098293692650297",
    "🇧🇴": "5294201479047957700",
    "🇧🇷": "5291892222975172390",
    "🇧🇸": "5294031587321600012",
    "🇧🇹": "5294121983498277263",
    "🇧🇼": "5294026179957772585",
    "🇧🇾": "5294134426018536120",
    "🇧🇿": "5294171848068584842",
    "🇨🇦": "5292290347450259214",
    "🇨🇩": "5292021761670404922",
    "🇨🇫": "5294210571493724819",
    "🇨🇬": "5294035229453865597",
    "🇨🇭": "5291791748991835084",
    "🇨🇮": "5291892096607739008",
    "🇨🇱": "5294231037012888049",
    "🇨🇲": "5291997306126626950",
    "🇨🇳": "5294068833277990704",
    "🇨🇴": "5294010206974397371",
    "🇨🇷": "5292098684534675100",
    "🇨🇺": "5291963947115631526",
    "🇨🇻": "5292203503211535593",
    "🇨🇾": "5294062721539526918",
    "🇨🇿": "5294242852467923382",
    "🇩🇪": "5292013274815028523",
    "🇩🇯": "529438934628405146",
    "🇩🇰": "5294531860817268837",
    "🇩🇲": "5294177148058228060",
    "🇩🇴": "5291826830284709120",
    "🇩🇿": "5294048127240655242",
    "🇪🇨": "5294378161117614233",
    "🇪🇪": "5294343084119708700",
    "🇪🇬": "5294058972033076492",
    "🇪🇷": "5294127824653797277",
    "🇪🇸": "5294513087515216901",
    "🇪🇹": "5294471336138134209",
    "🇫🇮": "5294444247779399477",
    "🇫🇯": "5294097669688415562",
    "🇫🇲": "5291838156113470124",
    "🇫🇷": "5291817660529533837",
    "🇬🇦": "5294321325815338913",
    "🇬🇧": "5293993521026453119",
    "🇬🇩": "5294505107465982830",
    "🇬🇪": "5294349389131697267",
    "🇬🇭": "5294347396266873249",
    "🇬🇲": "5294399820637688352",
    "🇬🇳": "5294336633078831209",
    "🇬🇶": "5294429743674840973",
    "🇬🇷": "5291948395039054764",
    "🇬🇹": "5294158486425325375",
    "🇬🇼": "5294409819321550432",
    "🇬🇾": "5292062692708736193",
    "🇭🇰": "5292166459118606932",
    "🇭🇳": "5294240825243358100",
    "🇭🇷": "5291999676948569127",
    "🇭🇹": "5292045130587462814",
    "🇭🇺": "5294229581018975260",
    "🇮🇩": "5294325010897327367",
    "🇮🇪": "5294471971793293647",
    "🇮🇱": "5294069056616289553",
    "🇮🇳": "5291933173674957761",
    "🇮🇶": "5294318478252070646",
    "🇮🇷": "5294220170745630736",
    "🇮🇸": "5294354358408859664",
    "🇮🇹": "5291826830284709120",
    "🇯🇲": "5294505107465982830",
    "🇯🇴": "5294236848103643477",
    "🇯🇵": "5291799063321139445",
    "🇰🇪": "5292111852904416801",
    "🇰🇬": "5292091954320922577",
    "🇰🇭": "5294225191562400452",
    "🇰🇮": "5294538934628405146",
    "🇰🇲": "5294351381996521508",
    "🇰🇳": "5294463274484521342",
    "🇰🇵": "5294193812531333564",
    "🇰🇷": "5294408281723262763",
    "🇰🇼": "5292066437920218075",
    "🇰🇿": "5294227175837290463",
    "🇱🇦": "5291981530711746037",
    "🇱🇧": "5294193108156699621",
    "🇱🇨": "5294283689016973348",
    "🇱🇮": "5292048742654957785",
    "🇱🇰": "5292102670264328257",
    "🇱🇷": "5291793810576137439",
    "🇱🇸": "5292040693886247604",
    "🇱🇹": "5294343084119708700",
    "🇱🇺": "5294423709245787718",
    "🇱🇻": "5292236016113966127",
    "🇱🇾": "5291858711826946840",
    "🇲🇦": "5292108962391414885",
    "🇲🇨": "5291901034434682297",
    "🇲🇩": "5291979952605333077",
    "🇲🇪": "5294458584380230360",
    "🇲🇬": "5292086972158858331",
    "🇲🇭": "5294180730060954484",
    "🇲🇰": "5294023611567332075",
    "🇲🇱": "5294456308047563965",
    "🇲🇲": "5294254478944393569",
    "🇲🇳": "5294316532631883496",
    "🇲🇴": "6323557758096377611",
    "🇲🇷": "5294429743674840973",
    "🇲🇹": "5294532213004588353",
    "🇲🇺": "5294127824653797277",
    "🇲🇻": "5292004203844097218",
    "🇲🇼": "5294241881805312589",
    "🇲🇽": "5294535073452809778",
    "🇲🇾": "5291858351049696702",
    "🇲🇿": "5294086708931874940",
    "🇳🇦": "5294013428199869487",
    "🇳🇪": "5291809418487290691",
    "🇳🇬": "5294456308047563965",
    "🇳🇮": "5294240825243358100",
    "🇳🇱": "5291917797692042265",
    "🇳🇴": "5291761718580502030",
    "🇳🇵": "5294458756178924088",
    "🇳🇷": "5434131139889478358",
    "🇳🇿": "5294189019347833274",
    "🇴🇲": "5291813666209946812",
    "🇵🇦": "5291959935616178405",
    "🇵🇪": "5292099427564018941",
    "🇵🇬": "5294362935458548705",
    "🇵🇰": "5291825606219029010",
    "🇵🇱": "5291798075478661634",
    "🇵🇷": "5292121516580820347",
    "🇵🇸": "5294289826525238172",
    "🇵🇹": "5294436555492973610",
    "🇵🇼": "5294448585696368047",
    "🇵🇾": "5294525611639852679",
    "🇶🇦": "5292166360334357676",
    "🇷🇴": "5291780728105753403",
    "🇷🇸": "5294458584380230360",
    "🇷🇺": "5294335323113807278",
    "🇷🇼": "5294191265615729158",
    "🇸🇦": "4985897134424328239",
    "🇸🇧": "5294283890880433237",
    "🇸🇨": "5292147350809106831",
    "🇸🇩": "5294177148058228060",
    "🇸🇪": "5291737091238026321",
    "🇸🇬": "5294451304410663668",
    "🇸🇮": "5294279359689938006",
    "🇸🇰": "5294538440707166931",
    "🇸🇱": "5292183188016222701",
    "🇸🇲": "5294163983983463099",
    "🇸🇳": "5292087023698466689",
    "🇸🇴": "5294058817414255960",
    "🇸🇷": "5294396668131692138",
    "🇸🇸": "5294177148058228060",
    "🇸🇹": "5292183188016222701",
    "🇸🇻": "5294231037012888049",
    "🇸🇾": "5294013428199869487",
    "🇸🇿": "5294312482477724867",
    "🇹🇩": "5291780728105753403",
    "🇹🇬": "5294097669688415562",
    "🇹🇭": "5293994384314882755",
    "🇹🇯": "5294120269806328883",
    "🇹🇱": "5294448585696368047",
    "🇹🇲": "5294098958178603764",
    "🇹🇳": "5294484680601521871",
    "🇹🇴": "5294283689016973348",
    "🇹🇷": "5293993400767367408",
    "🇹🇹": "5294362935458548705",
    "🇹🇻": "5433684690923961019",
    "🇹🇼": "5294095745543069603",
    "🇹🇿": "5292146096678658977",
    "🇺🇦": "5294263837678131580",
    "🇺🇬": "5294192317882716626",
    "🇺🇸": "5294244076533600593",
    "🇺🇾": "5291928449210932974",
    "🇺🇿": "5294217645304864345",
    "🇻🇦": "5294215205763434181",
    "🇻🇨": "5294228039125718124",
    "🇻🇪": "5294476442854247878",
    "🇻🇳": "5294235963340379688",
    "🇻🇺": "5294444858569636804",
    "🇼🇸": "5294283689016973348",
    "🇾🇪": "5294058972033076492",
    "🇿🇦": "5294325281480266304",
    "🇿🇲": "5294100109229838880",
    "🇿🇼": "5294422158762592930",
    "🏴󠁧󠁢󠁷󠁬󠁳󠁿": "5294139949346476093",
}

DEFAULT_PREMIUM_APPS = {
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

GLOBAL_BODY_EMOJIS = dict(DEFAULT_GLOBAL_BODY_EMOJIS)
PREMIUM_APPS = {k: dict(v) for k, v in DEFAULT_PREMIUM_APPS.items()}


def apply_emojis(text):
  hidden = []

  def hide(match):
    hidden.append(match.group(0))
    return f"__TG_EMOJI_{len(hidden)-1}__"

  text = re.sub(r"<tg-emoji[^>]*>.*?</tg-emoji>", hide, text)
  for char, eid in GLOBAL_BODY_EMOJIS.items():
    text = text.replace(char, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>')
  for i, h in enumerate(hidden):
    text = text.replace(f"__TG_EMOJI_{i}__", h)
  return text


SERVICE_SMS_KEYWORDS = {
    "Facebook": ["facebook", "fb code", "fb", "meta"],
    "WhatsApp": ["whats", "whatsapp", "whatsapp code"],
    "Telegram": ["telegram", "tg code"],
    "Instagram": ["instagram", "ig code"],
    "Google": ["google", "Googl"],
    "Microsoft": ["microsoft", "micro", "Microsof", "xbox"],
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

# ==========================================
# Complete & Conflict-Free Dialing Codes
# ==========================================
COUNTRY_CODES = {
    # 🌟 NANP (+1) Caribbean & Islands (Longest matches first)
    "1242": "🇧🇸 Bahamas",
    "1246": "🇧🇧 Barbados",
    "1264": "🇦🇮 Anguilla",
    "1268": "🇦🇬 Antigua and Barbuda",
    "1284": "🇻🇬 British Virgin Islands",
    "1340": "🇻🇮 US Virgin Islands",
    "1345": "🇰🇾 Cayman Islands",
    "1441": "🇧🇲 Bermuda",
    "1473": "🇬🇩 Grenada",
    "1649": "🇹🇨 Turks and Caicos",
    "1664": "🇲🇸 Montserrat",
    "1670": "🇲🇵 Northern Mariana",
    "1671": "🇬🇺 Guam",
    "1684": "🇦🇸 American Samoa",
    "1721": "🇸🇽 Sint Maarten",
    "1758": "🇱🇨 Saint Lucia",
    "1767": "🇩🇲 Dominica",
    "1784": "🇻🇨 Saint Vincent",
    "1787": "🇵🇷 Puerto Rico",
    "1939": "🇵🇷 Puerto Rico",
    "1809": "🇩🇴 Dominican Republic",
    "1829": "🇩🇴 Dominican Republic",
    "1849": "🇩🇴 Dominican Republic",
    "1868": "🇹🇹 Trinidad and Tobago",
    "1869": "🇰🇳 Saint Kitts and Nevis",
    "1876": "🇯🇲 Jamaica",
    "1": "🇺🇸 USA / 🇨🇦 Canada",
    # 🌟 +7 Eurasia Zone
    "76": "🇰🇿 Kazakhstan",
    "77": "🇰🇿 Kazakhstan",
    "7": "🇷🇺 Russia",
    # 🌟 Asia & Middle East
    "880": "🇧🇩 Bangladesh",
    "91": "🇮🇳 India",
    "92": "🇵🇰 Pakistan",
    "93": "🇦🇫 Afghanistan",
    "94": "🇱🇰 Sri Lanka",
    "95": "🇲🇲 Myanmar",
    "977": "🇳🇵 Nepal",
    "975": "🇧🇹 Bhutan",
    "960": "🇲🇻 Maldives",
    "86": "🇨🇳 China",
    "81": "🇯🇵 Japan",
    "82": "🇰🇷 South Korea",
    "850": "🇰🇵 North Korea",
    "886": "🇹🇼 Taiwan",
    "852": "🇭🇰 Hong Kong",
    "853": "🇲🇴 Macau",
    "84": "🇻🇳 Vietnam",
    "66": "🇹🇭 Thailand",
    "60": "🇲🇾 Malaysia",
    "65": "🇸🇬 Singapore",
    "62": "🇮🇩 Indonesia",
    "63": "🇵🇭 Philippines",
    "855": "🇰🇭 Cambodia",
    "856": "🇱🇦 Laos",
    "673": "🇧🇳 Brunei",
    "670": "🇹🇱 Timor-Leste",
    "98": "🇮🇷 Iran",
    "964": "🇮🇶 Iraq",
    "963": "🇸🇾 Syria",
    "961": "🇱🇧 Lebanon",
    "962": "🇯🇴 Jordan",
    "970": "🇵🇸 Palestine",
    "972": "🇮🇱 Israel",
    "966": "🇸🇦 Saudi Arabia",
    "971": "🇦🇪 UAE",
    "965": "🇰🇼 Kuwait",
    "974": "🇶🇦 Qatar",
    "973": "🇧🇭 Bahrain",
    "968": "🇴🇲 Oman",
    "967": "🇾🇪 Yemen",
    # 🌟 Central Asia & Caucasus
    "90": "🇹🇷 Turkey",
    "994": "🇦🇿 Azerbaijan",
    "995": "🇬🇪 Georgia",
    "374": "🇦🇲 Armenia",
    "998": "🇺🇿 Uzbekistan",
    "996": "🇰🇬 Kyrgyzstan",
    "992": "🇹🇯 Tajikistan",
    "993": "🇹🇲 Turkmenistan",
    "976": "🇲🇳 Mongolia",
    # 🌟 Europe
    "44": "🇬🇧 United Kingdom",
    "49": "🇩🇪 Germany",
    "33": "🇫🇷 France",
    "39": "🇮🇹 Italy",
    "34": "🇪🇸 Spain",
    "351": "🇵🇹 Portugal",
    "31": "🇳🇱 Netherlands",
    "32": "🇧🇪 Belgium",
    "41": "🇨🇭 Switzerland",
    "43": "🇦🇹 Austria",
    "46": "🇸🇪 Sweden",
    "47": "🇳🇴 Norway",
    "45": "🇩🇰 Denmark",
    "358": "🇫🇮 Finland",
    "354": "🇮🇸 Iceland",
    "353": "🇮🇪 Ireland",
    "48": "🇵🇱 Poland",
    "420": "🇨🇿 Czechia",
    "421": "🇸🇰 Slovakia",
    "36": "🇭🇺 Hungary",
    "380": "🇺🇦 Ukraine",
    "375": "🇧🇾 Belarus",
    "40": "🇷🇴 Romania",
    "359": "🇧🇬 Bulgaria",
    "30": "🇬🇷 Greece",
    "357": "🇨🇾 Cyprus",
    "356": "🇲🇹 Malta",
    "355": "🇦🇱 Albania",
    "381": "🇷🇸 Serbia",
    "385": "🇭🇷 Croatia",
    "386": "🇸🇮 Slovenia",
    "387": "🇧🇦 Bosnia",
    "382": "🇲🇪 Montenegro",
    "389": "🇲🇰 North Macedonia",
    "383": "🇽🇰 Kosovo",
    "373": "🇲🇩 Moldova",
    "370": "🇱🇹 Lithuania",
    "371": "🇱🇻 Latvia",
    "372": "🇪🇪 Estonia",
    "376": "🇦🇩 Andorra",
    "377": "🇲🇨 Monaco",
    "378": "🇸🇲 San Marino",
    "379": "🇻🇦 Vatican City",
    "423": "🇱🇮 Liechtenstein",
    "352": "🇱🇺 Luxembourg",
    "350": "🇬🇮 Gibraltar",
    # 🌟 Africa
    "20": "🇪🇬 Egypt",
    "212": "🇲🇦 Morocco",
    "213": "🇩🇿 Algeria",
    "216": "🇹🇳 Tunisia",
    "218": "🇱🇾 Libya",
    "249": "🇸🇩 Sudan",
    "211": "🇸🇸 South Sudan",
    "251": "🇪🇹 Ethiopia",
    "254": "🇰🇪 Kenya",
    "255": "🇹🇿 Tanzania",
    "256": "🇺🇬 Uganda",
    "234": "🇳🇬 Nigeria",
    "233": "🇬🇭 Ghana",
    "27": "🇿🇦 South Africa",
    "237": "🇨🇲 Cameroon",
    "225": "🇨🇮 Ivory Coast",
    "221": "🇸🇳 Senegal",
    "260": "🇿🇲 Zambia",
    "263": "🇿🇼 Zimbabwe",
    "258": "🇲🇿 Mozambique",
    "244": "🇦🇴 Angola",
    "264": "🇳🇦 Namibia",
    "267": "🇧🇼 Botswana",
    "250": "🇷🇼 Rwanda",
    "257": "🇧🇮 Burundi",
    "252": "🇸🇴 Somalia",
    "253": "🇩🇯 Djibouti",
    "291": "🇪🇷 Eritrea",
    "236": "🇨🇫 Central African Rep.",
    "235": "🇹🇩 Chad",
    "242": "🇨🇬 Congo",
    "243": "🇨🇩 DR Congo",
    "241": "🇬🇦 Gabon",
    "240": "🇬🇶 Equatorial Guinea",
    "228": "🇹🇬 Togo",
    "229": "🇧🇯 Benin",
    "226": "🇧🇫 Burkina Faso",
    "227": "🇳🇪 Niger",
    "223": "🇲🇱 Mali",
    "224": "🇬🇳 Guinea",
    "245": "🇬🇼 Guinea-Bissau",
    "220": "🇬🇲 Gambia",
    "232": "🇸🇱 Sierra Leone",
    "231": "🇱🇷 Liberia",
    "222": "🇲🇷 Mauritania",
    "261": "🇲🇬 Madagascar",
    "230": "🇲🇺 Mauritius",
    "248": "🇸🇨 Seychelles",
    "269": "🇰🇲 Comoros",
    "238": "🇨🇻 Cape Verde",
    "239": "🇸🇹 Sao Tome",
    "266": "🇱🇸 Lesotho",
    "268": "🇸🇿 Eswatini",
    "265": "🇲🇼 Malawi",
    # 🌟 Americas
    "52": "🇲🇽 Mexico",
    "55": "🇧🇷 Brazil",
    "54": "🇦🇷 Argentina",
    "56": "🇨🇱 Chile",
    "57": "🇨🇴 Colombia",
    "51": "🇵🇪 Peru",
    "58": "🇻🇪 Venezuela",
    "593": "🇪🇨 Ecuador",
    "595": "🇵🇾 Paraguay",
    "598": "🇺🇾 Uruguay",
    "591": "🇧🇴 Bolivia",
    "592": "🇬🇾 Guyana",
    "597": "🇸🇷 Suriname",
    "507": "🇵🇦 Panama",
    "506": "🇨🇷 Costa Rica",
    "505": "🇳🇮 Nicaragua",
    "504": "🇭🇳 Honduras",
    "503": "🇸🇻 El Salvador",
    "502": "🇬🇹 Guatemala",
    "501": "🇧🇿 Belize",
    "53": "🇨🇺 Cuba",
    "509": "🇭🇹 Haiti",
    # 🌟 Oceania & Pacific
    "61": "🇦🇺 Australia",
    "64": "🇳🇿 New Zealand",
    "675": "🇵🇬 Papua New Guinea",
    "679": "🇫🇯 Fiji",
    "685": "🇼🇸 Samoa",
    "676": "🇹🇴 Tonga",
    "677": "🇸🇧 Solomon Islands",
    "678": "🇻🇺 Vanuatu",
    "682": "🇨🇰 Cook Islands",
    "680": "🇵🇼 Palau",
    "686": "🇰🇮 Kiribati",
    "688": "🇹🇻 Tuvalu",
    "691": "🇫🇲 Micronesia",
    "692": "🇲🇭 Marshall Islands",
    "674": "🇳🇷 Nauru",
}


def get_country_info(range_str):
  clean_range = str(range_str or "").replace("X", "")
  for code, name in sorted(
      COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True
  ):
    if clean_range.startswith(code):
      return code, name
  return clean_range[:3], f"🏳️ Other (+{clean_range[:3]})"


def auto_cache_menu_thread():
  global cached_services_kb, cached_countries_kb, voltx_auto_mode, voltx_dynamic_data
  while True:
    try:
      if voltx_auto_mode and voltx_dynamic_data:
        service_hits = [
            (
                sid,
                s_data,
                sum(r["hits"] for r in s_data["ranges"].values()),
            )
            for sid, s_data in voltx_dynamic_data.items()
        ]
        top_services = sorted(service_hits, key=lambda x: x[2], reverse=True)[
            :15
        ]

        new_srv_kb = {"inline_keyboard": []}
        row = []
        styles = ["primary", "success", "danger"]
        style_idx = 0
        for sid, data, hits in top_services:
          safe_sid = html.escape(str(sid))
          row.append({
              "text": safe_sid,
              "callback_data": f"srv_{safe_sid[:15]}",
              "style": styles[style_idx % 3],
              "icon_custom_emoji_id": data["emoji_id"],
          })
          style_idx += 1
          if len(row) == 2:
            new_srv_kb["inline_keyboard"].append(row)
            row = []
        if row:
          new_srv_kb["inline_keyboard"].append(row)
        new_srv_kb["inline_keyboard"].append([{
            "text": "CLOSE",
            "callback_data": "close_panel",
            "icon_custom_emoji_id": "5438541186539232243",
            "style": "danger",
        }])

        cached_services_kb = new_srv_kb

        new_cnt_kb = {}
        for sid, data, hits in top_services:
          safe_sid_short = html.escape(str(sid))[:15]
          country_map = {}
          for r, r_data in data["ranges"].items():
            clean_r = str(r).replace("X", "")
            if not re.match(r"^\d+$", clean_r):
              continue
            c_code, c_name = get_country_info(clean_r)
            if c_code not in country_map:
              country_map[c_code] = {"name": c_name, "hits": 0}
            country_map[c_code]["hits"] += r_data["hits"]

          top_countries = sorted(
              country_map.items(), key=lambda x: x[1]["hits"], reverse=True
          )[:15]

          cnt_kb = {"inline_keyboard": []}
          styles_c = ["primary", "success", "danger"]
          style_idx_c = 0
          std_service = detect_service("", sid)
          rate = get_otp_reward(std_service)

          for c_code, c_data in top_countries:
            c_name_full = c_data["name"]
            parts = c_name_full.split(" ", 1)
            emoji_char = parts[0]
            clean_name = parts[1] if len(parts) > 1 else c_name_full

            btn_text = (
                f"Other (+{c_code}) - {rate} TK"
                if "Other" in clean_name
                else f"{clean_name} (+{c_code}) - {rate} TK"
            )
            btn = {
                "text": btn_text,
                "callback_data": f"cc_{safe_sid_short}_{c_code}",
                "style": styles_c[style_idx_c % 3],
            }
            if emoji_char in GLOBAL_BODY_EMOJIS:
              btn["icon_custom_emoji_id"] = GLOBAL_BODY_EMOJIS[emoji_char]

            cnt_kb["inline_keyboard"].append([btn])
            style_idx_c += 1

          cnt_kb["inline_keyboard"].append([{
              "text": "BACK",
              "callback_data": "back_to_services",
              "icon_custom_emoji_id": "5438541186539232243",
              "style": "danger",
          }])
          new_cnt_kb[safe_sid_short] = cnt_kb

        cached_countries_kb = new_cnt_kb

      global cached_leaderboard_text, daily_user_otps
      today = time.strftime("%Y-%m-%d")
      if daily_user_otps.get("date") != today:
        daily_user_otps["date"] = today
        daily_user_otps["users"] = {}

      top_users = sorted(
          daily_user_otps["users"].items(), key=lambda x: x[1], reverse=True
      )[:5]
      lb_msg = (
          '<blockquote><tg-emoji emoji-id="5240021484516185513">🏆</tg-emoji>'
          " <b>𝗧𝗢𝗣 𝟱 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗"
          " (TODAY)</b></blockquote>\n━━━━━━━━━━━━━━━━━\n"
      )
      emoji_map = [
          ("1️⃣", "5238176680098440792"),
          ("2️⃣", "5237806896299157399"),
          ("3️⃣", "5239965456667812809"),
          ("4️⃣", "5237911487342751418"),
          ("5️⃣", "5240278297790686165"),
      ]

      if not top_users:
        lb_msg += "<i>No OTPs received today.</i>\n"
      else:
        for idx, (uid_str, otp_count) in enumerate(top_users):
          u_data = get_user(int(uid_str))
          fname = u_data["first_name"] if u_data else "User"
          emoji_char, emoji_id = emoji_map[idx]
          lb_msg += (
              f'<blockquote><tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
              f" <a href='tg://user?id={uid_str}'>{html.escape(str(fname))}</a>"
              f" - {otp_count} OTP</blockquote>\n"
          )
      lb_msg += "━━━━━━━━━━━━━━━━━"
      cached_leaderboard_text = lb_msg

    except Exception:
      pass
    time.sleep(5)


# Admin Settings (DXA Control)
bot_settings = {
    "withdraw_on": True,
    "min_withdraw": 10.0,
    "support_link": "",
    "w_group": "",
    "auto_br_on": False,
    "auto_br_interval": 60,
    "cooldown": 5,
    "num_req": 1,
    "w_methods": ["bKash", "Nagad"],
    "otp_default_rate": 0.15,
    "otp_service_rates": {},
    "main_channel_link": "",
}

BOT_DATA_FILE = "bot_data.json"
USERS_LIST_FILE = "users_list.json"


def get_api_key():
  return random.choice(voltx_keys) if voltx_keys else API_2OO9_KEY_DEFAULT


def get_otp_reward(service_name):
  rates = bot_settings.get("otp_service_rates", {})
  val = rates.get(service_name, bot_settings.get("otp_default_rate", 0.5))
  return float(val)


def update_daily_stat(key, amount=1):
  global daily_stats
  today = time.strftime("%Y-%m-%d")
  if daily_stats.get("date") != today:
    daily_stats = {"date": today, "numbers": 0, "otps": 0}
  daily_stats[key] = daily_stats.get(key, 0) + amount


def load_local_data():
  global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels
  global voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings
  global user_active_sessions, daily_stats, daily_user_otps, GLOBAL_BODY_EMOJIS, PREMIUM_APPS
  if os.path.exists(BOT_DATA_FILE):
    try:
      with open(BOT_DATA_FILE, "r") as f:
        data = json.load(f)
        recent_traffic = data.get("recent_traffic", [])
        voltx_dynamic_data = data.get("voltx_dynamic_data", {})
        loaded_keys = data.get("voltx_keys", [])

        if not loaded_keys:
          voltx_keys = [API_2OO9_KEY_DEFAULT]
        else:
          voltx_keys = loaded_keys

        force_join_status = data.get("force_join_status", False)
        force_join_channels = data.get("force_join_channels", [])
        voltx_auto_mode = data.get("voltx_auto_mode", True)
        otp_forward_groups = data.get("otp_forward_groups", [])
        otp_button_link = data.get(
            "otp_button_link", "https://t.me/your_default_bot"
        )
        recent_success_otps = set(data.get("recent_success_otps", []))

        loaded_settings = data.get("bot_settings", {})
        for k, v in loaded_settings.items():
          bot_settings[k] = v

        daily_stats = data.get(
            "daily_stats", {"date": "", "numbers": 0, "otps": 0}
        )
        daily_user_otps = data.get(
            "daily_user_otps", {"date": "", "users": {}}
        )
        user_active_sessions = data.get("user_active_sessions", {})

        saved_body_emojis = data.get("custom_global_body_emojis", {})
        for k, v in saved_body_emojis.items():
          GLOBAL_BODY_EMOJIS[k] = v
        saved_app_emojis = data.get("custom_premium_apps", {})
        for k, v in saved_app_emojis.items():
          if k in PREMIUM_APPS:
            PREMIUM_APPS[k].update(v)
          else:
            PREMIUM_APPS[k] = v
    except Exception as e:
      print(f"Error loading local data: {e}")


def save_local_data():
  global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels
  global voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings
  global user_active_sessions, daily_stats, daily_user_otps, GLOBAL_BODY_EMOJIS, PREMIUM_APPS
  try:
    with open(BOT_DATA_FILE, "w") as f:
      json.dump(
          {
              "recent_traffic": recent_traffic,
              "voltx_dynamic_data": voltx_dynamic_data,
              "voltx_keys": voltx_keys,
              "force_join_status": force_join_status,
              "force_join_channels": force_join_channels,
              "voltx_auto_mode": voltx_auto_mode,
              "otp_forward_groups": otp_forward_groups,
              "otp_button_link": otp_button_link,
              "recent_success_otps": list(recent_success_otps),
              "bot_settings": bot_settings,
              "user_active_sessions": user_active_sessions,
              "daily_stats": daily_stats,
              "daily_user_otps": daily_user_otps,
              "custom_global_body_emojis": GLOBAL_BODY_EMOJIS,
              "custom_premium_apps": PREMIUM_APPS,
          },
          f,
      )
  except Exception as e:
    print(f"Error saving local data: {e}")

  if current_db_mode == "firebase" and db_firebase:
    try:
      db_firebase.collection("settings").document("bot_config").set(
          {
              "bot_settings": bot_settings,
              "force_join_status": force_join_status,
              "force_join_channels": force_join_channels,
              "otp_forward_groups": otp_forward_groups,
              "otp_button_link": otp_button_link,
              "voltx_keys": voltx_keys,
              "voltx_auto_mode": voltx_auto_mode,
              "custom_global_body_emojis": GLOBAL_BODY_EMOJIS,
              "custom_premium_apps": PREMIUM_APPS,
          },
          merge=True,
      )
    except:
      pass


cached_user_list = set()


def add_to_broadcast_list(user_id):
  global cached_user_list
  if not cached_user_list and os.path.exists(USERS_LIST_FILE):
    try:
      with open(USERS_LIST_FILE, "r") as f:
        cached_user_list = set(json.load(f))
    except:
      pass

  if user_id not in cached_user_list:
    cached_user_list.add(user_id)
    try:
      with open(USERS_LIST_FILE, "w") as f:
        json.dump(list(cached_user_list), f)
    except:
      pass


def get_all_user_ids():
  global user_cache
  users = set()
  for uid in user_cache.keys():
    users.add(int(uid))
  if os.path.exists(USERS_LIST_FILE):
    try:
      with open(USERS_LIST_FILE, "r") as f:
        for u in json.load(f):
          users.add(int(u))
    except:
      pass
  return list(users)


def get_bot_info():
  try:
    res = requests.get(BASE_URL + "getMe", timeout=10).json()
    if res.get("ok"):
      return res["result"]["username"]
  except Exception:
    pass
  return ""


def set_bot_commands():
  commands = [
      {"command": "start", "description": "Start the bot or refresh menu"}
  ]
  try:
    requests.post(
        BASE_URL + "setMyCommands", json={"commands": commands}, timeout=10
    )
  except Exception:
    pass


def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
  payload = {
      "chat_id": chat_id,
      "text": apply_emojis(text),
      "parse_mode": parse_mode,
  }
  if reply_markup:
    payload["reply_markup"] = reply_markup
  try:
    return requests.post(BASE_URL + "sendMessage", json=payload, timeout=12).json()
  except Exception:
    return None


def edit_message(
    chat_id, message_id, text, reply_markup=None, parse_mode="HTML"
):
  payload = {
      "chat_id": chat_id,
      "message_id": message_id,
      "text": apply_emojis(text),
      "parse_mode": parse_mode,
  }
  if reply_markup:
    payload["reply_markup"] = reply_markup
  try:
    requests.post(BASE_URL + "editMessageText", json=payload, timeout=12)
  except Exception:
    pass


def answer_callback_query(callback_query_id, text="", show_alert=False):
  payload = {
      "callback_query_id": callback_query_id,
      "text": text,
      "show_alert": show_alert,
  }
  try:
    requests.post(BASE_URL + "answerCallbackQuery", json=payload, timeout=8)
  except Exception:
    pass


def delete_message(chat_id, message_id):
  payload = {"chat_id": chat_id, "message_id": message_id}
  try:
    requests.post(BASE_URL + "deleteMessage", json=payload, timeout=8)
  except Exception:
    pass


def copy_message(chat_id, from_chat_id, message_id, reply_markup=None):
  payload = {
      "chat_id": chat_id,
      "from_chat_id": from_chat_id,
      "message_id": message_id,
  }
  if reply_markup:
    payload["reply_markup"] = reply_markup
  try:
    return requests.post(
        BASE_URL + "copyMessage", json=payload, timeout=12
    ).json()
  except Exception:
    return None


def get_chat_details(chat_identifier):
  chat_identifier = str(chat_identifier).strip()
  if chat_identifier.startswith("https://t.me/"):
    chat_identifier = "@" + chat_identifier.split("/")[-1]
  elif not chat_identifier.startswith("@") and not chat_identifier.startswith(
      "-100"
  ):
    chat_identifier = "@" + chat_identifier

  url = BASE_URL + "getChat"
  res = requests.get(
      url, params={"chat_id": chat_identifier}, timeout=10
  ).json()
  if res.get("ok"):
    chat = res["result"]
    chat_data = {
        "id": chat["id"],
        "username": "@" + chat["username"] if "username" in chat else "",
        "title": chat.get("title", "Private Channel"),
        "invite_link": chat.get("invite_link", ""),
    }
    if not chat_data["invite_link"]:
      inv_res = requests.post(
          BASE_URL + "exportChatInviteLink",
          json={"chat_id": chat["id"]},
          timeout=10,
      ).json()
      if inv_res.get("ok"):
        chat_data["invite_link"] = inv_res["result"]
    return chat_data
  return None


def is_user_joined(user_id):
  if not force_join_status or not force_join_channels:
    return True
  if user_id == ADMIN_ID:
    return True

  for ch in force_join_channels:
    try:
      res = requests.get(
          BASE_URL + "getChatMember",
          params={"chat_id": ch["id"], "user_id": user_id},
          timeout=8,
      ).json()
      if res.get("ok"):
        status = res["result"]["status"]
        if status in ["left", "kicked"]:
          return False
      else:
        return False
    except:
      return False
  return True


def detect_service(message_text, raw_sid=""):
  msg_lower = str(message_text).lower()
  sid_lower = str(raw_sid).lower()

  for service, keywords in SERVICE_SMS_KEYWORDS.items():
    for kw in keywords:
      if re.search(rf"\b{re.escape(kw)}\b", msg_lower) or kw in msg_lower:
        return service

  for service in PREMIUM_APPS.keys():
    if service.lower() in sid_lower:
      return service

  return "Other"


def get_service_info_html(service_name):
  app_info = PREMIUM_APPS.get(service_name, PREMIUM_APPS["Other"])
  emoji_id = app_info["id"]
  normal_emoji = app_info["emoji"]
  short_name = service_name.upper()
  if short_name == "FACEBOOK":
    short_name = "FB"
  if short_name == "WHATSAPP":
    short_name = "WS"
  if short_name == "INSTAGRAM":
    short_name = "IG"

  return (
      f'<tg-emoji emoji-id="{emoji_id}">{normal_emoji}</tg-emoji>'
      f" <b>{html.escape(short_name)}</b>",
      emoji_id,
  )


def extract_otp_code(message_text):
  match = re.search(r"\b(\d{3}[\s-]?\d{3,4}|\d{4,8})\b", str(message_text))
  if match:
    return match.group(1)
  return "COPY"


def deliver_to_inbox(
    user_id, service_name, raw_number, msg_text, current_balance, reward
):
  c_code, c_name = get_country_info(raw_number)
  service_html, srv_eid = get_service_info_html(service_name)
  clean_raw_number = str(raw_number).lstrip("+")

  text = (
      "— — — — — — — — — —\n"
      f"<blockquote>{service_html} <code>+{clean_raw_number}</code></blockquote>\n"
      f'<blockquote><tg-emoji emoji-id="5420323438508155202">➕</tg-emoji>'
      f" <b>ADDED</b>  ➜ {reward:.2f} TK</blockquote>\n"
      f'<blockquote><tg-emoji emoji-id="5190899075968441286">💳</tg-emoji>'
      f" <b>BALANCE</b> ➜ {current_balance:.2f} TK</blockquote>\n"
      "— — — — — — — — — —"
  )
  otp = extract_otp_code(msg_text)
  markup = {
      "inline_keyboard": [[{
          "text": f"{otp}",
          "icon_custom_emoji_id": srv_eid,
          "copy_text": {"text": otp},
          "style": "success",
      }]]
  }
  send_message(user_id, text, reply_markup=markup)


def generate_otp_display(service_name, raw_number, message_text):
  c_code, c_name = get_country_info(raw_number)
  parts = c_name.split(" ", 1)
  country_emoji = parts[0]

  if len(raw_number) > 6:
    masked_number = f"{raw_number[:3]}DXA{raw_number[-3:]}"
  else:
    masked_number = raw_number

  service_html, srv_eid = get_service_info_html(service_name)

  text = (
      "━━━━━━━━━━━━━━━━━\n"
      f"{service_html} ➜ {country_emoji} <code>{html.escape(masked_number)}</code>\n"
      "━━━━━━━━━━━━━━━━━"
  )

  otp = extract_otp_code(message_text)
  clean_range = (
      str(raw_number)[:5] if len(str(raw_number)) >= 5 else str(raw_number)
  )
  deep_link = f"https://t.me/{BOT_USERNAME}?start=alloc_{clean_range}_{service_name.lower()}"

  markup = {"inline_keyboard": []}
  row1 = []
  main_channel_link = bot_settings.get("main_channel_link", "")
  if main_channel_link:
    row1.append({
        "text": "𝗖𝗛𝗔𝗡𝗡𝗘𝗟",
        "url": main_channel_link,
        "icon_custom_emoji_id": "5429353834881261942",
        "style": "primary",
    })

  row1.append({
      "text": f"{otp}",
      "icon_custom_emoji_id": srv_eid,
      "copy_text": {"text": otp},
      "style": "success",
  })
  markup["inline_keyboard"].append(row1)

  markup["inline_keyboard"].append([{
      "text": "GET NUMBER",
      "url": deep_link,
      "icon_custom_emoji_id": "5429167978761461870",
      "style": "danger",
  }])

  return text, markup


def send_otp_to_groups(formatted_text, markup):
  global otp_forward_groups
  if not otp_forward_groups:
    return False

  sent_any = False
  for group_id in otp_forward_groups:
    resp = send_message(group_id, formatted_text, reply_markup=markup)
    if resp and resp.get("ok"):
      sent_any = True
    time.sleep(1)

  return sent_any


def fetch_live_access():
  headers = {"mauthapi": get_api_key()}
  try:
    res = requests.get(
        f"{API_2OO9_BASE}/liveaccess", headers=headers, timeout=10
    )
    data = res.json()
    if data.get("meta", {}).get("code") == 200:
      return data.get("data", {}).get("services", [])
  except:
    pass
  return []


def fetch_live_number(rid):
  headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
  payload = {"rid": str(rid)}
  try:
    res = requests.post(
        f"{API_2OO9_BASE}/getnum", headers=headers, json=payload, timeout=10
    )
    data = res.json()
    if data.get("meta", {}).get("code") == 200:
      return data.get("data", {})
  except:
    pass
  return None


def voltx_console_listener():
  global recent_traffic, voltx_dynamic_data
  cycle_count = 0
  while True:
    try:
      headers = {"mauthapi": get_api_key()}
      res = requests.get(f"{API_2OO9_BASE}/console", headers=headers, timeout=10)
      data = res.json()
      if data.get("meta", {}).get("code") == 200:
        hits = data.get("data", {}).get("hits", [])
        new_traffic, seen_signatures = [], set()
        current_time = int(time.time())

        for h in hits:
          sig = f"{h.get('time', 0)}_{h.get('range', '')}"
          if sig not in seen_signatures:
            h["local_receive_time"] = current_time
            new_traffic.append(h)
            seen_signatures.add(sig)

            raw_sid = h.get("sid") or "Unknown"
            raw_msg = h.get("message") or ""
            raw_range = str(h.get("range", "")).replace("X", "")

            if raw_range:
              detected_sid = detect_service(raw_msg, raw_sid)
              app_info = PREMIUM_APPS.get(detected_sid, PREMIUM_APPS["Other"])
              emoji_id, normal_emoji = app_info["id"], app_info["emoji"]

              if detected_sid not in voltx_dynamic_data:
                voltx_dynamic_data[detected_sid] = {
                    "emoji_id": emoji_id,
                    "normal_emoji": normal_emoji,
                    "ranges": {},
                }
              if raw_range not in voltx_dynamic_data[detected_sid]["ranges"]:
                voltx_dynamic_data[detected_sid]["ranges"][raw_range] = {
                    "last_seen": current_time,
                    "hits": 0,
                }
              voltx_dynamic_data[detected_sid]["ranges"][raw_range][
                  "last_seen"
              ] = current_time
              voltx_dynamic_data[detected_sid]["ranges"][raw_range]["hits"] += 1

        fifteen_mins_ago = current_time - 900
        for h in recent_traffic:
          if h.get("local_receive_time", 0) >= fifteen_mins_ago:
            sig = f"{h.get('time', 0)}_{h.get('range', '')}"
            if sig not in seen_signatures:
              new_traffic.append(h)
              seen_signatures.add(sig)

        new_traffic.sort(
            key=lambda x: x.get("local_receive_time", 0), reverse=True
        )
        recent_traffic = new_traffic

        services_to_delete = []
        for sid, s_data in voltx_dynamic_data.items():
          ranges_to_delete = []
          for r, r_data in s_data["ranges"].items():
            if current_time - r_data["last_seen"] > 300:
              ranges_to_delete.append(r)
          for r in ranges_to_delete:
            del s_data["ranges"][r]
          if not s_data["ranges"]:
            services_to_delete.append(sid)
        for sid in services_to_delete:
          del voltx_dynamic_data[sid]

        cycle_count += 1
        if cycle_count % 3 == 0:
          save_local_data()

    except Exception:
      pass
    time.sleep(10)


def voltx_sms_listener():
  global recent_success_otps, otp_forward_groups, user_active_sessions, daily_user_otps
  group_sent_otps = set()
  while True:
    try:
      headers = {
          "mauthapi": get_api_key(),
          "Content-Type": "application/json",
      }
      res = requests.get(
          f"{API_2OO9_BASE}/success-otp", headers=headers, timeout=15
      )

      if res.status_code == 200:
        data = res.json()
        otps = []

        if isinstance(data, dict):
          if "data" in data and isinstance(data["data"], list):
            otps = data["data"]
          elif "data" in data and isinstance(data["data"], dict):
            if "otps" in data["data"]:
              otps = data["data"]["otps"]
            elif "hits" in data["data"]:
              otps = data["data"]["hits"]
          elif "otps" in data:
            otps = data["otps"]
          elif "hits" in data:
            otps = data["hits"]
        elif isinstance(data, list):
          otps = data

        for otp_data in reversed(otps):
          msg_text = str(
              otp_data.get(
                  "message", otp_data.get("sms", otp_data.get("code", ""))
              )
          )
          raw_number = str(
              otp_data.get("number", otp_data.get("phone", ""))
          )
          raw_service = str(
              otp_data.get("sid", otp_data.get("service", "Unknown"))
          )

          if not msg_text or not raw_number:
            continue

          sig = f"{raw_number}_{msg_text}"
          detected_service = detect_service(msg_text, raw_service)

          if sig not in group_sent_otps:
            group_sent_otps.add(sig)
            if otp_forward_groups:
              formatted_message, markup = generate_otp_display(
                  detected_service, raw_number, msg_text
              )
              send_otp_to_groups(formatted_message, markup)

          if sig not in recent_success_otps:
            recent_success_otps.add(sig)

            owner_id = None
            last_8_digits = (
                raw_number[-8:] if len(raw_number) > 8 else raw_number
            )
            for active_num, uid in list(user_active_sessions.items()):
              if active_num.endswith(last_8_digits):
                owner_id = uid
                del user_active_sessions[active_num]
                break

            if owner_id:
              reward = get_otp_reward(detected_service)
              update_user_stats(owner_id, reward, 0)

              user_balance = get_user(owner_id).get("balance", 0.0)
              deliver_to_inbox(
                  owner_id,
                  detected_service,
                  raw_number,
                  msg_text,
                  user_balance,
                  reward,
              )

              today_date = time.strftime("%Y-%m-%d")
              if daily_user_otps.get("date") != today_date:
                daily_user_otps["date"] = today_date
                daily_user_otps["users"] = {}
              uid_str = str(owner_id)
              daily_user_otps["users"][uid_str] = (
                  daily_user_otps["users"].get(uid_str, 0) + 1
              )

            update_daily_stat("otps", 1)
            save_local_data()
            time.sleep(1)

      if len(recent_success_otps) > 2000:
        recent_success_otps = set(list(recent_success_otps)[-1000:])
        save_local_data()
      if len(group_sent_otps) > 2000:
        group_sent_otps = set(list(group_sent_otps)[-1000:])
    except Exception:
      pass
    time.sleep(10)


def init_sqlite():
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY,"
      " first_name TEXT DEFAULT 'User', balance REAL DEFAULT 0.0, total_invites"
      " INTEGER DEFAULT 0)"
  )
  try:
    cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT 'User'")
  except sqlite3.OperationalError:
    pass
  try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN total_otps INTEGER DEFAULT 0"
    )
  except sqlite3.OperationalError:
    pass
  conn.commit()
  conn.close()


def migrate_sqlite_to_firebase():
  global db_firebase, user_cache
  if not db_firebase:
    return
  try:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, first_name, balance, total_invites FROM users"
    )
    rows = cursor.fetchall()
    if not rows:
      return conn.close()

    count = 0
    batch = db_firebase.batch()
    for row in rows:
      uid, fname, bal, inv = row
      doc_ref = db_firebase.collection("users").document(str(uid))
      batch.set(
          doc_ref,
          {
              "user_id": uid,
              "first_name": fname,
              "balance": firestore.Increment(bal),
              "total_invites": firestore.Increment(inv),
          },
          merge=True,
      )
      count += 1
      if count % 400 == 0:
        batch.commit()
        batch = db_firebase.batch()
    if count % 400 != 0:
      batch.commit()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    user_cache.clear()
  except Exception as e:
    print(f"Migration Error: {e}")


def init_firebase_from_file():
  global current_db_mode, db_firebase, bot_settings, force_join_status, force_join_channels
  global otp_forward_groups, otp_button_link, voltx_keys, voltx_auto_mode, GLOBAL_BODY_EMOJIS, PREMIUM_APPS
  if os.path.exists("temp_firebase.json"):
    try:
      if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate("temp_firebase.json")
        )
      db_firebase = firestore.client()
      current_db_mode = "firebase"
      print("✅ Firebase Auto-Connected on Startup!")

      doc = db_firebase.collection("settings").document("bot_config").get()
      if doc.exists:
        data = doc.to_dict()
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
        if "voltx_keys" in data:
          voltx_keys = data["voltx_keys"]
        if "voltx_auto_mode" in data:
          voltx_auto_mode = data["voltx_auto_mode"]
        if "custom_global_body_emojis" in data:
          GLOBAL_BODY_EMOJIS.update(data["custom_global_body_emojis"])
        if "custom_premium_apps" in data:
          PREMIUM_APPS.update(data["custom_premium_apps"])
        print("✅ Settings & Emojis synced from Firebase!")

      try:
        local_users = set()
        if os.path.exists(USERS_LIST_FILE):
          with open(USERS_LIST_FILE, "r") as f:
            local_users = set(json.load(f))

        docs = db_firebase.collection("users").select([]).stream()
        fb_users = set(int(doc.id) for doc in docs)

        combined_users = local_users.union(fb_users)
        if len(combined_users) > len(local_users):
          with open(USERS_LIST_FILE, "w") as f:
            json.dump(list(combined_users), f)
          print(f"✅ Auto-Synced {len(fb_users)} users on Startup!")
      except Exception as e:
        print(f"Startup Sync Error: {e}")

    except Exception as e:
      print(f"❌ Firebase Auto-Connect Error: {e}")


def get_user(user_id):
  global current_db_mode, db_firebase, user_cache
  if user_id in user_cache:
    return user_cache[user_id]
  if current_db_mode == "firebase" and db_firebase:
    doc = db_firebase.collection("users").document(str(user_id)).get()
    if doc.exists:
      user_data = doc.to_dict()
      user_cache[user_id] = user_data
      return user_data
    return None
  else:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT first_name, balance, total_invites FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
      user_data = {
          "user_id": user_id,
          "first_name": row[0],
          "balance": row[1],
          "total_invites": row[2],
      }
      user_cache[user_id] = user_data
      return user_data
    return None


def add_user(user_id, first_name="User"):
  global current_db_mode, db_firebase, user_cache
  add_to_broadcast_list(user_id)
  if user_id in user_cache and user_cache[user_id]["first_name"] == first_name:
    return

  if current_db_mode == "firebase" and db_firebase:
    doc_ref = db_firebase.collection("users").document(str(user_id))
    if not doc_ref.get().exists:
      new_data = {
          "user_id": user_id,
          "first_name": first_name,
          "balance": 0.0,
          "total_invites": 0,
      }
      doc_ref.set(new_data)
      user_cache[user_id] = new_data
    else:
      doc_ref.update({"first_name": first_name})
      if user_id in user_cache:
        user_cache[user_id]["first_name"] = first_name
  else:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, first_name, balance,"
        " total_invites) VALUES (?, ?, 0.0, 0)",
        (user_id, first_name),
    )
    cursor.execute(
        "UPDATE users SET first_name = ? WHERE user_id = ?",
        (first_name, user_id),
    )
    conn.commit()
    conn.close()
    if user_id not in user_cache:
      user_cache[user_id] = {
          "user_id": user_id,
          "first_name": first_name,
          "balance": 0.0,
          "total_invites": 0,
      }
    else:
      user_cache[user_id]["first_name"] = first_name


def update_user_stats(user_id, balance_add, invite_add):
  global current_db_mode, db_firebase, user_cache
  bal_add = float(balance_add)
  inv_add = int(invite_add)

  if user_id not in user_cache:
    get_user(user_id)

  if user_id in user_cache:
    user_cache[user_id]["balance"] = round(
        user_cache[user_id]["balance"] + bal_add, 2
    )
    user_cache[user_id]["total_invites"] += inv_add

  if current_db_mode == "firebase" and db_firebase:
    db_firebase.collection("users").document(str(user_id)).update({
        "balance": firestore.Increment(bal_add),
        "total_invites": firestore.Increment(inv_add),
    })
  else:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance + ?, total_invites = total_invites"
        " + ? WHERE user_id = ?",
        (bal_add, inv_add, user_id),
    )
    conn.commit()
    conn.close()


def get_total_users():
  return len(get_all_user_ids())


def get_top_users(limit=5):
  global current_db_mode, db_firebase
  if current_db_mode == "firebase" and db_firebase:
    docs = (
        db_firebase.collection("users")
        .order_by("balance", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [
        (
            doc.to_dict().get("user_id"),
            doc.to_dict().get("first_name", "User"),
            doc.to_dict().get("balance"),
        )
        for doc in docs
    ]
  else:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, first_name, balance FROM users ORDER BY balance DESC"
        " LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_otp_group_keyboard():
  kb = {"inline_keyboard": []}

  link_display = otp_button_link if otp_button_link else "Not Set"
  if len(link_display) > 25:
    link_display = link_display[:25] + "..."
  kb["inline_keyboard"].append([{
      "text": f"Link: {link_display}",
      "callback_data": "edit_otp_link",
      "icon_custom_emoji_id": "5420517437885943844",
      "style": "primary",
  }])

  mc_link = bot_settings.get("main_channel_link", "")
  mc_display = mc_link if mc_link else "Not Set"
  if len(mc_display) > 25:
    mc_display = mc_display[:25] + "..."
  kb["inline_keyboard"].append([{
      "text": f"Main Channel: {mc_display}",
      "callback_data": "edit_main_channel",
      "icon_custom_emoji_id": "5429353834881261942",
      "style": "primary",
  }])

  if otp_forward_groups:
    grp = otp_forward_groups[0]
    kb["inline_keyboard"].append([{
        "text": f"Delete Group: {grp}",
        "callback_data": "del_otp_group_0",
        "icon_custom_emoji_id": "5422557736330106570",
        "style": "danger",
    }])

  kb["inline_keyboard"].append([{
      "text": "Set Forward Group",
      "callback_data": "add_otp_group",
      "icon_custom_emoji_id": "5429501315468270290",
      "style": "success",
  }])
  kb["inline_keyboard"].append([{
      "text": "BACK",
      "callback_data": "back_to_admin",
      "icon_custom_emoji_id": "5267490665117275176",
      "style": "danger",
  }])
  return kb


def get_force_join_keyboard():
  kb = {"inline_keyboard": []}
  status_text = "STATUS: ON" if force_join_status else "STATUS: OFF"
  status_icon = (
      "5352694861990501856" if force_join_status else "5420130255174145507"
  )

  kb["inline_keyboard"].append([{
      "text": status_text,
      "callback_data": "toggle_fj",
      "icon_custom_emoji_id": status_icon,
      "style": "primary" if force_join_status else "danger",
  }])

  for idx, ch in enumerate(force_join_channels):
    name = ch.get("username", ch.get("title", f"Channel {idx}"))
    kb["inline_keyboard"].append([{
        "text": f"Delete: {name}",
        "callback_data": f"del_fj_{idx}",
        "icon_custom_emoji_id": "5438178416421544431",
        "style": "danger",
    }])

  kb["inline_keyboard"].append([{
      "text": "Add Channel",
      "callback_data": "add_fj",
      "icon_custom_emoji_id": "5429501315468270290",
      "style": "success",
  }])
  kb["inline_keyboard"].append([{
      "text": "Back",
      "callback_data": "back_to_admin",
      "icon_custom_emoji_id": "5438541186539232243",
      "style": "primary",
  }])
  return kb


def get_force_join_alert_keyboard():
  kb = {"inline_keyboard": []}
  for ch in force_join_channels:
    name = ch.get("title", ch.get("username", "Our Channel"))
    url = ch.get("invite_link", "")
    if not url and ch.get("username"):
      url = f"https://t.me/{ch['username'].replace('@', '')}"
    kb["inline_keyboard"].append([{
        "text": f"JOIN {name}",
        "url": url,
        "icon_custom_emoji_id": "5420517437885943844",
        "style": "danger",
    }])

  kb["inline_keyboard"].append([{
      "text": "VERIFY",
      "callback_data": "check_fj_joined",
      "icon_custom_emoji_id": "5352694861990501856",
      "style": "success",
  }])
  return kb


def get_voltx_keys_keyboard():
  kb = {"inline_keyboard": []}
  status_text = "PANEL AUTO: ON" if voltx_auto_mode else "PANEL AUTO: OFF"
  status_icon = (
      "5352694861990501856" if voltx_auto_mode else "5420130255174145507"
  )

  kb["inline_keyboard"].append([{
      "text": status_text,
      "callback_data": "toggle_vk",
      "icon_custom_emoji_id": status_icon,
      "style": "primary" if voltx_auto_mode else "danger",
  }])

  for idx, key in enumerate(voltx_keys):
    masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else key
    kb["inline_keyboard"].append([{
        "text": f"Delete: {masked_key}",
        "callback_data": f"del_vk_{idx}",
        "icon_custom_emoji_id": "5438178416421544431",
        "style": "danger",
    }])

  kb["inline_keyboard"].append([{
      "text": "Add Panel Key",
      "callback_data": "add_vk",
      "icon_custom_emoji_id": "5429501315468270290",
      "style": "success",
  }])
  kb["inline_keyboard"].append([{
      "text": "Back",
      "callback_data": "back_to_admin",
      "icon_custom_emoji_id": "5438541186539232243",
      "style": "primary",
  }])
  return kb


def get_main_keyboard(user_id):
  keyboard_layout = [
      [
          {
              "text": "𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥",
              "icon_custom_emoji_id": "5429167978761461870",
              "style": "success",
          },
          {
              "text": "𝗖𝗛𝗘𝗖𝗞 𝗧𝗥𝗔𝗙𝗙𝗜𝗖",
              "icon_custom_emoji_id": "5429571662737611814",
              "style": "danger",
          },
      ],
      [
          {
              "text": "𝗜𝗡𝗩𝗜𝗧𝗘 𝗙𝗥𝗜𝗘𝗡𝗗",
              "icon_custom_emoji_id": "5850323366476519158",
              "style": "danger",
          },
          {
              "text": "𝗕𝗔𝗟𝗔𝗡𝗖𝗘",
              "icon_custom_emoji_id": "5429105001655999635",
              "style": "success",
          },
      ],
      [{
          "text": "𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗",
          "icon_custom_emoji_id": "5240021484516185513",
          "style": "primary",
      }],
  ]
  if user_id == ADMIN_ID:
    keyboard_layout.append([{
        "text": "𝗢𝗪𝗡𝗘𝗥 𝗣𝗔𝗡𝗘𝗟",
        "icon_custom_emoji_id": "5429427051188756948",
        "style": "success",
    }])
  return {"keyboard": keyboard_layout, "resize_keyboard": True}


def get_admin_inline_keyboard():
  global current_db_mode
  db_status = (
      "SQLITE ACTIVE" if current_db_mode == "sqlite" else "FIREBASE ACTIVE"
  )

  return {
      "inline_keyboard": [
          [{
              "text": "STEX SETTINGS",
              "callback_data": "manage_voltx",
              "icon_custom_emoji_id": "5877466056548691003",
              "style": "danger",
          }],
          [
              {
                  "text": "BROADCAST",
                  "callback_data": "broadcast_menu",
                  "icon_custom_emoji_id": "5296633779157243809",
                  "style": "primary",
              },
              {
                  "text": "FORCE JOIN",
                  "callback_data": "manage_fj",
                  "icon_custom_emoji_id": "5429353834881261942",
                  "style": "success",
              },
          ],
          [
              {
                  "text": "OTP GROUP",
                  "callback_data": "manage_otp_group",
                  "icon_custom_emoji_id": "5429208347159077664",
                  "style": "danger",
              },
              {
                  "text": "USER CONTROL",
                  "callback_data": "user_control",
                  "icon_custom_emoji_id": "5429274992166609833",
                  "style": "primary",
              },
          ],
          [
              {
                  "text": "DXA CONTROL",
                  "callback_data": "dxa_control",
                  "icon_custom_emoji_id": "5240451569656308978",
                  "style": "danger",
              },
              {
                  "text": "EMOJI MANAGER",
                  "callback_data": "manage_emojis",
                  "icon_custom_emoji_id": "5337267511261960341",
                  "style": "primary",
              },
          ],
          [{
              "text": "UPLOAD FIREBASE",
              "callback_data": "upload_firebase",
              "icon_custom_emoji_id": "5429362935916962442",
              "style": "primary",
          }],
          [{
              "text": db_status,
              "callback_data": "db_status",
              "icon_custom_emoji_id": "5429591316507963112",
              "style": "success",
          }],
          [{
              "text": "CLOSE",
              "callback_data": "close_panel",
              "icon_custom_emoji_id": "5438541186539232243",
              "style": "danger",
          }],
      ]
  }


def get_emoji_manager_keyboard():
  return {
      "inline_keyboard": [
          [{
              "text": "APP SERVICE EMOJIS",
              "callback_data": "emj_apps",
              "icon_custom_emoji_id": "5429503209548847635",
              "style": "primary",
          }],
          [{
              "text": "SET ANY GLOBAL EMOJI",
              "callback_data": "emj_custom_global",
              "icon_custom_emoji_id": "5395444784611480792",
              "style": "success",
          }],
          [{
              "text": "RESET ALL EMOJIS",
              "callback_data": "emj_reset_all",
              "icon_custom_emoji_id": "5422557736330106570",
              "style": "danger",
          }],
          [{
              "text": "BACK",
              "callback_data": "back_to_admin",
              "icon_custom_emoji_id": "5267490665117275176",
              "style": "danger",
          }],
      ]
  }


def get_apps_emoji_keyboard():
  kb = {"inline_keyboard": []}
  row = []
  for app_name, app_info in PREMIUM_APPS.items():
    row.append({
        "text": f"{app_info['emoji']} {app_name}",
        "callback_data": f"set_app_emj_{app_name}",
        "icon_custom_emoji_id": app_info["id"],
        "style": "primary",
    })
    if len(row) == 2:
      kb["inline_keyboard"].append(row)
      row = []
  if row:
    kb["inline_keyboard"].append(row)
  kb["inline_keyboard"].append([{
      "text": "BACK",
      "callback_data": "manage_emojis",
      "icon_custom_emoji_id": "5267490665117275176",
      "style": "danger",
  }])
  return kb


def dxa_control_keyboard():
  grp = bot_settings.get("w_group", "")
  grp_status = grp if grp else "NOT SET"
  return {
      "inline_keyboard": [
          [
              {
                  "text": f"MIN WITHDRAW: {bot_settings['min_withdraw']}",
                  "icon_custom_emoji_id": "5352877703043258544",
                  "callback_data": "dxa_min_w",
                  "style": "success",
              },
              {
                  "text": "OTP CONTROL",
                  "icon_custom_emoji_id": "5190576863226933563",
                  "callback_data": "dxa_otp_control",
                  "style": "primary",
              },
          ],
          [
              {
                  "text": (
                      f"REFER REWARD: {bot_settings.get('refer_reward', 0.2)}"
                  ),
                  "icon_custom_emoji_id": "5420396762189831222",
                  "callback_data": "dxa_ref_r",
                  "style": "success",
              },
              {
                  "text": f"COOLDOWN: {bot_settings['cooldown']}s",
                  "icon_custom_emoji_id": "5337172996211648018",
                  "callback_data": "dxa_cool",
                  "style": "primary",
              },
          ],
          [
              {
                  "text": f"NUM/REQ: {bot_settings['num_req']}",
                  "icon_custom_emoji_id": "5337132498965010628",
                  "callback_data": "dxa_num_req",
                  "style": "success",
              },
              {
                  "text": "W. METHODS",
                  "icon_custom_emoji_id": "5190899075968441286",
                  "callback_data": "manage_w_methods",
                  "style": "primary",
              },
          ],
          [{
              "text": f"W. GROUP: {grp_status}",
              "icon_custom_emoji_id": "5420517437885943844",
              "callback_data": "dxa_w_group",
              "style": "success",
          }],
          [{
              "text": "BACK",
              "icon_custom_emoji_id": "5267490665117275176",
              "callback_data": "back_to_admin",
              "style": "danger",
          }],
      ]
  }


def dxa_otp_control_keyboard():
  kb = {
      "inline_keyboard": [
          [{
              "text": f"Default Rate: {bot_settings['otp_default_rate']}",
              "icon_custom_emoji_id": "5352877703043258544",
              "callback_data": "dxa_def_rate",
              "style": "primary",
          }],
          [{
              "text": "Set Service Rate",
              "icon_custom_emoji_id": "5395444784611480792",
              "callback_data": "dxa_srv_rate",
              "style": "success",
          }],
      ]
  }

  for srv_name, rate in bot_settings.get("otp_service_rates", {}).items():
    app_info = PREMIUM_APPS.get(srv_name, PREMIUM_APPS["Other"])
    kb["inline_keyboard"].append([{
        "text": f"Delete: {srv_name} ({rate})",
        "icon_custom_emoji_id": app_info["id"],
        "callback_data": f"del_srv_rate_{srv_name}",
        "style": "danger",
    }])

  kb["inline_keyboard"].append([{
      "text": "BACK",
      "icon_custom_emoji_id": "5267490665117275176",
      "callback_data": "dxa_control",
      "style": "danger",
  }])
  return kb


def dxa_manage_w_methods_keyboard():
  kb = {"inline_keyboard": []}
  for idx, method in enumerate(bot_settings.get("w_methods", [])):
    kb["inline_keyboard"].append([{
        "text": f"Delete: {method}",
        "callback_data": f"del_w_method_{idx}",
        "style": "danger",
    }])
  kb["inline_keyboard"].append(
      [{"text": "Add Method", "callback_data": "add_w_method", "style": "success"}]
  )
  kb["inline_keyboard"].append(
      [{"text": "BACK", "callback_data": "dxa_control", "style": "primary"}]
  )
  return kb


def get_user_control_keyboard():
  return {
      "inline_keyboard": [
          [{
              "text": "USER PROFILE",
              "icon_custom_emoji_id": "5352861489541714456",
              "callback_data": "uc_profile",
              "style": "primary",
          }],
          [{
              "text": "BACK",
              "icon_custom_emoji_id": "5267490665117275176",
              "callback_data": "back_to_admin",
              "style": "danger",
          }],
      ]
  }


def get_user_profile_keyboard(target_uid):
  return {
      "inline_keyboard": [
          [{
              "text": "BALANCE",
              "icon_custom_emoji_id": "5429612421977253466",
              "callback_data": f"uc_balance_{target_uid}",
              "style": "success",
          }],
          [{
              "text": "BACK",
              "icon_custom_emoji_id": "5267490665117275176",
              "callback_data": "user_control",
              "style": "danger",
          }],
      ]
  }


def get_upload_firebase_keyboard():
  return {
      "inline_keyboard": [[{
          "text": "CANCEL",
          "callback_data": "back_to_admin",
          "icon_custom_emoji_id": "5420130255174145507",
          "style": "danger",
      }]]
  }


def get_back_only_keyboard():
  return {
      "inline_keyboard": [[{
          "text": "BACK",
          "callback_data": "user_cancel",
          "icon_custom_emoji_id": "5438541186539232243",
          "style": "danger",
      }]]
  }


def get_leaderboard_keyboard():
  return {
      "inline_keyboard": [[{
          "text": "REFRESH",
          "callback_data": "refresh_leaderboard",
          "icon_custom_emoji_id": "5229111790842952353",
          "style": "success",
      }]]
  }


def get_owner_panel_text():
  today = time.strftime("%Y-%m-%d")
  if daily_stats.get("date") != today:
    daily_stats["date"] = today
    daily_stats["numbers"] = 0
    daily_stats["otps"] = 0

  return (
      "<b>📊 OWNER ZONE 📊</b>\n"
      "━━━━━━━━━━━━━━━━━━\n"
      "<b>📊 DATABASE OVERVIEW</b>\n"
      "— — — — — — — — — —\n"
      f"<blockquote><b>👤 TOTAL USER         » {get_total_users()}</b></blockquote>\n"
      f"<blockquote><b>📱 TODAY NUMBER  » {daily_stats['numbers']}</b></blockquote>\n"
      f"<blockquote><b>💬 TODAY OTP           » {daily_stats['otps']}</b></blockquote>\n"
      "━━━━━━━━━━━━━━━━━━"
  )


def get_leaderboard_text():
  global cached_leaderboard_text
  if cached_leaderboard_text:
    return cached_leaderboard_text
  return "⏳ <b>Loading leaderboard, please wait...</b>"


def get_live_traffic_content():
  global recent_traffic
  hits_to_show = recent_traffic
  markup = {
      "inline_keyboard": [[{
          "text": "REFRESH",
          "callback_data": "refresh_traffic",
          "icon_custom_emoji_id": "5229111790842952353",
          "style": "primary",
      }]]
  }

  if not hits_to_show:
    return (
        "╔═════════════════╗\n║  <tg-emoji"
        ' emoji-id="5352877703043258544">📈</tg-emoji> <b>15M LIVE'
        " TRAFFIC</b>\n╚═════════════════╝\n<i>No traffic data"
        " available.</i>\n━━━━━━━━━━━━━━━━━━━",
        markup,
    )

  service_counts = {}
  for h in hits_to_show:
    raw_sid = h.get("sid") or "Unknown"
    raw_msg = h.get("message") or ""
    detected_sid = detect_service(raw_msg, raw_sid)
    app_info = PREMIUM_APPS.get(detected_sid, PREMIUM_APPS["Other"])

    if detected_sid not in service_counts:
      service_counts[detected_sid] = {
          "count": 0,
          "emoji_id": app_info["id"],
          "normal_emoji": app_info["emoji"],
      }
    service_counts[detected_sid]["count"] += 1

  sorted_services = sorted(
      service_counts.items(), key=lambda item: item[1]["count"], reverse=True
  )[:8]

  msg = (
      "╔═════════════════╗\n║  <tg-emoji"
      ' emoji-id="5352877703043258544">📈</tg-emoji> <b>15M LIVE'
      " TRAFFIC</b>\n╚═════════════════╝\n"
  )
  fire_emoji_id = GLOBAL_BODY_EMOJIS.get("🔥", "5337267511261960341")

  for i, (sid, data) in enumerate(sorted_services):
    msg += (
        f"<tg-emoji emoji-id=\"{data['emoji_id']}\">{data['normal_emoji']}</tg-emoji>"
        f" {html.escape(str(sid))} ➜ <tg-emoji emoji-id=\"{fire_emoji_id}\">🔥</tg-emoji>"
        f" {data['count']} OTP\n"
    )
    if i < len(sorted_services) - 1:
      msg += "— — — — — — — — — —\n"
  msg += "━━━━━━━━━━━━━━━━━━━"
  return msg, markup


def get_services_content():
  global cached_services_kb
  if cached_services_kb:
    return "📱 <b>Select Top Service:</b>", cached_services_kb
  return (
      "⏳ <b>Loading services, please try again in a few seconds...</b>",
      None,
  )


def get_countries_content(sid_short):
  global cached_countries_kb
  if sid_short in cached_countries_kb:
    return f"🌍 <b>Select Country:</b>", cached_countries_kb[sid_short], None
  return (
      None,
      None,
      "❌ <b>No active countries for this service. (Out of Stock)</b>",
  )


def get_number_allocation_content(sid_short, c_code, user_id=None):
  global voltx_auto_mode, voltx_dynamic_data, user_active_sessions, bot_settings, otp_button_link
  target_ranges = []
  full_sid = sid_short

  if voltx_auto_mode:
    for sid, data in voltx_dynamic_data.items():
      if sid.lower().startswith(sid_short.lower()):
        full_sid = sid
        for r, r_data in data["ranges"].items():
          if c_code.startswith(r) or r.startswith(c_code):
            target_ranges.append((r, r_data["hits"]))
        break
    target_ranges.sort(key=lambda x: x[1], reverse=True)
    best_ranges = [x[0] for x in target_ranges[:3]]
  else:
    services_data = fetch_live_access()
    for s in services_data:
      sid_val = s.get("sid") or ""
      if sid_val.lower().startswith(sid_short.lower()):
        full_sid = sid_val
        for r in s.get("ranges", []):
          clean_r = str(r).replace("X", "")
          if c_code.startswith(clean_r) or clean_r.startswith(c_code):
            if clean_r not in target_ranges:
              target_ranges.append(clean_r)
        break
    best_ranges = target_ranges[:3]

  if not best_ranges:
    best_ranges = [c_code]

  req_count = bot_settings.get("num_req", 1)
  fetched_numbers = []

  for _ in range(req_count):
    selected_rid = random.choice(best_ranges)
    num_data = fetch_live_number(selected_rid)
    if num_data:
      full_number = html.escape(str(num_data.get("full_number", "")))
      country = html.escape(str(num_data.get("country", "Unknown")))
      operator = html.escape(str(num_data.get("operator", "Unknown")))
      fetched_numbers.append((full_number, country, operator))

      if user_id and full_number:
        user_active_sessions[str(full_number)] = user_id

  if fetched_numbers:
    update_daily_stat("numbers", len(fetched_numbers))
    save_local_data()

    service_html, srv_eid = get_service_info_html(full_sid)
    _, country_with_flag = get_country_info(c_code)

    msg = (
        "━━━━━━━━━━━━━━━\n"
        '<tg-emoji emoji-id="5337172996211648018">⌛</tg-emoji> <b>ACTIVE'
        " NUMBER 15M</b>\n"
        "— — — — — — — — — —\n"
        f"{service_html} ➜ {country_with_flag}\n"
        "━━━━━━━━━━━━━━━"
    )

    kb = {"inline_keyboard": []}

    for f_num, ctry, op in fetched_numbers:
      clean_f_num = str(f_num).lstrip("+")
      kb["inline_keyboard"].append([{
          "text": f"+{clean_f_num}",
          "icon_custom_emoji_id": "5226929552319594190",
          "copy_text": {"text": f"+{clean_f_num}"},
          "style": "primary",
      }])

    kb["inline_keyboard"].append([
        {
            "text": "Change Number",
            "icon_custom_emoji_id": "5429386648431405093",
            "callback_data": f"cc_{sid_short}_{c_code}",
            "style": "danger",
        },
        {
            "text": "OTP Group",
            "icon_custom_emoji_id": "5314366268898300483",
            "url": otp_button_link,
            "style": "success",
        },
    ])
    kb["inline_keyboard"].append([{
        "text": "BACK",
        "icon_custom_emoji_id": "5438541186539232243",
        "callback_data": f"srv_{sid_short}",
        "style": "danger",
    }])

    return msg, kb
  else:
    return (
        "❌ <b>Out of stock in these ranges. Please try again.</b>",
        {
            "inline_keyboard": [[{
                "text": "BACK",
                "callback_data": f"srv_{sid_short}",
                "icon_custom_emoji_id": "5438541186539232243",
                "style": "danger",
            }]]
        },
    )


def broadcast_worker(from_chat_id, message_id, target_msg_id):
  users = get_all_user_ids()
  success_count = 0
  for uid in users:
    try:
      res = copy_message(uid, from_chat_id, message_id)
      if res and res.get("ok"):
        success_count += 1
      time.sleep(0.05)
    except:
      pass

  send_message(
      from_chat_id,
      "✅ <b>Broadcast Completed!</b>\nSuccessfully sent to"
      f" {success_count} users out of {len(users)}.",
  )

  if target_msg_id:
    edit_message(
        from_chat_id,
        target_msg_id,
        get_owner_panel_text(),
        reply_markup=get_admin_inline_keyboard(),
    )


def handle_message(message):
  global waiting_for_firebase, current_db_mode, db_firebase, user_states, voltx_keys
  global force_join_channels, otp_forward_groups, otp_button_link, bot_settings, GLOBAL_BODY_EMOJIS, PREMIUM_APPS

  if message.get("chat", {}).get("type") != "private":
    return

  chat_id = message["chat"]["id"]
  user_id = message["from"]["id"]
  text = message.get("text", "")
  message_id = message["message_id"]
  first_name = message["from"].get("first_name", "User")

  if text == "🔙 BACK" and user_id == ADMIN_ID:
    send_message(
        chat_id,
        "❌ <b>Action Cancelled!</b>",
        reply_markup=get_main_keyboard(user_id),
    )
    if user_id in user_states:
      del user_states[user_id]
    send_message(
        chat_id,
        get_owner_panel_text(),
        reply_markup=get_admin_inline_keyboard(),
    )
    return

  if "chat_shared" in message:
    shared_chat_id = message["chat_shared"]["chat_id"]
    if user_id == ADMIN_ID and user_id in user_states:
      state_data = user_states[user_id]
      state = state_data.get("state")
      target_msg_id = state_data.get("msg_id")

      send_message(
          chat_id,
          "✅ <b>Successfully Selected!</b>",
          reply_markup=get_main_keyboard(user_id),
      )

      if state == "waiting_otp_group":
        otp_forward_groups.clear()
        otp_forward_groups.append(str(shared_chat_id))

        inv_res = requests.post(
            BASE_URL + "exportChatInviteLink",
            json={"chat_id": shared_chat_id},
            timeout=10,
        ).json()
        if inv_res.get("ok"):
          otp_button_link = inv_res["result"]

        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:",
              reply_markup=get_otp_group_keyboard(),
          )
        del user_states[user_id]
        return

      elif state == "waiting_dxa_w_group":
        bot_settings["w_group"] = str(shared_chat_id)
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:",
              reply_markup=dxa_control_keyboard(),
          )
        del user_states[user_id]
        return

      elif state == "waiting_fj_channel":
        chat_details = get_chat_details(str(shared_chat_id))
        if chat_details:
          force_join_channels.append(chat_details)
          save_local_data()
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:",
                reply_markup=get_force_join_keyboard(),
            )
        else:
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "❌ <b>Failed to verify channel! Make sure bot is"
                " admin.</b>",
                reply_markup=get_back_only_keyboard(),
            )
        del user_states[user_id]
        return

  if not is_user_joined(user_id):
    fj_msg = (
        "<b>════《 <tg-emoji emoji-id=\"5337267511261960341\">🔥</tg-emoji>"
        " ACCESS REQUIRED 》════</b>\n\n"
        '<b><tg-emoji emoji-id="5420517437885943844">🔗</tg-emoji> JOIN ALL'
        " CHANNELS BELOW TO USE THIS BOT.</b>\n\n"
        '<b><tg-emoji emoji-id="5352694861990501856">✅</tg-emoji> JOIN ALL'
        " CHANNELS, THEN CLICK VERIFY.</b>"
    )
    send_message(chat_id, fj_msg, reply_markup=get_force_join_alert_keyboard())
    return

  if user_id in user_states:
    state_data = user_states[user_id]
    if isinstance(state_data, dict):
      state = state_data.get("state")
      target_msg_id = state_data.get("msg_id")
    else:
      state = state_data
      target_msg_id = None

    if state == "waiting_vk_key":
      voltx_keys.append(text.strip())
      save_local_data()
      if target_msg_id:
        edit_message(
            chat_id,
            target_msg_id,
            "🔑 <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:",
            reply_markup=get_voltx_keys_keyboard(),
        )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_otp_link":
      if text.startswith("http"):
        otp_button_link = text.strip()
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:",
              reply_markup=get_otp_group_keyboard(),
          )
      else:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid URL format. Must start with http/https.</b>",
              reply_markup=get_back_only_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_main_channel_link":
      if text.startswith("http"):
        bot_settings["main_channel_link"] = text.strip()
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:",
              reply_markup=get_otp_group_keyboard(),
          )
      else:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid URL format. Must start with http/https.</b>",
              reply_markup=get_back_only_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_broadcast":
      if target_msg_id:
        edit_message(
            chat_id, target_msg_id, "⏳ <b>Broadcasting message to all users...</b>"
        )
      threading.Thread(
          target=broadcast_worker,
          args=(chat_id, message_id, target_msg_id),
          daemon=True,
      ).start()
      del user_states[user_id]
      return

    elif state == "waiting_firebase":
      try:
        if "document" in message:
          file_id = message["document"]["file_id"]
          file_info = requests.get(
              BASE_URL + f"getFile?file_id={file_id}", timeout=10
          ).json()
          file_path = file_info["result"]["file_path"]
          file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
          text = requests.get(file_url, timeout=10).text

        text = (
            text.replace("“", '"')
            .replace("”", '"')
            .replace("‘", "'")
            .replace("’", "'")
        )

        firebase_cred = json.loads(text)
        with open("temp_firebase.json", "w") as f:
          json.dump(firebase_cred, f)
        try:
          if not firebase_admin._apps:
            firebase_admin.initialize_app(
                credentials.Certificate("temp_firebase.json")
            )
          db_firebase = firestore.client()
          current_db_mode = "firebase"
          waiting_for_firebase = False

          try:
            local_users = set()
            if os.path.exists(USERS_LIST_FILE):
              with open(USERS_LIST_FILE, "r") as f:
                local_users = set(json.load(f))

            docs = db_firebase.collection("users").select([]).stream()
            fb_users = set(int(doc.id) for doc in docs)

            combined_users = local_users.union(fb_users)
            if len(combined_users) > len(local_users):
              with open(USERS_LIST_FILE, "w") as f:
                json.dump(list(combined_users), f)
              print(f"✅ Synced {len(fb_users)} users from Firebase to Local List!")
          except Exception as e:
            print(f"User Sync Error: {e}")

          try:
            config_ref = db_firebase.collection("settings").document(
                "bot_config"
            )
            doc = config_ref.get()
            if not doc.exists:
              config_data = {
                  "bot_settings": bot_settings,
                  "force_join_status": force_join_status,
                  "force_join_channels": force_join_channels,
                  "otp_forward_groups": otp_forward_groups,
                  "otp_button_link": otp_button_link,
                  "voltx_keys": voltx_keys,
                  "voltx_auto_mode": voltx_auto_mode,
                  "custom_global_body_emojis": GLOBAL_BODY_EMOJIS,
                  "custom_premium_apps": PREMIUM_APPS,
              }
              config_ref.set(config_data)
            else:
              data = doc.to_dict()
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
              if "voltx_keys" in data:
                voltx_keys = data["voltx_keys"]
              if "voltx_auto_mode" in data:
                voltx_auto_mode = data["voltx_auto_mode"]
              if "custom_global_body_emojis" in data:
                GLOBAL_BODY_EMOJIS.update(data["custom_global_body_emojis"])
              if "custom_premium_apps" in data:
                PREMIUM_APPS.update(data["custom_premium_apps"])
              save_local_data()
          except Exception as e:
            pass

          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "⏳ <b>Syncing SQLite data to Firebase... Please wait.</b>",
            )
          migrate_sqlite_to_firebase()

          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                get_owner_panel_text(),
                reply_markup=get_admin_inline_keyboard(),
            )
          send_message(
              chat_id, "✅ <b>Firebase successfully connected & Synced!</b>"
          )
        except Exception as e:
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "❌ <b>Failed to connect to Firebase:</b>\n<code>"
                f"{html.escape(str(e))}</code>",
                reply_markup=get_back_only_keyboard(),
            )
      except Exception:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "⚠️ <b>Invalid JSON format. Please upload the .json file"
              " directly.</b>",
              reply_markup=get_back_only_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif isinstance(state, str) and state.startswith("waiting_app_emj_id_"):
      target_app = state[19:]
      clean_eid = text.strip()
      if re.match(r"^\d+$", clean_eid):
        if target_app in PREMIUM_APPS:
          PREMIUM_APPS[target_app]["id"] = clean_eid
          save_local_data()
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                f"✅ <b>Emoji ID updated for {target_app}!</b>",
                reply_markup=get_apps_emoji_keyboard(),
            )
      else:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid Emoji ID! Must be digits only.</b>",
              reply_markup=get_back_only_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_custom_global_emj":
      try:
        parts = text.strip().split()
        if len(parts) >= 2:
          emj_char = parts[0]
          emj_id = parts[1]
          if re.match(r"^\d+$", emj_id):
            GLOBAL_BODY_EMOJIS[emj_char] = emj_id
            save_local_data()
            if target_msg_id:
              edit_message(
                  chat_id,
                  target_msg_id,
                  f"✅ <b>Emoji ID set:</b> {emj_char} ➜ <code>{emj_id}</code>",
                  reply_markup=get_emoji_manager_keyboard(),
              )
          else:
            if target_msg_id:
              edit_message(
                  chat_id,
                  target_msg_id,
                  "❌ <b>ID must be numbers only.</b>",
                  reply_markup=get_back_only_keyboard(),
              )
        else:
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "❌ <b>Invalid format! Example: 🔥 5337267511261960341</b>",
                reply_markup=get_back_only_keyboard(),
            )
      except Exception:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Failed to parse input!</b>",
              reply_markup=get_back_only_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif isinstance(state, str) and state.startswith("waiting_withdraw_amount_"):
      method = state[24:]
      user_data = get_user(user_id)
      bal = user_data.get("balance", 0)
      min_w = bot_settings.get("min_withdraw", 10.0)

      try:
        amount = float(text.strip())
        if amount < min_w:
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                f"❌ <b>Minimum withdraw is {min_w} BDT.</b>\nTry again:",
                reply_markup=get_back_only_keyboard(),
            )
        elif amount > bal:
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "❌ <b>Insufficient balance! You only have"
                f" {bal:.2f} BDT.</b>\nTry again:",
                reply_markup=get_back_only_keyboard(),
            )
        else:
          user_states[user_id] = {
              "state": f"waiting_withdraw_number_{method}_{amount}",
              "msg_id": target_msg_id,
          }
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                f"✅ <b>Amount Set: {amount:.2f} BDT</b>\n\n💳"
                f" <b>Method:</b> {method}\n💬 <b>Now send your {method}"
                " account number:</b>",
                reply_markup=get_back_only_keyboard(),
            )
      except ValueError:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid amount. Send numbers only.</b>\nTry again:",
              reply_markup=get_back_only_keyboard(),
          )
      delete_message(chat_id, message_id)
      return

    elif isinstance(state, str) and state.startswith("waiting_withdraw_number_"):
      parts = state.split("_")
      method = parts[3]
      amount = float(parts[4])

      user_data = get_user(user_id)
      bal = user_data.get("balance", 0)

      if bal < amount:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Insufficient balance!</b>",
              reply_markup=get_main_keyboard(user_id),
          )
      else:
        account_number = text.strip()
        update_user_stats(user_id, -amount, 0)

        w_group = bot_settings.get("w_group", "")
        if w_group:
          w_msg = (
              '<tg-emoji emoji-id="5420396762189831222">🆕</tg-emoji> <b>NEW'
              " WITHDRAW REQUEST</b>\n"
              "━━━━━━━━━━━━━━━━━\n"
              '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>'
              f" <b>User:</b> <a href='tg://user?id={user_id}'>"
              f"{html.escape(first_name)}</a>\n"
              "— — — — — — — — — —\n"
              '<tg-emoji emoji-id="5226929552319594190">🆔</tg-emoji> <b>ID:</b>'
              f" <code>{user_id}</code>\n"
              "— — — — — — — — — —\n"
              '<tg-emoji emoji-id="5429612421977253466">💵</tg-emoji>'
              f" <b>Amount:</b> <b>{amount:.2f} BDT</b>\n"
              "— — — — — — — — — —\n"
              '<tg-emoji emoji-id="5190899075968441286">💳</tg-emoji>'
              f" <b>Method:</b> {method}\n"
              "— — — — — — — — — —\n"
              '<tg-emoji emoji-id="5337132498965010628">📞</tg-emoji>'
              f" <b>Number:</b> <code>{account_number}</code>\n"
              "━━━━━━━━━━━━━━━━━"
          )

          w_markup = {
              "inline_keyboard": [[
                  {
                      "text": "APPROVE",
                      "icon_custom_emoji_id": "5352694861990501856",
                      "callback_data": (
                          "admin_w_approve_"
                          f"{user_id}_{amount}_{account_number}"
                      ),
                      "style": "success",
                  },
                  {
                      "text": "REJECT",
                      "icon_custom_emoji_id": "5420130255174145507",
                      "callback_data": (
                          f"admin_w_reject_{user_id}_{amount}_{account_number}"
                      ),
                      "style": "danger",
                  },
              ]]
          }
          send_message(w_group, w_msg, reply_markup=w_markup)

        success_msg = (
            "━━━━━━━━━━━━━━━━━\n"
            '<tg-emoji emoji-id="5429612421977253466">💵</tg-emoji>'
            f" <b>Amount:</b> {amount:.2f} BDT\n"
            "— — — — — — — — — —\n"
            '<tg-emoji emoji-id="5190899075968441286">💳</tg-emoji>'
            f" <b>Method:</b> {method}\n"
            "— — — — — — — — — —\n"
            '<tg-emoji emoji-id="5337132498965010628">📞</tg-emoji>'
            f" <b>Number:</b> <code>{account_number}</code>\n"
            "━━━━━━━━━━━━━━━━━"
        )
        if target_msg_id:
          delete_message(chat_id, target_msg_id)
        send_message(
            chat_id, success_msg, reply_markup=get_main_keyboard(user_id)
        )

      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_dxa_ref_r":
      try:
        bot_settings["refer_reward"] = float(text.strip())
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:",
              reply_markup=dxa_control_keyboard(),
          )
      except ValueError:
        pass
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_dxa_min_w":
      try:
        bot_settings["min_withdraw"] = float(text.strip())
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:",
              reply_markup=dxa_control_keyboard(),
          )
      except ValueError:
        pass
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_dxa_cool":
      try:
        bot_settings["cooldown"] = int(text.strip())
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:",
              reply_markup=dxa_control_keyboard(),
          )
      except ValueError:
        pass
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_dxa_num_req":
      try:
        bot_settings["num_req"] = int(text.strip())
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:",
              reply_markup=dxa_control_keyboard(),
          )
      except ValueError:
        pass
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_w_method":
      bot_settings["w_methods"].append(text.strip())
      save_local_data()
      if target_msg_id:
        edit_message(
            chat_id,
            target_msg_id,
            "💳 <b>WITHDRAW METHODS</b>\nManage methods below:",
            reply_markup=dxa_manage_w_methods_keyboard(),
        )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_dxa_def_rate":
      try:
        bot_settings["otp_default_rate"] = float(text.strip())
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:",
              reply_markup=dxa_otp_control_keyboard(),
          )
      except ValueError:
        pass
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_dxa_srv_rate":
      try:
        parts = text.split("-")
        srv_name = parts[0].strip()
        srv_rate = float(parts[1].strip())
        bot_settings["otp_service_rates"][srv_name] = srv_rate
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:",
              reply_markup=dxa_otp_control_keyboard(),
          )
      except Exception:
        send_message(
            chat_id,
            "❌ Invalid format. Use: ServiceName - Rate (e.g. Telegram - 5.0)",
        )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif isinstance(state, str) and state.startswith("waiting_rate_value_"):
      srv_name = state[19:]
      try:
        srv_rate = float(text.strip())
        bot_settings["otp_service_rates"][srv_name] = srv_rate
        save_local_data()
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:",
              reply_markup=dxa_otp_control_keyboard(),
          )
      except ValueError:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid rate format! Use numbers (e.g. 2.5).</b>\n\n💰"
              f" <b>Enter Reward Rate for {html.escape(srv_name)}:</b>",
              reply_markup=get_back_only_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif state == "waiting_uc_id":
      try:
        target_uid = int(text.strip())
        target_data = get_user(target_uid)

        if target_data:
          safe_name = html.escape(str(target_data.get("first_name", "User")))
          total_otps = target_data.get("total_otps", 0)
          msg = (
              '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji> <b>USER'
              " PROFILE</b>\n━━━━━━━━━━━━━━━━━\n"
              f"<b>Name:</b> {safe_name}\n<b>ID:</b>"
              f" <code>{target_uid}</code>\n<b>Balance:</b>"
              f" {target_data.get('balance', 0):.2f} BDT\n<b>Total OTPs:</b>"
              f" {total_otps}\n<b>Total Invites:</b>"
              f" {target_data.get('total_invites', 0)}\n━━━━━━━━━━━━━━━━━"
          )
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                msg,
                reply_markup=get_user_profile_keyboard(target_uid),
            )
        else:
          if target_msg_id:
            edit_message(
                chat_id,
                target_msg_id,
                "❌ <b>User not found in database!</b>",
                reply_markup=get_user_control_keyboard(),
            )
      except ValueError:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid User ID format!</b>",
              reply_markup=get_user_control_keyboard(),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

    elif isinstance(state, str) and state.startswith("waiting_uc_balance_"):
      target_uid = int(state[19:])
      try:
        amount_to_add = float(text.strip())
        update_user_stats(target_uid, amount_to_add, 0)

        target_data = get_user(target_uid)
        msg = (
            "✅ <b>Balance Updated Successfully!</b>\n\n"
            '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji> <b>Name:</b>'
            f" {html.escape(target_data['first_name'])}\n"
            '<tg-emoji emoji-id="5429612421977253466">💵</tg-emoji> <b>New'
            f" Balance:</b> {target_data['balance']:.2f} BDT"
        )
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              msg,
              reply_markup=get_user_profile_keyboard(target_uid),
          )
      except ValueError:
        if target_msg_id:
          edit_message(
              chat_id,
              target_msg_id,
              "❌ <b>Invalid amount format! Use numbers (e.g. 50 or -10).</b>",
              reply_markup=get_user_profile_keyboard(target_uid),
          )
      del user_states[user_id]
      delete_message(chat_id, message_id)
      return

  if text in [
      "𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥",
      "𝗖𝗛𝗘𝗖𝗞 𝗧𝗥𝗔𝗙𝗙𝗜𝗖",
      "𝗜𝗡𝗩𝗜𝗧𝗘 𝗙𝗥𝗜𝗘𝗡𝗗",
      "𝗕𝗔𝗟𝗔𝗡𝗖𝗘",
      "𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗",
      "𝗢𝗪𝗡𝗘𝗥 𝗣𝗔𝗡𝗘𝗟",
  ]:
    if user_id in user_states:
      del user_states[user_id]

  is_new_user = get_user(user_id) is None
  add_user(user_id, first_name)
  user_data = get_user(user_id)

  if text.startswith("/start"):
    parts = text.split()
    if len(parts) > 1:
      param = parts[1]
      if param.startswith("alloc_"):
        try:
          _, req_range, req_sid = param.split("_", 2)

          last_req = user_cooldowns.get(user_id, 0)
          now = time.time()
          if now - last_req < bot_settings.get("cooldown", 0):
            send_message(
                chat_id,
                "⌛ <b>Please wait"
                f" {int(bot_settings['cooldown'] - (now - last_req))} seconds"
                " before requesting again.</b>",
            )
            return
          user_cooldowns[user_id] = now

          wait_msg = send_message(
              chat_id,
              "⏳ <b>Fetching number for"
              f" {req_sid.title().replace('_', ' ')}...</b>",
          )
          msg, markup = get_number_allocation_content(
              req_sid, req_range, user_id=user_id
          )

          if wait_msg and "result" in wait_msg:
            edit_message(
                chat_id,
                wait_msg["result"]["message_id"],
                msg,
                reply_markup=markup,
            )
          else:
            send_message(chat_id, msg, reply_markup=markup)
          return
        except Exception:
          pass
      else:
        try:
          inviter_id = int(param)
          if is_new_user and inviter_id != user_id and get_user(inviter_id):
            ref_amount = bot_settings.get("refer_reward", 0.2)
            update_user_stats(inviter_id, ref_amount, 1)
            send_message(
                inviter_id,
                "🎉 <b>New Referral!</b>\nSomeone joined using your link. You"
                f" received {ref_amount} BDT.",
            )
        except ValueError:
          pass
    send_message(
        chat_id,
        "🔥 <b>PREMIUM NUMBER BOT </b>\n\nWelcome"
        f" {html.escape(str(first_name))}, please select an option from the"
        " menu.",
        reply_markup=get_main_keyboard(user_id),
    )

  elif text == "𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥":
    msg, markup = get_services_content()
    if markup:
      send_message(chat_id, msg, reply_markup=markup)
    else:
      send_message(chat_id, msg)

  elif text == "𝗖𝗛𝗘𝗖𝗞 𝗧𝗥𝗔𝗙𝗙𝗜𝗖":
    msg, markup = get_live_traffic_content()
    send_message(chat_id, msg, reply_markup=markup)

  elif text == "𝗜𝗡𝗩𝗜𝗧𝗘 𝗙𝗥𝗜𝗘𝗡𝗗":
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    ref_reward = bot_settings.get("refer_reward", 0.2)
    msg = (
        "━━━━━━━━━━━━━━━━━\n"
        '<tg-emoji emoji-id="5420145051336485498">👥</tg-emoji> <b>Referral'
        " Program</b>\n"
        "━━━━━━━━━━━━━━━━━\n"
        '<tg-emoji emoji-id="5420517437885943844">🔗</tg-emoji> <b>Your Invite'
        f" Link:</b>\n<code>{invite_link}</code>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5420396762189831222">🎁</tg-emoji> <b>PER INVITE :'
        f" {ref_reward} TK</b>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5353032893096567467">📊</tg-emoji> <b>Total'
        f" Invites:</b> {user_data['total_invites']}\n"
        "━━━━━━━━━━━━━━━━━"
    )
    send_message(
        chat_id,
        msg,
        reply_markup={
            "inline_keyboard": [[{
                "text": "COPY LINK",
                "icon_custom_emoji_id": "5379889727325350343",
                "copy_text": {"text": invite_link},
                "style": "success",
            }]]
        },
    )

  elif text == "𝗕𝗔𝗟𝗔𝗡𝗖𝗘":
    wallet_txt = (
        '<tg-emoji emoji-id="5429105001655999635">💰</tg-emoji> <b>YOUR'
        " WALLET</b>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji> <b>NAME :</b>'
        f" {html.escape(str(first_name))}\n"
        "— — — — — — — — — —\n"
        f'<tg-emoji emoji-id="5226929552319594190">🆔</tg-emoji> <b>ID :</b>'
        f" <code>{user_id}</code>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5429612421977253466">💵</tg-emoji> <b>BALANCE :'
        f" {user_data['balance']:.2f} BDT</b>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5190899075968441286">💳</tg-emoji> <b>WITHDRAWAL'
        " METHODS :</b>"
    )
    kb = {"inline_keyboard": []}
    for method in bot_settings.get("w_methods", []):
      kb["inline_keyboard"].append([{
          "text": method,
          "icon_custom_emoji_id": "5431783519355444455",
          "callback_data": f"user_withdraw_{method}",
          "style": "primary",
      }])
    send_message(chat_id, wallet_txt, reply_markup=kb)

  elif text == "𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗":
    send_message(
        chat_id,
        get_leaderboard_text(),
        reply_markup=get_leaderboard_keyboard(),
    )

  elif text == "𝗢𝗪𝗡𝗘𝗥 𝗣𝗔𝗡𝗘𝗟":
    if user_id == ADMIN_ID:
      send_message(
          chat_id,
          get_owner_panel_text(),
          reply_markup=get_admin_inline_keyboard(),
      )
    else:
      send_message(
          chat_id,
          "⚠️ <b>Access Denied!</b>\nThis menu is restricted to the admin.",
      )


def handle_callback(callback_query):
  global user_states, voltx_auto_mode, current_db_mode, force_join_status, force_join_channels, voltx_keys
  global otp_forward_groups, bot_settings, GLOBAL_BODY_EMOJIS, PREMIUM_APPS
  query_id = callback_query["id"]
  user_id = callback_query["from"]["id"]
  data = callback_query["data"]
  chat_id = callback_query["message"]["chat"]["id"]
  message_id = callback_query["message"]["message_id"]

  if data == "check_fj_joined":
    if is_user_joined(user_id):
      delete_message(chat_id, message_id)
      send_message(
          chat_id,
          "✅ <b>Thank you for joining! You can now use the bot.</b>",
          reply_markup=get_main_keyboard(user_id),
      )
    else:
      answer_callback_query(
          query_id, "❌ You haven't joined all channels!", show_alert=True
      )
    return

  if not is_user_joined(user_id):
    answer_callback_query(query_id, "Join channels first!", show_alert=True)
    return

  if data == "refresh_traffic":
    msg, markup = get_live_traffic_content()
    edit_message(chat_id, message_id, msg, reply_markup=markup)
    answer_callback_query(query_id, "Traffic Refreshed!")
    return

  if data == "back_to_services":
    msg, markup = get_services_content()
    edit_message(chat_id, message_id, msg, reply_markup=markup)
    answer_callback_query(query_id)
    return

  if data.startswith("srv_"):
    sid_short = data[4:]
    msg, markup, err = get_countries_content(sid_short)
    if err:
      answer_callback_query(query_id, err, show_alert=True)
    else:
      edit_message(chat_id, message_id, msg, reply_markup=markup)
      answer_callback_query(query_id)
    return

  if data.startswith("cc_"):
    parts = data.split("_")
    sid_short = parts[1]
    c_code = parts[2]

    last_req = user_cooldowns.get(user_id, 0)
    now = time.time()
    if now - last_req < bot_settings.get("cooldown", 0):
      answer_callback_query(
          query_id,
          f"Please wait {int(bot_settings['cooldown'] - (now - last_req))}"
          " seconds.",
          show_alert=True,
      )
      return
    user_cooldowns[user_id] = now

    answer_callback_query(query_id, "Allocating number...")
    edit_message(
        chat_id,
        message_id,
        "⏳ <b>Fetching best top range and allocating number...</b>",
    )

    msg, markup = get_number_allocation_content(
        sid_short, c_code, user_id=user_id
    )
    edit_message(chat_id, message_id, msg, reply_markup=markup)
    return

  if data == "refresh_leaderboard":
    edit_message(
        chat_id,
        message_id,
        get_leaderboard_text(),
        reply_markup=get_leaderboard_keyboard(),
    )
    answer_callback_query(query_id, "Leaderboard Refreshed!")
    return

  if data.startswith("user_withdraw_"):
    method = data[14:]
    user_data = get_user(user_id)
    bal = user_data.get("balance", 0)
    min_w = bot_settings.get("min_withdraw", 10.0)

    if bal < min_w:
      answer_callback_query(
          query_id,
          f"❌ Minimum withdraw is {min_w} BDT. You have {bal:.2f} BDT.",
          show_alert=True,
      )
      return

    user_states[user_id] = {
        "state": f"waiting_withdraw_amount_{method}",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        f"💳 <b>Withdraw via {method}</b>\n\n💵 Your Balance: {bal:.2f}"
        " BDT\n💬 <b>Enter the amount you want to withdraw:</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
    return

  if data == "user_cancel":
    if user_id in user_states:
      del user_states[user_id]
    delete_message(chat_id, message_id)
    send_message(
        chat_id,
        "❌ Action Cancelled.",
        reply_markup=get_main_keyboard(user_id),
    )
    answer_callback_query(query_id)
    return

  if user_id != ADMIN_ID:
    answer_callback_query(query_id, "Access Denied!", show_alert=True)
    return

  if data.startswith("admin_w_approve_") or data.startswith("admin_w_reject_"):
    parts = data.split("_")
    action = parts[2]
    req_user_id = int(parts[3])
    amount = float(parts[4])
    acc_number = parts[5]

    masked_number = (
        f"{acc_number[:3]}DXA{acc_number[-3:]}"
        if len(acc_number) >= 6
        else acc_number
    )

    msg_text = callback_query.get("message", {}).get("text", "")
    fname_match = re.search(r"User:\s*(.+)", msg_text)
    req_first_name = fname_match.group(1) if fname_match else "User"
    method_match = re.search(r"Method:\s*(.+)", msg_text)
    req_method = method_match.group(1) if method_match else "Unknown"

    if action == "approve":
      btn_text = "APPROVED BY ADMIN"
      btn_style = "success"
      btn_icon = "5352694861990501856"
      send_message(
          req_user_id,
          '<tg-emoji emoji-id="5420396762189831222">🎉</tg-emoji>'
          " <b>Withdrawal Approved!</b>\nYour request of"
          f" {amount:.2f} BDT has been sent to <code>{masked_number}</code>.",
      )
    else:
      btn_text = "REJECTED BY ADMIN"
      btn_style = "danger"
      btn_icon = "5420130255174145507"
      update_user_stats(req_user_id, amount, 0)
      send_message(
          req_user_id,
          '<tg-emoji emoji-id="5336944168944047463">⚠️</tg-emoji>'
          " <b>Withdrawal Rejected!</b>\nYour request of"
          f" {amount:.2f} BDT to <code>{masked_number}</code> was rejected and"
          " refunded.",
      )

    updated_msg = (
        '<tg-emoji emoji-id="5420396762189831222">🆕</tg-emoji> <b>WITHDRAW'
        " REQUEST PROCESSED</b>\n"
        "━━━━━━━━━━━━━━━━━\n"
        '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>'
        f" <b>User:</b> <a href='tg://user?id={req_user_id}'>"
        f"{html.escape(req_first_name)}</a>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5226929552319594190">🆔</tg-emoji> <b>ID:</b>'
        f" <code>{req_user_id}</code>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5429612421977253466">💵</tg-emoji>'
        f" <b>Amount:</b> <b>{amount:.2f} BDT</b>\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5190899075968441286">💳</tg-emoji>'
        f" <b>Method:</b> {req_method}\n"
        "— — — — — — — — — —\n"
        '<tg-emoji emoji-id="5431783519355444455">📞</tg-emoji>'
        f" <b>Number:</b> <code>{masked_number}</code>\n"
        "━━━━━━━━━━━━━━━━━"
    )

    updated_markup = {
        "inline_keyboard": [[{
            "text": btn_text,
            "icon_custom_emoji_id": btn_icon,
            "callback_data": "ignore_action",
            "style": btn_style,
        }]]
    }

    edit_message(chat_id, message_id, updated_msg, reply_markup=updated_markup)
    answer_callback_query(query_id, f"Request {action.title()}d!")
    return

  # ===== Voltx Key Manager =====
  if data == "manage_voltx":
    edit_message(
        chat_id,
        message_id,
        "🔑 <b>PANEL KEY SYSTEM</b>\nManage API Keys below:",
        reply_markup=get_voltx_keys_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "toggle_vk":
    voltx_auto_mode = not voltx_auto_mode
    save_local_data()
    edit_message(
        chat_id,
        message_id,
        "🔑 <b>PANEL KEY SYSTEM</b>\nManage API Keys below:",
        reply_markup=get_voltx_keys_keyboard(),
    )
    answer_callback_query(
        query_id, f"Panel Mode: {'ON' if voltx_auto_mode else 'OFF'}"
    )
  elif data == "add_vk":
    user_states[user_id] = {"state": "waiting_vk_key", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "🔑 <b>Please reply to this message with the new Panel API Key.</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data.startswith("del_vk_"):
    idx = int(data[7:])
    if idx < len(voltx_keys):
      if len(voltx_keys) > 1:
        voltx_keys.pop(idx)
        save_local_data()
        edit_message(
            chat_id,
            message_id,
            "🔑 <b>PANEL KEY SYSTEM</b>\nManage API Keys below:",
            reply_markup=get_voltx_keys_keyboard(),
        )
        answer_callback_query(query_id, "Key Deleted!")
      else:
        answer_callback_query(
            query_id, "Cannot delete the only key!", show_alert=True
        )

  # ===== Force Join Manager =====
  elif data == "manage_fj":
    edit_message(
        chat_id,
        message_id,
        "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:",
        reply_markup=get_force_join_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "toggle_fj":
    force_join_status = not force_join_status
    save_local_data()
    edit_message(
        chat_id,
        message_id,
        "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:",
        reply_markup=get_force_join_keyboard(),
    )
    answer_callback_query(
        query_id, f"Force Join: {'ON' if force_join_status else 'OFF'}"
    )
  elif data == "add_fj":
    user_states[user_id] = {
        "state": "waiting_fj_channel",
        "msg_id": message_id,
    }
    select_kb = {
        "keyboard": [
            [{
                "text": "Select Force Join Channel",
                "request_chat": {"request_id": 3, "chat_is_channel": True},
            }],
            [{"text": "🔙 BACK"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    send_message(
        chat_id,
        "👇 <b>Select Channel from below:</b>\n<i>(Make sure bot is an admin"
        " there)</i>",
        reply_markup=select_kb,
    )
    answer_callback_query(query_id)
  elif data.startswith("del_fj_"):
    idx = int(data[7:])
    if idx < len(force_join_channels):
      force_join_channels.pop(idx)
    save_local_data()
    edit_message(
        chat_id,
        message_id,
        "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:",
        reply_markup=get_force_join_keyboard(),
    )
    answer_callback_query(query_id, "Channel Deleted!")

  # ===== OTP Group Manager =====
  elif data == "manage_otp_group":
    edit_message(
        chat_id,
        message_id,
        "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:",
        reply_markup=get_otp_group_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "add_otp_group":
    user_states[user_id] = {"state": "waiting_otp_group", "msg_id": message_id}
    select_kb = {
        "keyboard": [
            [{
                "text": "Select OTP Group",
                "request_chat": {"request_id": 1, "chat_is_channel": False},
            }],
            [{"text": "🔙 BACK"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    send_message(
        chat_id,
        "👇 <b>Select OTP Group from below:</b>",
        reply_markup=select_kb,
    )
    answer_callback_query(query_id)
  elif data.startswith("del_otp_group_"):
    idx = int(data[14:])
    if idx < len(otp_forward_groups):
      otp_forward_groups.pop(idx)
    save_local_data()
    edit_message(
        chat_id,
        message_id,
        "🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:",
        reply_markup=get_otp_group_keyboard(),
    )
    answer_callback_query(query_id, "Group Deleted!")
  elif data == "edit_otp_link":
    user_states[user_id] = {"state": "waiting_otp_link", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "🔗 <b>Please send the new URL for the inline button attached to"
        " forwarded OTPs.</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "edit_main_channel":
    user_states[user_id] = {
        "state": "waiting_main_channel_link",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        "🔗 <b>Please send the URL for the MAIN CHANNEL inline button.</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)

  # ===== DXA Control Panel =====
  elif data == "dxa_control":
    edit_message(
        chat_id,
        message_id,
        "⚙️ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:",
        reply_markup=dxa_control_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "dxa_min_w":
    user_states[user_id] = {"state": "waiting_dxa_min_w", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "💸 <b>Enter new Minimum Withdraw Amount (e.g. 50):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "dxa_ref_r":
    user_states[user_id] = {"state": "waiting_dxa_ref_r", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "💸 <b>Enter new Referral Reward Amount (e.g. 5.0):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "dxa_otp_control":
    edit_message(
        chat_id,
        message_id,
        "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:",
        reply_markup=dxa_otp_control_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "dxa_def_rate":
    user_states[user_id] = {
        "state": "waiting_dxa_def_rate",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        "💰 <b>Enter new Default OTP Rate (e.g. 0.5):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)

  elif data.startswith("del_srv_rate_"):
    srv_name = data[13:]
    if srv_name in bot_settings["otp_service_rates"]:
      del bot_settings["otp_service_rates"][srv_name]
      save_local_data()
    edit_message(
        chat_id,
        message_id,
        "💰 <b>OTP REWARD CONTROL</b>\nManage rates below:",
        reply_markup=dxa_otp_control_keyboard(),
    )
    answer_callback_query(query_id, f"Rate for {srv_name} deleted!")
  elif data == "dxa_srv_rate":
    kb = {"inline_keyboard": []}
    row = []
    for sid, s_data in voltx_dynamic_data.items():
      safe_sid = html.escape(str(sid))
      row.append({
          "text": safe_sid,
          "callback_data": f"s_rt_{safe_sid[:15]}",
          "icon_custom_emoji_id": s_data["emoji_id"],
          "style": "primary",
      })
      if len(row) == 2:
        kb["inline_keyboard"].append(row)
        row = []
    if row:
      kb["inline_keyboard"].append(row)

    kb["inline_keyboard"].append([{
        "text": "Manual Entry",
        "callback_data": "dxa_srv_rate_manual",
        "style": "success",
    }])
    kb["inline_keyboard"].append([{
        "text": "BACK",
        "callback_data": "dxa_otp_control",
        "icon_custom_emoji_id": "5267490665117275176",
        "style": "danger",
    }])

    edit_message(
        chat_id,
        message_id,
        "💰 <b>Select a Service to Set Rate:</b>",
        reply_markup=kb,
    )
    answer_callback_query(query_id)

  elif data == "dxa_srv_rate_manual":
    user_states[user_id] = {
        "state": "waiting_dxa_srv_rate",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        "💰 <b>Enter Specific Service Rate.</b>\nFormat: <code>ServiceName -"
        " Rate</code>\nExample: <code>Telegram - 2.5</code>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)

  elif data.startswith("s_rt_"):
    sid_short = data[5:]
    full_sid = sid_short
    for sid in voltx_dynamic_data:
      if str(sid).startswith(sid_short):
        full_sid = str(sid)
        break
    user_states[user_id] = {
        "state": f"waiting_rate_value_{full_sid}",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        f"💰 <b>Enter Reward Rate for {html.escape(full_sid)}:</b>\n(e.g. 2.5)",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "dxa_cool":
    user_states[user_id] = {"state": "waiting_dxa_cool", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "⏳ <b>Enter new Cooldown time in seconds (e.g. 10):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "dxa_num_req":
    user_states[user_id] = {
        "state": "waiting_dxa_num_req",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        "📱 <b>Enter how many numbers a user gets per request (e.g. 3):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "manage_w_methods":
    edit_message(
        chat_id,
        message_id,
        "💳 <b>WITHDRAW METHODS</b>\nManage methods below:",
        reply_markup=dxa_manage_w_methods_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "add_w_method":
    user_states[user_id] = {"state": "waiting_w_method", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "💳 <b>Enter new Withdraw Method Name (e.g. bKash):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data.startswith("del_w_method_"):
    idx = int(data[13:])
    if idx < len(bot_settings["w_methods"]):
      bot_settings["w_methods"].pop(idx)
    save_local_data()
    edit_message(
        chat_id,
        message_id,
        "💳 <b>WITHDRAW METHODS</b>\nManage methods below:",
        reply_markup=dxa_manage_w_methods_keyboard(),
    )
    answer_callback_query(query_id, "Method Deleted!")
  elif data == "dxa_w_group":
    user_states[user_id] = {
        "state": "waiting_dxa_w_group",
        "msg_id": message_id,
    }
    select_kb = {
        "keyboard": [
            [{
                "text": "Select Withdraw Group",
                "request_chat": {"request_id": 2, "chat_is_channel": False},
            }],
            [{"text": "🔙 BACK"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    send_message(
        chat_id,
        "👇 <b>Select Withdraw Group from below:</b>",
        reply_markup=select_kb,
    )
    answer_callback_query(query_id)

  # ===== Dynamic Emoji Manager Callbacks =====
  elif data == "manage_emojis":
    edit_message(
        chat_id,
        message_id,
        "🎨 <b>CUSTOM EMOJI MANAGER</b>\nConfigure Telegram Custom Emoji IDs"
        " dynamically:",
        reply_markup=get_emoji_manager_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "emj_apps":
    edit_message(
        chat_id,
        message_id,
        "📱 <b>Select an App Service to update its Telegram Custom Emoji"
        " ID:</b>",
        reply_markup=get_apps_emoji_keyboard(),
    )
    answer_callback_query(query_id)
  elif data.startswith("set_app_emj_"):
    app_name = data[12:]
    user_states[user_id] = {
        "state": f"waiting_app_emj_id_{app_name}",
        "msg_id": message_id,
    }
    current_id = PREMIUM_APPS.get(app_name, {}).get("id", "None")
    edit_message(
        chat_id,
        message_id,
        f"🎨 <b>Changing Emoji ID for: {app_name}</b>\n\n📌 <b>Current"
        f" ID:</b> <code>{current_id}</code>\n\n💬 <b>Reply with the new"
        " Custom Emoji ID (Digits only):</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "emj_custom_global":
    user_states[user_id] = {
        "state": "waiting_custom_global_emj",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        "✨ <b>Set Any Character/Flag/Body Emoji ID</b>\n\nFormat: <code>Emoji"
        " ID</code>\nExample: <code>🔥 5337267511261960341</code> or <code>🇧🇩"
        " 5291824687096027834</code>\n\n💬 <b>Send your emoji and new ID"
        " separated by a space:</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)
  elif data == "emj_reset_all":
    GLOBAL_BODY_EMOJIS = dict(DEFAULT_GLOBAL_BODY_EMOJIS)
    PREMIUM_APPS = {k: dict(v) for k, v in DEFAULT_PREMIUM_APPS.items()}
    save_local_data()
    edit_message(
        chat_id,
        message_id,
        "✅ <b>All Emoji IDs have been reset to factory defaults!</b>",
        reply_markup=get_emoji_manager_keyboard(),
    )
    answer_callback_query(query_id, "Emojis Reset!")

  # ===== Broadcast System =====
  elif data == "broadcast_menu":
    user_states[user_id] = {"state": "waiting_broadcast", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "📣 <b>BROADCAST SYSTEM</b>\n\nSend any text, photo, video, or audio"
        " message you want to broadcast to all users.",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)

  elif data == "upload_firebase":
    user_states[user_id] = {"state": "waiting_firebase", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "🔥 <b>FIREBASE SETUP</b>\n\nPlease reply with the <b>entire JSON"
        " content</b> of your Firebase Service Account file.",
        reply_markup=get_upload_firebase_keyboard(),
    )
    answer_callback_query(query_id, "Send JSON Now")

  # ===== User Control =====
  elif data == "user_control":
    msg = (
        "👥 <b>USER CONTROL</b>\n━━━━━━━━━━━━━━━━━\n📊 <b>Total Users:</b>"
        f" {get_total_users()}\n\n👇 Manage users below:"
    )
    edit_message(
        chat_id,
        message_id,
        msg,
        reply_markup=get_user_control_keyboard(),
    )
    answer_callback_query(query_id)

  elif data == "uc_profile":
    user_states[user_id] = {"state": "waiting_uc_id", "msg_id": message_id}
    edit_message(
        chat_id,
        message_id,
        "🆔 <b>Send the Telegram User ID to view profile:</b>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)

  elif data.startswith("uc_balance_"):
    target_uid = int(data[11:])
    user_states[user_id] = {
        "state": f"waiting_uc_balance_{target_uid}",
        "msg_id": message_id,
    }
    edit_message(
        chat_id,
        message_id,
        "💵 <b>Send the amount to Add or Subtract.</b>\n<i>(Examples: To add use"
        " 50, to deduct use -10)</i>",
        reply_markup=get_back_only_keyboard(),
    )
    answer_callback_query(query_id)

  elif data == "back_to_admin":
    if user_id in user_states:
      del user_states[user_id]
    edit_message(
        chat_id,
        message_id,
        get_owner_panel_text(),
        reply_markup=get_admin_inline_keyboard(),
    )
    answer_callback_query(query_id)

  elif data == "db_status":
    answer_callback_query(
        query_id, f"Current DB: {current_db_mode.upper()}", show_alert=True
    )

  elif data == "close_panel":
    answer_callback_query(query_id, "Closed")
    delete_message(chat_id, message_id)

  else:
    answer_callback_query(query_id, f"{data} clicked!", show_alert=True)


# ==========================================
# Render Port Binding Helper
# ==========================================
class DummyServerHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.send_header("Content-type", "text/plain")
    self.end_headers()
    self.wfile.write(b"Bot is alive and running!")

  def log_message(self, format, *args):
    return


def run_http_server():
  port = int(os.environ.get("PORT", 8080))
  server = HTTPServer(("0.0.0.0", port), DummyServerHandler)
  server.serve_forever()


# ==========================================
# Main
# ==========================================
def main():
  global BOT_USERNAME

  # 🌟 Render Free Web Service Port Binding Thread
  threading.Thread(target=run_http_server, daemon=True).start()

  load_local_data()
  init_sqlite()
  init_firebase_from_file()

  BOT_USERNAME = get_bot_info()
  set_bot_commands()

  threading.Thread(target=voltx_console_listener, daemon=True).start()
  threading.Thread(target=voltx_sms_listener, daemon=True).start()
  threading.Thread(target=auto_cache_menu_thread, daemon=True).start()

  print(
      f"Bot @{BOT_USERNAME} is running with Voltx, DXA Control, Emoji Manager &"
      " OTP Forwarding..."
  )

  offset = None
  while True:
    try:
      url = BASE_URL + "getUpdates"
      res = requests.get(
          url, params={"timeout": 30, "offset": offset}, timeout=35
      ).json()
      if res.get("ok"):
        for update in res["result"]:
          offset = update["update_id"] + 1
          if "message" in update:
            threading.Thread(
                target=handle_message, args=(update["message"],)
            ).start()
          elif "callback_query" in update:
            threading.Thread(
                target=handle_callback, args=(update["callback_query"],)
            ).start()
    except Exception as e:
      time.sleep(3)


if __name__ == "__main__":
  main()