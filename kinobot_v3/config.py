import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
STORAGE_CHANNEL_ID: int = int(os.getenv("STORAGE_CHANNEL_ID", "0"))

# Majburiy obuna kanallar: "kanal_id:kanal_linki" formatida, vergul bilan ajratilgan
# Misol: -1001234567890:https://t.me/kanal1,-1009876543210:https://t.me/kanal2
_raw_channels = os.getenv("REQUIRED_CHANNELS", "")

REQUIRED_CHANNELS: list[dict] = []
if _raw_channels.strip():
    for item in _raw_channels.split(","):
        item = item.strip()
        if ":" in item:
            parts = item.split(":", 1)
            try:
                REQUIRED_CHANNELS.append({
                    "id": int(parts[0].strip()),
                    "link": parts[1].strip(),
                })
            except ValueError:
                pass

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID .env faylida topilmadi!")
if not STORAGE_CHANNEL_ID:
    raise ValueError("STORAGE_CHANNEL_ID .env faylida topilmadi!")


