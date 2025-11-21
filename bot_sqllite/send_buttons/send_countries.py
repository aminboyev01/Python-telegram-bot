from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_countries


def send_countries_list():
    countries = get_countries()
    keyboard = []

    for cid, name in countries:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"country_{cid}")])

    return InlineKeyboardMarkup(keyboard)
