import logging
import time
from collections import defaultdict

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import STORAGE_CHANNEL_ID, REQUIRED_CHANNELS
from database import get_movie
from utils.subscription import check_subscription, subscription_keyboard
from utils.ads import send_ad_before_movie, maybe_send_ad

router = Router()
logger = logging.getLogger(__name__)

# ─── Rate Limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_SECONDS = 1
_last_request: dict[int, float] = defaultdict(float)


def is_rate_limited(user_id: int) -> bool:
    now = time.monotonic()
    if now - _last_request[user_id] < RATE_LIMIT_SECONDS:
        return True
    _last_request[user_id] = now
    return False


# ─── Kinoni forward qilish ────────────────────────────────────────────────────

async def _forward_movie(bot, user_id: int, movie: dict) -> bool:
    try:
        await send_ad_before_movie(bot, user_id)
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=movie["message_id"],
        )
        await maybe_send_ad(bot, user_id)
        logger.info("Kino yuborildi: kod=%s → user=%s", movie["code"], user_id)
        return True
    except Exception as e:
        logger.error("Forward xatosi (user=%s): %s", user_id, e)
        return False


# ─── Kino kodi handler ────────────────────────────────────────────────────────

@router.message(F.text.regexp(r"^\d+$"))
async def handle_movie_code(message: Message) -> None:
    user_id = message.from_user.id
    code = message.text.strip()

    if is_rate_limited(user_id):
        await message.answer("⏳ Iltimos, bir oz kuting va qayta urinib ko'ring.")
        return

    logger.info("Foydalanuvchi %s kod yubordi: %s", user_id, code)

    movie = await get_movie(code)
    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi.\n\n"
            "🔍 Kodni to'g'ri yozganingizni tekshiring.",
            parse_mode="HTML",
        )
        return

    if REQUIRED_CHANNELS:
        not_subscribed = await check_subscription(message.bot, user_id)
        if not_subscribed:
            kb = subscription_keyboard(not_subscribed, pending_code=code)
            await message.answer(
                "⚠️ <b>Kinoni olish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
                "Obuna bo'lgach <b>✅ Obunani tekshirish</b> tugmasini bosing.",
                parse_mode="HTML",
                reply_markup=kb,
            )
            return

    success = await _forward_movie(message.bot, user_id, movie)
    if not success:
        await message.answer(
            "⚠️ Kinoni yuborishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
        )


# ─── "Obunani tekshirish" tugmasi ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("check_sub:"))
async def callback_check_subscription(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    code = callback.data.split(":", 1)[1]

    # Darhol tugmani "bosildi" holatiga o'tkazamiz — UI tez reaksiya beradi
    await callback.answer()

    # Parallel tekshirish
    not_subscribed = await check_subscription(callback.bot, user_id)

    if not_subscribed:
        kb = subscription_keyboard(not_subscribed, pending_code=code)
        try:
            await callback.message.edit_text(
                "❌ <b>Siz hali barcha kanallarga obuna bo'lmagansiz!</b>\n\n"
                "Obuna bo'lib, <b>✅ Obunani tekshirish</b> tugmasini bosing.",
                parse_mode="HTML",
                reply_markup=kb,
            )
        except Exception:
            pass
        return

    # ✅ Obuna to'g'ri — xabarni o'chiramiz
    try:
        await callback.message.delete()
    except Exception:
        pass

    # /start dan kelgan — kino kodi so'raymiz
    if code == "start":
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ <b>Obuna tasdiqlandi!</b>\n\n"
                "🎬 Endi kino kodini yuboring va kinoni oling!\n\n"
                "📌 Kino kodini asosiy kanalimizdan topishingiz mumkin."
            ),
            parse_mode="HTML",
        )
        return

    # Kino kodi bilan kelgan — darhol kinoni yuboramiz
    movie = await get_movie(code)
    if not movie:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"❌ <b>{code}</b> kodli kino topilmadi.",
            parse_mode="HTML",
        )
        return

    success = await _forward_movie(callback.bot, user_id, movie)
    if not success:
        await callback.bot.send_message(
            chat_id=user_id,
            text="⚠️ Kinoni yuborishda xatolik yuz berdi. Keyinroq urinib ko'ring.",
        )
