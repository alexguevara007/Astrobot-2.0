from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os
import copy

from keyboards import get_back_to_menu_inline
from locales import get_text

# Загрузка данных совместимости из JSON
with open("data/compatibility.json", encoding="utf-8") as f:
    COMPATIBILITY_DATA = json.load(f)

# Автоматическое добавление обратных сочетаний
for sign1 in list(COMPATIBILITY_DATA.keys()):
    for sign2 in COMPATIBILITY_DATA[sign1]:
        if sign2 not in COMPATIBILITY_DATA:
            COMPATIBILITY_DATA[sign2] = {}
        if sign1 not in COMPATIBILITY_DATA[sign2]:
            COMPATIBILITY_DATA[sign2][sign1] = copy.deepcopy(COMPATIBILITY_DATA[sign1][sign2])

# Универсальные ключи знаков (на английском lower для JSON и callback)
ZODIAC_KEYS = [
    "aries", "taurus", "gemini",
    "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius",
    "capricorn", "aquarius", "pisces"
]

# Отображаемые названия знаков по языкам
ZODIAC_DISPLAY = {
    'ru': [
        "Овен", "Телец", "Близнецы",
        "Рак", "Лев", "Дева",
        "Весы", "Скорпион", "Стрелец",
        "Козерог", "Водолей", "Рыбы"
    ],
    'en': [
        "Aries", "Taurus", "Gemini",
        "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius",
        "Capricorn", "Aquarius", "Pisces"
    ]
}

# Клавиатура выбора знака зодиака
def get_sign_selection_keyboard(step: str = "first", lang: str = 'ru'):
    display_names = ZODIAC_DISPLAY.get(lang, ZODIAC_DISPLAY['ru'])
    
    keyboard = []
    for i in range(0, len(display_names), 3):
        row = display_names[i:i+3]
        keyboard_row = [
            InlineKeyboardButton(
                name, callback_data=f"compatibility_{step}:{ZODIAC_KEYS[i + j]}"
            ) for j, name in enumerate(row)
        ]
        keyboard.append(keyboard_row)

    keyboard.append([InlineKeyboardButton(get_text('back_to_menu', lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

# Получение текста совместимости
def get_compatibility_text(sign1: str, sign2: str, lang: str = 'ru') -> str:
    try:
        compatibility = COMPATIBILITY_DATA[sign1][sign2]
        
        sign1_display = next((d for k, d in zip(ZODIAC_KEYS, ZODIAC_DISPLAY[lang]) if k == sign1), sign1.title())
        sign2_display = next((d for k, d in zip(ZODIAC_KEYS, ZODIAC_DISPLAY[lang]) if k == sign2), sign2.title())
        
        return get_text(
            'compatibility_result', 
            lang,
            sign1=sign1_display,
            sign2=sign2_display,
            general=compatibility['general'],
            love=compatibility['love'],
            friendship=compatibility['friendship'],
            work=compatibility['work'],
            description=compatibility['description']
        )
    except Exception as e:
        print(f"[ERROR] Ошибка при получении совместимости: {e}")
        return get_text('compatibility_error', lang)

# Обработчик совместимости
async def compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        if not hasattr(context, 'user_data'):
            context.user_data = {}

        if update.callback_query:
            query = update.callback_query
            data = query.data

            if data == "compatibility":
                await query.message.edit_text(
                    get_text('compatibility_select', lang),
                    reply_markup=get_sign_selection_keyboard("first", lang)
                )

            elif data.startswith("compatibility_first:"):
                sign_key = data.split(":")[1]
                context.user_data['first_sign'] = sign_key
                
                first_display = next((d for k, d in zip(ZODIAC_KEYS, ZODIAC_DISPLAY[lang]) if k == sign_key), sign_key.title())

                await query.message.edit_text(
                    get_text('compatibility_second_select', lang, sign=first_display),
                    reply_markup=get_sign_selection_keyboard("second", lang),
                    parse_mode="HTML"
                )

            elif data.startswith("compatibility_second:"):
                second_sign = data.split(":")[1]
                first_sign = context.user_data.get('first_sign')

                if not first_sign:
                    await query.message.edit_text(
                        get_text('compatibility_error_first', lang),
                        reply_markup=get_back_to_menu_inline(lang=lang)
                    )
                    return

                result = get_compatibility_text(first_sign, second_sign, lang)

                await query.message.edit_text(
                    result,
                    reply_markup=get_back_to_menu_inline(lang=lang),
                    parse_mode="HTML"
                )

                context.user_data.pop("first_sign", None)

        else:
            await update.message.reply_text(
                get_text('compatibility_select', lang),
                reply_markup=get_sign_selection_keyboard("first", lang)
            )

    except Exception as e:
        error_message = get_text('error', lang)
        print(f"[ERROR] Произошла ошибка: {str(e)}")
        if update.callback_query:
            await update.callback_query.message.edit_text(
                error_message,
                reply_markup=get_back_to_menu_inline(lang=lang)
            )
        else:
            await update.message.reply_text(
                error_message,
                reply_markup=get_back_to_menu_inline(lang=lang)
            )
