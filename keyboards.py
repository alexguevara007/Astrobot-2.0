from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# 🔮 Знаки зодиака (для гороскопов и подписки)
ZODIAC_SIGNS = [
    ["Овен", "Телец", "Близнецы"],
    ["Рак", "Лев", "Дева"],
    ["Весы", "Скорпион", "Стрелец"],
    ["Козерог", "Водолей", "Рыбы"]
]


def get_main_menu_keyboard():
    """
    Обычная клавиатура, отображается под полем ввода сообщений.
    Используется после команд /start, /menu.
    """
    keyboard = [
        ["🌞 Гороскоп на сегодня", "🌜 Гороскоп на завтра"],
        ["🃏 Таро-карта дня", "🔮 Таро 3 карты"],
        ["✨ Таро 5 карт", "❤️ Совместимость"],
        ["🔔 Подписка"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_zodiac_inline_keyboard(prefix: str = "horoscope") -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для выбора знака зодиака по префиксу.
    Используется для получения гороскопа на сегодня/завтра.
    Пример callback_data: horoscope:овен
    """
    keyboard = [
        [
            InlineKeyboardButton(sign, callback_data=f"{prefix}:{sign.lower()}")
            for sign in row
        ] for row in ZODIAC_SIGNS
    ]

    keyboard.append([
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_zodiac_subscribe_keyboard() -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для выбора знака с целью подписки.
    Пример callback_data: subscribe_овен
    """
    keyboard = [
        [
            InlineKeyboardButton(sign, callback_data=f"subscribe_{sign.lower()}")
            for sign in row
        ] for row in ZODIAC_SIGNS
    ]

    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_inline() -> InlineKeyboardMarkup:
    """
    Одна кнопка: вернуться в меню.
    Используется как переход после любых действий.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Вернуться в меню", callback_data="back_to_menu")]
    ])


def get_inline_menu(options: list[tuple[str, str]], row_width: int = 2) -> InlineKeyboardMarkup:
    """
    Генератор произвольной inline-клавиатуры из списка.
    :param options: список пар ("текст кнопки", "callback_data")
    :param row_width: сколько кнопок в ряду
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text, callback_data=data)
            for text, data in options[i:i+row_width]
        ]
        for i in range(0, len(options), row_width)
    ])


def get_back_or_repeat_inline(prefix: str = "main_menu", repeat_command: str = "") -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками: Повторить + Вернуться в меню.
    Можно передать обе кнопки, или только одну.
    """
    buttons = []
    
    if repeat_command:
        buttons.append(InlineKeyboardButton("🔄 Повторить", callback_data=repeat_command))
    
    buttons.append(InlineKeyboardButton("🏠 Главное меню", callback_data=prefix))

    return InlineKeyboardMarkup([buttons])
