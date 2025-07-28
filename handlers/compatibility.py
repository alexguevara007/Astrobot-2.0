from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os
import copy

from keyboards import get_back_to_menu_inline


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


# Клавиатура выбора знака зодиака
def get_sign_selection_keyboard(step: str = "first"):
    signs = [
        ["Овен", "Телец", "Близнецы"],
        ["Рак", "Лев", "Дева"],
        ["Весы", "Скорпион", "Стрелец"],
        ["Козерог", "Водолей", "Рыбы"]
    ]

    keyboard = []
    for row in signs:
        keyboard_row = [
            InlineKeyboardButton(
                sign, callback_data=f"compatibility_{step}:{sign.lower()}"
            ) for sign in row
        ]
        keyboard.append(keyboard_row)

    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


# Получение текста совместимости
def get_compatibility_text(sign1: str, sign2: str) -> str:
    try:
        compatibility = COMPATIBILITY_DATA[sign1.lower()][sign2.lower()]
        return (
            f"<b>Совместимость {sign1.title()} + {sign2.title()}</b>\n\n"
            f"✨ <b>Общая:</b> {compatibility['general']}\n"
            f"❤️ <b>Любовь:</b> {compatibility['love']}\n"
            f"👫 <b>Дружба:</b> {compatibility['friendship']}\n"
            f"💼 <b>Работа:</b> {compatibility['work']}\n\n"
            f"<i>{compatibility['description']}</i>"
        )
    except Exception as e:
        print(f"[ERROR] Ошибка при получении совместимости: {e}")
        return "⚠️ Данные о совместимости не найдены."


# Обработчик совместимости
async def compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not hasattr(context, 'user_data'):
            context.user_data = {}

        if update.callback_query:
            query = update.callback_query
            data = query.data

            if data == "compatibility":
                await query.message.edit_text(
                    "❤️ Выберите первый знак зодиака:",
                    reply_markup=get_sign_selection_keyboard("first")
                )

            elif data.startswith("compatibility_first:"):
                sign = data.split(":")[1]
                context.user_data['first_sign'] = sign

                await query.message.edit_text(
                    f"Первый знак: <b>{sign.title()}</b>\n\nВыберите второй знак:",
                    reply_markup=get_sign_selection_keyboard("second"),
                    parse_mode="HTML"
                )

            elif data.startswith("compatibility_second:"):
                second_sign = data.split(":")[1]
                first_sign = context.user_data.get('first_sign')

                if not first_sign:
                    await query.message.edit_text(
                        "⚠️ Ошибка: сначала выберите первый знак.",
                        reply_markup=get_back_to_menu_inline()
                    )
                    return

                result = get_compatibility_text(first_sign, second_sign)

                await query.message.edit_text(
                    result,
                    reply_markup=get_back_to_menu_inline(),
                    parse_mode="HTML"
                )

                context.user_data.pop("first_sign", None)

        else:
            await update.message.reply_text(
                "❤️ Выберите первый знак зодиака:",
                reply_markup=get_sign_selection_keyboard("first")
            )

    except Exception as e:
        error_message = f"[ERROR] Произошла ошибка: {str(e)}"
        print(error_message)
        if update.callback_query:
            await update.callback_query.message.edit_text(
                error_message,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                error_message,
                reply_markup=get_back_to_menu_inline()
            )