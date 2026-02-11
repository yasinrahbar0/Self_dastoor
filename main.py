import os, json, asyncio, threading, glob, importlib, random
from datetime import datetime
from collections import defaultdict
from flask import Flask
from telethon import TelegramClient, events, Button, functions
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from googletrans import Translator

# ========= ENV =========
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
LOG_CHAT = int(os.getenv("LOG_CHAT", 0))

# ========= FLASK =========
app = Flask(__name__)
@app.route("/")
def home():
    return "Ultimate Modular Userbot Running 🔥"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# ========= CLIENT =========
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
translator = Translator()

# ========= SETTINGS =========
SETTINGS_FILE = "settings.json"
BACKUP_FILE = "backup_settings.json"

if not os.path.exists(SETTINGS_FILE):
    json.dump({}, open(SETTINGS_FILE, "w", encoding="utf-8"))

try:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
except Exception:
    settings = {}

settings.setdefault("style", {"bold": False, "italic": False, "code": False, "quote": False})
settings.setdefault("god", False)
settings.setdefault("autoreply", False)
settings.setdefault("antidelete", False)
settings.setdefault("invisible", False)
settings.setdefault("lock", True)
settings.setdefault("spam_limit", 5)
settings.setdefault("spam_time", 5)
settings.setdefault("keywords", {})
settings.setdefault("pass", "")

user_spam = defaultdict(list)
group_stats = defaultdict(int)

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def is_owner(e):
    if e.sender_id != OWNER_ID:
        return False
    if settings["pass"]:
        if not e.text or not e.text.startswith(f".{settings['pass']}"):
            return False
    return True

def get_real_text(text):
    if not settings["pass"]:
        return text
    prefix = f".{settings['pass']}"
    if text.startswith(prefix):
        return text[len(prefix):].strip()
    return text

def apply_style(text):
    if not text:
        return text
    if settings["style"]["bold"]:
        text = f"**{text}**"
    if settings["style"]["italic"]:
        text = f"__{text}__"
    if settings["style"]["code"]:
        text = f"`{text}`"
    if settings["style"]["quote"]:
        text = f"> {text}"
    return text

# ========= STYLE HANDLER =========
@client.on(events.NewMessage(outgoing=True))
async def style_handler(e):
    if not e.text or e.text.startswith("."):
        return
    styled = apply_style(e.text)
    if styled != e.text:
        await e.edit(styled)

# ========= HELP =========
@client.on(events.NewMessage(pattern=r"\.help"))
async def help_cmd(e):
    if not is_owner(e):
        return
    msg = """
🔥 Ultimate Modular Userbot 🔥

📌 Styles:
.bold on/off → فعال/غیر فعال کردن بولد
.italic on/off → فعال/غیر فعال کردن ایتالیک
.code on/off → فعال/غیر فعال کردن کد
.quote on/off → فعال/غیر فعال کردن نقل قول

🌍 Translate:
.tr <lang> → ترجمه پیام ریپلای‌شده

⚡ Modes:
.god on/off → پاسخ خودکار سلطنتی
.autoreply on/off → پاسخ خودکار ساده
.antidelete on/off → جلوگیری از حذف پیام
.invisible on/off → Seen نخوردن و مخفی بودن
.lock on/off → قفل کردن دستورات فقط برای OWNER

🛡 Security:
.spam <limit> <time> → کنترل اسپم کاربران
.clean <count> → حذف پیام‌های ارسال‌شده خودت
.stats → تعداد پیام‌های این چت

🧠 Keyword Replies:
.addreply key=value → اضافه کردن پاسخ خودکار
.delreply key → حذف پاسخ خودکار

💾 Media:
.save → ذخیره فایل نابودشونده

🎛 Management:
.panel → باز کردن پنل مدیریتی
.backup → بکاپ تنظیمات
.restore → ریستور تنظیمات
.setpass <password> → گذاشتن رمز برای دستورات
"""
    await e.reply(msg)

