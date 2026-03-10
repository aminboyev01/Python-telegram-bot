"""
Reklama yuborish uchun yordamchi modul.
- Kino yuborishdan OLDIN reklama chiqadi
- Har N ta so'rovdan keyin chiqadi (bazadan olinadi)
"""
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_active_ad, increment_request_count

logger = logging.getLogger(__name__)


def _make_ad_keyboard(ad: dict) -> InlineKeyboardMarkup | None:
    """Reklama tugmasi bo'lsa klaviatura yaratadi."""
    if ad.get("button_text") and ad.get("button_url"):
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=ad["button_text"],
                url=ad["button_url"],
            )
        ]])
    return None


async def maybe_send_ad(bot: Bot, user_id: int) -> bool:
    """
    Reklamani yuborish kerakligini tekshiradi va kerak bo'lsa yuboradi.
    Reklama YUBORILGAN bo'lsa True, yuborilmagan bo'lsa False qaytaradi.

    Mantiq:
      1. Faol reklama bormi? → Yo'q → skip
      2. Foydalanuvchi so'rovlar sonini oshir
      3. Son % every_n == 0 bo'lsa → reklama yubor
      4. Har doim ham kino yuborishdan oldin reklama (before=True rejimi)
    """
    ad = await get_active_ad()
    if not ad:
        # Faol reklama yo'q — hech narsa qilmaymiz
        await increment_request_count(user_id)
        return False

    count = await increment_request_count(user_id)
    every_n = ad.get("every_n", 3)

    # Har N ta so'rovdan keyin reklama
    if every_n > 0 and count % every_n == 0:
        try:
            kb = _make_ad_keyboard(ad)
            await bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Reklama</b>\n\n{ad['text']}",
                parse_mode="HTML",
                reply_markup=kb,
            )
            logger.info("Reklama yuborildi → user=%s (so'rov #%s)", user_id, count)
            return True
        except Exception as e:
            logger.warning("Reklama yuborishda xatolik (user=%s): %s", user_id, e)

    return False


async def send_ad_before_movie(bot: Bot, user_id: int) -> None:
    """
    Kino yuborishdan OLDIN reklamani yuboradi (agar faol reklama bo'lsa).
    Bu funksiya so'rov hisoblagichini o'zgartirmaydi.
    """
    ad = await get_active_ad()
    if not ad:
        return

    try:
        kb = _make_ad_keyboard(ad)
        await bot.send_message(
            chat_id=user_id,
            text=f"📢 <b>Reklama</b>\n\n{ad['text']}",
            parse_mode="HTML",
            reply_markup=kb,
        )
        logger.info("Kino oldidan reklama yuborildi → user=%s", user_id)
    except Exception as e:
        logger.warning("Reklama yuborishda xatolik (user=%s): %s", user_id, e)
