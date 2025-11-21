from telegram import ReplyKeyboardMarkup

def main_menu():
    markup = ReplyKeyboardMarkup(
        [['Country', 'Job']],
        resize_keyboard=True
    )
    return markup
