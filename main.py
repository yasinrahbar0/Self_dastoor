import os, json, asyncio, threading, glob, importlib, random
from datetime import datetime
from collections import defaultdict
from flask import Flask
from telethon import TelegramClient, events, functions, Button
from telethon.sessions import StringSession

# ========= ENV =========
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
LOG_CHAT = int(os.getenv("LOG_CHAT", 0))

# ========= FLASK =========
app = Flask(__name__)
@app.route("/")
def home():
    return "Ultimate Modular Userbot + Bot Panel Running 🔥"

def run_web():
    print("--- Starting Flask Server ---")
    app.run(host="0.0.0.0", port=10000)

# ========= CLIENTS =========
user_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
bot_client = None
if BOT_TOKEN:
    bot_client = TelegramClient('bot_panel', API_ID, API_HASH)

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

settings.setdefault("style", {
    "bold": False,
    "italic": False,
    "code": False,
    "quote": False,
    "spoiler": False,
    "strike": False
})
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

    if settings["style"]["strike"]:
        text = f"~~{text}~~"

    if settings["style"]["spoiler"]:
        text = f"||{text}||"

    return text

# ========= USER CLIENT HANDLERS =========

@user_client.on(events.NewMessage(outgoing=True))
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

# ========= BOT PANEL LOGIC =========

PANEL_TEXT = "🔥 **Ultimate Control Panel** 🔥\n━━━━━━━━━━━━━━━━━━\nمدیریت کامل یوزربات"

def status_emoji(val):
    return "🟢" if val else "🔴"

async def create_panel():
    if not bot_client:
        return

    # Try to find existing panel message in bot's chat with owner
    panel_msg_id = None
    async for msg in bot_client.iter_messages(OWNER_ID, limit=20):
        if msg.text and "Ultimate Control Panel" in msg.text:
            panel_msg_id = msg.id
            break

    buttons = [
        [
            Button.inline("🎨 Styles", b"panel_styles"),
            Button.inline("⚡ Modes", b"panel_modes")
        ],
        [
            Button.inline("📊 Status", b"panel_status"),
            Button.inline("❌ Close", b"panel_close")
        ]
    ]

    if panel_msg_id:
        try:
            await bot_client.edit_message(OWNER_ID, panel_msg_id, PANEL_TEXT, buttons=buttons)
        except Exception:
            msg = await bot_client.send_message(OWNER_ID, PANEL_TEXT, buttons=buttons)
    else:
        await bot_client.send_message(OWNER_ID, PANEL_TEXT, buttons=buttons)

if bot_client:
    @bot_client.on(events.CallbackQuery)
    async def panel_handler(e):
        if e.sender_id != OWNER_ID:
            return await e.answer("⚠️ You are not the owner!", alert=True)

        data = e.data.decode()

        if data == "panel_close":
            await e.delete()
        elif data == "panel_styles":
            buttons = [
                [Button.inline(f"Bold {status_emoji(settings['style']['bold'])}", b"toggle_bold"),
                 Button.inline(f"Italic {status_emoji(settings['style']['italic'])}", b"toggle_italic")],
                [Button.inline(f"Code {status_emoji(settings['style']['code'])}", b"toggle_code"),
                 Button.inline(f"Quote {status_emoji(settings['style']['quote'])}", b"toggle_quote")],
                [Button.inline(f"Spoiler {status_emoji(settings['style']['spoiler'])}", b"toggle_spoiler"),
                 Button.inline(f"Strike {status_emoji(settings['style']['strike'])}", b"toggle_strike")],
                [Button.inline("🔙 Back", b"panel_main"),
                 Button.inline("❌ Close", b"panel_close")]
            ]
            await e.edit("🎨 **Style Settings**", buttons=buttons)
        elif data == "panel_modes":
            buttons = [
                [Button.inline(f"God {status_emoji(settings['god'])}", b"toggle_god"),
                 Button.inline(f"Auto {status_emoji(settings['autoreply'])}", b"toggle_autoreply")],
                [Button.inline(f"AntiDel {status_emoji(settings['antidelete'])}", b"toggle_antidelete"),
                 Button.inline(f"Invis {status_emoji(settings['invisible'])}", b"toggle_invisible")],
                [Button.inline(f"Lock {status_emoji(settings['lock'])}", b"toggle_lock")],
                [Button.inline("🔙 Back", b"panel_main"),
                 Button.inline("❌ Close", b"panel_close")]
            ]
            await e.edit("⚡ **Mode Settings**", buttons=buttons)
        elif data == "panel_status":
            text = "📊 **Current Status**\n━━━━━━━━━━━━━━━━━━\n\n"
            for k, v in settings["style"].items():
                text += f"{k.capitalize()}: {'ON' if v else 'OFF'}\n"
            text += "\n"
            for k in ["god", "autoreply", "antidelete", "invisible", "lock"]:
                text += f"{k.capitalize()}: {'ON' if settings[k] else 'OFF'}\n"
            buttons = [
                [Button.inline("🔙 Back", b"panel_main"),
                 Button.inline("❌ Close", b"panel_close")]
            ]
            await e.edit(text, buttons=buttons)
        elif data == "panel_main":
            buttons = [
                [Button.inline("🎨 Styles", b"panel_styles"),
                 Button.inline("⚡ Modes", b"panel_modes")],
                [Button.inline("📊 Status", b"panel_status"),
                 Button.inline("❌ Close", b"panel_close")]
            ]
            await e.edit(PANEL_TEXT, buttons=buttons)
        elif data.startswith("toggle_"):
            key = data.replace("toggle_", "")
            if key in settings["style"]:
                settings["style"][key] = not settings["style"][key]
            elif key in settings:
                settings[key] = not settings[key]
            save_settings()
            # Reuse the current state to update buttons
            parent_data = "panel_styles" if key in settings["style"] else "panel_modes"
            # Simulate navigation to refresh view
            e.data = parent_data.encode()
            await panel_handler(e)