# ========= STYLE =========
@client.on(events.NewMessage(pattern=r"\.(bold|italic|code|quote) (on|off)"))
async def toggle_style(e):
    if not is_owner(e):
        return
    cmd, state = e.pattern_match.groups()
    settings["style"][cmd] = state == "on"
    save_settings()
    await e.reply(f"{cmd} => {state}")

# ========= TRANSLATE =========
@client.on(events.NewMessage(pattern=r"\.tr (.+)"))
async def translate_cmd(e):
    if not is_owner(e):
        return
    lang = e.pattern_match.group(1)
    if not e.reply_to_msg_id:
        return await e.reply("Reply to message")
    msg = await e.get_reply_message()
    if not msg or not msg.text:
        return await e.reply("Message has no text")
    try:
        # translator.translate is sync, but we are in async.
        # Ideally use a threadpool or an async translator.
        result = await asyncio.to_thread(translator.translate, msg.text, dest=lang)
        await e.reply(result.text)
    except Exception as ex:
        await e.reply(f"Translation Error: {str(ex)}")

# ========= MODES =========
@client.on(events.NewMessage(pattern=r"\.(god|autoreply|antidelete|invisible|lock) (on|off)"))
async def toggle_modes(e):
    if not is_owner(e):
        return
    cmd, state = e.pattern_match.groups()
    state = state == "on"
    settings[cmd] = state
    save_settings()
    await e.reply(f"{cmd} => {'ON' if state else 'OFF'}")

# ========= SPAM CONTROL =========
@client.on(events.NewMessage(incoming=True))
async def spam_control(e):
    if e.sender_id == OWNER_ID:
        return
    now = datetime.now().timestamp()
    user_spam[e.sender_id] = [t for t in user_spam[e.sender_id] if now - t < settings["spam_time"]]
    user_spam[e.sender_id].append(now)
    if len(user_spam[e.sender_id]) > settings["spam_limit"]:
        await e.delete()

@client.on(events.NewMessage(pattern=r"\.spam (\d+) (\d+)"))
async def set_spam(e):
    if not is_owner(e):
        return
    settings["spam_limit"] = int(e.pattern_match.group(1))
    settings["spam_time"] = int(e.pattern_match.group(2))
    save_settings()
    await e.reply("Spam control updated")

# ========= CLEANER =========
@client.on(events.NewMessage(pattern=r"\.clean (\d+)"))
async def cleaner(e):
    if not is_owner(e):
        return
    count = int(e.pattern_match.group(1))
    async for msg in client.iter_messages(e.chat_id, limit=count):
        if msg.out:
            await msg.delete()

# ========= STATS =========
@client.on(events.NewMessage(pattern=r"\.stats"))
async def stats_cmd(e):
    if not is_owner(e):
        return
    count = group_stats[e.chat_id]
    await e.reply(f"Messages in this chat: {count}")

@client.on(events.NewMessage(incoming=True))
async def stats_counter(e):
    group_stats[e.chat_id] += 1

# ========= KEYWORD REPLY =========
@client.on(events.NewMessage(pattern=r"\.addreply (.+)"))
async def add_reply(e):
    if not is_owner(e):
        return
    data = e.pattern_match.group(1)
    if "=" not in data:
        return
    k, v = data.split("=", 1)
    settings["keywords"][k.strip()] = v.strip()
    save_settings()
    await e.reply("Reply added")

@client.on(events.NewMessage(pattern=r"\.delreply (.+)"))
async def del_reply(e):
    if not is_owner(e):
        return
    k = e.pattern_match.group(1)
    settings["keywords"].pop(k, None)
    save_settings()
    await e.reply("Reply deleted")

@client.on(events.NewMessage(incoming=True))
async def keyword_auto(e):
    if not e.text:
        return
    for k, v in settings["keywords"].items():
        if k in e.text:
            await e.reply(v)

