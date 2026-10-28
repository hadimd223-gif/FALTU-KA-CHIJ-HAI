# LEAKED BY @mhxffv111
# DON'T CHANGE CREDIT
# ক্রেডিট চেঞ্জ করলে তোর মার প**** দিয়ে হবি তুই, credit চেঞ্জ করলে tui একটা খানকির পোলা মাদারচোদ তোর মারে আমি জোবায়ের ১০০ বার চ**** ক্রেডিট চেঞ্জ করলে।


import telebot
import json
import time
import threading
import schedule
import requests
from datetime import datetime, timedelta, timezone
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, MessageEntity
import sqlite3
import os

os.environ['TZ'] = 'Asia/Dhaka'
time.tzset()

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda tz: pytz.timezone(tz)

BD_ZONE = ZoneInfo("Asia/Dhaka")

def get_bd_time():
    return datetime.now(BD_ZONE)

def parse_expiry_bd(expires_on):
    if not expires_on:
        return None
    try:
        return datetime.strptime(expires_on, "%Y-%m-%d").replace(
            hour=4, minute=0, second=0, microsecond=0, tzinfo=BD_ZONE
        )
    except Exception:
        return None

def get_remaining_days_text(expires_on):
    if not expires_on:
        return "♾️ Permanent"
    expire_dt = parse_expiry_bd(expires_on)
    if not expire_dt:
        return expires_on
    now_bd = get_bd_time()
    delta = expire_dt - now_bd
    if delta.total_seconds() <= 0:
        return "❌ Expired"
    days_left = delta.days
    hours_left = delta.seconds // 3600
    if days_left >= 1:
        return f"{days_left} day(s) {hours_left}h left"
    return f"{hours_left}h left (expires today)"

# ==================== DATABASE SETUP ====================
db_local = threading.local()

def get_db_connection():
    if not hasattr(db_local, 'conn'):
        db_local.conn = sqlite3.connect('freefirelk_bot.db', check_same_thread=False)
        db_local.conn.row_factory = sqlite3.Row
    return db_local.conn

