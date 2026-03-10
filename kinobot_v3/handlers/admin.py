import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, Video, Document
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, STORAGE_CHANNEL_ID
from database import add_movie, delete_movie, list_movies, movie_count, user_count

router = Router()
logger = logging.getLogger(__name__)


# ─── FSM States ───────────────────────────────────────────────────────────────

class AdminStates(StatesGroup):
    waiting_for_video = State()


# ─── Admin filter ─────────────────────────────────────────────────────────────

def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


# ─── /add <kod> ───────────────────────────────────────────────────────────────

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer(
            "❗ Foydalanish: <code>/add &lt;kod&gt;</code>\n"
            "Misol: <code>/add 101</code>",
            parse_mode="HTML",
        )
        return

    code = parts[1].strip()
    await state.update_data(code=code)
    await state.set_state(AdminStates.waiting_for_video)
    await message.answer(
        f"📹 <b>{code}</b> kodi uchun video yuboring.\n\n"
        "⚠️ Video <b>private kanal</b>ga forward bo'lishi uchun "
        "botni kanalga admin qilib qo'shganingizni tekshiring.",
        parse_mode="HTML",
    )


@router.message(AdminStates.waiting_for_video, F.video | F.document)
async def receive_video(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return

    data = await state.get_data()
    code = data.get("code")

    # Video yoki document sifatida qabul qilish
    media = message.video or message.document
    if not media:
        await message.answer("❗ Iltimos, video yuboring.")
        return

    try:
        # Private kanalga yuborish va message_id olish
        forwarded = await message.forward(chat_id=STORAGE_CHANNEL_ID)
        message_id = forwarded.message_id
    except Exception as e:
        logger.error("Kanalga yuborish xatosi: %s", e)
        await message.answer(
            "⚠️ Kanalga yuborishda xatolik!\n"
            "Botni kanalga admin qilib qo'shdingizmi?"
        )
        await state.clear()
        return

    success = await add_movie(code=code, message_id=message_id)
    await state.clear()

    if success:
        await message.answer(
            f"✅ Kino muvaffaqiyatli qo'shildi!\n\n"
            f"🔢 Kod: <code>{code}</code>\n"
            f"🆔 Message ID: <code>{message_id}</code>",
            parse_mode="HTML",
        )
        logger.info("Kino qo'shildi: kod=%s, message_id=%s", code, message_id)
    else:
        # Kanal xabari zoe ketmasin — o'chirib tashlaymiz
        try:
            await message.bot.delete_message(
                chat_id=STORAGE_CHANNEL_ID, message_id=message_id
            )
        except Exception:
            pass
        await message.answer(
            f"⚠️ <b>{code}</b> kodi allaqachon mavjud!\n"
            "Avval /delete buyrug'i bilan o'chiring.",
            parse_mode="HTML",
        )


@router.message(AdminStates.waiting_for_video)
async def wrong_file_type(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    await message.answer("❗ Iltimos, faqat video yuboring.")


# ─── /delete <kod> ────────────────────────────────────────────────────────────

@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer(
            "❗ Foydalanish: <code>/delete &lt;kod&gt;</code>\n"
            "Misol: <code>/delete 101</code>",
            parse_mode="HTML",
        )
        return

    code = parts[1].strip()
    deleted = await delete_movie(code)

    if deleted:
        await message.answer(
            f"🗑 <b>{code}</b> kodi o'chirildi.", parse_mode="HTML"
        )
        logger.info("Kino o'chirildi: kod=%s", code)
    else:
        await message.answer(
            f"❌ <b>{code}</b> kodi topilmadi.", parse_mode="HTML"
        )


# ─── /list ────────────────────────────────────────────────────────────────────

@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    movies = await list_movies()
    if not movies:
        await message.answer("📭 Hozircha hech qanday kino yo'q.")
        return

    lines = ["🎬 <b>Kinolar ro'yxati:</b>\n"]
    for m in movies:
        title = m["title"] or "—"
        lines.append(
            f"• Kod: <code>{m['code']}</code> | "
            f"ID: <code>{m['message_id']}</code>"
        )

    # Telegram 4096 belgidan oshmasin
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (ro'yxat qisqartirildi)"

    await message.answer(text, parse_mode="HTML")


# ─── /stats ───────────────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    m_count = await movie_count()
    u_count = await user_count()

    await message.answer(
        "📊 <b>Bot statistikasi:</b>\n\n"
        f"🎬 Kinolar soni: <b>{m_count}</b>\n"
        f"👤 Foydalanuvchilar soni: <b>{u_count}</b>",
        parse_mode="HTML",
    )


# ─── /channels ────────────────────────────────────────────────────────────────

@router.message(Command("channels"))
async def cmd_channels(message: Message) -> None:
    """Majburiy obuna kanallarini ko'rsatish."""
    if not is_admin(message):
        await message.answer("⛔ Siz admin emassiz.")
        return

    from config import REQUIRED_CHANNELS

    if not REQUIRED_CHANNELS:
        await message.answer(
            "📭 Hozircha majburiy obuna kanallari yo'q.\n\n"
            "Qo'shish uchun <code>.env</code> faylida "
            "<code>REQUIRED_CHANNELS</code> ni sozlang.",
            parse_mode="HTML",
        )
        return

    lines = ["📢 <b>Majburiy obuna kanallari:</b>\n"]
    for i, ch in enumerate(REQUIRED_CHANNELS, start=1):
        lines.append(f"{i}. ID: <code>{ch['id']}</code>\n   Link: {ch['link']}")

    await message.answer("\n".join(lines), parse_mode="HTML")