# ========= USER COMMANDS =========

@user_client.on(events.NewMessage(outgoing=True, pattern=r".*\.help($|\s)"))
async def help_cmd(e):
    if not is_owner(e):
        return

    if bot_client:
        await create_panel()
        await e.edit("✅ پنل مدیریتی در چت بات باز شد / آپدیت شد.")
    else:
        # Fallback to text help if no bot token
        msg = """
🔥 **Ultimate Userbot Help** 🔥
━━━━━━━━━━━━━━━━━━
🎨 **Styles**: .bold, .italic, .code, .quote, .spoiler, .strike (on/off)
⚡ **Modes**: .god, .autoreply, .antidelete, .invisible, .lock (on/off)
🛡️ **Security**: .spam <limit> <time>, .clean <count>, .stats
🧠 **Keywords**: .addreply k=v, .delreply k
🎲 **Dice**: .tas <1-6>
💾 **Media**: .save (reply)
🎛️ **Management**: .status, .backup, .restore, .setpass <pass>
"""
        await e.edit(msg)

@user_client.on(events.NewMessage(pattern=r".*\.(bold|italic|code|quote|spoiler|strike) (on|off)"))
async def toggle_style(e):
    if not is_owner(e):
        return
    cmd, state = e.pattern_match.groups()
    settings["style"][cmd] = state == "on"
    save_settings()
    await e.reply(f"{cmd} => {state}")

@user_client.on(events.NewMessage(pattern=r".*\.tas (\d)"))
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

@user_client.on(events.NewMessage(pattern=r".*\.(god|autoreply|antidelete|invisible|lock) (on|off)"))
async def toggle_modes(e):
    if not is_owner(e):
        return
    cmd, state = e.pattern_match.groups()
    state = state == "on"
    settings[cmd] = state
    save_settings()
    await e.reply(f"{cmd} => {'ON' if state else 'OFF'}")

@user_client.on(events.NewMessage(incoming=True))
async def spam_control(e):
    if not e.sender_id or e.sender_id == OWNER_ID or e.out:
        return
    now = datetime.now().timestamp()
    user_spam[e.sender_id] = [t for t in user_spam[e.sender_id] if now - t < settings["spam_time"]]
    user_spam[e.sender_id].append(now)
    if len(user_spam[e.sender_id]) > settings["spam_limit"]:
        await e.delete()

@user_client.on(events.NewMessage(pattern=r".*\.spam (\d+) (\d+)"))
async def set_spam(e):
    if not is_owner(e):
        return
    settings["spam_limit"] = int(e.pattern_match.group(1))
    settings["spam_time"] = int(e.pattern_match.group(2))
    save_settings()
    await e.reply("Spam control updated")

@user_client.on(events.NewMessage(pattern=r".*\.clean (\d+)"))
async def cleaner(e):
    if not is_owner(e):
        return
    count = int(e.pattern_match.group(1))
    async for msg in user_client.iter_messages(e.chat_id, limit=count):
        if msg.out:
            await msg.delete()

@user_client.on(events.NewMessage(pattern=r".*\.stats"))
async def stats_cmd(e):
    if not is_owner(e):
        return
    count = group_stats[e.chat_id]
    await e.reply(f"Messages in this chat: {count}")

@user_client.on(events.NewMessage(incoming=True))
async def stats_counter(e):
    group_stats[e.chat_id] += 1

@user_client.on(events.NewMessage(pattern=r".*\.addreply (.+)"))
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

