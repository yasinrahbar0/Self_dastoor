import os, json, asyncio, threading, glob, importlib, random
from datetime import datetime
from collections import defaultdict
from flask import Flask
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

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
    print("--- Starting Flask Server ---")
    app.run(host="0.0.0.0", port=10000)

# ========= CLIENT =========
# We must always have a client instance for decorators to work.
# If SESSION is empty, it will fail later in main() with a clear message.
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

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
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def is_owner(e):
    # Check if sender is owner (either outgoing or matches OWNER_ID)
    is_owner_id = e.out or (e.sender_id and e.sender_id == OWNER_ID)

    if not is_owner_id:
        return False

    if settings["pass"]:
        prefix = f".{settings['pass']}"
        if not e.text or not e.text.startswith(prefix):
            return False
    return True

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
    if not e.text:
        return
    # Don't style commands
    if e.text.startswith("."):
        return
    styled = apply_style(e.text)
    if styled != e.text:
        await e.edit(styled)

# ====== EMOJI TASH ======
DICE_EMOJIS = {
    1: "🎲1️⃣",
    2: "🎲2️⃣",
    3: "🎲3️⃣",
    4: "🎲4️⃣",
    5: "🎲5️⃣",
    6: "🎲6️⃣"
}

# ========= HELP =========
@client.on(events.NewMessage(pattern=r"(^|\s)\.help($|\s)"))
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

⚡ Modes:
.god on/off → پاسخ خودکار سلطنتی
.autoreply on/off → پاسخ خودکار ساده
.antidelete on/off → لاگ آیدی پیام‌های حذف شده
.invisible on/off → حالت روح (Seen نخوردن)
.lock on/off → قفل کردن دستورات فقط برای OWNER

🛡 Security:
.spam <limit> <time> → کنترل اسپم کاربران
.clean <count> → حذف پیام‌های ارسال‌شده خودت
.stats → تعداد پیام‌های این چت

🧠 Keyword Replies:
.addreply key=value → اضافه کردن پاسخ خودکار
.delreply key → حذف پاسخ خودکار

🎲 Dice:
.tas <1-6> → ارسال تاس با عدد دلخواه

💾 Media:
.save → ذخیره فایل نابودشونده

