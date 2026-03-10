"""
Majburiy obuna tekshiruvi — asyncio.gather bilan parallel tekshirish.
"""
import asyncio
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import REQUIRED_CHANNELS

logger = logging.getLogger(__name__)


async def _check_one(bot: Bot, user_id: int, channel: dict) -> dict | None:
    """
    Bitta kanalga obunani tekshiradi.
    Obuna bo'lmagan bo'lsa channel dict qaytaradi, bo'lgan bo'lsa None.
    """
    try:
        member = await bot.get_chat_member(
            chat_id=channel["id"],
            user_id=user_id,
        )
        if member.status in ("left", "kicked"):
            return channel
        return None
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        logger.warning("Kanal tekshirishda xatolik (id=%s): %s", channel["id"], e)
        return channel
    except Exception as e:
        logger.error("Kutilmagan xatolik (id=%s): %s", channel["id"], e)
        return channel


async def check_subscription(bot: Bot, user_id: int) -> list[dict]:
    """
    Barcha kanallarga obunani PARALLEL tekshiradi (asyncio.gather).
    Obuna bo'lmagan kanallar ro'yxatini qaytaradi.
    Bo'sh ro'yxat = hamma kanalga obuna bo'lgan.
    """
    if not REQUIRED_CHANNELS:
        return []

    # Barcha kanallarni bir vaqtda tekshiramiz
    results = await asyncio.gather(
        *[_check_one(bot, user_id, ch) for ch in REQUIRED_CHANNELS],
        return_exceptions=False,
    )

    # None bo'lmaganlar = obuna bo'lmagan kanallar
    return [ch for ch in results if ch is not None]


def subscription_keyboard(not_subscribed: list[dict], pending_code: str = "") -> InlineKeyboardMarkup:
    """Obuna tugmalari + Tekshirish tugmasi."""
    buttons = []

    for i, channel in enumerate(not_subscribed, start=1):
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 {i}-Kanalga obuna bo'lish",
                url=channel["link"],
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data=f"check_sub:{pending_code}",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
