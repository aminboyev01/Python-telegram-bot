import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import REQUIRED_CHANNELS
from database import register_user
from utils.subscription import check_subscription, subscription_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await register_user(user_id=user.id, username=user.username or "")
    logger.info("Foydalanuvchi: %s (id=%s)", user.full_name, user.id)

    # Majburiy obuna tekshiruvi
    if REQUIRED_CHANNELS:
        not_subscribed = await check_subscription(message.bot, user.id)
        if not_subscribed:
            kb = subscription_keyboard(not_subscribed, pending_code="start")
            await message.answer(
                f"👋 Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
                "🔒 Botdan foydalanish uchun avval quyidagi kanallarga "
                "obuna bo'lishingiz kerak:\n\n"
                "Obuna bo'lgach <b>✅ Obunani tekshirish</b> tugmasini bosing.",
                parse_mode="HTML",
                reply_markup=kb,
            )
            return

    # Obuna yo'q yoki hammasi to'g'ri
    await message.answer(
        f"👋 Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        "🎬 <b>Kino Botga xush kelibsiz!</b>\n\n"
        "📌 <b>Qanday ishlaydi?</b>\n"
        "1️⃣ Asosiy kanalimizda yoqqan kinoning kodini toping\n"
        "2️⃣ Shu kodni botga yuboring\n"
        "3️⃣ Bot kinoni sizga yuboradi 🍿\n\n"
        "📥 Kino kodini yuboring:",
        parse_mode="HTML",
    )