🎛 Management:
.status → نمایش وضعیت تنظیمات
.backup → بکاپ تنظیمات
.restore → ریستور تنظیمات
.setpass <password> → گذاشتن رمز برای دستورات (off برای غیرفعال کردن)
"""
    await e.reply(msg)

# ========= STYLE =========
@client.on(events.NewMessage(pattern=r".*\.(bold|italic|code|quote) (on|off)"))
async def toggle_style(e):
    if not is_owner(e):
        return
    cmd, state = e.pattern_match.groups()
    settings["style"][cmd] = state == "on"
    save_settings()
    await e.reply(f"{cmd} => {state}")

# ========= TAS =========
@client.on(events.NewMessage(pattern=r".*\.tas (\d)"))
async def tas(e):
    if not is_owner(e):
        return
    try:
        number = int(e.pattern_match.group(1))
        if 1 <= number <= 6:
            await e.reply(DICE_EMOJIS[number])
        else:
            await e.reply("عدد باید بین 1 تا 6 باشه 🎲")
    except:
        await e.reply("خطا در دریافت عدد تاس 🎲")

# ========= MODES =========
@client.on(events.NewMessage(pattern=r".*\.(god|autoreply|antidelete|invisible|lock) (on|off)"))
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
    if not e.sender_id or e.sender_id == OWNER_ID or e.out:
        return
    now = datetime.now().timestamp()
    user_spam[e.sender_id] = [t for t in user_spam[e.sender_id] if now - t < settings["spam_time"]]
    user_spam[e.sender_id].append(now)
    if len(user_spam[e.sender_id]) > settings["spam_limit"]:
        await e.delete()

@client.on(events.NewMessage(pattern=r".*\.spam (\d+) (\d+)"))
async def set_spam(e):
    if not is_owner(e):
        return
    settings["spam_limit"] = int(e.pattern_match.group(1))
    settings["spam_time"] = int(e.pattern_match.group(2))
    save_settings()
    await e.reply("Spam control updated")

# ========= CLEANER =========
@client.on(events.NewMessage(pattern=r".*\.clean (\d+)"))
async def cleaner(e):
    if not is_owner(e):
        return
    count = int(e.pattern_match.group(1))
    async for msg in client.iter_messages(e.chat_id, limit=count):
        if msg.out:
            await msg.delete()

# ========= STATS =========
@client.on(events.NewMessage(pattern=r".*\.stats"))
async def stats_cmd(e):
    if not is_owner(e):
        return
    count = group_stats[e.chat_id]
    await e.reply(f"Messages in this chat: {count}")

@client.on(events.NewMessage(incoming=True))
async def stats_counter(e):
    group_stats[e.chat_id] += 1

# ========= KEYWORD REPLY =========
@client.on(events.NewMessage(pattern=r".*\.addreply (.+)"))
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

@client.on(events.NewMessage(pattern=r".*\.delreply (.+)"))
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
@client.on(events.NewMessage(pattern=r".*\.save"))
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
        if os.path.exists(file):
            os.remove(file)

# ========= STATUS =========
@client.on(events.NewMessage(pattern=r".*\.status"))
async def status_cmd(e):
    if not is_owner(e):
        return
    status_text = f"⚙️ **Bot Status:**\n\n"
    status_text += f"God Mode: {'ON' if settings['god'] else 'OFF'}\n"
    status_text += f"Auto Reply: {'ON' if settings['autoreply'] else 'OFF'}\n"
    status_text += f"Anti-Delete: {'ON' if settings['antidelete'] else 'OFF'}\n"
    status_text += f"Invisible: {'ON' if settings['invisible'] else 'OFF'}\n"
    status_text += f"Password: {'Set' if settings['pass'] else 'OFF'}\n"
    await e.reply(status_text)

# ========= BACKUP =========
@client.on(events.NewMessage(pattern=r".*\.backup"))
async def backup(e):
    if not is_owner(e):
        return
    save_settings()
    await e.reply("Backup saved")

@client.on(events.NewMessage(pattern=r".*\.restore"))
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
@client.on(events.NewMessage(pattern=r".*\.setpass (.+)"))
async def setpass(e):
    if not is_owner(e):
        return
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
                msg = await client.get_messages(e.chat_id, ids=msg_id)
                if msg:
                    # فقط متن، عکس، ویدیو، ویس و اهنگ
                    if msg.text or msg.media:
                        sender_name = "کاربر"
                        if msg.sender:
                            if hasattr(msg.sender, "username") and msg.sender.username:
                                sender_name = f"@{msg.sender.username}"
                            elif hasattr(msg.sender, "first_name") and msg.sender.first_name:
                                sender_name = msg.sender.first_name

                        content = msg.text if msg.text else "[مدیا]"
                        await client.send_message(
                            LOG_CHAT,
                            f"🛡️ پیام حذف شد از {sender_name}:\n\n{content}"
                        )
            except Exception as ex:
                print(f"Error in anti-delete: {ex}")

# ========= INVISIBLE =========
@client.on(events.NewMessage)
async def invisible_func(e):
    # For userbots, "Invisible" typically means NOT sending read receipts.
    # Telethon doesn't send them automatically unless you call ReadHistoryRequest.
    # So if "Invisible" is ON, we just DO NOTHING.
    # The previous code was sending them if ON, which is the opposite of ghost mode.
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
    if not SESSION:
        print("--- ERROR: SESSION environment variable is missing! ---")
        return

    print("--- Connecting to Telegram ---")
    try:
        await client.start()
        if not await client.is_user_authorized():
            print("--- ERROR: SESSION is invalid or expired! ---")
            return
    except Exception as ex:
        print(f"--- Connection Failed: {ex} ---")
        return

    me = await client.get_me()
    print(f"🔥 Ultimate Modular Userbot Started as {me.first_name} ({me.id})")
    await client.run_until_disconnected()

async def start_all():
    # Run web server in executor (thread)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_web)
    # Start client
    await main()

if __name__ == "__main__":
    try:
        asyncio.run(start_all())
    except KeyboardInterrupt:
        pass
