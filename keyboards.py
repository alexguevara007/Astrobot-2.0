from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from services.locales import get_text  # перевод текстов по ключам с учетом языка пользователя

# 🔮 Знаки зодиака (для гороскопов и подписки)
ZODIAC_SIGNS = [
    ["Овен", "Телец", "Близнецы"],
    ["Рак", "Лев", "Дева"],
    ["Весы", "Скорпион", "Стрелец"],
    ["Козерог", "Водолей", "Рыбы"]
]

def get_main_menu_keyboard(lang="ru"):
    """
    Главное меню ReplyKeyboardMarkup (под полем ввода)
    """
    keyboard = [
        [get_text("today_horoscope", lang), get_text("tomorrow_horoscope", lang)],
        [get_text("tarot_one", lang), get_text("tarot_three", lang)],
        [get_text("tarot_five", lang), get_text("compatibility", lang)],
        [get_text("magic_ball", lang), get_text("subscribe", lang)],
        [f"🌐 {'Русский 🇷🇺' if lang == 'en' else 'English 🇬🇧'}"]  # кнопка смены языка
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_zodiac_inline_keyboard(prefix: str = "horoscope", lang="ru") -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для выбора знака (гороскоп)
    Пример callback: horoscope:овен
    """
    keyboard = [
        [
            InlineKeyboardButton(sign, callback_data=f"{prefix}:{sign.lower()}")
            for sign in row
        ] for row in ZODIAC_SIGNS
    ]

    keyboard.append([
        InlineKeyboardButton(get_text("main_menu", lang), callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_zodiac_subscribe_keyboard(lang="ru") -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для подписки по знаку
    Пример callback: subscribe_овен
    """
    keyboard = [
        [
            InlineKeyboardButton(sign, callback_data=f"subscribe_{sign.lower()}")
            for sign in row
        ] for row in ZODIAC_SIGNS
    ]

    keyboard.append([
        InlineKeyboardButton(get_text("back", lang), callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

def get_back_to_menu_inline(lang="ru") -> InlineKeyboardMarkup:
    """
    Inline-кнопка "Вернуться в меню"
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("back_to_menu", lang), callback_data="back_to_menu")]
    ])

def get_inline_menu(options: list[tuple[str, str]], row_width: int = 2) -> InlineKeyboardMarkup:
    """
    Произвольная inline-клавиатура из списка пар ("текст", "callback")
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text, callback_data=data)
            for text, data in options[i:i+row_width]
        ]
        for i in range(0, len(options), row_width)
    ])

def get_back_or_repeat_inline(prefix: str = "main_menu", repeat_command: str = "", lang="ru") -> InlineKeyboardMarkup:
    """
    Inline-кнопки: Повторить и Назад
    """
    buttons = []
    
    if repeat_command:
        buttons.append(InlineKeyboardButton(get_text("repeat", lang), callback_data=repeat_command))
    
    buttons.append(InlineKeyboardButton(get_text("main_menu", lang), callback_data=prefix))

    return InlineKeyboardMarkup([buttons])
