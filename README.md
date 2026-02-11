# Ultimate Modular Userbot

## Description
Ultimate Modular Final Build – Everything for the OWNER only.

### Features:
- All modes (God, AutoReply, AntiDelete, Invisible, Lock)
- Text Style (Bold, Italic, Code, Quote)
- Smart Response (.addreply/.delreply)
- Save self-destructing files (.save)
- Spam Control, Cleaner, Stats
- Button Management Panel (.panel)
- Backup and Restore (.backup/.restore)
- Password System (.setpass)
- Plugin System
- 100% for OWNER only
- Fully compatible with Render

## Setup

### Environment Variables for Render:
- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash
- `SESSION`: Your Telethon String Session
- `OWNER_ID`: Your Telegram User ID
- `LOG_CHAT`: Chat ID for logs (Anti-delete notifications)

### Installation:
```bash
pip install -r requirements.txt
python3 main.py
```

> **Note for Render Users:** Render's free tier uses an ephemeral file system. Any changes to settings (passwords, keywords, etc.) made while the bot is running will be lost when the bot restarts or redeploys.
