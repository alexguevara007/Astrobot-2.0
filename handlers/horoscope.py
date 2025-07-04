from telegram import Update
from telegram.ext import ContextTypes
from services.gpt_horoscope import generate_horoscope
from keyboards import get_zodiac_inline_keyboard, get_back_to_menu_inline

# Карта знаков
SIGNS = {
    "овен": "aries", "телец": "taurus", "близнецы": "gemini",
    "рак": "cancer", "лев": "leo", "дева": "virgo",
    "весы": "libra", "скорпион": "scorpio", "стрелец": "sagittarius",
    "козерог": "capricorn", "водолей": "aquarius", "рыбы": "pisces"
}

async def send_horoscope(update_or_query, sign: str, day: str):
    """Отправляет гороскоп пользователю"""
    try:
        # Проверка знака
        if sign.lower() not in SIGNS:
            text = "🚫 Неверный знак зодиака. Попробуйте ещё раз."
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(text)
            else:
                await update_or_query.edit_message_text(text)
            return

        sign_eng = SIGNS[sign.lower()]
        
        # Сообщение о генерации
        loading_text = "🔮 Генерируется гороскоп..." if day == "today" else "🌙 Генерируется гороскоп на завтра..."
        if hasattr(update_or_query, 'message'):
            message = await update_or_query.message.reply_text(loading_text)
        else:
            message = await update_or_query.edit_message_text(loading_text)

        # Получаем гороскоп
        horoscope_text = generate_horoscope(sign_eng, day=day)

        # Формируем ответ
        day_text = "сегодня" if day == "today" else "завтра"
        response = f"♈ Гороскоп для {sign.title()} на {day_text}:\n\n{horoscope_text}"

        # Отправляем ответ
        await message.edit_text(
            text=response,
            reply_markup=get_back_to_menu_inline()
        )

    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(
                error_message,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update_or_query.edit_message_text(
                error_message,
                reply_markup=get_back_to_menu_inline()
            )

async def horoscope_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды гороскопа на сегодня"""
    try:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "🔮 Выберите знак зодиака:",
                reply_markup=get_zodiac_inline_keyboard("horoscope")
            )
        else:
            await update.message.reply_text(
                "🔮 Выберите знак зодиака:",
                reply_markup=get_zodiac_inline_keyboard("horoscope")
            )
    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)

async def horoscope_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды гороскопа на завтра"""
    try:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "🌜 Выберите знак зодиака:",
                reply_markup=get_zodiac_inline_keyboard("horoscope_tomorrow")
            )
        else:
            await update.message.reply_text(
                "🌜 Выберите знак зодиака:",
                reply_markup=get_zodiac_inline_keyboard("horoscope_tomorrow")
            )
    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)

async def handle_zodiac_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки выбора знака зодиака"""
    try:
        query = update.callback_query
        data = query.data

        if ":" not in data:
            await query.message.edit_text(
                "⚠️ Неверный формат данных. Вернитесь в главное меню:",
                reply_markup=get_back_to_menu_inline()
            )
            return

        prefix, sign = data.split(":", 1)
        
        if prefix == "horoscope":
            await send_horoscope(query, sign, day="today")
        elif prefix == "horoscope_tomorrow":
            await send_horoscope(query, sign, day="tomorrow")
        else:
            await query.message.edit_text(
                "⚠️ Неизвестный тип гороскопа. Вернитесь в главное меню:",
                reply_markup=get_back_to_menu_inline()
            )

    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        await update.callback_query.message.reply_text(
            error_message,
            reply_markup=get_back_to_menu_inline()
        )