# ========= SAVE SELF-DESTRUCT FILE =========
@client.on(events.NewMessage(pattern=r"\.save"))
async def save_media(e):
    if not is_owner(e):
        return
    if not e.reply_to_msg_id:
        return await e.reply("Reply to self-destruct media")
    msg = await e.get_reply_message()
    if msg and msg.media:
        file = await msg.download_media()
        await client.send_file("me", file)
        await e.reply("Saved to Saved Messages ✅")

# ========= PANEL =========
@client.on(events.NewMessage(pattern=r"\.panel"))
async def panel(e):
    if not is_owner(e):
        return
    await e.respond(
        "⚙️ Control Panel",
        buttons=[
            [Button.inline("God Mode", b"god")],
            [Button.inline("Auto Reply", b"auto")],
            [Button.inline("Invisible", b"invisible")],
            [Button.inline("Status", b"status")]
        ]
    )

@client.on(events.CallbackQuery)
async def callbacks(e):
    if e.sender_id != OWNER_ID:
        return
    data = e.data.decode()
    if data == "god":
        settings["god"] = not settings["god"]
        save_settings()
        await e.answer("God toggled")
    elif data == "auto":
        settings["autoreply"] = not settings["autoreply"]
        save_settings()
        await e.answer("Auto toggled")
    elif data == "invisible":
        settings["invisible"] = not settings["invisible"]
        save_settings()
        await e.answer("Invisible toggled")
    elif data == "status":
        await e.answer("Settings updated", alert=True)

# ========= BACKUP =========
@client.on(events.NewMessage(pattern=r"\.backup"))
async def backup(e):
    if not is_owner(e):
        return
    save_settings()
    await e.reply("Backup saved")

@client.on(events.NewMessage(pattern=r"\.restore"))
async def restore(e):
    if not is_owner(e):
        return
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        settings.update(data)
        save_settings()
        await e.reply("Restored")

# ========= SET PASSWORD =========
@client.on(events.NewMessage(pattern=r"\.setpass (.+)"))
async def setpass(e):
    if not is_owner(e):
        return
    # Note: password is set without the prefix
    new_pass = e.pattern_match.group(1).strip()
    if new_pass == "off":
        settings["pass"] = ""
    else:
        settings["pass"] = new_pass
    save_settings()
    await e.reply(f"Password set to: {settings['pass'] or 'OFF'}")

# ========= GOD MODE =========
@client.on(events.NewMessage(incoming=True))
async def god_mode_func(e):
    if settings["god"] and not e.out:
        if e.is_private:
            await e.reply("👑 Supreme Mode Active")

# ========= AUTO REPLY =========
@client.on(events.NewMessage(incoming=True))
async def auto_reply_func(e):
    if settings["autoreply"] and not e.out:
        if e.is_private:
            await e.reply("⚡ Auto Reply Active")

# ========= ANTI DELETE =========
@client.on(events.MessageDeleted)
async def anti_delete_func(e):
    if settings["antidelete"]:
        for msg_id in e.deleted_ids:
            try:
                await client.send_message(LOG_CHAT, f"🚨 Deleted ID: {msg_id}")
            except Exception:
                pass

# ========= INVISIBLE =========
@client.on(events.NewMessage)
async def invisible_func(e):
    if settings["invisible"] and not e.out:
        try:
            await client(functions.messages.ReadHistoryRequest(peer=e.chat_id, max_id=0))
        except Exception:
            pass

# ========= PLUGIN LOADER =========
if not os.path.exists("plugins"):
    os.mkdir("plugins")

for file in glob.glob("plugins/*.py"):
    name = file.replace("/", ".").replace("\\", ".")[:-3]
    try:
        importlib.import_module(name)
    except Exception as ex:
        print(f"Failed to load plugin {name}: {ex}")

# ========= MAIN =========
async def main():
    await client.start()
    print("🔥 Ultimate Modular Userbot Started")
    await client.run_until_disconnected()

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    asyncio.run(main())
