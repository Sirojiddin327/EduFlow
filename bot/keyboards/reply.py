from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def phone_buttons():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📱 Raqamni yuborish", request_contact=True),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )