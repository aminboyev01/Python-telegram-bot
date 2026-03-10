"""
Admin uchun reklama boshqaruvi.

Komandalar:
  /adadd          — yangi reklama qo'shish (FSM)
  /adlist         — barcha reklamalar ro'yxati
  /addelete <id>  — reklamani o'chirish
  /adoff <id>     — reklamani o'chirish (deaktiv)
  /adon <id>      — reklamani yoqish (aktiv)
  /adinterval <id> <N> — har N so'rovdan keyin chiqishi
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import (
    add_ad, list_ads, delete_ad,
    toggle_ad, update_ad_every_n, get_ad_by_id,
)

router = Router()
logger = logging.getLogger(__name__)


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


# ─── FSM ──────────────────────────────────────────────────────────────────────

class AdStates(StatesGroup):
    waiting_text       = State()
    waiting_button_ask = State()
    waiting_button     = State()
    waiting_interval   = State()


# ─── /adadd ───────────────────────────────────────────────────────────────────

@router.message(Command("adadd"))
async def cmd_adadd(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    await state.set_state(AdStates.waiting_text)
    await message.answer(
        "📝 <b>Reklama matni</b>ni yuboring:\n\n"
        "HTML teglari ishlatishingiz mumkin:\n"
        "<code>&lt;b&gt;qalin&lt;/b&gt;</code>  "
        "<code>&lt;i&gt;kursiv&lt;/i&gt;</code>  "
        "<code>&lt;a href='url'&gt;link&lt;/a&gt;</code>",
        parse_mode="HTML",
    )


@router.message(AdStates.waiting_text)
async def receive_ad_text(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return

    await state.update_data(ad_text=message.text or message.caption or "")
    await state.set_state(AdStates.waiting_button_ask)
    await message.answer(
        "🔘 Reklamaga <b>tugma</b> qo'shmoqchimisiz?\n\n"
        "<b>Ha</b> — tugma qo'shish uchun: <code>Tugma nomi | https://link.com</code> formatida yuboring\n"
        "<b>Yo'q</b> — tugmasiz davom etish uchun: <code>yo'q</code> yuboring",
        parse_mode="HTML",
    )


@router.message(AdStates.waiting_button_ask)
async def receive_ad_button(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return

    text = (message.text or "").strip()

    if text.lower() in ("yo'q", "yoq", "no", "-"):
        await state.update_data(button_text="", button_url="")
    elif "|" in text:
        parts = text.split("|", 1)
        btn_text = parts[0].strip()
        btn_url = parts[1].strip()
        if not btn_url.startswith("http"):
            await message.answer(
                "❗ URL <code>https://</code> bilan boshlanishi kerak. Qayta yuboring:"
            )
            return
        await state.update_data(button_text=btn_text, button_url=btn_url)
    else:
        await message.answer(
            "❗ Format noto'g'ri. Misol:\n"
            "<code>Bizning kanal | https://t.me/kanal</code>\n\n"
            "Tugmasiz bo'lsa <code>yo'q</code> yuboring.",
            parse_mode="HTML",
        )
        return

    await state.set_state(AdStates.waiting_interval)
    await message.answer(
        "🔢 Har necha so'rovdan keyin reklama chiqsin?\n\n"
        "Masalan: <code>3</code> — har 3 ta so'rovdan keyin\n"
        "Faqat raqam yuboring:",
        parse_mode="HTML",
    )


@router.message(AdStates.waiting_interval)
async def receive_ad_interval(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return

    text = (message.text or "").strip()
    if not text.isdigit() or int(text) < 1:
        await message.answer("❗ Faqat musbat son kiriting (masalan: 3).")
        return

    every_n = int(text)
    data = await state.get_data()
    await state.clear()

    ad_id = await add_ad(
        text=data["ad_text"],
        button_text=data.get("button_text", ""),
        button_url=data.get("button_url", ""),
        every_n=every_n,
    )

    btn_info = ""
    if data.get("button_text"):
        btn_info = f"\n🔘 Tugma: <b>{data['button_text']}</b>"

    await message.answer(
        f"✅ Reklama qo'shildi!\n\n"
        f"🆔 ID: <code>{ad_id}</code>\n"
        f"🔄 Har <b>{every_n}</b> so'rovdan keyin chiqadi{btn_info}\n\n"
        f"📋 Ko'rish: /adlist\n"
        f"🔴 O'chirish: /adoff {ad_id}",
        parse_mode="HTML",
    )
    logger.info("Reklama qo'shildi: id=%s, every_n=%s", ad_id, every_n)


# ─── /adlist ──────────────────────────────────────────────────────────────────

@router.message(Command("adlist"))
async def cmd_adlist(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    ads = await list_ads()
    if not ads:
        await message.answer(
            "📭 Hozircha hech qanday reklama yo'q.\n"
            "Qo'shish: /adadd"
        )
        return

    lines = ["📢 <b>Reklamalar ro'yxati:</b>\n"]
    for ad in ads:
        status = "🟢 Faol" if ad["is_active"] else "🔴 Nofaol"
        short_text = ad["text"][:60] + ("..." if len(ad["text"]) > 60 else "")
        btn = f" | 🔘 Tugma bor" if ad.get("button_text") else ""
        lines.append(
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{ad['id']}</code>  {status}\n"
            f"📝 {short_text}\n"
            f"🔄 Har <b>{ad['every_n']}</b> so'rovdan keyin{btn}\n"
            f"📅 {ad['created_at'][:16]}"
        )

    lines.append(
        "\n━━━━━━━━━━━━━━━\n"
        "🟢 Yoqish: /adon &lt;id&gt;\n"
        "🔴 O'chirish: /adoff &lt;id&gt;\n"
        "🗑 O'chirish: /addelete &lt;id&gt;\n"
        "⏱ Intervalni o'zgartirish: /adinterval &lt;id&gt; &lt;N&gt;"
    )

    await message.answer("\n".join(lines), parse_mode="HTML")


# ─── /addelete <id> ───────────────────────────────────────────────────────────

@router.message(Command("addelete"))
async def cmd_addelete(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❗ Foydalanish: <code>/addelete &lt;id&gt;</code>", parse_mode="HTML")
        return

    ad_id = int(parts[1])
    deleted = await delete_ad(ad_id)

    if deleted:
        await message.answer(f"🗑 Reklama <code>#{ad_id}</code> o'chirildi.", parse_mode="HTML")
    else:
        await message.answer(f"❌ <code>#{ad_id}</code> topilmadi.", parse_mode="HTML")


# ─── /adoff <id> ──────────────────────────────────────────────────────────────

@router.message(Command("adoff"))
async def cmd_adoff(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❗ Foydalanish: <code>/adoff &lt;id&gt;</code>", parse_mode="HTML")
        return

    ad_id = int(parts[1])
    ok = await toggle_ad(ad_id, False)
    if ok:
        await message.answer(f"🔴 Reklama <code>#{ad_id}</code> nofaol qilindi.", parse_mode="HTML")
    else:
        await message.answer(f"❌ <code>#{ad_id}</code> topilmadi.", parse_mode="HTML")


# ─── /adon <id> ───────────────────────────────────────────────────────────────

@router.message(Command("adon"))
async def cmd_adon(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❗ Foydalanish: <code>/adon &lt;id&gt;</code>", parse_mode="HTML")
        return

    ad_id = int(parts[1])
    ok = await toggle_ad(ad_id, True)
    if ok:
        await message.answer(f"🟢 Reklama <code>#{ad_id}</code> faollashtirildi.", parse_mode="HTML")
    else:
        await message.answer(f"❌ <code>#{ad_id}</code> topilmadi.", parse_mode="HTML")


# ─── /adinterval <id> <N> ─────────────────────────────────────────────────────

@router.message(Command("adinterval"))
async def cmd_adinterval(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer(
            "❗ Foydalanish: <code>/adinterval &lt;id&gt; &lt;N&gt;</code>\n"
            "Misol: <code>/adinterval 1 5</code> — har 5 so'rovdan keyin",
            parse_mode="HTML",
        )
        return

    ad_id = int(parts[1])
    every_n = int(parts[2])
    if every_n < 1:
        await message.answer("❗ N kamida 1 bo'lishi kerak.")
        return

    ok = await update_ad_every_n(ad_id, every_n)
    if ok:
        await message.answer(
            f"✅ Reklama <code>#{ad_id}</code> endi har <b>{every_n}</b> so'rovdan keyin chiqadi.",
            parse_mode="HTML",
        )
    else:
        await message.answer(f"❌ <code>#{ad_id}</code> topilmadi.", parse_mode="HTML")
