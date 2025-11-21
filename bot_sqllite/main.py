from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CommandHandler
from telegram import ParseMode

from config import TOKEN
from send_buttons.send_menu import main_menu
from send_buttons.send_countries import send_countries_list
from send_buttons.send_jobs import send_jobs_list
from database import get_capital_by_country, get_salary


def start(update, context):
    update.message.reply_text(
        "Salom, Shohrux!👇\nQuyidagilardan birini tanlang:",
        reply_markup=main_menu()
    )


def message_handler(update, context):
    text = update.message.text

    if text == "Country":
        update.message.reply_text(
            "Mamlakatlardan birini tanlang:",
            reply_markup=send_countries_list()
        )

    elif text == "Job":
        update.message.reply_text(
            "Kasblardan birini tanlang:",
            reply_markup=send_jobs_list()
        )

    else:
        update.message.reply_text("Iltimos, menyudan tanlang!",reply_markup=main_menu() )


def callback_handler(update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("country_"):
        cid = data.split("_")[1]
        capital = get_capital_by_country(cid)
        query.answer()
        query.edit_message_text(f"🇨🇦 Poytaxt: <b>{capital}</b>", parse_mode=ParseMode.HTML)

    elif data.startswith("job_"):
        jid = data.split("_")[1]
        salary = get_salary(jid)
        query.answer()
        query.edit_message_text(f"💼 Oylik: <b>{salary}</b>", parse_mode=ParseMode.HTML)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # 👉 TO‘G‘RI ULASH
    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CallbackQueryHandler(callback_handler))
    dp.add_handler(MessageHandler(Filters.text, message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