@user_client.on(events.NewMessage(pattern=r".*\.delreply (.+)"))
async def del_reply(e):
    if not is_owner(e):
        return
    k = e.pattern_match.group(1)
    settings["keywords"].pop(k, None)
    save_settings()
    await e.reply("Reply deleted")

@user_client.on(events.NewMessage(incoming=True))
async def keyword_auto(e):
    if not e.text:
        return
    for k, v in settings["keywords"].items():
        if k in e.text:
            await e.reply(v)

@user_client.on(events.NewMessage(pattern=r".*\.save"))
async def save_media(e):
    if not is_owner(e):
        return
    if not e.reply_to_msg_id:
        return await e.reply("Reply to self-destruct media")
    msg = await e.get_reply_message()
    if msg and msg.media:
        file = await msg.download_media()
        await user_client.send_file("me", file)
        await e.reply("Saved to Saved Messages ✅")
        if os.path.exists(file):
            os.remove(file)

@user_client.on(events.NewMessage(pattern=r".*\.status"))
async def status_cmd_user(e):
    if not is_owner(e):
        return
    status_text = f"⚙️ **Bot Status:**\n\n"
    status_text += f"God Mode: {'ON' if settings['god'] else 'OFF'}\n"
    status_text += f"Auto Reply: {'ON' if settings['autoreply'] else 'OFF'}\n"
    status_text += f"Anti-Delete: {'ON' if settings['antidelete'] else 'OFF'}\n"
    status_text += f"Invisible: {'ON' if settings['invisible'] else 'OFF'}\n"
    status_text += f"Password: {'Set' if settings['pass'] else 'OFF'}\n"
    await e.reply(status_text)

@user_client.on(events.NewMessage(pattern=r".*\.backup"))
async def backup(e):
    if not is_owner(e):
        return
    save_settings()
    await e.reply("Backup saved")

@user_client.on(events.NewMessage(pattern=r".*\.restore"))
async def restore(e):
    if not is_owner(e):
        return
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        settings.update(data)
        save_settings()
        await e.reply("Restored")

@user_client.on(events.NewMessage(pattern=r".*\.setpass (.+)"))
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

@user_client.on(events.NewMessage(incoming=True))
async def god_mode_func(e):
    if settings["god"] and not e.out:
        if e.is_private:
            await e.reply("👑 Supreme Mode Active")

@user_client.on(events.NewMessage(incoming=True))
async def auto_reply_func(e):
    if settings["autoreply"] and not e.out:
        if e.is_private:
            await e.reply("⚡ Auto Reply Active")

@user_client.on(events.NewMessage)
async def invisible_handler(e):
    if settings["invisible"] and not e.out:
        # Ghost mode implementation: usually involves suppressing ReadHistory
        # Telethon doesn't send ReadHistory by default, so we just exist as a placeholder.
        pass

@user_client.on(events.MessageDeleted)
async def anti_delete_func(e):
    if settings["antidelete"]:
        for msg_id in e.deleted_ids:
            try:
                msg = await user_client.get_messages(e.chat_id, ids=msg_id)
                if msg:
                    if msg.text or msg.media:
                        sender_name = "کاربر"
                        if msg.sender:
                            if hasattr(msg.sender, "username") and msg.sender.username:
                                sender_name = f"@{msg.sender.username}"
                            elif hasattr(msg.sender, "first_name") and msg.sender.first_name:
                                sender_name = msg.sender.first_name

                        content = msg.text if msg.text else "[مدیا]"
                        await user_client.send_message(
                            LOG_CHAT,
                            f"🛡️ پیام حذف شد از {sender_name}:\n\n{content}"
                        )
            except Exception as ex:
                print(f"Error in anti-delete: {ex}")

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

    print("--- Starting Clients ---")
    try:
        await user_client.start()
        if not await user_client.is_user_authorized():
            print("--- ERROR: SESSION is invalid or expired! ---")
            return

        me = await user_client.get_me()
        print(f"🔥 Userbot Started as {me.first_name} ({me.id})")

        if bot_client:
            await bot_client.start(bot_token=BOT_TOKEN)
            print("🔥 Bot Panel Client Started")
            await create_panel()
            print("🔥 Control Panel Ready in Bot Chat")

    except Exception as ex:
        print(f"--- Initialization Failed: {ex} ---")
        return

    # Run both clients
    if bot_client:
        await asyncio.gather(
            user_client.run_until_disconnected(),
            bot_client.run_until_disconnected()
        )
    else:
        await user_client.run_until_disconnected()

async def start_all():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_web)
    await main()

if __name__ == "__main__":
    try:
        asyncio.run(start_all())
    except KeyboardInterrupt:
        pass
