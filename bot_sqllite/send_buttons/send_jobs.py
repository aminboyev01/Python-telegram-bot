from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_jobs


def send_jobs_list():
    jobs = get_jobs()
    keyboard = []

    for jid, title in jobs:
        keyboard.append([InlineKeyboardButton(title, callback_data=f"job_{jid}")])

    return InlineKeyboardMarkup(keyboard)