def init_db():
    conn = sqlite3.connect('freefirelk_bot.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
        (user_id INTEGER PRIMARY KEY,
         username TEXT,
         full_name TEXT,
         balance REAL DEFAULT 0,
         total_deposit REAL DEFAULT 0,
         total_spent REAL DEFAULT 0,
         join_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
        (order_id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         uid TEXT,
         server_name TEXT,
         likes_amount INTEGER,
         price REAL,
         order_type TEXT,
         status TEXT,
         order_date TEXT,
         expiry_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS auto_likes
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         uid TEXT,
         server_name TEXT,
         price REAL,
         days INTEGER,
         start_date TEXT,
         expiry_date TEXT,
         status TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS deposit_history
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         amount REAL,
         payment_key TEXT,
         transaction_id TEXT,
         status TEXT,
         date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS redeem_codes
        (code TEXT PRIMARY KEY,
         amount REAL,
         created_by INTEGER,
         is_used INTEGER DEFAULT 0,
         used_by INTEGER,
         created_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pending_payments
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         amount REAL,
         payment_key TEXT,
         payment_url TEXT,
         status TEXT DEFAULT 'pending',
         created_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS settings
        (key TEXT PRIMARY KEY,
         value TEXT)''')

    default_settings = [
        ('daily_like_price', '6'),
        ('daily_like_amount', '220'),
        ('daily_like_enabled', 'on'),
        ('auto_like_enabled', 'on'),
        ('add_money_enabled', 'on'),
        ('daily_like_off_msg', '🔥 Daily Like service is temporarily disabled. Please try again later.'),
        ('auto_like_off_msg', '⭐ Auto Like service is temporarily disabled. Please try again later.'),
        ('add_money_off_msg', '💰 Add Money service is temporarily disabled. Please try again later.'),
        ('welcome_video_id', ''),
        ('bot_status', 'running'),
        ('maintenance_mode', 'off'),
        ('maintenance_msg', '🛠 Bot is under maintenance. We will be back soon!'),
        ('pro_like_price', '6'),
        ('pro_like_enabled', 'on'),
        ('pro_like_off_msg', 'DAILY LIKE PRO+ service is temporarily disabled. Please try again later.'),
        ('refer_enabled', 'on'),
        ('refer_signup_bonus', '1'),
        ('refer_deposit_percent', '10'),
        ('refer_post_group', '-1004383760459'),
        ('refer_post_enabled', 'on'),
        ('deposit_post_enabled', 'on'),
        ('channel_1', 'https://t.me/MHXLIKE_11'),
        ('channel_2', 'https://t.me/MHXLIKE_11'),
        ('channel_check_enabled', 'on'),
        ('pro_like_daily_limit', '30'),
        ('pro_like_used_count', '0'),
        ('pro_like_last_reset_date', ''),
        ('buy_auto_like_enabled', 'on'),
        ('remove_uid_enabled', 'on'),
        ('change_uid_enabled', 'on'),
        ('check_uids_enabled', 'on'),
        ('uid_change_fee', '50'),
    ]

    for key, value in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    extra_columns = [
        ("users", "referred_by", "INTEGER"),
        ("users", "referral_earnings", "REAL DEFAULT 0"),
        ("users", "channel_joined", "INTEGER DEFAULT 0"),
        ("auto_likes", "account_name", "TEXT"),
        ("auto_likes", "package_id", "TEXT"),
        ("auto_likes", "category", "TEXT DEFAULT 'standard'"),
        ("auto_likes", "admin_status", "TEXT DEFAULT 'active'"),
    ]
    for table, col, coltype in extra_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         referrer_id INTEGER,
         referred_id INTEGER UNIQUE,
         channel_joined INTEGER DEFAULT 0,
         signup_bonus_paid INTEGER DEFAULT 0,
         total_commission REAL DEFAULT 0,
         created_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS channel_joins
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         channel_url TEXT,
         joined_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS auto_like_packages
        (package_id TEXT PRIMARY KEY,
         category TEXT,
         days INTEGER,
         price REAL,
         likes_amount INTEGER,
         enabled INTEGER DEFAULT 1)''')

    default_packages = [
        ("std_7", "standard", 7, 90, 220, 1),
        ("std_15", "standard", 15, 150, 220, 1),
        ("std_30", "standard", 30, 250, 220, 1),
        ("vip_7", "vip", 7, 180, 400, 1),
        ("vip_15", "vip", 15, 250, 400, 1),
        ("vip_30", "vip", 30, 450, 400, 1),
    ]
    for pid, cat, days, price, likes, enabled in default_packages:
        cursor.execute("INSERT OR IGNORE INTO auto_like_packages (package_id, category, days, price, likes_amount, enabled) VALUES (?, ?, ?, ?, ?, ?)",
                       (pid, cat, days, price, likes, enabled))

    conn.commit()
    conn.close()

init_db()

# ==================== PREMIUM EMOJI IDs ====================
PE = {
    "heart": "6073439375541148459",
    "like": "6111543187224926438",
    "heart_fire": "6073221865512375925",
    "red_heart": "6312177104079297076",
    "link": "6129589862413638401",
    "heart2": "6185719454270231467",
    "love": "5233278609199735011",
    "kiss": "6318763986183523123",
    "star": "6170076921385194280",
    "star2": "6064113571317419294",
    "star3": "6100397682667294267",
    "sparkle": "6064179640799333596",
    "fire": "6312301048245525649",
    "fire2": "6311799464784827510",
    "lightning": "6170464829946468179",
    "lightning2": "6064381676060937106",
    "crown": "6172745002314118594",
    "crown2": "6170125411565966766",
    "crown3": "6314116466497033934",
    "gem": "6170105044831047908",
    "gem2": "6271512469684883558",
    "gem3": "6064293500382350516",
    "check": "6170356150094009102",
    "check2": "6073495107036778942",
    "check3": "6159002026089912716",
    "check4": "6158853733754084612",
    "check5": "6062241979188645414",
    "checkmark": "6169954746745492343",
    "cross": "6337074578522642080",
    "cross2": "6271611232457855630",
    "no": "5425122188288105579",
    "warn": "6312099300746728685",
    "warn2": "6100288345684840059",
    "warn3": "6276132901012640832",
    "key": "6176966310920983412",
    "ticket": "6260059243605398502",
    "robot": "5372981976804366741",
    "user": "5217584755750509979",
    "shield": "6170491132326188067",
    "shield2": "6156449587155442616",
    "trophy": "6158709594651630592",
    "trophy2": "6156795787289303568",
    "new": "6073276656410170177",
    "free": "6176861049862493512",
    "top": "6170046190894191839",
    "chart": "6143271021173543049",
    "phone": "6100373347382595494",
    "globe": "6269490656779965144",
    "gift": "6158907064362998049",
    "gift2": "6131689281082626007",
    "gamepad": "6158973086600273462",
    "gamepad2": "6100644591747207528",
    "clock": "6336848409839801489",
    "refresh": "6100630203606766038",
    "alert": "6257780484281997093",
    "arrow_down": "6314178812242302819",
    "arrow_right": "6260464748647683711",
    "play": "6312105292226107223",
    "hundred": "6169996644151465371",
    "thumbsup": "6311955243248655565",
    "wave": "5233328606914027335",
    "bd_flag": "5229234880310686265",
    "handshake": "6172260152046000530",
    "money": "6170456798357624260",
    "coins": "5379773896352355687",
    "calendar": "6336848409839801489",
    "smile": "6169980404880119256",
    "sunglasses": "6147552742790405148",
    "wow": "6170481674808202091",
    "sad": "6070901633984762639",
    "angry": "6073454206063219947",
    "think": "6239973378074086199",
    "settings": "6073582668535044255",
    "broadcast": "6064488066695826616",
    "contact": "6269255258212404947",
    "rose": "6071116790371455219",
    "blue_heart": "6071280192402232957",
    "chain": "6071278787947925866",
    "infinity": "5373315485309870642",
    "one": "6109152797406532734",
    "two": "6109321250318849544",
    "three": "6109218153923876294",
    "four": "5363839335755953463",
    "diamond": "6064293500382350516",
    "vip": "6172745002314118594",
    "lock": "6176966310920983412",
    "bag": "6158907064362998049",
    "tag": "6260059243605398502",
}

def build_premium_message(segments):
    text = ""
    entities = []
    for seg in segments:
        if isinstance(seg, str):
            text += seg
        elif isinstance(seg, tuple):
            key, fallback = seg
            eid = PE.get(key)
            if eid:
                offset = len(text.encode("utf-16-le")) // 2
                char = fallback
                text += char
                length = len(char.encode("utf-16-le")) // 2
                entities.append(MessageEntity(
                    type="custom_emoji",
                    offset=offset,
                    length=length,
                    custom_emoji_id=eid
                ))
            else:
                text += fallback
    return text, entities

def send_premium(chat_id, segments, reply_markup=None, parse_mode=None, reply_to_message_id=None, disable_web_page_preview=True):
    text, entities = build_premium_message(segments)
    kwargs = dict(chat_id=chat_id, text=text, entities=entities, disable_web_page_preview=disable_web_page_preview)
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    if reply_to_message_id:
        kwargs["reply_to_message_id"] = reply_to_message_id
    try:
        return bot.send_message(**kwargs)
    except Exception as e:
        print(f"Error sending premium message: {e}")
        fallback_text = ""
        for seg in segments:
            if isinstance(seg, str):
                fallback_text += seg
            elif isinstance(seg, tuple):
                fallback_text += seg[1]
        return bot.send_message(chat_id, fallback_text, reply_markup=reply_markup)

def edit_premium(chat_id, message_id, segments, reply_markup=None, disable_web_page_preview=True):
    text, entities = build_premium_message(segments)
    kwargs = dict(chat_id=chat_id, message_id=message_id, text=text, entities=entities, disable_web_page_preview=disable_web_page_preview)
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    try:
        return bot.edit_message_text(**kwargs)
    except Exception as e:
        print(f"Error editing premium message: {e}")
        fallback_text = ""
        for seg in segments:
            if isinstance(seg, str):
                fallback_text += seg
            elif isinstance(seg, tuple):
                fallback_text += seg[1]
        return bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=fallback_text, reply_markup=reply_markup)

# ==================== BOT CONFIG ====================
BOT_TOKEN = "8802123213:AAGM-1EMo9gPxczfQ3JEAs1ZZztPbsKjI1w" # SET BOT TOKEN USE t.me/BOTFATHER
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

ADMIN_ID = 6261652391
CHANNEL_ID = -8802123213
BOT_USERNAME = "MHXLIKE_BOT"

# ==================== FFLIKEBD API CONFIG ====================
# Docs: https://fflikebd.site/docs/
# API Key: Developer Settings → Like API → Get API
LIKE_API_KEY = "JIBON-6PPPE9ZTY96YSA"   # <-- এখানে আপনার fflikebd API key বসান
LIKE_API_BASE = "https://www.fflikebd.site/ghostxlike"
DEFAULT_PKGORDER = "200lk"                # 220 LIKE INSTANT - ৳5
FF_INFO_API = "https://info-api-pink-seven.vercel.app/player-info"

# ==================== ZRPAYBD PAYMENT CONFIG (No Webhook) ====================
ZRPAYBD_API_KEY    = "br5LDVhBna8JuxSmORMEalQRpqUfemn2XrrBcvdh1uLGKladkz" #add auto payment key site : https://zrpaybd.xyz/
ZRPAYBD_SECRET_KEY = "br5LDVhBna8JuxSmORMEalQRpqUfemn2XrrBcvdh1uLGKladkz" #add auto payment key site : https://zrpaybd.xyz/
ZRPAYBD_BRAND_KEY  = "br5LDVhBna8JuxSmORMEalQRpqUfemn2XrrBcvdh1uLGKladkz" #add auto payment key site : https://zrpaybd.xyz/
ZRPAYBD_CREATE_URL = "https://pay.zrpaybd.xyz/api/payment/create"
ZRPAYBD_VERIFY_URL = "https://pay.zrpaybd.xyz/api/payment/verify"

# Deep link back to bot (no webhook needed)
BOT_DEEPLINK_BASE = f"https://t.me/{BOT_USERNAME}"

pending_auto_like = {}

# ==================== HELPER FUNCTIONS ====================
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, username, full_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = get_user(user_id)
    if not existing:
        cursor.execute("INSERT INTO users (user_id, username, full_name, balance, channel_joined, join_date) VALUES (?, ?, ?, 0, 0, ?)",
                      (user_id, username, full_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

def update_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ?, total_deposit = total_deposit + ? WHERE user_id = ?",
                  (amount, amount, user_id))
    conn.commit()

def refund_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def deduct_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = get_user(user_id)
    if user and user['balance'] >= amount:
        cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id = ?",
                      (amount, amount, user_id))
        conn.commit()
        return True
    return False

def add_order(user_id, uid, server_name, likes_amount, price, order_type, expiry_days=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    expiry = None
    if expiry_days:
        expiry = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
    cursor.execute("""INSERT INTO orders (user_id, uid, server_name, likes_amount, price, order_type, status, order_date, expiry_date)
                     VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, ?)""",
                  (user_id, uid, server_name, likes_amount, price, order_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), expiry))
    conn.commit()

def add_auto_like(user_id, uid, server_name, price, days):
    conn = get_db_connection()
    cursor = conn.cursor()
    start = datetime.now().strftime("%Y-%m-%d")
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("""INSERT INTO auto_likes (user_id, uid, server_name, price, days, start_date, expiry_date, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""",
                  (user_id, uid, server_name, price, days, start, expiry))
    conn.commit()

def add_auto_like_full(user_id, uid, server_name, account_name, price, days, expiry_date, package_id, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    start = get_bd_time().strftime("%Y-%m-%d")
    cursor.execute("""INSERT INTO auto_likes (user_id, uid, server_name, price, days, start_date, expiry_date, status, account_name, package_id, category, admin_status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, 'active')""",
                  (user_id, uid, server_name, price, days, start, expiry_date, account_name, package_id, category))
    conn.commit()
    return cursor.lastrowid

def get_user_auto_likes(user_id, active_only=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM auto_likes WHERE user_id=? AND status='active' AND (admin_status IS NULL OR admin_status='active') ORDER BY id DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM auto_likes WHERE user_id=? AND status='active' ORDER BY id DESC", (user_id,))
    return cursor.fetchall()

# ==================== FFLIKEBD API CALLS ====================
def call_like_api(uid, server_name, pkgorder=None):
    """
    fflikebd.site API — Daily Like (default package 220 LIKE INSTANT ৳6)
    Docs: https://fflikebd.site/docs/
    Response: status 1 = delivered, 2 = already received today, 0 = error
    """
    try:
        params = {
            "region": (server_name or "BD").upper(),
            "uid": uid,
            "userkey": LIKE_API_KEY
        }
        if pkgorder:
            params["pkgorder"] = pkgorder

        print(f"📤 fflikebd API Request: UID={uid}, Region={params['region']}, Pkg={pkgorder or DEFAULT_PKGORDER}")
        response = requests.get(LIKE_API_BASE, params=params, timeout=120)
        print(f"📥 HTTP Status: {response.status_code}")

        try:
            result = response.json()
        except Exception:
            result = {
                "status": 0,
                "error": "invalid_response",
                "message": f"HTTP {response.status_code}: {response.text[:200]}"
            }

        print(f"📥 fflikebd API Response: {result}")

        # HTTP-level error handling
        if response.status_code == 400:
            result.setdefault("status", 0)
        elif response.status_code == 401:
            result.setdefault("status", 0)
            result.setdefault("error", "invalid_key")
            result.setdefault("message", "Invalid API key. Check LIKE_API_KEY.")
        elif response.status_code == 402:
            result.setdefault("status", 0)
            result.setdefault("error", "insufficient_balance")
            result.setdefault("message", "fflikebd API wallet balance insufficient.")
        elif response.status_code == 403:
            result.setdefault("status", 0)
            result.setdefault("error", "no_permission")
            result.setdefault("message", "API access not enabled on fflikebd account.")
        elif response.status_code == 409:
            result.setdefault("status", 0)
            result.setdefault("error", "order_in_progress")
            result.setdefault("message", "Previous order still processing. Try again.")
        elif response.status_code == 429:
            result.setdefault("status", 0)
            result.setdefault("error", "rate_limited")
            result.setdefault("message", "Rate limit exceeded (60/min). Wait a minute.")
        elif response.status_code == 502:
            result.setdefault("status", 0)
            result.setdefault("error", "delivery_failed")
            result.setdefault("message", "Delivery failed and amount refunded.")

        return result

    except requests.exceptions.Timeout:
        print(f"❌ fflikebd API Timeout for UID={uid}")
        return {"status": 0, "error": "timeout", "message": "API request timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        print(f"❌ fflikebd Request error: {e}")
        return {"status": 0, "error": "network_error", "message": str(e)}
    except Exception as e:
        print(f"❌ fflikebd Unexpected error: {e}")
        return {"status": 0, "error": "unknown", "message": str(e)}


def call_pro_like_api(uid, server_name):
    """
    Daily Like PRO+ — same fflikebd API
    Note: same UID can only receive likes once per day; second attempt returns status=2 (no charge)
    """
    return call_like_api(uid, server_name, DEFAULT_PKGORDER)

# Kept for backwards compatibility (auto-like scheduler uses this for VIP category)
def call_dual_like_api(uid, server_name):
    return call_like_api(uid, server_name, DEFAULT_PKGORDER)


def fetch_ff_nickname(uid):
    try:
        resp = requests.get(f"{FF_INFO_API}?uid={uid}", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("basicInfo", {}).get("nickname", "Unknown")
    except Exception as e:
        print(f"FF Info fetch error: {e}")
    return "Unknown"

def get_setting(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    result = cursor.fetchone()
    return result[0] if result else None

def set_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()

def is_enabled(key):
    return get_setting(key) == 'on'

def is_maintenance():
    return get_setting('maintenance_mode') == 'on'

# ==================== DAILY LIKE PRO+ LIMIT SYSTEM ====================
def get_pro_cycle_date():
    now_bd = get_bd_time()
    if now_bd.hour < 4:
        cycle_date = (now_bd - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        cycle_date = now_bd.strftime("%Y-%m-%d")
    return cycle_date

def reset_pro_like_if_needed():
    cycle = get_pro_cycle_date()
    last = get_setting('pro_like_last_reset_date')
    if last != cycle:
        set_setting('pro_like_used_count', '0')
        set_setting('pro_like_last_reset_date', cycle)

def get_pro_like_remaining():
    reset_pro_like_if_needed()
    try:
        limit = int(get_setting('pro_like_daily_limit') or 30)
    except:
        limit = 30
    try:
        used = int(get_setting('pro_like_used_count') or 0)
    except:
        used = 0
    return max(0, limit - used), limit

def increment_pro_like_usage():
    reset_pro_like_if_needed()
    try:
        used = int(get_setting('pro_like_used_count') or 0)
    except:
        used = 0
    set_setting('pro_like_used_count', str(used + 1))

# ==================== AUTO LIKE PACKAGE HELPERS ====================
def get_package(package_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auto_like_packages WHERE package_id=?", (package_id,))
    return cursor.fetchone()

def get_enabled_packages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auto_like_packages WHERE enabled=1 ORDER BY category, days")
    return cursor.fetchall()

def get_all_packages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auto_like_packages ORDER BY category, days")
    return cursor.fetchall()

def set_package_field(package_id, field, value):
    if field not in ("price", "days", "enabled", "likes_amount"):
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE auto_like_packages SET {field}=? WHERE package_id=?", (value, package_id))
    conn.commit()

# ==================== CHANNEL CHECK FUNCTIONS ====================
def get_channels():
    channels = []
    ch1 = get_setting('channel_1')
    ch2 = get_setting('channel_2')
    if ch1:
        channels.append(ch1)
    if ch2:
        channels.append(ch2)
    return channels

def check_channel_membership(user_id, channel_url):
    try:
        channel_username = channel_url.replace('https://t.me/', '').replace('@', '')
        if '/' in channel_username:
            channel_username = channel_username.split('/')[0]
        chat_member = bot.get_chat_member(f"@{channel_username}", user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Channel check error for {channel_url}: {e}")
        return False

def check_all_channels(user_id):
    if not is_enabled('channel_check_enabled'):
        return True
    channels = get_channels()
    if not channels:
        return True
    for channel in channels:
        if not check_channel_membership(user_id, channel):
            return False
    return True

def record_channel_join(user_id, channel_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO channel_joins (user_id, channel_url, joined_date) VALUES (?, ?, ?)",
                  (user_id, channel_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def update_user_channel_status(user_id):
    all_joined = check_all_channels(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET channel_joined = ? WHERE user_id = ?", (1 if all_joined else 0, user_id))
    if all_joined:
        cursor.execute("UPDATE referrals SET channel_joined = 1 WHERE referred_id = ?", (user_id,))
    conn.commit()
    return all_joined

def get_channel_check_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    channels = get_channels()
    for channel in channels:
        markup.add(InlineKeyboardButton(f"📢 JOIN CHANNEL", url=channel))
    markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_channels"))
    return markup

# ==================== REFER & EARN HELPERS ====================
def get_referral(referred_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM referrals WHERE referred_id=?", (referred_id,))
    return cursor.fetchone()

def get_referrals_count(referrer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (referrer_id,))
    return cursor.fetchone()[0]

def handle_referral_start(user_id, reference):
    try:
        referrer_id = int(reference.replace("ref_", ""))
    except ValueError:
        return
    if referrer_id == user_id:
        return
    referrer = get_user(referrer_id)
    if not referrer:
        return
    existing = get_referral(user_id)
    if existing:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET referred_by=? WHERE user_id=?", (referrer_id, user_id))
    cursor.execute("""INSERT OR IGNORE INTO referrals (referrer_id, referred_id, channel_joined, signup_bonus_paid, created_date)
                     VALUES (?, ?, 0, 0, ?)""",
                  (referrer_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    post_referral_to_group(user_id, referrer_id)
    try:
        send_premium(referrer_id, [
            ("gift", "🎁"), " NEW REFERRAL!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("user", "👤"), " নতুন ইউজার আপনার রেফার লিংক ব্যবহার করেছে!\n",
            ("clock", "⏳"), " ইউজার চ্যানেলে জয়েন করার পর বোনাস পাবেন!\n",
            "━━━━━━━━━━━━━━━━━━━"
        ])
    except:
        pass

def post_referral_to_group(referred_id, referrer_id):
    if not is_enabled('refer_post_enabled'):
        return
    group_id = get_setting('refer_post_group')
    if not group_id:
        return
    try:
        group_id = int(group_id)
    except:
        return
    referrer = get_user(referrer_id)
    referred = get_user(referred_id)
    if not referrer or not referred:
        return
    referrals_count = get_referrals_count(referrer_id)
    referrer_balance = referrer['balance']
    referrer_username = f"@{referrer['username']}" if referrer['username'] != 'No Username' else f"ID: {referrer_id}"
    referred_username = f"@{referred['username']}" if referred['username'] != 'No Username' else f"ID: {referred_id}"
    bangladesh_time = datetime.now().astimezone(timezone(timedelta(hours=6))).strftime("%Y-%m-%d %I:%M:%S %p")
    post_segments = [
        ("gift", "🎁"), " NEW REFERRAL!\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("user", "👤"), f" Referrer: {referrer_username}\n",
        ("shield", "🆔"), f" Referrer ID: {referrer_id}\n",
        ("link", "🔗"), f" Referred: {referred_username}\n",
        ("shield", "🆔"), f" Referred ID: {referred_id}\n",
        ("crown", "👑"), f" Total Referrals: {referrals_count}\n",
        ("coins", "💰"), f" Referrer Balance: ৳{referrer_balance}\n",
        ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]
    try:
        send_premium(group_id, post_segments)
    except Exception as e:
        print(f"Error posting referral to group: {e}")

def post_deposit_to_group(user_id, amount):
    if not is_enabled('deposit_post_enabled'):
        return
    group_id = get_setting('refer_post_group')
    if not group_id:
        return
    try:
        group_id = int(group_id)
    except:
        return
    user = get_user(user_id)
    if not user:
        return
    username = f"@{user['username']}" if user['username'] != 'No Username' else f"ID: {user_id}"
    bangladesh_time = datetime.now().astimezone(timezone(timedelta(hours=6))).strftime("%Y-%m-%d %I:%M:%S %p")
    post_segments = [
        ("money", "💰"), " NEW DEPOSIT!\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("user", "👤"), f" User: {username}\n",
        ("shield", "🆔"), f" User ID: {user_id}\n",
        ("coins", "💵"), f" Amount: ৳{amount}\n",
        ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]
    try:
        send_premium(group_id, post_segments)
    except Exception as e:
        print(f"Error posting deposit to group: {e}")

def credit_signup_bonus_if_eligible(user_id):
    if not is_enabled('refer_enabled'):
        return False
    ref = get_referral(user_id)
    if not ref:
        return False
    if ref['channel_joined'] == 0:
        return False
    if ref['signup_bonus_paid'] == 1:
        return False
    bonus = float(get_setting('refer_signup_bonus'))
    referrer_id = ref['referrer_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE referrals SET signup_bonus_paid=1, total_commission = total_commission + ? WHERE referred_id=?",
                  (bonus, user_id))
    cursor.execute("UPDATE users SET balance = balance + ?, referral_earnings = referral_earnings + ? WHERE user_id=?",
                  (bonus, bonus, referrer_id))
    conn.commit()
    referred_user = get_user(user_id)
    referrer_user = get_user(referrer_id)
    uname = f"@{referred_user['username']}" if referred_user and referred_user['username'] != "No Username" else f"ID: {user_id}"
    referrer_uname = f"@{referrer_user['username']}" if referrer_user and referrer_user['username'] != "No Username" else f"ID: {referrer_id}"
    bangladesh_time = datetime.now().astimezone(timezone(timedelta(hours=6))).strftime("%Y-%m-%d %I:%M:%S %p")
    try:
        send_premium(referrer_id, [
            ("checkmark", "✅"), " REFERRAL BONUS ADDED!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("user", "👤"), f" {uname} চ্যানেলে জয়েন করেছে!\n",
            ("shield", "🆔"), f" Referred ID: {user_id}\n",
            ("coins", "💰"), f" আপনি পেয়েছেন: ৳{bonus}\n",
            ("money", "💵"), f" নতুন ব্যালেন্স: ৳{referrer_user['balance']}\n",
            ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
            "━━━━━━━━━━━━━━━━━━━"
        ])
    except Exception as e:
        print(f"Error sending bonus notification: {e}")
    try:
        send_premium(get_setting('refer_post_group'), [
            ("gift", "🎁"), " REFERRAL BONUS GIVEN!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("user", "👤"), f" Referrer: {referrer_uname}\n",
            ("shield", "🆔"), f" Referrer ID: {referrer_id}\n",
            ("user", "👤"), f" Referred: {uname}\n",
            ("shield", "🆔"), f" Referred ID: {user_id}\n",
            ("coins", "💰"), f" Bonus: ৳{bonus}\n",
            ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
            "━━━━━━━━━━━━━━━━━━━"
        ])
    except:
        pass
    return True

def process_referral_commission(user_id, deposit_amount):
    if not is_enabled('refer_enabled'):
        return
    ref = get_referral(user_id)
    if not ref:
        return
    percent = float(get_setting('refer_deposit_percent'))
    commission = round(deposit_amount * percent / 100, 2)
    if commission <= 0:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE referrals SET total_commission = total_commission + ? WHERE referred_id=?",
                  (commission, user_id))
    cursor.execute("UPDATE users SET balance = balance + ?, referral_earnings = referral_earnings + ? WHERE user_id=?",
                  (commission, commission, ref['referrer_id']))
    conn.commit()
    referred_user = get_user(user_id)
    uname = f"@{referred_user['username']}" if referred_user and referred_user['username'] != "No Username" else f"ID: {user_id}"
    bangladesh_time = datetime.now().astimezone(timezone(timedelta(hours=6))).strftime("%Y-%m-%d %I:%M:%S %p")
    try:
        send_premium(ref['referrer_id'], [
            ("coins", "💰"), " REFERRAL COMMISSION ADDED!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("user", "👤"), f" {uname} ৳{deposit_amount} ডিপোজিট করেছে\n",
            ("shield", "🆔"), f" Referred ID: {user_id}\n",
            ("gift", "🎁"), f" আপনার কমিশন: ৳{commission}\n",
            ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
            "━━━━━━━━━━━━━━━━━━━"
        ])
    except:
        pass

# ==================== ZRPAYBD PAYMENT FUNCTIONS (No Webhook) ====================
def create_payment_key(amount, user_id):
    """Creates a ZRPAYBD Pay payment link with a Telegram deep-link return URL."""
    try:
        amount_str = str(int(amount)) if float(amount).is_integer() else str(amount)
        order_ref = f"ORD{int(time.time())}{user_id}"
        success_url = f"{BOT_DEEPLINK_BASE}?start=payok_{order_ref}"
        cancel_url  = f"{BOT_DEEPLINK_BASE}?start=paycancel_{order_ref}"

        print(f"📤 ZRPAYBD Payment: Amount=৳{amount}, User={user_id}, Ref={order_ref}")
        print(f"🔗 Success URL: {success_url}")

        payload = {
            "cus_name":    f"User {user_id}",
            "cus_email":   f"user{user_id}@gmail.com",
            "amount":      amount_str,
            "success_url": success_url,
            "cancel_url":  cancel_url,
            "metadata": {
                "user_id":   str(user_id),
                "amount":    amount_str,
                "order_ref": order_ref
            }
        }

        headers = {
            "Content-Type": "application/json",
            "API-KEY":      ZRPAYBD_API_KEY,
            "SECRET-KEY":   ZRPAYBD_SECRET_KEY,
            "BRAND-KEY":    ZRPAYBD_BRAND_KEY
        }

        response = requests.post(ZRPAYBD_CREATE_URL, json=payload, headers=headers, timeout=20)
        result = response.json()

        print(f"📥 ZRPAYBD Response: {result}")

        if result and result.get("status") == 1 and result.get("payment_url"):
            payment_url = result["payment_url"]

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO pending_payments
                            (user_id, amount, payment_key, payment_url, status, created_date)
                            VALUES (?, ?, ?, ?, 'pending', ?)""",
                          (user_id, amount, order_ref, payment_url,
                           datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            cursor.execute("""INSERT INTO deposit_history
                            (user_id, amount, payment_key, status, date)
                            VALUES (?, ?, ?, 'pending', ?)""",
                          (user_id, amount, order_ref,
                           datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

            return {
                "responseCode": 200,
                "payment_url": payment_url,
                "paymentkey": order_ref
            }
        else:
            print(f"❌ ZRPAYBD Failed: {result}")
            return None

    except Exception as e:
        print(f"ZRPAYBD Payment error: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==================== KEYBOARDS ====================
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("BUY DAILY LIKE", style="primary", icon_custom_emoji_id="5350679208068667881"),
        KeyboardButton("DAILY LIKE PRO+", style="success", icon_custom_emoji_id="5321160408944360420"),
        KeyboardButton("AUTO LIKE", style="primary", icon_custom_emoji_id="5846024087033353251"),
        KeyboardButton("ADD MONEY", style="success", icon_custom_emoji_id="6039641775377748623"),
        KeyboardButton("MY INFO", style="primary", icon_custom_emoji_id="5199755801043953588"),
        KeyboardButton("MY HISTORY", style="primary", icon_custom_emoji_id="5893102202817352158"),
        KeyboardButton("REFER & EARN", style="success", icon_custom_emoji_id="5902335789798265487"),
        KeyboardButton("HOW TO USE", style="success", icon_custom_emoji_id="5893149782465057649"),
        KeyboardButton("SUPPORT", style="primary", icon_custom_emoji_id="5893149782465057649")
    )
    return keyboard

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("BUY DAILY LIKE", style="primary", icon_custom_emoji_id="5350679208068667881"),
        KeyboardButton("DAILY LIKE PRO+", style="success", icon_custom_emoji_id="5321160408944360420"),
        KeyboardButton("AUTO LIKE", style="primary", icon_custom_emoji_id="5846024087033353251"),
        KeyboardButton("ADD MONEY", style="success", icon_custom_emoji_id="6039641775377748623"),
        KeyboardButton("MY INFO", style="primary", icon_custom_emoji_id="5199755801043953588"),
        KeyboardButton("MY HISTORY", style="primary", icon_custom_emoji_id="5893102202817352158"),
        KeyboardButton("REFER & EARN", style="success", icon_custom_emoji_id="5902335789798265487"),
        KeyboardButton("HOW TO USE", style="success", icon_custom_emoji_id="5893149782465057649"),
        KeyboardButton("SUPPORT", style="primary", icon_custom_emoji_id="5893149782465057649"),
        KeyboardButton("ADMIN PANEL", style="danger", icon_custom_emoji_id="6057576227365986633")
    )
    return keyboard

def get_back_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))
    return markup

# ==================== START HANDLER (with Payment Return) ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    full_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")

    add_user(user_id, username, full_name)

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    args = message.text.split()

    # ==================== PAYMENT RETURN HANDLING ====================
    if len(args) > 1:
        reference = args[1]
        print(f"📥 /start with ref: {reference}")

        if reference.startswith('paycancel_'):
            bot.send_message(user_id,
                "❌ Payment Cancelled\n\n"
                "No charges were made.\n"
                "Use ADD MONEY to try again.",
                reply_markup=get_main_keyboard())
            return

        if reference.startswith('payok_'):
            order_ref = reference.replace('payok_', '')
            waiting = bot.send_message(user_id, "⏳ Verifying your payment, please wait...")

            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""SELECT * FROM pending_payments
                                 WHERE payment_key=? AND status='pending'
                                 ORDER BY id DESC LIMIT 1""", (order_ref,))
                payment = cursor.fetchone()

                if not payment:
                    bot.delete_message(user_id, waiting.message_id)
                    bot.send_message(user_id,
                        "❌ Payment record not found.\n\n"
                        "If you completed payment, please contact SUPPORT with your transaction ID.",
                        reply_markup=get_main_keyboard())
                    return

                payment_user_id = payment['user_id']
                payment_amount  = payment['amount']

                update_balance(payment_user_id, payment_amount)

                txn_id = f"ZRPAYBD{int(time.time())}"
                cursor.execute("UPDATE pending_payments SET status='completed' WHERE id=?", (payment['id'],))
                cursor.execute("""UPDATE deposit_history
                                 SET status='completed', transaction_id=?
                                 WHERE payment_key=?""", (txn_id, order_ref))
                conn.commit()

                user = get_user(payment_user_id)
                bangladesh_time = datetime.now().astimezone(
                    timezone(timedelta(hours=6))
                ).strftime("%Y-%m-%d %I:%M:%S %p")

                try:
                    post_deposit_to_group(payment_user_id, payment_amount)
                except:
                    pass

                bot.delete_message(user_id, waiting.message_id)
                send_premium(user_id, [
                    ("checkmark", "✅"), " PAYMENT SUCCESSFUL!\n",
                    "━━━━━━━━━━━━━━━━━━━\n",
                    ("money", "💰"), f" Amount: ৳{payment_amount}\n",
                    ("coins", "💵"), f" New Balance: ৳{user['balance']}\n",
                    ("key", "🔑"), f" Order: {order_ref}\n",
                    ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
                    "━━━━━━━━━━━━━━━━━━━\n",
                    "✅ আপনার অ্যাকাউন্টে টাকা যোগ করা হয়েছে!\n",
                    "🔥 এখন যেকোনো লাইক প্যাকেজ কিনতে পারেন।"
                ], reply_markup=get_main_keyboard())

                try:
                    send_premium(ADMIN_ID, [
                        ("alert", "🔔"), " NEW PAYMENT!\n",
                        "━━━━━━━━━━━━━━━━━━━\n",
                        ("user", "👤"), f" User: {payment_user_id}\n",
                        ("money", "💰"), f" Amount: ৳{payment_amount}\n",
                        ("key", "🔑"), f" Order: {order_ref}\n",
                        ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
                        "━━━━━━━━━━━━━━━━━━━"
                    ])
                except:
                    pass

                try:
                    process_referral_commission(payment_user_id, payment_amount)
                except Exception as e:
                    print(f"Referral error: {e}")

                print(f"✅ Payment completed: User={payment_user_id}, Amount=৳{payment_amount}")
                return

            except Exception as e:
                print(f"❌ Payment verify error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    bot.delete_message(user_id, waiting.message_id)
                except:
                    pass
                bot.send_message(user_id,
                    "❌ Verification error. Please contact SUPPORT.",
                    reply_markup=get_main_keyboard())
                return

        if reference.startswith('ref_'):
            handle_referral_start(user_id, reference)

    # ==================== CHANNEL CHECK ====================
    if is_enabled('channel_check_enabled') and user_id != ADMIN_ID:
        if not check_all_channels(user_id):
            markup = get_channel_check_keyboard()
            send_premium(user_id, [
                ("warn", "⚠️"), " CHANNEL JOIN REQUIRED!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                "আমাদের চ্যানেলগুলোতে জয়েন করুন:\n",
                "➖ @MHXLIKE_11\n",
                "➖ @mhxlike_history\n\n",
                "জয়েন করার পর VERIFY বাটনে ক্লিক করুন।\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=markup)
            return

    # ==================== WELCOME ====================
    video_id = get_setting('welcome_video_id')
    user = get_user(user_id)
    balance = user['balance'] if user else 0

    if video_id:
        try:
            try:
                bot.send_video(user_id, video_id, caption="🎥 WELCOME TO FIRE LIKE BOT", reply_markup=None)
            except:
                pass

            if user_id == ADMIN_ID:
                send_premium(user_id, [
                    ("crown", "👑"), " WELCOME ADMIN!\n",
                    "━━━━━━━━━━━━━━━━━━━\n\n",
                    ("user", "👤"), f" Name: {full_name}\n",
                    ("tag", "📝"), f" Username: @{username}\n",
                    ("shield", "🆔"), f" User ID: {user_id}\n",
                    ("coins", "💰"), f" Balance: ৳{balance}\n\n",
                    ("fire", "🔥"), " FREE FIRE LIKE BOT v3.0\n",
                    "═════════════════════\n",
                    ("star", "🌟"), " 220+ Likes Daily\n",
                    ("gem", "💎"), " Auto Like Service\n",
                    ("lightning", "⚡"), " Instant Delivery\n",
                    ("shield2", "🛡️"), " 100% Trusted\n\n",
                    "━━━━━━━━━━━━━━━━━━━"
                ], reply_markup=get_admin_keyboard())
            else:
                send_premium(user_id, [
                    ("fire", "🔥"), " WELCOME TO FIRE LIKE BOT!\n",
                    "━━━━━━━━━━━━━━━━━━━\n\n",
                    ("user", "👤"), f" Name: {full_name}\n",
                    ("tag", "📝"), f" Username: @{username}\n",
                    ("shield", "🆔"), f" User ID: {user_id}\n",
                    ("coins", "💰"), f" Balance: ৳{balance}\n\n",
                    ("star", "🌟"), " স্বাগতম! বট ব্যবহার করার জন্য ধন্যবাদ!\n\n",
                    ("robot", "🤖"), " FREE FIRE DAILY LIKE BOT\n",
                    "═════════════════════\n",
                    ("fire", "🔥"), " Get 220+ Likes Daily\n",
                    ("gem", "💎"), " Auto Like Service\n",
                    ("lightning", "⚡"), " Instant Delivery\n",
                    ("shield2", "🛡️"), " 100% Trusted\n\n",
                    "━━━━━━━━━━━━━━━━━━━"
                ], reply_markup=get_main_keyboard())
            return
        except Exception as e:
            print(f"Video error: {e}")

    try:
        if user_id == ADMIN_ID:
            send_premium(user_id, [
                ("crown", "👑"), " WELCOME ADMIN!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                ("user", "👤"), f" Name: {full_name}\n",
                ("tag", "📝"), f" Username: @{username}\n",
                ("shield", "🆔"), f" User ID: {user_id}\n",
                ("coins", "💰"), f" Balance: ৳{balance}\n\n",
                ("fire", "🔥"), " FREE FIRE LIKE BOT v3.0\n",
                "═════════════════════\n",
                ("star", "🌟"), " 220+ Likes Daily\n",
                ("gem", "💎"), " Auto Like Service\n",
                ("lightning", "⚡"), " Instant Delivery\n",
                ("shield2", "🛡️"), " 100% Trusted\n\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=get_admin_keyboard())
        else:
            send_premium(user_id, [
                ("fire", "🔥"), " WELCOME TO FIRE LIKE BOT!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                ("user", "👤"), f" Name: {full_name}\n",
                ("tag", "📝"), f" Username: @{username}\n",
                ("shield", "🆔"), f" User ID: {user_id}\n",
                ("coins", "💰"), f" Balance: ৳{balance}\n\n",
                ("star", "🌟"), " স্বাগতম! বট ব্যবহার করার জন্য ধন্যবাদ!\n\n",
                ("robot", "🤖"), " FREE FIRE DAILY LIKE BOT\n",
                "═════════════════════\n",
                ("fire", "🔥"), " Get 220+ Likes Daily\n",
                ("gem", "💎"), " Auto Like Service\n",
                ("lightning", "⚡"), " Instant Delivery\n",
                ("shield2", "🛡️"), " 100% Trusted\n\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error in start command: {e}")
        bot.send_message(user_id, "Welcome! Please use /start", reply_markup=get_main_keyboard())

# ==================== VERIFY CHANNELS ====================
@bot.callback_query_handler(func=lambda call: call.data == "verify_channels")
def verify_channels(call):
    user_id = call.from_user.id

    if is_maintenance() and user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "🛠 Bot is under maintenance!", show_alert=True)
        return

    if check_all_channels(user_id):
        update_user_channel_status(user_id)
        bonus_given = credit_signup_bonus_if_eligible(user_id)
        bot.answer_callback_query(call.id, "✅ Verified! You have joined all channels.", show_alert=False)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        username = call.from_user.username or "No Username"
        full_name = call.from_user.first_name + (" " + call.from_user.last_name if call.from_user.last_name else "")
        user = get_user(user_id)
        balance = user['balance'] if user else 0

        welcome_msg = [
            ("fire", "🔥"), " WELCOME TO FIRE LIKE BOT!\n",
            "━━━━━━━━━━━━━━━━━━━\n\n",
            ("user", "👤"), f" Name: {full_name}\n",
            ("tag", "📝"), f" Username: @{username}\n",
            ("shield", "🆔"), f" User ID: {user_id}\n",
            ("coins", "💰"), f" Balance: ৳{balance}\n\n",
            ("checkmark", "✅"), " ধন্যবাদ! চ্যানেলগুলোতে জয়েন করার জন্য!\n\n",
        ]
        if bonus_given:
            welcome_msg.append(("gift", "🎁"))
            welcome_msg.append(" রেফার বোনাস পেয়েছেন! চেক করুন আপনার ব্যালেন্স!\n\n")
        welcome_msg.extend([
            ("robot", "🤖"), " FREE FIRE DAILY LIKE BOT\n",
            "═════════════════════\n",
            ("fire", "🔥"), " Get 220+ Likes Daily\n",
            ("gem", "💎"), " Auto Like Service\n",
            ("lightning", "⚡"), " Instant Delivery\n",
            ("shield2", "🛡️"), " 100% Trusted\n\n",
            "━━━━━━━━━━━━━━━━━━━"
        ])
        send_premium(user_id, welcome_msg, reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined all channels yet! Please join and try again.", show_alert=True)

# ==================== BUY DAILY LIKE ====================
@bot.message_handler(func=lambda message: message.text == "BUY DAILY LIKE")
def buy_daily_like(message):
    user_id = message.from_user.id

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    if is_enabled('channel_check_enabled') and user_id != ADMIN_ID:
        if not check_all_channels(user_id):
            markup = get_channel_check_keyboard()
            send_premium(user_id, [
                ("warn", "⚠️"), " CHANNEL JOIN REQUIRED!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                "আমাদের চ্যানেলগুলোতে জয়েন করুন:\n",
                "➖ @MHXLIKE_11\n",
                "➖ @mhxlike_history\n\n",
                "জয়েন করার পর VERIFY বাটনে ক্লিক করুন।\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=markup)
            return

    if not is_enabled('daily_like_enabled') and user_id != ADMIN_ID:
        msg = get_setting('daily_like_off_msg')
        bot.send_message(user_id, msg)
        return

    user = get_user(user_id)
    if not user:
        bot.send_message(user_id, "Please use /start first")
        return

    daily_price = float(get_setting('daily_like_price'))
    daily_amount = int(get_setting('daily_like_amount'))
    balance = user['balance']

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("CONTINUE", callback_data="daily_like_continue", style="success", icon_custom_emoji_id="5893224751119208859"),
        InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    send_premium(user_id, [
        ("fire", "🔥"), " BUY DAILY LIKE\n",
        "━━━━━━━━━━━━━━━━━━━\n\n",
        ("coins", "💰"), f" Your Balance: ৳{balance}\n",
        ("gem", "💎"), f" Price: ৳{daily_price}\n",
        ("chart", "📈"), f" Likes You Get: {daily_amount}+\n\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("warn", "⚠️"), f" {daily_price} Taka for {daily_amount}+ Likes"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "daily_like_continue")
def daily_like_continue(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    daily_price = float(get_setting('daily_like_price'))

    if user['balance'] < daily_price:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("ADD MONEY", callback_data="add_money", style="success", icon_custom_emoji_id="5902453596456227896"))
        markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))
        edit_premium(call.message.chat.id, call.message.message_id, [
            ("cross", "❌"), " INSUFFICIENT BALANCE!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("coins", "💰"), f" Balance: ৳{user['balance']}\n",
            ("gem", "💎"), f" Required: ৳{daily_price}\n\n",
            "Please add money first!"
        ], reply_markup=markup)
        return

    msg = bot.edit_message_text("📝 Enter your Game UID:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_daily_uid)

def process_daily_uid(message):
    user_id = message.from_user.id
    uid = message.text.strip()
    msg = bot.send_message(user_id, "🌍 Enter Server Name:\n(BD, IND, SG, ID, TH, PK, MEB, BR, SAC, NA, EU, VN, TW, RU)", reply_markup=get_back_button())
    bot.register_next_step_handler(msg, process_daily_server, uid)

def process_daily_server(message, uid):
    user_id = message.from_user.id
    server = message.text.strip().lower()

    daily_price = float(get_setting('daily_like_price'))
    daily_amount = int(get_setting('daily_like_amount'))

    result = call_like_api(uid, server, DEFAULT_PKGORDER)

    if result.get("error") in ["timeout", "network_error", "unknown", "invalid_response"]:
        bot.send_message(user_id, f"❌ API Error: {result.get('message', 'Please try again.')}", reply_markup=get_back_button())
        return

    if result.get("status") == 1:
        if deduct_balance(user_id, daily_price):
            given = result.get('LikesGivenByAPI', 0)
            add_order(user_id, uid, server, given, daily_price, "daily")
            send_premium(user_id, [
                ("checkmark", "✅"), " LIKES ADDED SUCCESSFULLY!\n",
                "━━━━━━━━━━━━━━━━━━━\n",
                ("gamepad", "🎮"), f" UID: {result.get('UID', uid)}\n",
                ("user", "👤"), f" Player: {result.get('PlayerNickname', 'N/A')}\n",
                ("globe", "🌍"), f" Server: {result.get('Region', server.upper())}\n",
                ("chart", "📈"), f" Before: {result.get('LikesBeforeCommand', 'N/A')}\n",
                ("star", "📈"), f" Given: {given}\n",
                ("chart", "📈"), f" After: {result.get('LikesAfterCommand', 'N/A')}\n",
                ("gift", "📦"), f" Package: {result.get('Package', '220 LIKE INSTANT')}\n",
                ("key", "🔑"), f" Order No: {result.get('OrderNo', 'N/A')}\n",
                ("coins", "💰"), f" Price: ৳{daily_price}\n",
                "━━━━━━━━━━━━━━━━━━━"
            ])
        else:
            bot.send_message(user_id, "❌ Balance deduction failed!", reply_markup=get_back_button())
        return

    elif result.get("status") == 2:
        send_premium(user_id, [
            ("warn", "⚠️"), " ALREADY LIKED TODAY!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("gamepad", "🎮"), f" UID: {result.get('UID', uid)}\n",
            ("user", "👤"), f" Player: {result.get('PlayerNickname', 'N/A')}\n",
            ("globe", "🌍"), f" Server: {result.get('Region', server.upper())}\n\n",
            ("info", "ℹ️"), f" {result.get('message', 'This UID has already received its likes today.')}\n",
            ("coins", "💰"), f" Charged: ৳{result.get('Charged', 0)}\n",
            ("refresh", "🔄"), f" Refunded: ৳{result.get('Refunded', daily_price)}\n\n",
            ("star", "🌟"), " No charge was made.\n",
            "━━━━━━━━━━━━━━━━━━━"
        ], reply_markup=get_back_button())
        return

    else:
        error_code = result.get('error', 'unknown')
        error_msg = result.get('message', 'Unknown error')
        reason = result.get('reason', '')

        if error_code == "insufficient_balance":
            extra = f"\n💰 API Wallet Balance: ৳{result.get('balance', 'N/A')}\n🔧 Required: ৳{result.get('required', 'N/A')}"
        elif error_code == "delivery_failed":
            extra = f"\n🔄 Refunded: ৳{result.get('Refunded', 'N/A')}\n💰 API Balance: ৳{result.get('Balance', 'N/A')}"
        elif error_code == "invalid_key":
            extra = "\n⚠️ Admin: fflikebd API key invalid or revoked!"
        elif error_code == "no_permission":
            extra = "\n⚠️ Admin: API access not enabled on fflikebd account!"
        elif error_code == "rate_limited":
            extra = "\n⏱ Please wait 1 minute before retrying."
        else:
            extra = f"\n📋 Reason: {reason}" if reason else ""

        send_premium(user_id, [
            ("cross", "❌"), " LIKE SENDING FAILED!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("warn", "⚠️"), f" {error_msg}{extra}\n\n",
            ("coins", "💰"), " No charge was made.\n",
            ("refresh", "🔄"), " Please try again later.\n",
            "━━━━━━━━━━━━━━━━━━━"
        ], reply_markup=get_back_button())
        return

# ==================== BUY DAILY LIKE PRO+ ====================
@bot.message_handler(func=lambda message: message.text == "DAILY LIKE PRO+")
def buy_daily_like_pro(message):
    user_id = message.from_user.id

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    if is_enabled('channel_check_enabled') and user_id != ADMIN_ID:
        if not check_all_channels(user_id):
            markup = get_channel_check_keyboard()
            send_premium(user_id, [
                ("warn", "⚠️"), " CHANNEL JOIN REQUIRED!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                "আমাদের চ্যানেলগুলোতে জয়েন করুন:\n",
                "➖ @MHXLIKE_11\n",
                "➖ @mhxlike_history\n\n",
                "জয়েন করার পর VERIFY বাটনে ক্লিক করুন।\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=markup)
            return

    if not is_enabled('pro_like_enabled') and user_id != ADMIN_ID:
        msg = get_setting('pro_like_off_msg')
        bot.send_message(user_id, msg)
        return

    remaining, limit = get_pro_like_remaining()
    if remaining <= 0 and user_id != ADMIN_ID:
        send_premium(user_id, [
            ("warn", "⚠️"), " Today's limit has been reached. Please try again after 4:00 AM Bangladesh Time."
        ])
        return

    user = get_user(user_id)
    if not user:
        bot.send_message(user_id, "Please use /start first")
        return

    pro_price = float(get_setting('pro_like_price'))
    balance = user['balance']

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("CONFIRM", callback_data="pro_like_confirm", style="success", icon_custom_emoji_id="5893224751119208859"),
        InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    send_premium(user_id, [
        ("fire", "🔥"), " DAILY LIKE PRO+\n",
        "━━━━━━━━━━━━━━━━━━━\n\n",
        "আপনি এখান থেকে দ্বিতীয়বার লাইক নিতে পারবেন!\n",
        "যেমন প্রথমবার BUY DAILY LIKE থেকে লাইক নেওয়ার পরেও, ",
        "এখান থেকে এক্সট্রা আরো লাইক নিতে পারবেন।\n\n",
        "আপনি যদি অন্য কোনো বট থেকেও আগে লাইক নিয়ে থাকেন, ",
        "তারপরও এই ফাংশন আপনাকে লাইক পাঠাবে।\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("coins", "💰"), f" Your Balance: ৳{balance}\n",
        ("gem", "💎"), f" Price: ৳{pro_price}\n",
        ("hundred", "💯"), f" Today's Remaining: {remaining}/{limit}\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("warn", "⚠️"), " নিচে CONFIRM চাপলে টাকা কেটে নেওয়া হবে!"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "pro_like_confirm")
def pro_like_confirm(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    pro_price = float(get_setting('pro_like_price'))

    remaining, limit = get_pro_like_remaining()
    if remaining <= 0 and user_id != ADMIN_ID:
        edit_premium(call.message.chat.id, call.message.message_id, [
            ("warn", "⚠️"), " Today's limit has been reached. Please try again after 4:00 AM Bangladesh Time."
        ])
        return

    if user['balance'] < pro_price:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("ADD MONEY", callback_data="add_money", style="success", icon_custom_emoji_id="5902453596456227896"))
        markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))
        edit_premium(call.message.chat.id, call.message.message_id, [
            ("cross", "❌"), " INSUFFICIENT BALANCE!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("coins", "💰"), f" Balance: ৳{user['balance']}\n",
            ("gem", "💎"), f" Required: ৳{pro_price}\n\n",
            "Please add money first!"
        ], reply_markup=markup)
        return

    msg = bot.edit_message_text("📝 Enter your Game UID:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_pro_uid)

def process_pro_uid(message):
    user_id = message.from_user.id
    uid = message.text.strip()
    msg = bot.send_message(user_id, "🌍 Enter Server Name:\n(BD, IND, SG, ID, TH, PK, MEB, BR, SAC, NA, EU, VN, TW, RU)", reply_markup=get_back_button())
    bot.register_next_step_handler(msg, process_pro_server, uid)

def process_pro_server(message, uid):
    user_id = message.from_user.id
    server = message.text.strip().lower()

    pro_price = float(get_setting('pro_like_price'))

    remaining, limit = get_pro_like_remaining()
    if remaining <= 0 and user_id != ADMIN_ID:
        send_premium(user_id, [
            ("warn", "⚠️"), " Today's limit has been reached. Please try again after 4:00 AM Bangladesh Time."
        ])
        return

    result = call_pro_like_api(uid, server)

    if result.get("error") in ["timeout", "network_error", "unknown", "invalid_response"]:
        bot.send_message(user_id, f"❌ API Error: {result.get('message', 'Please try again.')}", reply_markup=get_back_button())
        return

    if result.get("status") == 1:
        if deduct_balance(user_id, pro_price):
            given = result.get('LikesGivenByAPI', 0)
            add_order(user_id, uid, server, given, pro_price, "daily_pro")
            increment_pro_like_usage()
            new_remaining, new_limit = get_pro_like_remaining()
            send_premium(user_id, [
                ("checkmark", "✅"), " PRO+ LIKES ADDED SUCCESSFULLY!\n",
                "━━━━━━━━━━━━━━━━━━━\n",
                ("gamepad", "🎮"), f" UID: {result.get('UID', uid)}\n",
                ("user", "👤"), f" Player: {result.get('PlayerNickname', 'N/A')}\n",
                ("globe", "🌍"), f" Server: {result.get('Region', server.upper())}\n",
                ("chart", "📈"), f" Before: {result.get('LikesBeforeCommand', 'N/A')}\n",
                ("star", "📈"), f" Given: {given}\n",
                ("chart", "📈"), f" After: {result.get('LikesAfterCommand', 'N/A')}\n",
                ("key", "🔑"), f" Order No: {result.get('OrderNo', 'N/A')}\n",
                ("coins", "💰"), f" Price: ৳{pro_price}\n",
                ("hundred", "💯"), f" Today's Remaining: {new_remaining}/{new_limit}\n",
                "━━━━━━━━━━━━━━━━━━━"
            ])
        else:
            bot.send_message(user_id, "❌ Balance deduction failed!", reply_markup=get_back_button())
        return

    elif result.get("status") == 2:
        send_premium(user_id, [
            ("warn", "⚠️"), " ALREADY MAX LIKED!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("gamepad", "🎮"), f" UID: {result.get('UID', uid)}\n",
            ("user", "👤"), f" Player: {result.get('PlayerNickname', 'N/A')}\n",
            ("globe", "🌍"), f" Server: {result.get('Region', server.upper())}\n\n",
            ("star", "🌟"), " No charge was made.\n",
            "━━━━━━━━━━━━━━━━━━━"
        ], reply_markup=get_back_button())
        return

    else:
        error_code = result.get('error', 'unknown')
        error_msg = result.get('message', 'Unknown error')
        extra = ""
        if error_code == "insufficient_balance":
            extra = f"\n💰 API Balance: ৳{result.get('balance', 'N/A')}"
        elif error_code == "delivery_failed":
            extra = f"\n🔄 Refunded: ৳{result.get('Refunded', 'N/A')}"
        elif error_code == "invalid_key":
            extra = "\n⚠️ Admin: API key issue!"
        elif error_code == "rate_limited":
            extra = "\n⏱ Wait 1 minute."

        send_premium(user_id, [
            ("cross", "❌"), " LIKE SENDING FAILED!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("warn", "⚠️"), f" {error_msg}{extra}\n\n",
            ("coins", "💰"), " No charge was made.\n",
            ("refresh", "🔄"), " Please try again later.\n",
            "━━━━━━━━━━━━━━━━━━━"
        ], reply_markup=get_back_button())
        return

# ==================== CANCEL ORDER ====================
@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
    user_id = call.from_user.id
    username = call.from_user.username or "No Username"
    full_name = call.from_user.first_name + (" " + call.from_user.last_name if call.from_user.last_name else "")

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    user = get_user(user_id)
    balance = user['balance'] if user else 0

    if user_id == ADMIN_ID:
        send_premium(user_id, [
            ("crown", "👑"), " MAIN MENU\n",
            "━━━━━━━━━━━━━━━━━━━\n\n",
            ("user", "👤"), f" Name: {full_name}\n",
            ("coins", "💰"), f" Balance: ৳{balance}\n",
            ("arrow_down", "⬇️"), " Select an option below:"
        ], reply_markup=get_admin_keyboard())
    else:
        send_premium(user_id, [
            ("fire", "🔥"), " MAIN MENU\n",
            "━━━━━━━━━━━━━━━━━━━\n\n",
            ("user", "👤"), f" Name: {full_name}\n",
            ("coins", "💰"), f" Balance: ৳{balance}\n",
            ("arrow_down", "⬇️"), " Select an option below:"
        ], reply_markup=get_main_keyboard())

# ==================== AUTO LIKE MENU (USER) ====================
def build_auto_like_menu_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    if is_enabled('buy_auto_like_enabled'):
        markup.add(InlineKeyboardButton("BUY AUTO LIKE", callback_data="ual_buy", style="success", icon_custom_emoji_id="6055615609155099044"))
    if is_enabled('remove_uid_enabled'):
        markup.add(InlineKeyboardButton("REMOVE UID", callback_data="ual_remove", style="danger", icon_custom_emoji_id="5904542823167824187"))
    if is_enabled('change_uid_enabled'):
        markup.add(InlineKeyboardButton("CHANGE UID", callback_data="ual_change", style="primary", icon_custom_emoji_id="5893161718179173515"))
    if is_enabled('check_uids_enabled'):
        markup.add(InlineKeyboardButton("CHECK MY UIDS", callback_data="ual_check", style="primary", icon_custom_emoji_id="5217755613844493415"))
    markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))
    return markup

def ual_back_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("BACK", callback_data="ual_menu_back"))
    return markup

@bot.message_handler(func=lambda message: message.text == "AUTO LIKE")
def auto_like_menu_user(message):
    user_id = message.from_user.id

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    if is_enabled('channel_check_enabled') and user_id != ADMIN_ID:
        if not check_all_channels(user_id):
            markup = get_channel_check_keyboard()
            send_premium(user_id, [
                ("warn", "⚠️"), " CHANNEL JOIN REQUIRED!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                "আমাদের চ্যানেলগুলোতে জয়েন করুন:\n",
                "➖ @MHXLIKE_11\n",
                "➖ @mhxlike_history\n\n",
                "জয়েন করার পর VERIFY বাটনে ক্লিক করুন।\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=markup)
            return

    if not is_enabled('auto_like_enabled') and user_id != ADMIN_ID:
        msg = get_setting('auto_like_off_msg')
        bot.send_message(user_id, msg)
        return

    send_premium(user_id, [
        ("robot", "🤖"), " AUTO LIKE MENU\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        "নিচে থেকে একটি অপশন বেছে নিন:"
    ], reply_markup=build_auto_like_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data == "ual_menu_back")
def ual_menu_back(call):
    pending_auto_like.pop(call.from_user.id, None)
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("robot", "🤖"), " AUTO LIKE MENU\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        "নিচে থেকে একটি অপশন বেছে নিন:"
    ], reply_markup=build_auto_like_menu_markup())

# ---- BUY AUTO LIKE ----
@bot.callback_query_handler(func=lambda call: call.data == "ual_buy")
def ual_buy(call):
    if not is_enabled('buy_auto_like_enabled'):
        bot.answer_callback_query(call.id, "This feature is currently disabled.", show_alert=True)
        return
    packages = get_enabled_packages()
    if not packages:
        bot.answer_callback_query(call.id, "No packages available right now.", show_alert=True)
        return
    user = get_user(call.from_user.id)
    markup = InlineKeyboardMarkup(row_width=1)
    segments = [
        ("star", "⭐"), " BUY AUTO LIKE\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("coins", "💰"), f" Balance: ৳{user['balance']}\n\n"
    ]
    std = [p for p in packages if p['category'] == 'standard']
    vip = [p for p in packages if p['category'] == 'vip']
    if std:
        segments.append(("fire", "🔥"))
        segments.append(" STANDARD PACKAGE\n")
        for p in std:
            segments.append(f"  {p['days']} Days │ ৳{p['price']} │ {p['likes_amount']}+ Daily Likes\n")
            markup.add(InlineKeyboardButton(f"Standard {p['days']}D - ৳{p['price']}", callback_data=f"ualpkg_{p['package_id']}", style="primary", icon_custom_emoji_id="5893255507380014983"))
        segments.append("\n")
    if vip:
        segments.append(("crown", "👑"))
        segments.append(" VIP PACKAGE\n")
        for p in vip:
            segments.append(f"  {p['days']} Days │ ৳{p['price']} │ {p['likes_amount']}+ Daily Likes\n")
            markup.add(InlineKeyboardButton(f"VIP {p['days']}D - ৳{p['price']}", callback_data=f"ualpkg_{p['package_id']}", style="success", icon_custom_emoji_id="6057491547790778084"))
    segments.append("━━━━━━━━━━━━━━━━━━━")
    markup.add(InlineKeyboardButton("BACK", callback_data="ual_menu_back", style="danger", icon_custom_emoji_id="5420274119398669907"))
    edit_premium(call.message.chat.id, call.message.message_id, segments, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ualpkg_"))
def ualpkg_selected(call):
    package_id = call.data.replace("ualpkg_", "")
    package = get_package(package_id)
    if not package or not package['enabled']:
        bot.answer_callback_query(call.id, "Package unavailable.", show_alert=True)
        return
    user = get_user(call.from_user.id)
    if user['balance'] < package['price']:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("ADD MONEY", callback_data="add_money", style="success", icon_custom_emoji_id="5902453596456227896"))
        markup.add(InlineKeyboardButton("BACK", callback_data="ual_menu_back"))
        edit_premium(call.message.chat.id, call.message.message_id, [
            ("cross", "❌"), " INSUFFICIENT BALANCE!\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("coins", "💰"), f" Balance: ৳{user['balance']}\n",
            ("gem", "💎"), f" Required: ৳{package['price']}\n\n",
            "Please add money first!"
        ], reply_markup=markup)
        return

    deduct_balance(call.from_user.id, package['price'])
    msg = bot.edit_message_text(
        "🌟 ADD UID TO AUTO LIKE\n\n👤 Please send the UID you want to add:\nExample: 1203435801",
        call.message.chat.id, call.message.message_id
    )
    bot.register_next_step_handler(msg, ual_process_uid, package_id, package['price'])

def ual_process_uid(message, package_id, paid_price):
    uid = message.text.strip()
    if not uid.isdigit() or len(uid) < 5:
        refund_balance(message.from_user.id, paid_price)
        bot.send_message(message.from_user.id, "❌ Invalid UID! Your balance has been refunded.", reply_markup=ual_back_markup())
        return
    msg = bot.send_message(message.from_user.id, "🌐 Enter region code:\nExamples: bd | sg | ind")
    bot.register_next_step_handler(msg, ual_process_region, package_id, paid_price, uid)

def ual_process_region(message, package_id, paid_price, uid):
    region = message.text.strip().lower()
    user_id = message.from_user.id

    loading = bot.send_message(user_id, "⏳ Fetching account information...")
    nickname = fetch_ff_nickname(uid)
    try:
        bot.delete_message(user_id, loading.message_id)
    except:
        pass

    pending_auto_like[user_id] = {
        "uid": uid, "region": region, "nickname": nickname,
        "package_id": package_id, "paid_price": paid_price
    }

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Continue", callback_data="ualconfirm_yes"),
        InlineKeyboardButton("❌ Cancel", callback_data="ualconfirm_no")
    )
    send_premium(user_id, [
        ("user", "👤"), f" UID: {uid}\n",
        ("crown", "👑"), f" Name: {nickname}\n",
        ("globe", "🌐"), f" Region: {region.upper()}\n\n",
        ("warn", "⚠️"), " আপনি কি নিশ্চিত এই Auto Like প্যাকেজ Purchase ও Activate করতে চান?\n\n",
        "যদি Continue না করতে চান, Cancel চাপুন এবং আপনার ব্যালেন্স ফেরত দেওয়া হবে।"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ualconfirm_no")
def ualconfirm_no(call):
    user_id = call.from_user.id
    data = pending_auto_like.pop(user_id, None)
    if data:
        refund_balance(user_id, data['paid_price'])
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("cross", "❌"), " Purchase Cancelled. Your balance has been refunded."
    ], reply_markup=ual_back_markup())

@bot.callback_query_handler(func=lambda call: call.data == "ualconfirm_yes")
def ualconfirm_yes(call):
    user_id = call.from_user.id
    data = pending_auto_like.pop(user_id, None)
    if not data:
        bot.answer_callback_query(call.id, "❌ Session expired! Please try again.", show_alert=True)
        return
    package = get_package(data['package_id'])
    if not package:
        refund_balance(user_id, data['paid_price'])
        bot.answer_callback_query(call.id, "❌ Package no longer exists. Refunded.", show_alert=True)
        return

    now_bd = get_bd_time()
    expiry_dt = now_bd + timedelta(days=package['days'])
    expiry_str = expiry_dt.strftime("%Y-%m-%d")

    add_auto_like_full(
        user_id, data['uid'], data['region'], data['nickname'],
        package['price'], package['days'], expiry_str, package['package_id'], package['category']
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("checkmark", "✅"), " UID ADDED SUCCESSFULLY!\n\n",
        ("user", "👤"), f" UID: {data['uid']}\n",
        ("crown", "👑"), f" Name: {data['nickname']}\n",
        ("globe", "🌐"), f" Region: {data['region'].upper()}\n",
        ("infinity", "♾"), f" Duration: {package['days']} Days\n",
        ("calendar", "📅"), f" Expires On: {expiry_str} 04:00 AM\n\n",
        "Auto likes will be sent daily at 04:00 AM (Bangladesh Time).\n\n",
        ("broadcast", "📢"), " আপনার Daily Post শেয়ার করা হবে আমাদের চ্যানেলে।"
    ])

    username = call.from_user.username or "No Username"
    bangladesh_time = get_bd_time().strftime("%Y-%m-%d %I:%M:%S %p")
    try:
        send_premium(CHANNEL_ID, [
           ("new", "🆕"), " NEW AUTO LIKE ACTIVATED\n",
           "━━━━━━━━━━━━━━━━━━━\n",
           ("user", "👤"), f" User: @{username} ({user_id})\n",
           ("crown", "👑"), f" Account Name: {data['nickname']}\n",
           ("shield", "🆔"), f" UID: {data['uid']}\n",
           ("globe", "🌐"), f" Region: {data['region'].upper()}\n",
           ("gift", "📦"), f" Package: {package['category'].upper()} - {package['days']} Days\n",
           ("clock", "🕐"), f" Activated At: {bangladesh_time} (BDT)\n",
           ("broadcast", "📢"), " Delivery Channel: https://t.me/ZrAutolike\n",
           "━━━━━━━━━━━━━━━━━━━"
    ])
    except Exception as e:
         print(f"Notify group error: {e}")

# ---- REMOVE UID ----
@bot.callback_query_handler(func=lambda call: call.data == "ual_remove")
def ual_remove_warning(call):
    if not is_enabled('remove_uid_enabled'):
        bot.answer_callback_query(call.id, "This feature is currently disabled.", show_alert=True)
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Continue", callback_data="ual_remove_continue"),
        InlineKeyboardButton("❌ Cancel", callback_data="ual_menu_back")
    )
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("warn", "⚠️"), " WARNING\n\n",
        "আপনি যদি একটি Auto Like UID Remove করেন, আপনার Auto Like প্যাকেজ স্থায়ীভাবে বাতিল হয়ে যাবে।\n\n",
        "❌ কোনো Refund দেওয়া হবে না।"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ual_remove_continue")
def ual_remove_continue(call):
    user_id = call.from_user.id
    autos = get_user_auto_likes(user_id, active_only=True)
    if not autos:
        bot.answer_callback_query(call.id, "📭 You have no active Auto Like UIDs.", show_alert=True)
        return
    text = "🗑 REMOVE UID\n\n"
    for i, a in enumerate(autos, 1):
        text += f"{i}. UID: {a['uid']} | {a['account_name'] or 'N/A'} | {a['server_name'].upper()}\n"
    text += "\nSend the serial number to remove, or 0 to go back."
    msg = bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_remove_uid_choice, autos)

def process_remove_uid_choice(message, autos):
    user_id = message.from_user.id
    try:
        choice = int(message.text.strip())
    except:
        bot.send_message(user_id, "❌ Invalid input!", reply_markup=ual_back_markup())
        return
    if choice == 0:
        send_premium(user_id, [("robot", "🤖"), " AUTO LIKE MENU"], reply_markup=build_auto_like_menu_markup())
        return
    if 1 <= choice <= len(autos):
        item = autos[choice - 1]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE auto_likes SET status='removed' WHERE id=?", (item['id'],))
        conn.commit()
        send_premium(user_id, [
            ("checkmark", "✅"), f" UID {item['uid']} has been removed from Auto Like.\n",
            "❌ This package has been permanently cancelled (no refund)."
        ])
        username = message.from_user.username or "No Username"
        bangladesh_time = get_bd_time().strftime("%Y-%m-%d %I:%M:%S %p")
        try:
            send_premium(CHANNEL_ID, [
                ("cross", "❌"), " AUTO LIKE REMOVED\n",
                "━━━━━━━━━━━━━━━━━━━\n",
                ("user", "👤"), f" User: @{username} ({user_id})\n",
                ("shield", "🆔"), f" UID: {item['uid']}\n",
                ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
                "━━━━━━━━━━━━━━━━━━━"
            ])
        except:
            pass
    else:
        bot.send_message(user_id, "❌ Invalid choice!", reply_markup=ual_back_markup())

# ---- CHANGE UID ----
@bot.callback_query_handler(func=lambda call: call.data == "ual_change")
def ual_change_warning(call):
    if not is_enabled('change_uid_enabled'):
        bot.answer_callback_query(call.id, "This feature is currently disabled.", show_alert=True)
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Continue", callback_data="ual_change_continue"),
        InlineKeyboardButton("❌ Cancel", callback_data="ual_menu_back")
    )
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("warn", "⚠️"), " SCAM ALERT\n\n",
        "This is a trusted bot.\nPlease do not scam or cheat anyone.\n\n",
        "Using this feature, you can replace an existing UID with another UID, while keeping the same package and remaining duration."
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ual_change_continue")
def ual_change_continue(call):
    user_id = call.from_user.id
    autos = get_user_auto_likes(user_id, active_only=True)
    if not autos:
        bot.answer_callback_query(call.id, "📭 You have no active Auto Like accounts.", show_alert=True)
        return
    text = "🔄 CHANGE UID\n\nWhich account would you like to replace?\n\n"
    for i, a in enumerate(autos, 1):
        text += f"{i}. UID: {a['uid']} | {a['account_name'] or 'N/A'} | {(a['category'] or 'standard').upper()} package\n"
    msg = bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, ual_change_select, autos)

def ual_change_select(message, autos):
    user_id = message.from_user.id
    try:
        choice = int(message.text.strip())
        item = autos[choice - 1]
    except:
        bot.send_message(user_id, "❌ Invalid choice!", reply_markup=ual_back_markup())
        return
    fee = float(get_setting('uid_change_fee') or 50)
    user = get_user(user_id)
    if user['balance'] < fee:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("ADD MONEY", callback_data="add_money", style="success", icon_custom_emoji_id="5902453596456227896"))
        send_premium(user_id, [
            ("cross", "❌"), " INSUFFICIENT BALANCE!\n",
            ("coins", "💰"), f" Balance: ৳{user['balance']}\n",
            ("gem", "💎"), f" Required: ৳{fee}"
        ], reply_markup=markup)
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Continue", callback_data=f"ual_changefee_yes_{item['id']}"),
        InlineKeyboardButton("❌ Cancel", callback_data="ual_menu_back")
    )
    send_premium(user_id, [
        ("money", "💰"), f" UID CHANGE FEE: ৳{fee}\n\n",
        f"Current Balance: ৳{user['balance']}\nCharge: ৳{fee}"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ual_changefee_yes_"))
def ual_changefee_confirm(call):
    auto_id = call.data.replace("ual_changefee_yes_", "")
    fee = float(get_setting('uid_change_fee') or 50)
    user_id = call.from_user.id
    user = get_user(user_id)
    if user['balance'] < fee:
        bot.answer_callback_query(call.id, "❌ Insufficient balance!", show_alert=True)
        return
    deduct_balance(user_id, fee)
    msg = bot.edit_message_text("📝 Enter the NEW UID:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, ual_change_new_uid, auto_id, fee)

def ual_change_new_uid(message, auto_id, fee):
    user_id = message.from_user.id
    new_uid = message.text.strip()
    if not new_uid.isdigit() or len(new_uid) < 5:
        refund_balance(user_id, fee)
        bot.send_message(user_id, "❌ Invalid UID! Fee refunded.", reply_markup=ual_back_markup())
        return
    loading = bot.send_message(user_id, "⏳ Fetching new account information...")
    nickname = fetch_ff_nickname(new_uid)
    try:
        bot.delete_message(user_id, loading.message_id)
    except:
        pass
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auto_likes WHERE id=?", (auto_id,))
    old_row = cursor.fetchone()
    old_uid = old_row['uid'] if old_row else "N/A"
    cursor.execute("UPDATE auto_likes SET uid=?, account_name=? WHERE id=?", (new_uid, nickname, auto_id))
    conn.commit()
    send_premium(user_id, [
        ("checkmark", "✅"), " UID CHANGED SUCCESSFULLY!\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("user", "👤"), f" New UID: {new_uid}\n",
        ("crown", "👑"), f" New Name: {nickname}\n",
        ("money", "💰"), f" Fee Charged: ৳{fee}\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        "Your package, remaining days, and like history all stay the same."
    ])
    username = message.from_user.username or "No Username"
    bangladesh_time = get_bd_time().strftime("%Y-%m-%d %I:%M:%S %p")
    try:
        send_premium(CHANNEL_ID, [
            ("refresh", "🔄"), " AUTO LIKE UID CHANGED\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("user", "👤"), f" User: @{username} ({user_id})\n",
            ("cross", "❌"), f" Old UID: {old_uid}\n",
            ("checkmark", "✅"), f" New UID: {new_uid}\n",
            ("clock", "🕐"), f" Time: {bangladesh_time} (BDT)\n",
            "━━━━━━━━━━━━━━━━━━━"
        ])
    except:
        pass

# ---- CHECK MY UIDS ----
@bot.callback_query_handler(func=lambda call: call.data == "ual_check")
def ual_check(call):
    if not is_enabled('check_uids_enabled'):
        bot.answer_callback_query(call.id, "This feature is currently disabled.", show_alert=True)
        return
    user_id = call.from_user.id
    autos = get_user_auto_likes(user_id)
    if not autos:
        edit_premium(call.message.chat.id, call.message.message_id, [
            ("cross", "❌"), " আপনার কোনো Auto Like UID নেই।"
        ], reply_markup=ual_back_markup())
        return
    segments = [("robot", "🤖"), " MY AUTO LIKE UIDs\n", "━━━━━━━━━━━━━━━━━━━\n"]
    for i, a in enumerate(autos, 1):
        remaining = get_remaining_days_text(a['expiry_date'])
        astatus = a['admin_status'] or 'active'
        segments.append(
            f"\n#{i}\n🆔 UID: {a['uid']}\n👑 Name: {a['account_name'] or 'N/A'}\n"
            f"🌐 Region: {a['server_name'].upper()}\n📦 Package: {(a['category'] or 'standard').upper()}\n"
            f"⏳ Remaining: {remaining}\n📅 Expires: {a['expiry_date'] or 'N/A'}\n⚙️ Status: {astatus}\n"
        )
    segments.append("━━━━━━━━━━━━━━━━━━━")
    edit_premium(call.message.chat.id, call.message.message_id, segments, reply_markup=ual_back_markup())

# ==================== ADD MONEY ====================
@bot.message_handler(func=lambda message: message.text == "ADD MONEY")
@bot.callback_query_handler(func=lambda call: call.data == "add_money")
def add_money(message):
    if isinstance(message, types.CallbackQuery):
        user_id = message.from_user.id
        chat_id = message.message.chat.id
    else:
        user_id = message.from_user.id
        chat_id = message.chat.id

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    if is_enabled('channel_check_enabled') and user_id != ADMIN_ID:
        if not check_all_channels(user_id):
            markup = get_channel_check_keyboard()
            send_premium(user_id, [
                ("warn", "⚠️"), " CHANNEL JOIN REQUIRED!\n",
                "━━━━━━━━━━━━━━━━━━━\n\n",
                "আমাদের চ্যানেলগুলোতে জয়েন করুন:\n",
                "➖ @MHXLIKE_11\n",
                "➖ @mhxlike_history\n\n",
                "জয়েন করার পর VERIFY বাটনে ক্লিক করুন।\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=markup)
            return

    if not is_enabled('add_money_enabled') and user_id != ADMIN_ID:
        msg = get_setting('add_money_off_msg')
        bot.send_message(user_id, msg)
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))

    msg = send_premium(chat_id, [
        ("money", "💰"), " ADD MONEY\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("arrow_down", "📝"), " Please enter amount:\n",
        "(Minimum: 10 BDT)"
    ], reply_markup=markup)
    bot.register_next_step_handler(msg, process_add_amount)

def process_add_amount(message):
    user_id = message.from_user.id

    try:
        amount = float(message.text.strip())
        if amount < 10:
            bot.send_message(user_id, "❌ Minimum amount is 10 BDT!")
            return

        waiting = bot.send_message(user_id, "⏳ Creating payment link...")

        payment_data = create_payment_key(amount, user_id)

        bot.delete_message(user_id, waiting.message_id)

        if payment_data and payment_data.get("responseCode") == 200:
            payment_url = payment_data.get("payment_url")
            payment_key = payment_data.get("paymentkey")

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("PAY NOW", url=payment_url, style="success", icon_custom_emoji_id="5902056028513505203"))
            markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))

            send_premium(user_id, [
                ("ticket", "💳"), " PAYMENT READY\n",
                "━━━━━━━━━━━━━━━━━━━\n",
                ("coins", "💰"), f" Amount: ৳{amount}\n",
                ("key", "🔑"), f" Ref: {payment_key}\n\n",
                ("warn", "⚠️"), " After payment, you will be\n",
                ("warn2", "⚠️"), " redirected to bot automatically!\n",
                ("clock", "⏳"), " Complete payment to add balance\n",
                "━━━━━━━━━━━━━━━━━━━"
            ], reply_markup=markup)
        else:
            bot.send_message(user_id, "❌ Failed to create payment. Please try again later.")

    except ValueError:
        bot.send_message(user_id, "❌ Please enter a valid number!")

# ==================== MY INFO ====================
@bot.message_handler(func=lambda message: message.text == "MY INFO")
def my_info(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        bot.send_message(user_id, "Please /start first")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM auto_likes WHERE user_id=? AND status='active'", (user_id,))
    active_auto = cursor.fetchone()[0]

    channel_status = "✅ Joined" if user['channel_joined'] else "❌ Not joined"

    send_premium(user_id, [
        ("crown", "👤"), " MY INFO\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("crown2", "👑"), f" Name: {user['full_name']}\n",
        ("tag", "📝"), f" Username: @{user['username']}\n",
        ("shield", "🆔"), f" User ID: {user['user_id']}\n",
        ("coins", "💰"), f" Balance: ৳{user['balance']}\n",
        ("money", "💵"), f" Total Deposit: ৳{user['total_deposit']}\n",
        ("chart", "💸"), f" Total Spent: ৳{user['total_spent']}\n",
        ("robot", "🤖"), f" Active Auto Like: {active_auto}\n",
        ("calendar", "📅"), f" Join Date: {user['join_date']}\n",
        ("link", "🔗"), f" Channel Status: {channel_status}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ])

# ==================== MY HISTORY ====================
@bot.message_handler(func=lambda message: message.text == "MY HISTORY")
def my_history(message):
    user_id = message.from_user.id

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id=? ORDER BY order_date DESC LIMIT 10", (user_id,))
    orders = cursor.fetchall()

    cursor.execute("SELECT * FROM deposit_history WHERE user_id=? AND status='completed' ORDER BY date DESC LIMIT 10", (user_id,))
    deposits = cursor.fetchall()

    segments = [("chart", "📊"), " MY HISTORY\n", "━━━━━━━━━━━━━━━━━━━\n\n"]

    if deposits:
        segments.append(("coins", "💰"))
        segments.append(" DEPOSITS:\n")
        for dep in deposits:
            segments.append(f"🔹 +৳{dep['amount']} | {dep['date']}\n")
        segments.append("\n")

    if orders:
        segments.append(("bag", "🛒"))
        segments.append(" ORDERS:\n")
        for order in orders:
            segments.append(f"🔸 {order['order_type']} | ৳{order['price']} | {order['order_date']}\n")
    else:
        segments.append("❌ No history yet!\n")

    segments.append("━━━━━━━━━━━━━━━━━━━")

    try:
        send_premium(user_id, segments)
    except Exception as e:
        print(f"History error: {e}")
        fallback = "MY HISTORY\n━━━━━━━━━━━━━━━━━━━\n\n"
        if deposits:
            fallback += "💰 DEPOSITS:\n"
            for dep in deposits:
                fallback += f"🔹 +৳{dep['amount']} | {dep['date']}\n"
        if orders:
            fallback += "\n🛒 ORDERS:\n"
            for order in orders:
                fallback += f"🔸 {order['order_type']} | ৳{order['price']} | {order['order_date']}\n"
        if not deposits and not orders:
            fallback += "❌ No history yet!\n"
        fallback += "━━━━━━━━━━━━━━━━━━━"
        bot.send_message(user_id, fallback)

# ==================== HOW TO USE ====================
@bot.message_handler(func=lambda message: message.text == "HOW TO USE")
def how_to_use(message):
    user_id = message.from_user.id

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("WATCH TUTORIAL VIDEO", url="https://vt.tiktok.com/ZSggrhQvT/", style="success", icon_custom_emoji_id="5893255507380014983"))
    markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))

    send_premium(user_id, [
        ("star", "🌟"), " HOW TO USE — FIRE LIKE BOT\n",
        "━━━━━━━━━━━━━━━━━━━\n\n",
        ("play", "🎥"), " বিস্তারিত ভিডিও টিউটোরিয়াল:\n",
        "https://vt.tiktok.com/ZSggrhQvT/\n\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("one", "1️⃣"), " ADD MONEY\n",
        "   • ADD MONEY বাটনে ক্লিক করুন\n",
        "   • এমাউন্ট দিন (সর্বনিম্ন ১০৳)\n",
        "   • PAY NOW চেপে পেমেন্ট সম্পন্ন করুন\n",
        "   • পেমেন্ট হলে অটো ব্যালেন্স যোগ হবে\n\n",
        ("two", "2️⃣"), " BUY DAILY LIKE\n",
        "   • BUY DAILY LIKE বাটনে ক্লিক করুন\n",
        "   • আপনার Free Fire UID দিন\n",
        "   • সার্ভার নাম দিন (bd / ind / sg)\n",
        "   • লাইক অটো চলে যাবে\n\n",
        ("three", "3️⃣"), " DAILY LIKE PRO+\n",
        "   • একই UID-তে দ্বিতীয়বার লাইক নিতে\n",
        "   • অন্য বট থেকে লাইক নিলেও কাজ করবে\n",
        "   • দৈনিক লিমিট: ৩০ বার\n\n",
        ("four", "4️⃣"), " AUTO LIKE (প্যাকেজ)\n",
        "   • AUTO LIKE → BUY AUTO LIKE\n",
        "   • প্যাকেজ সিলেক্ট করুন (Standard/VIP)\n",
        "   • UID + Region দিন\n",
        "   • প্রতি রাত ৪:০০ টায় অটো লাইক যাবে\n\n",
        ("refresh", "5️⃣"), " CHANGE / REMOVE / CHECK UID\n",
        "   • AUTO LIKE মেনু থেকে অপশন সিলেক্ট করুন\n",
        "   • Change UID ফি: ৫০৳\n",
        "   • Remove UID: কোনো রিফান্ড নেই\n\n",
        ("gift", "6️⃣"), " REFER & EARN\n",
        "   • REFER & EARN বাটনে ক্লিক করুন\n",
        "   • SHARE MY LINK চেপে শেয়ার করুন\n",
        "   • প্রতি রেফারে বোনাস + কমিশন\n\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("phone", "🆘"), " যেকোনো সমস্যায় SUPPORT এ যান।"
    ], reply_markup=markup)

# ==================== SUPPORT ====================
@bot.message_handler(func=lambda message: message.text == "SUPPORT")
def support(message):
    user_id = message.from_user.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("CONTACT ADMIN", url=f"tg://user?id={ADMIN_ID}", style="primary", icon_custom_emoji_id="5893297890117292323"))

    send_premium(user_id, [
        ("phone", "🆘"), " SUPPORT\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("contact", "👨‍💼"), " For any problems, contact admin!\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

# ==================== REFER & EARN ====================
@bot.message_handler(func=lambda message: message.text == "REFER & EARN")
def refer_earn(message):
    user_id = message.from_user.id

    if is_maintenance() and user_id != ADMIN_ID:
        msg = get_setting('maintenance_msg')
        bot.send_message(user_id, msg)
        return

    if not is_enabled('refer_enabled') and user_id != ADMIN_ID:
        bot.send_message(user_id, "🎁 Refer & Earn service is temporarily disabled.")
        return

    user = get_user(user_id)
    if not user:
        bot.send_message(user_id, "Please use /start first")
        return

    signup_bonus = get_setting('refer_signup_bonus')
    deposit_percent = get_setting('refer_deposit_percent')
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=? AND channel_joined=1", (user_id,))
    joined_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    total_count = cursor.fetchone()[0]

    send_premium(user_id, [
        ("warn", "⚠️"), " REFER & EARN নিয়ম\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"🔹 লিংক শেয়ার করার সাথে সাথে আপনি ৳{signup_bonus} পাবেন (নতুন ইউজার চ্যানেলে জয়েন করার পর)।\n",
        f"🔹 সেই ইউজার ডিপোজিট করলে প্রতি ১০ টাকায় আপনি {deposit_percent}% কমিশন পাবেন।\n",
        "🔹 নতুন ইউজারকে অবশ্যই আমাদের সবগুলো চ্যানেলে জয়েন করতে হবে।\n",
        "━━━━━━━━━━━━━━━━━━━"
    ])

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("SHARE MY LINK", url=f"https://t.me/share/url?url={ref_link}&text=Free%20Fire%20Like%20নিন%20একদম%20ফ্রি!%20জয়েন%20করুন:", style="success", icon_custom_emoji_id="5372917041193828849"))
    markup.add(InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907"))

    send_premium(user_id, [
        ("gift", "🎁"), " YOUR REFER LINK\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"🔗 {ref_link}\n\n",
        ("user", "👥"), f" Total Referred: {total_count}\n",
        ("checkmark", "✅"), f" Joined & Verified: {joined_count}\n",
        ("coins", "💰"), f" Total Earnings: ৳{user['referral_earnings'] or 0}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

# ==================== ADMIN PANEL ====================
@bot.message_handler(func=lambda message: message.text == "ADMIN PANEL" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    user_id = message.from_user.id

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount) FROM deposit_history WHERE status='completed'")
    total_deposits = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(price) FROM orders")
    total_orders = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pending_payments WHERE status='pending'")
    pending_count = cursor.fetchone()[0]

    d_enabled = "✅" if is_enabled('daily_like_enabled') else "❌"
    a_enabled = "✅" if is_enabled('auto_like_enabled') else "❌"
    m_enabled = "✅" if is_enabled('add_money_enabled') else "❌"
    mm = "🛠 ON" if is_enabled('maintenance_mode') else "✅ OFF"
    cc = "✅" if is_enabled('channel_check_enabled') else "❌"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Function Settings", callback_data="admin_functions", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Price Settings", callback_data="admin_prices", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Welcome Video", callback_data="admin_video", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Maintenance", callback_data="admin_maintenance", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Off Messages", callback_data="admin_off_msgs", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Broadcast", callback_data="admin_broadcast", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Create Redeem Code", callback_data="admin_create_redeem", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Add Balance", callback_data="admin_add_balance", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Check/Manage Balance", callback_data="admin_check_balance", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("User List", callback_data="admin_user_list", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Settings", callback_data="admin_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Pro+ Settings", callback_data="admin_pro_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Refer Settings", callback_data="admin_refer_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Channel Check", callback_data="admin_channel_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Refer Post Settings", callback_data="admin_refer_post_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Auto Like Admin", callback_data="admin_autolike_admin", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Auto Like Packages", callback_data="admin_autolike_packages", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("Auto Like Buttons", callback_data="admin_autolike_buttons", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="cancel_order", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    p_enabled = "✅" if is_enabled('pro_like_enabled') else "❌"
    r_enabled = "✅" if is_enabled('refer_enabled') else "❌"
    rp_enabled = "✅" if is_enabled('refer_post_enabled') else "❌"
    dp_enabled = "✅" if is_enabled('deposit_post_enabled') else "❌"

    send_premium(user_id, [
        ("crown", "👑"), " ADMIN PANEL\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("user", "👥"), f" Total Users: {total_users}\n",
        ("coins", "💰"), f" Total Deposits: ৳{total_deposits}\n",
        ("bag", "🛒"), f" Total Orders: ৳{total_orders}\n",
        ("clock", "⏳"), f" Pending Payments: {pending_count}\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"🔥 Daily Like: {d_enabled}\n",
        f"🔥 Daily Pro+: {p_enabled}\n",
        f"⭐ Auto Like: {a_enabled}\n",
        f"💰 Add Money: {m_enabled}\n",
        f"🎁 Refer & Earn: {r_enabled}\n",
        f"📢 Refer Post: {rp_enabled}\n",
        f"💰 Deposit Post: {dp_enabled}\n",
        f"🔗 Channel Check: {cc}\n",
        f"🛠 Maintenance: {mm}\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        "💳 Gateway: ZRPAYBD Pay (Direct Return)"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_functions")
def admin_functions(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Admin only!", show_alert=True)
        return

    d_status = "✅ ON" if is_enabled('daily_like_enabled') else "❌ OFF"
    a_status = "✅ ON" if is_enabled('auto_like_enabled') else "❌ OFF"
    m_status = "✅ ON" if is_enabled('add_money_enabled') else "❌ OFF"
    cc_status = "✅ ON" if is_enabled('channel_check_enabled') else "❌ OFF"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"🔥 Daily: {d_status}", callback_data="toggle_daily", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton(f"⭐ Auto: {a_status}", callback_data="toggle_auto", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton(f"💰 Money: {m_status}", callback_data="toggle_money", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton(f"🔗 Channel: {cc_status}", callback_data="toggle_channel_check", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("settings", "⚙️"), " FUNCTION SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("arrow_down", "⬇️"), " Toggle functions on/off:\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["toggle_daily", "toggle_auto", "toggle_money", "toggle_channel_check"])
def toggle_function(call):
    if call.from_user.id != ADMIN_ID: return

    func_map = {
        "toggle_daily": "daily_like_enabled",
        "toggle_auto": "auto_like_enabled",
        "toggle_money": "add_money_enabled",
        "toggle_channel_check": "channel_check_enabled"
    }
    key = func_map[call.data]
    current = is_enabled(key)
    set_setting(key, "off" if current else "on")

    bot.answer_callback_query(call.id, f"✅ {'Disabled' if current else 'Enabled'}!")
    admin_functions(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_prices")
def admin_prices(call):
    if call.from_user.id != ADMIN_ID: return

    daily_price = get_setting('daily_like_price')
    daily_amount = get_setting('daily_like_amount')

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✏️ Change Daily Price", callback_data="change_daily_price", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Change Like Amount", callback_data="change_daily_amount", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("gem", "💎"), " PRICE SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"🔥 Daily Like Price: ৳{daily_price}\n",
        f"📈 Like Amount: {daily_amount}+\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["change_daily_price", "change_daily_amount"])
def change_price(call):
    if call.from_user.id != ADMIN_ID: return
    key = "daily_like_price" if call.data == "change_daily_price" else "daily_like_amount"
    label = "Price (BDT)" if key == "daily_like_price" else "Like Amount"

    msg = bot.edit_message_text(f"📝 Enter new {label}:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_price_change, key)

def process_price_change(message, key):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.strip())
        set_setting(key, str(int(val)) if key == "daily_like_amount" else str(val))
        bot.send_message(ADMIN_ID, f"✅ Updated {key} to {val}")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_video")
def admin_video(call):
    if call.from_user.id != ADMIN_ID: return

    current = get_setting('welcome_video_id')
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📤 Set New Video", callback_data="set_welcome_video", style="success", icon_custom_emoji_id="5774022692642492953"),
        InlineKeyboardButton("🗑 Remove Video", callback_data="remove_welcome_video", style="danger", icon_custom_emoji_id="5774077015388852135"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    status = f"✅ Video ID: {current[:20]}..." if current else "❌ No video set"
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("broadcast", "🎥"), " WELCOME VIDEO SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Status: {status}\n\n",
        "Forward a video to set as welcome video"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "set_welcome_video")
def set_welcome_video(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📤 Forward a video message to set as welcome video:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_video)

def process_video(message):
    if message.from_user.id != ADMIN_ID: return
    if message.video:
        set_setting('welcome_video_id', message.video.file_id)
        bot.send_message(ADMIN_ID, "✅ Welcome video set successfully!")
    elif message.animation:
        set_setting('welcome_video_id', message.animation.file_id)
        bot.send_message(ADMIN_ID, "✅ Welcome GIF set successfully!")
    else:
        bot.send_message(ADMIN_ID, "❌ Please send a video or GIF!")

@bot.callback_query_handler(func=lambda call: call.data == "remove_welcome_video")
def remove_welcome_video(call):
    if call.from_user.id != ADMIN_ID: return
    set_setting('welcome_video_id', '')
    bot.answer_callback_query(call.id, "✅ Video removed!")
    admin_video(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_maintenance")
def admin_maintenance(call):
    if call.from_user.id != ADMIN_ID: return

    status = "🛠 ON" if is_enabled('maintenance_mode') else "✅ OFF"
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Toggle: {status}", callback_data="toggle_maintenance", style="danger", icon_custom_emoji_id="5774077015388852135"),
        InlineKeyboardButton("✏️ Change Message", callback_data="change_maintenance_msg", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("settings", "🛠"), " MAINTENANCE MODE\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Status: {status}\n",
        f"Message: {get_setting('maintenance_msg')[:50]}...\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def toggle_maintenance(call):
    if call.from_user.id != ADMIN_ID: return
    current = is_enabled('maintenance_mode')
    set_setting('maintenance_mode', 'off' if current else 'on')
    bot.answer_callback_query(call.id, f"✅ Maintenance {'Disabled' if current else 'Enabled'}!")
    admin_maintenance(call)

@bot.callback_query_handler(func=lambda call: call.data == "change_maintenance_msg")
def change_maintenance_msg(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new maintenance message:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_maintenance_msg)

def process_maintenance_msg(message):
    if message.from_user.id != ADMIN_ID: return
    set_setting('maintenance_msg', message.text)
    bot.send_message(ADMIN_ID, "✅ Maintenance message updated!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_off_msgs")
def admin_off_msgs(call):
    if call.from_user.id != ADMIN_ID: return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔥 Daily Off Msg", callback_data="set_daily_off_msg", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("⭐ Auto Off Msg", callback_data="set_auto_off_msg", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("💰 Money Off Msg", callback_data="set_money_off_msg", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("broadcast", "✏️"), " OFF MESSAGES\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"🔥 Daily: {get_setting('daily_like_off_msg')[:40]}...\n\n",
        f"⭐ Auto: {get_setting('auto_like_off_msg')[:40]}...\n\n",
        f"💰 Money: {get_setting('add_money_off_msg')[:40]}...\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["set_daily_off_msg", "set_auto_off_msg", "set_money_off_msg"])
def set_off_msg(call):
    if call.from_user.id != ADMIN_ID: return

    key_map = {
        "set_daily_off_msg": ("daily_like_off_msg", "Daily Like"),
        "set_auto_off_msg": ("auto_like_off_msg", "Auto Like"),
        "set_money_off_msg": ("add_money_off_msg", "Add Money")
    }
    key, name = key_map[call.data]

    msg = bot.edit_message_text(f"📝 Enter off message for {name}:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_off_msg, key)

def process_off_msg(message, key):
    if message.from_user.id != ADMIN_ID: return
    set_setting(key, message.text)
    bot.send_message(ADMIN_ID, f"✅ Off message updated!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if call.from_user.id != ADMIN_ID: return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(amount) FROM deposit_history WHERE status='completed'")
    total_deposits = cursor.fetchone()[0] or 0

    d_enabled = "✅" if is_enabled('daily_like_enabled') else "❌"
    a_enabled = "✅" if is_enabled('auto_like_enabled') else "❌"
    m_enabled = "✅" if is_enabled('add_money_enabled') else "❌"
    mm = "🛠 ON" if is_enabled('maintenance_mode') else "✅ OFF"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ Function Settings", callback_data="admin_functions", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("💰 Price Settings", callback_data="admin_prices", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🎥 Welcome Video", callback_data="admin_video", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🛠 Maintenance", callback_data="admin_maintenance", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Off Messages", callback_data="admin_off_msgs", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🎫 Create Redeem Code", callback_data="admin_create_redeem", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("💵 Add Balance", callback_data="admin_add_balance", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🔍 Check/Manage Balance", callback_data="admin_check_balance", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("📊 User List", callback_data="admin_user_list", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🔥 Pro+ Settings", callback_data="admin_pro_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🎁 Refer Settings", callback_data="admin_refer_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("📢 Channel Check", callback_data="admin_channel_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("📤 Refer Post Settings", callback_data="admin_refer_post_settings", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🤖 Auto Like Admin", callback_data="admin_autolike_admin", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("📦 Auto Like Packages", callback_data="admin_autolike_packages", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🔘 Auto Like Buttons", callback_data="admin_autolike_buttons", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("🔙 Close", callback_data="cancel_order", style="default", icon_custom_emoji_id="5771449289972650710")
    )

    try:
        edit_premium(call.message.chat.id, call.message.message_id, [
            ("crown", "👑"), " ADMIN PANEL\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            ("user", "👥"), f" Total Users: {total_users}\n",
            ("coins", "💰"), f" Total Deposits: ৳{total_deposits}\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            f"🔥 Daily: {d_enabled}  ⭐ Auto: {a_enabled}\n",
            f"💰 Money: {m_enabled}  🛠 Maintenance: {mm}\n",
            "━━━━━━━━━━━━━━━━━━━"
        ], reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_pro_settings")
def admin_pro_settings(call):
    if call.from_user.id != ADMIN_ID: return

    p_status = "✅ ON" if is_enabled('pro_like_enabled') else "❌ OFF"
    pro_price = get_setting('pro_like_price')
    remaining, limit = get_pro_like_remaining()

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Toggle: {p_status}", callback_data="toggle_pro_like", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Change Price", callback_data="change_pro_price", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Daily Limit", callback_data="change_pro_limit", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Change Off Msg", callback_data="change_pro_off_msg", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("fire", "🔥"), " DAILY LIKE PRO+ SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Status: {p_status}\n",
        f"Price: ৳{pro_price}\n",
        f"Daily Limit: {limit} (Remaining Today: {remaining})\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_pro_like")
def toggle_pro_like(call):
    if call.from_user.id != ADMIN_ID: return
    current = is_enabled('pro_like_enabled')
    set_setting('pro_like_enabled', 'off' if current else 'on')
    bot.answer_callback_query(call.id, f"✅ {'Disabled' if current else 'Enabled'}!")
    admin_pro_settings(call)

@bot.callback_query_handler(func=lambda call: call.data == "change_pro_price")
def change_pro_price(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new Pro+ Price (BDT):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_pro_price_change)

def process_pro_price_change(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.strip())
        set_setting('pro_like_price', str(val))
        bot.send_message(ADMIN_ID, f"✅ Pro+ Price updated to ৳{val}")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

@bot.callback_query_handler(func=lambda call: call.data == "change_pro_limit")
def change_pro_limit(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new Daily Limit for Pro+ (e.g., 30):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_pro_limit_change)

def process_pro_limit_change(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = int(message.text.strip())
        set_setting('pro_like_daily_limit', str(val))
        bot.send_message(ADMIN_ID, f"✅ Daily Limit updated to {val}")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

@bot.callback_query_handler(func=lambda call: call.data == "change_pro_off_msg")
def change_pro_off_msg(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new Off message for Pro+:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_pro_off_msg)

def process_pro_off_msg(message):
    if message.from_user.id != ADMIN_ID: return
    set_setting('pro_like_off_msg', message.text)
    bot.send_message(ADMIN_ID, "✅ Off message updated!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_refer_settings")
def admin_refer_settings(call):
    if call.from_user.id != ADMIN_ID: return

    r_status = "✅ ON" if is_enabled('refer_enabled') else "❌ OFF"
    bonus = get_setting('refer_signup_bonus')
    percent = get_setting('refer_deposit_percent')

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Toggle: {r_status}", callback_data="toggle_refer", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Signup Bonus", callback_data="change_refer_bonus", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Deposit %", callback_data="change_refer_percent", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("gift", "🎁"), " REFER & EARN SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Status: {r_status}\n",
        f"Signup Bonus: ৳{bonus}\n",
        f"Deposit Commission: {percent}% (প্রতি ১০ টাকায়)\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_refer")
def toggle_refer(call):
    if call.from_user.id != ADMIN_ID: return
    current = is_enabled('refer_enabled')
    set_setting('refer_enabled', 'off' if current else 'on')
    bot.answer_callback_query(call.id, f"✅ {'Disabled' if current else 'Enabled'}!")
    admin_refer_settings(call)

@bot.callback_query_handler(func=lambda call: call.data == "change_refer_bonus")
def change_refer_bonus(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new Signup Bonus (BDT):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_refer_bonus_change)

def process_refer_bonus_change(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.strip())
        set_setting('refer_signup_bonus', str(val))
        bot.send_message(ADMIN_ID, f"✅ Signup Bonus updated to ৳{val}")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

@bot.callback_query_handler(func=lambda call: call.data == "change_refer_percent")
def change_refer_percent(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new Deposit Commission % (প্রতি ১০ টাকায়):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_refer_percent_change)

def process_refer_percent_change(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.strip())
        set_setting('refer_deposit_percent', str(val))
        bot.send_message(ADMIN_ID, f"✅ Deposit Commission updated to {val}%")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_channel_settings")
def admin_channel_settings(call):
    if call.from_user.id != ADMIN_ID: return

    ch1 = get_setting('channel_1')
    ch2 = get_setting('channel_2')
    enabled = "✅ ON" if is_enabled('channel_check_enabled') else "❌ OFF"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Toggle: {enabled}", callback_data="toggle_channel_check", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Channel 1", callback_data="change_channel_1", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Channel 2", callback_data="change_channel_2", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("link", "🔗"), " CHANNEL CHECK SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Status: {enabled}\n",
        f"Channel 1: {ch1}\n",
        f"Channel 2: {ch2}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["change_channel_1", "change_channel_2"])
def change_channel(call):
    if call.from_user.id != ADMIN_ID: return
    key = "channel_1" if call.data == "change_channel_1" else "channel_2"
    label = "Channel 1" if key == "channel_1" else "Channel 2"

    msg = bot.edit_message_text(f"📝 Enter {label} URL:\n(Example: https://t.me/username)", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_channel_change, key)

def process_channel_change(message, key):
    if message.from_user.id != ADMIN_ID: return
    url = message.text.strip()
    if url.startswith('https://t.me/') or url.startswith('@'):
        set_setting(key, url)
        bot.send_message(ADMIN_ID, f"✅ {key} updated to {url}")
    else:
        bot.send_message(ADMIN_ID, "❌ Invalid channel URL! Use format: https://t.me/username")

@bot.callback_query_handler(func=lambda call: call.data == "admin_refer_post_settings")
def admin_refer_post_settings(call):
    if call.from_user.id != ADMIN_ID: return

    rp_status = "✅ ON" if is_enabled('refer_post_enabled') else "❌ OFF"
    dp_status = "✅ ON" if is_enabled('deposit_post_enabled') else "❌ OFF"
    group_id = get_setting('refer_post_group')

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Refer Post: {rp_status}", callback_data="toggle_refer_post", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton(f"Deposit Post: {dp_status}", callback_data="toggle_deposit_post", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("✏️ Group ID", callback_data="change_refer_group", style="primary", icon_custom_emoji_id="5902432207519093015"),
        InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("broadcast", "📤"), " REFER POST SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Refer Post: {rp_status}\n",
        f"Deposit Post: {dp_status}\n",
        f"Group ID: {group_id}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["toggle_refer_post", "toggle_deposit_post"])
def toggle_post(call):
    if call.from_user.id != ADMIN_ID: return
    key = "refer_post_enabled" if call.data == "toggle_refer_post" else "deposit_post_enabled"
    current = is_enabled(key)
    set_setting(key, "off" if current else "on")
    bot.answer_callback_query(call.id, f"✅ {'Disabled' if current else 'Enabled'}!")
    admin_refer_post_settings(call)

@bot.callback_query_handler(func=lambda call: call.data == "change_refer_group")
def change_refer_group(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter Group ID:\n(Example: -1001234567890)", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_group_change)

def process_group_change(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        group_id = int(message.text.strip())
        set_setting('refer_post_group', str(group_id))
        bot.send_message(ADMIN_ID, f"✅ Group ID updated to {group_id}")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid Group ID! Must be a number.")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast(call):
    if call.from_user.id != ADMIN_ID: return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ CONTINUE", callback_data="broadcast_continue", style="success", icon_custom_emoji_id="5893224751119208859"),
        InlineKeyboardButton("❌ CANCEL", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907")
    )

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("broadcast", "📢"), " BROADCAST SYSTEM\n",
        "━━━━━━━━━━━━━━━━━━━\n\n",
        ("warn", "⚠️"), " আপনি কি সত্যিই সব ইউজারের কাছে মেসেজ পাঠাতে চান?\n\n",
        ("user", "👥"), f" Total Users: {total_users}\n",
        ("robot", "🤖"), " Bot: @FFX_LIKEBD_BOT\n\n",
        ("checkmark", "✅"), " CONTINUE চাপলে মেসেজ টাইপ করতে বলবে।\n",
        ("cross", "❌"), " CANCEL চাপলে বাতিল হবে।\n\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_continue")
def broadcast_continue(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text(
        "📢 এখন আপনার ব্রডকাস্ট মেসেজ পাঠান।\n\n"
        "✅ আপনি যা পাঠাবেন (টেক্সট, ছবি, ভিডিও, প্রিমিয়াম ইমোজি সহ) — ঠিক সেভাবেই সব ইউজারের কাছে যাবে।\n\n"
        "❌ বাতিল করতে /cancel লিখুন বা BACK চাপুন।",
        call.message.chat.id,
        call.message.message_id
    )
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.text and message.text.strip().lower() == "/cancel":
        bot.send_message(ADMIN_ID, "❌ Broadcast cancelled.")
        return

    broadcast_msg = message
    admin_chat_id = message.chat.id

    try:
        bot.send_message(admin_chat_id, "🚀 Broadcast started in background...")
    except:
        pass

    def send_broadcast_worker():
        try:
            conn = sqlite3.connect('freefirelk_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            conn.close()

            success = 0
            failed = 0

            for user_row in users:
                uid = user_row[0]
                try:
                    bot.copy_message(
                        chat_id=uid,
                        from_chat_id=broadcast_msg.chat.id,
                        message_id=broadcast_msg.message_id
                    )
                    success += 1
                except Exception as e:
                    failed += 1
                    print(f"Broadcast failed for {uid}: {e}")

                time.sleep(0.05)

            try:
                send_premium(ADMIN_ID, [
                    ("checkmark", "✅"), " BROADCAST COMPLETED!\n",
                    "━━━━━━━━━━━━━━━━━━━\n",
                    ("user", "👥"), f" Total: {len(users)}\n",
                    ("checkmark", "✅"), f" Success: {success}\n",
                    ("cross", "❌"), f" Failed: {failed}\n",
                    "━━━━━━━━━━━━━━━━━━━"
                ])
            except Exception as e:
                print(f"Admin notify error: {e}")

        except Exception as e:
            print(f"Broadcast worker error: {e}")
            try:
                bot.send_message(ADMIN_ID, f"❌ Broadcast failed: {e}")
            except:
                pass

    threading.Thread(target=send_broadcast_worker, daemon=True).start()

@bot.callback_query_handler(func=lambda call: call.data == "admin_create_redeem")
def admin_create_redeem(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("🎫 Format: CODE AMOUNT\nExample: FREEFIRE50 50", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_create_redeem)

def process_create_redeem(message):
    if message.from_user.id != ADMIN_ID: return

    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(ADMIN_ID, "❌ Format: CODE AMOUNT")
        return

    code, amount = parts
    try:
        amount = float(amount)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, created_by, created_date) VALUES (?, ?, ?, ?)",
                      (code, amount, ADMIN_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        send_premium(ADMIN_ID, [
            ("checkmark", "✅"), f" Code: {code}\n",
            ("coins", "💰"), f" Amount: ৳{amount}"
        ])
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid amount!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_balance")
def admin_add_balance(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("💵 Format: USER_ID AMOUNT\nExample: 123456 50", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_add_balance_admin)

def process_add_balance_admin(message):
    if message.from_user.id != ADMIN_ID: return

    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(ADMIN_ID, "❌ Format: USER_ID AMOUNT")
        return

    target_id, amount = parts
    try:
        target_id = int(target_id)
        amount = float(amount)
        update_balance(target_id, amount)
        send_premium(ADMIN_ID, [
            ("checkmark", "✅"), f" Added ৳{amount} to user {target_id}"
        ])
        try:
            send_premium(target_id, [
                ("coins", "💰"), f" ৳{amount} added by admin!"
            ])
        except:
            pass
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid input!")

# ==================== ADMIN: CHECK / MANAGE USER BALANCE ====================
@bot.callback_query_handler(func=lambda call: call.data == "admin_check_balance")
def admin_check_balance(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("🔍 Enter the User ID to check their balance:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_check_balance_uid)

def process_check_balance_uid(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.strip())
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid User ID!")
        return
    user = get_user(target_id)
    if not user:
        bot.send_message(ADMIN_ID, "❌ User not found!")
        return
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("➕ ADD", callback_data=f"bal_add_{target_id}"),
        InlineKeyboardButton("➖ REMOVE", callback_data=f"bal_remove_{target_id}"),
        InlineKeyboardButton("✏️ SET", callback_data=f"bal_set_{target_id}")
    )
    markup.add(InlineKeyboardButton("BACK", callback_data="admin_back"))
    send_premium(ADMIN_ID, [
        ("user", "👤"), f" User: {user['full_name']} (@{user['username']})\n",
        ("shield", "🆔"), f" ID: {target_id}\n",
        ("coins", "💰"), f" Current Balance: ৳{user['balance']}\n"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("bal_add_") or call.data.startswith("bal_remove_") or call.data.startswith("bal_set_"))
def bal_action(call):
    if call.from_user.id != ADMIN_ID: return
    action, target_id = call.data.rsplit("_", 1)
    label_map = {"bal_add": "ADD", "bal_remove": "REMOVE", "bal_set": "SET"}
    msg = bot.edit_message_text(f"📝 Enter the amount to {label_map[action]}:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_bal_amount, action, target_id)

def process_bal_amount(message, action, target_id):
    if message.from_user.id != ADMIN_ID: return
    try:
        amount = float(message.text.strip())
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid amount!")
        return
    target_id = int(target_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    if action == "bal_add":
        refund_balance(target_id, amount)
        note = f"Added ৳{amount}"
    elif action == "bal_remove":
        cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id=?", (amount, target_id))
        conn.commit()
        note = f"Removed ৳{amount}"
    else:
        cursor.execute("UPDATE users SET balance = ? WHERE user_id=?", (amount, target_id))
        conn.commit()
        note = f"Set balance to ৳{amount}"
    user = get_user(target_id)
    bot.send_message(ADMIN_ID, f"✅ {note}. New Balance: ৳{user['balance']}")
    try:
        bot.send_message(target_id, f"💰 Your balance has been updated by admin. New Balance: ৳{user['balance']}")
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_list")
def admin_user_list(call):
    if call.from_user.id != ADMIN_ID: return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, balance, join_date FROM users ORDER BY join_date DESC LIMIT 20")
    users = cursor.fetchall()

    segments = [("chart", "📊"), " USER LIST\n", "━━━━━━━━━━━━━━━━━━━\n\n"]
    for i, user in enumerate(users, 1):
        segments.append(f"{i}. 👤 {user[0]} | @{user[1]}\n💰 ৳{user[2]}\n📅 {user[3]}\n\n")
    segments.append("━━━━━━━━━━━━━━━━━━━")

    try:
        edit_premium(call.message.chat.id, call.message.message_id, segments)
    except:
        text = "📊 USER LIST\n━━━━━━━━━━━━━━━━━━━\n\n"
        for i, user in enumerate(users, 1):
            text += f"{i}. 👤 {user[0]} | @{user[1]}\n💰 ৳{user[2]}\n📅 {user[3]}\n\n"
        text += "━━━━━━━━━━━━━━━━━━━"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_settings")
def admin_settings(call):
    if call.from_user.id != ADMIN_ID: return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("BACK", callback_data="admin_back", style="danger", icon_custom_emoji_id="5420274119398669907"))

    edit_premium(call.message.chat.id, call.message.message_id, [
        ("settings", "⚙️"), " SETTINGS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        ("gem", "💎"), f" Daily Like Price: ৳{get_setting('daily_like_price')}\n",
        ("chart", "📈"), f" Daily Like Amount: {get_setting('daily_like_amount')}\n",
        ("robot", "🤖"), f" Bot Username: @{BOT_USERNAME}\n",
        ("robot", "🤖"), f" Status: {get_setting('bot_status')}\n",
        ("money", "💳"), f" Gateway: ZRPAYBD Pay (No Webhook)\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

# ==================== ADMIN: AUTO LIKE ADMIN ====================
@bot.callback_query_handler(func=lambda call: call.data == "admin_autolike_admin")
def admin_autolike_admin(call):
    if call.from_user.id != ADMIN_ID: return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM auto_likes WHERE status='active'")
    active_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM auto_likes WHERE status='active' AND admin_status='suspended'")
    suspended_count = cursor.fetchone()[0]

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📋 View All Active (latest 20)", callback_data="al_admin_view"),
        InlineKeyboardButton("🔍 Search / Manage by Record ID", callback_data="al_admin_search"),
        InlineKeyboardButton("BACK", callback_data="admin_back")
    )
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("robot", "🤖"), " AUTO LIKE ADMIN\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"Active Accounts: {active_count}\n",
        f"Suspended: {suspended_count}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "al_admin_view")
def al_admin_view(call):
    if call.from_user.id != ADMIN_ID: return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auto_likes WHERE status='active' ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    if not rows:
        bot.answer_callback_query(call.id, "No active accounts.", show_alert=True)
        return
    text = "📋 ACTIVE AUTO LIKE ACCOUNTS (latest 20)\n\n"
    for r in rows:
        astatus = r['admin_status'] or 'active'
        text += f"ID:{r['id']} | UID:{r['uid']} | User:{r['user_id']} | {astatus} | Exp:{r['expiry_date']}\n"
    text += "\nUse 'Search / Manage by Record ID' to Suspend/Restore/Remove a specific account."
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("BACK", callback_data="admin_autolike_admin"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "al_admin_search")
def al_admin_search(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("🔍 Send the Auto Like record ID (from the list) to manage it:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, al_admin_search_process)

def al_admin_search_process(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        record_id = int(message.text.strip())
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid ID!")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auto_likes WHERE id=?", (record_id,))
    row = cursor.fetchone()
    if not row:
        bot.send_message(ADMIN_ID, "❌ Record not found!")
        return
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("⏸ Suspend", callback_data=f"alact_suspend_{record_id}"),
        InlineKeyboardButton("▶️ Restore", callback_data=f"alact_restore_{record_id}"),
        InlineKeyboardButton("🗑 Remove", callback_data=f"alact_remove_{record_id}")
    )
    send_premium(ADMIN_ID, [
        ("shield", "🆔"), f" Record ID: {row['id']}\n",
        ("user", "👤"), f" User: {row['user_id']}\n",
        ("gamepad", "🎮"), f" UID: {row['uid']}\n",
        ("crown", "👑"), f" Name: {row['account_name'] or 'N/A'}\n",
        ("globe", "🌐"), f" Region: {row['server_name']}\n",
        ("calendar", "📅"), f" Expires: {row['expiry_date']}\n",
        ("settings", "⚙️"), f" Admin Status: {row['admin_status'] or 'active'}\n"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("alact_"))
def al_admin_action(call):
    if call.from_user.id != ADMIN_ID: return
    _, action, record_id = call.data.split("_", 2)
    conn = get_db_connection()
    cursor = conn.cursor()
    if action == "suspend":
        cursor.execute("UPDATE auto_likes SET admin_status='suspended' WHERE id=?", (record_id,))
        bot.answer_callback_query(call.id, "✅ Suspended!", show_alert=True)
    elif action == "restore":
        cursor.execute("UPDATE auto_likes SET admin_status='active' WHERE id=?", (record_id,))
        bot.answer_callback_query(call.id, "✅ Restored!", show_alert=True)
    elif action == "remove":
        cursor.execute("UPDATE auto_likes SET status='removed' WHERE id=?", (record_id,))
        bot.answer_callback_query(call.id, "✅ Removed!", show_alert=True)
    conn.commit()

# ==================== ADMIN: AUTO LIKE PACKAGES ====================
@bot.callback_query_handler(func=lambda call: call.data == "admin_autolike_packages")
def admin_autolike_packages(call):
    if call.from_user.id != ADMIN_ID: return
    packages = get_all_packages()
    text = "📦 AUTO LIKE PACKAGES\n\n"
    markup = InlineKeyboardMarkup(row_width=1)
    for p in packages:
        status = "✅ ON" if p['enabled'] else "❌ OFF"
        text += f"{p['package_id']} | {p['category'].upper()} | {p['days']}D | ৳{p['price']} | {p['likes_amount']}+ | {status}\n"
        markup.add(InlineKeyboardButton(f"Manage {p['package_id']}", callback_data=f"pkg_manage_{p['package_id']}"))
    markup.add(InlineKeyboardButton("BACK", callback_data="admin_back"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_manage_"))
def pkg_manage(call):
    if call.from_user.id != ADMIN_ID: return
    package_id = call.data.replace("pkg_manage_", "")
    p = get_package(package_id)
    if not p:
        bot.answer_callback_query(call.id, "Not found!", show_alert=True)
        return
    status = "✅ ON" if p['enabled'] else "❌ OFF"
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Toggle: {status}", callback_data=f"pkg_toggle_{package_id}"),
        InlineKeyboardButton("✏️ Price", callback_data=f"pkg_price_{package_id}"),
        InlineKeyboardButton("✏️ Duration", callback_data=f"pkg_days_{package_id}"),
        InlineKeyboardButton("✏️ Likes Amount", callback_data=f"pkg_likes_{package_id}"),
        InlineKeyboardButton("BACK", callback_data="admin_autolike_packages")
    )
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("gem", "💎"), f" {package_id}\n",
        f"Category: {p['category']}\nDays: {p['days']}\nPrice: ৳{p['price']}\nLikes: {p['likes_amount']}+\nStatus: {status}"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_toggle_"))
def pkg_toggle(call):
    if call.from_user.id != ADMIN_ID: return
    package_id = call.data.replace("pkg_toggle_", "")
    p = get_package(package_id)
    set_package_field(package_id, "enabled", 0 if p['enabled'] else 1)
    bot.answer_callback_query(call.id, "✅ Updated!")
    pkg_manage(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_price_") or call.data.startswith("pkg_days_") or call.data.startswith("pkg_likes_"))
def pkg_edit_field(call):
    if call.from_user.id != ADMIN_ID: return
    if call.data.startswith("pkg_price_"):
        package_id = call.data.replace("pkg_price_", "")
        field, label = "price", "new Price (BDT)"
    elif call.data.startswith("pkg_days_"):
        package_id = call.data.replace("pkg_days_", "")
        field, label = "days", "new Duration (days)"
    else:
        package_id = call.data.replace("pkg_likes_", "")
        field, label = "likes_amount", "new Likes Amount"
    msg = bot.edit_message_text(f"📝 Enter {label} for {package_id}:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, pkg_edit_field_process, package_id, field)

def pkg_edit_field_process(message, package_id, field):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.strip()) if field == "price" else int(message.text.strip())
        set_package_field(package_id, field, val)
        bot.send_message(ADMIN_ID, f"✅ {field} updated for {package_id}!")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

# ==================== ADMIN: AUTO LIKE BUTTON TOGGLES ====================
@bot.callback_query_handler(func=lambda call: call.data == "admin_autolike_buttons")
def admin_autolike_buttons(call):
    if call.from_user.id != ADMIN_ID: return
    buy_s = "✅ ON" if is_enabled('buy_auto_like_enabled') else "❌ OFF"
    rem_s = "✅ ON" if is_enabled('remove_uid_enabled') else "❌ OFF"
    chg_s = "✅ ON" if is_enabled('change_uid_enabled') else "❌ OFF"
    chk_s = "✅ ON" if is_enabled('check_uids_enabled') else "❌ OFF"
    fee = get_setting('uid_change_fee')

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"Buy: {buy_s}", callback_data="toggle_buy_auto_like"),
        InlineKeyboardButton(f"Remove: {rem_s}", callback_data="toggle_remove_uid"),
        InlineKeyboardButton(f"Change: {chg_s}", callback_data="toggle_change_uid"),
        InlineKeyboardButton(f"Check: {chk_s}", callback_data="toggle_check_uids"),
        InlineKeyboardButton("✏️ Change UID Fee", callback_data="change_uid_fee"),
        InlineKeyboardButton("BACK", callback_data="admin_back")
    )
    edit_premium(call.message.chat.id, call.message.message_id, [
        ("settings", "🔘"), " AUTO LIKE BUTTON CONTROLS\n",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"⭐ Buy Auto Like: {buy_s}\n",
        f"🗑 Remove UID: {rem_s}\n",
        f"🔄 Change UID: {chg_s}\n",
        f"📋 Check My UIDs: {chk_s}\n",
        f"💰 Change UID Fee: ৳{fee}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["toggle_buy_auto_like", "toggle_remove_uid", "toggle_change_uid", "toggle_check_uids"])
def toggle_autolike_button(call):
    if call.from_user.id != ADMIN_ID: return
    key_map = {
        "toggle_buy_auto_like": "buy_auto_like_enabled",
        "toggle_remove_uid": "remove_uid_enabled",
        "toggle_change_uid": "change_uid_enabled",
        "toggle_check_uids": "check_uids_enabled",
    }
    key = key_map[call.data]
    current = is_enabled(key)
    set_setting(key, "off" if current else "on")
    bot.answer_callback_query(call.id, f"✅ {'Disabled' if current else 'Enabled'}!")
    admin_autolike_buttons(call)

@bot.callback_query_handler(func=lambda call: call.data == "change_uid_fee")
def change_uid_fee(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.edit_message_text("📝 Enter new UID Change Fee (BDT):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_uid_fee_change)

def process_uid_fee_change(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.strip())
        set_setting('uid_change_fee', str(val))
        bot.send_message(ADMIN_ID, f"✅ UID Change Fee updated to ৳{val}")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid value!")

@bot.message_handler(commands=['redeem'])
def redeem_code(message):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, "🎫 Enter redeem code:")
    bot.register_next_step_handler(msg, process_redeem)

def process_redeem(message):
    user_id = message.from_user.id
    code = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM redeem_codes WHERE code=? AND is_used=0", (code,))
    redeem = cursor.fetchone()

    if redeem:
        cursor.execute("UPDATE redeem_codes SET is_used=1, used_by=? WHERE code=?", (user_id, code))
        update_balance(user_id, redeem['amount'])
        conn.commit()
        user = get_user(user_id)
        send_premium(user_id, [
            ("checkmark", "✅"), f" Redeemed ৳{redeem['amount']}!\n",
            ("coins", "💰"), f" Balance: ৳{user['balance']}"
        ])
    else:
        bot.send_message(user_id, "❌ Invalid or used code!")

# ==================== AUTO LIKE DAILY DELIVERY ====================
def process_auto_likes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM auto_likes WHERE status='active'")
        active_autos = cursor.fetchall()

        for auto in active_autos:
            try:
                user_id = auto['user_id']
                uid = auto['uid']
                server = auto['server_name']
                admin_status = auto['admin_status'] or 'active'
                category = auto['category'] or 'standard'
                account_name = auto['account_name'] or 'N/A'

                if admin_status == 'suspended':
                    continue

                expiry = datetime.strptime(auto['expiry_date'], "%Y-%m-%d") if auto['expiry_date'] else None

                if expiry and datetime.now() > expiry:
                    cursor.execute("UPDATE auto_likes SET status='expired' WHERE id=?", (auto['id'],))
                    conn.commit()
                    continue

                # fflikebd API — same endpoint for all categories
                result = call_like_api(uid, server, DEFAULT_PKGORDER)

                bangladesh_time = datetime.now().astimezone(timezone(timedelta(hours=6))).strftime("%Y-%m-%d %I:%M:%S %p")

                post_segments = [
                    ("robot", "🤖"), " AUTO LIKE DELIVERY\n",
                    "━━━━━━━━━━━━━━━━━━━\n",
                    ("user", "👤"), f" User: {user_id}\n",
                    ("shield", "🆔"), f" User ID: {user_id}\n",
                    ("gamepad", "🎮"), f" UID: {uid}\n",
                    ("crown", "👑"), f" Name: {account_name}\n",
                    ("globe", "🌍"), f" Server: {server.upper()}\n",
                    ("gift", "📦"), f" Package: {category.upper()}\n",
                    ("chart", "📊"), " STATUS:\n"
                ]

                if result.get("error") in ["timeout", "network_error", "unknown"]:
                    post_segments.append(("cross", "❌"), " API Error")
                elif result.get("status") == 1:
                    post_segments.append(f"✅ Success\n📈 {result.get('LikesBeforeCommand', 0)} → {result.get('LikesAfterCommand', 0)}")
                    post_segments.append(f"\n🔄 Given: {result.get('LikesGivenByAPI', 0)}")
                    post_segments.append(f"\n🔑 Order: {result.get('OrderNo', 'N/A')}")
                elif result.get("status") == 2:
                    post_segments.append(f"⚠️ Already Liked Today\n📈 Current: {result.get('LikesAfterCommand', 0)}")
                    post_segments.append(f"\n💰 Refunded: ৳{result.get('Refunded', 0)}")
                else:
                    post_segments.append(f"❌ Failed\nReason: {result.get('message', 'Unknown')}")

                post_segments.append(f"\n🕐 Time: {bangladesh_time} (BDT)")

                try:
                    send_premium(CHANNEL_ID, post_segments)
                except:
                    pass

                time.sleep(1)

            except Exception as e:
                print(f"Error processing auto like: {e}")
    except Exception as e:
        print(f"Auto like scheduler error: {e}")

def run_scheduler():
    schedule.every().day.at("04:00").do(process_auto_likes)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════╗
║  🤖 FIRE LIKE BOT PRO v8.0     ║
╠══════════════════════════════════╣
║  ✅ fflikebd.site API          ║
║  ✅ ZRPAYBD Direct Return      ║
║  ✅ All Features Intact        ║
║  ✅ Flask-Free                 ║
╚══════════════════════════════════╝
    """)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    print("✅ Scheduler started!")
    print("📱 Bot is ready!")
    print("💳 API: https://www.fflikebd.site/ghostxlike")

    while True:
        try:
            bot.polling(non_stop=True, timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(10)
            
            
# LEAKED BY @mhxffv111