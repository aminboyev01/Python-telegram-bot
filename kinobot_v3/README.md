# 🎬 KinoBot — Telegram Kino Bot

Python + aiogram 3.x yordamida yozilgan professional Telegram kino boti.

---

## 📁 Loyiha strukturasi

```
kinobot/
├── bot.py              ← Asosiy ishga tushirish fayli
├── config.py           ← Sozlamalar (.env o'qish)
├── database.py         ← SQLite asinxron bazasi
├── handlers/
│   ├── start.py        ← /start komandasi
│   ├── movie.py        ← Kino kodi qidirish + rate limit
│   └── admin.py        ← Admin panel (/add /delete /list /stats)
├── utils/
│   └── models.py       ← Ma'lumot modellari
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ O'rnatish va Sozlash

### 1. BotFather orqali bot yaratish

1. Telegramda **@BotFather** ni oching
2. `/newbot` yozing
3. Bot nomini kiriting (masalan: `Kino Bot`)
4. Bot username kiriting (masalan: `mening_kinobot`)
5. BotFather sizga **BOT_TOKEN** beradi — uni saqlang!

---

### 2. Private kino kanali yaratish

1. Telegramda yangi kanal yarating: **New Channel**
2. Kanalni **Private** qilib sozlang
3. Kanal nomini kiriting (masalan: `KinoStorage`)
4. Bu kanal faqat videolarni saqlash uchun — foydalanuvchilar ko'rmaydi

---

### 3. Botni kanalga admin qilish

1. Private kanalga kiring
2. **Kanal sozlamalari → Administrators → Add Administrator**
3. Botning username ini qidiring va admin qiling
4. Ruxsatlardan **"Post Messages"** ni yoqing
5. Saqlang

---

### 4. Kanal ID olish

**Usul 1 — @userinfobot orqali:**
1. Kanalingizga @userinfobot ni qo'shing
2. Kanalda `/start` yozing
3. Bot sizga kanal ID sini beradi (masalan: `-1001234567890`)

**Usul 2 — @username_to_id_bot orqali:**
1. Botga kanal linkini yuboring
2. ID ni oling

> ⚠️ Kanal ID manfiy raqam bo'ladi va odatda `-100` bilan boshlanadi!

---

### 5. Admin ID olish

1. Telegramda **@userinfobot** ga `/start` yozing
2. U sizning **User ID** ingizni ko'rsatadi

---

### 6. .env faylini to'ldirish

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
ADMIN_ID=123456789
STORAGE_CHANNEL_ID=-1001234567890
```

---

### 7. Python muhitini sozlash

```bash
# Virtual muhit yaratish (tavsiya etiladi)
python -m venv venv

# Aktivlashtirish
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

---

### 8. Botni ishga tushirish

```bash
python bot.py
```

Muvaffaqiyatli ishga tushsa konsolda quyidagini ko'rasiz:
```
2024-01-01 12:00:00 | INFO     | __main__ | KinoBot ishga tushmoqda...
2024-01-01 12:00:00 | INFO     | database | Ma'lumotlar bazasi tayyor.
2024-01-01 12:00:00 | INFO     | __main__ | Bot polling rejimida ishga tushdi.
```

---

## 📱 Bot buyruqlari

### 👤 Foydalanuvchi uchun
| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `101` | Kino kodi yuboring |

### 🔧 Admin uchun
| Buyruq | Tavsif |
|--------|--------|
| `/add 101` | Yangi kino qo'shish |
| `/delete 101` | Kinoni o'chirish |
| `/list` | Barcha kinolar ro'yxati |
| `/stats` | Bot statistikasi |

---

## 🎬 Kino qo'shish jarayoni (Admin)

1. `/add 101` yuboring
2. Bot sizdan video so'raydi
3. Video yuboring
4. Bot avtomatik ravishda:
   - Videoni private kanalga forward qiladi
   - `message_id` ni oladi
   - Ma'lumotlar bazasiga saqlaydi

---

## 📺 Asosiy kanalda post namunasi

```
🎬 Kino: Avatar

📥 Kino kodi: 101
Kinoni olish uchun botga yozing: @sizning_botingiz
```

---

## 🗂 Ma'lumotlar bazasi

**movies jadvali:**
| id | code | message_id | title | added_at |
|----|------|------------|-------|----------|
| 1  | 101  | 456789     |       | 2024-... |

**users jadvali:**
| id | user_id   | username | joined_at |
|----|-----------|----------|-----------|
| 1  | 123456789 | ali_123  | 2024-...  |

---

## 🛡 Xavfsizlik

- Faqat **ADMIN_ID** dagi foydalanuvchi kino qo'sha/o'chira oladi
- Faqat **raqamli** kodlar qabul qilinadi
- **Rate limit**: 3 soniyada bitta so'rov
- Barcha xatolar `logging` orqali qayd etiladi
- `kinobot.log` faylida barcha harakatlar saqlanadi

---

## 🔄 Serverda ishga tushirish (systemd)

```ini
# /etc/systemd/system/kinobot.service
[Unit]
Description=KinoBot Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kinobot
ExecStart=/home/ubuntu/kinobot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable kinobot
sudo systemctl start kinobot
sudo systemctl status kinobot
```
