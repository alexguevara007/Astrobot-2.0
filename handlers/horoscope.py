from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
import time
from datetime import datetime

from services.gpt_horoscope import generate_horoscope
from keyboards import get_zodiac_inline_keyboard, get_back_to_menu_inline

logger = logging.getLogger(__name__)

# Карта знаков зодиака
ZODIAC_SIGNS = {
    "овен":      {"eng": "aries",       "emoji": "♈️", "element": "🔥 Огонь",    "planet": "♂️ Марс"},
    "телец":     {"eng": "taurus",      "emoji": "♉️", "element": "🌍 Земля",    "planet": "♀️ Венера"},
    "близнецы":  {"eng": "gemini",      "emoji": "♊️", "element": "💨 Воздух",   "planet": "☿ Меркурий"},
    "рак":       {"eng": "cancer",      "emoji": "♋️", "element": "💧 Вода",     "planet": "🌙 Луна"},
    "лев":       {"eng": "leo",         "emoji": "♌️", "element": "🔥 Огонь",    "planet": "☀️ Солнце"},
    "дева":      {"eng": "virgo",       "emoji": "♍️", "element": "🌍 Земля",    "planet": "☿ Меркурий"},
    "весы":      {"eng": "libra",       "emoji": "♎️", "element": "💨 Воздух",   "planet": "♀️ Венера"},
    "скорпион":  {"eng": "scorpio",     "emoji": "♏️", "element": "💧 Вода",     "planet": "♇ Плутон"},
    "стрелец":   {"eng": "sagittarius", "emoji": "♐️", "element": "🔥 Огонь",    "planet": "♃ Юпитер"},
    "козерог":   {"eng": "capricorn",   "emoji": "♑️", "element": "🌍 Земля",    "planet": "♄ Сатурн"},
    "водолей":   {"eng": "aquarius",    "emoji": "♒️", "element": "💨 Воздух",   "planet": "⛢ Уран"},
    "рыбы":      {"eng": "pisces",      "emoji": "♓️", "element": "💧 Вода",     "planet": "♆ Нептун"}
}

# Клавиатура после гороскопа
def get_horoscope_actions_keyboard(sign: str, day: str, detailed: bool = False):
    buttons = []

    if not detailed:
        buttons.append([
            InlineKeyboardButton("📝 Подробнее", callback_data=f"horoscope:{sign}:{day}:true")
        ])

    buttons.extend([
        [InlineKeyboardButton("🔮 Другой знак", callback_data=f"horoscope_menu:{day}")],
        [InlineKeyboardButton("« Назад в меню", callback_data="main_menu")]
    ])
    
    return InlineKeyboardMarkup(buttons)


async def send_horoscope(update_or_query, sign: str, day: str, detailed: bool = False):
    sign_lower = sign.lower()

    if sign_lower not in ZODIAC_SIGNS:
        text = "🚫 Неверный знак зодиака. Попробуйте ещё раз."
        reply_markup = get_zodiac_inline_keyboard("horoscope")
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update_or_query.edit_message_text(text, reply_markup=reply_markup)
        return

    sign_info = ZODIAC_SIGNS[sign_lower]

    loading_text = (
        f"{sign_info['emoji']} Генерация гороскопа для {sign.title()}\n"
        f"Стихия: {sign_info['element']}\n"
        f"Управитель: {sign_info['planet']}\n\n"
        "⏳ Пожалуйста, подождите..."
    )

    if hasattr(update_or_query, 'message'):
        message = await update_or_query.message.reply_text(loading_text)
    else:
        message = await update_or_query.edit_message_text(loading_text)

    try:
        start_time = time.time()
        horoscope_text = generate_horoscope(sign_info["eng"], day=day, detailed=detailed)
        duration = time.time() - start_time
        logger.info(f"Гороскоп для {sign} сгенерирован за {duration:.2f} сек")
    except Exception as e:
        logger.error(f"Ошибка генерации гороскопа: {e}")
        await message.edit_text(
            "⚠️ Ошибка при генерации гороскопа. Попробуйте позже.",
            reply_markup=get_back_to_menu_inline()
        )
        return

    day_text = "сегодня" if day == "today" else "завтра"
    current_date = datetime.now().strftime("%d.%m.%Y")

    header = (
        f"{sign_info['emoji']} <b>{sign.title()}</b>\n"
        f"Стихия: {sign_info['element']}\n"
        f"Планета: {sign_info['planet']}\n"
        f"<b>{'Подробный' if detailed else 'Краткий'} гороскоп на {day_text} ({current_date})</b>\n"
        f"{'─' * 30}\n\n"
    )

    response = header + horoscope_text

    # Отправка сообщения
    try:
        await message.edit_text(
            text=response,
            reply_markup=get_horoscope_actions_keyboard(sign, day, detailed),
            parse_mode="HTML"
        )
    except BadRequest as e:
        if "Message is too long" in str(e):
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for i, part in enumerate(parts):
                if i == 0:
                    await message.edit_text(part)
                else:
                    await message.reply_text(part)
            await message.reply_text("Выберите действие:", reply_markup=get_horoscope_actions_keyboard(sign, day, detailed))
        else:
            raise


# Команды
async def horoscope_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reply_markup = get_zodiac_inline_keyboard("horoscope")
        text = "🔮 Выберите знак зодиака:"
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"horoscope_today error: {e}")
        await update.effective_message.reply_text("⚠️ Ошибка. Попробуйте позже.", reply_markup=get_back_to_menu_inline())


async def horoscope_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reply_markup = get_zodiac_inline_keyboard("horoscope_tomorrow")
        text = "🌜 Выберите знак зодиака:"
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"horoscope_tomorrow error: {e}")
        await update.effective_message.reply_text("⚠️ Ошибка. Попробуйте позже.", reply_markup=get_back_to_menu_inline())


# Обработка кнопок
async def handle_zodiac_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if ":" not in data:
            await query.message.edit_text("⚠️ Неверные данные.", reply_markup=get_back_to_menu_inline())
            return

        parts = data.split(":")

        # ✅ Обработка кнопки "🔮 Другой знак"
        if parts[0] == "horoscope_menu":
            day = parts[1] if len(parts) > 1 else "today"
            selected_markup = get_zodiac_inline_keyboard("horoscope_tomorrow" if day == "tomorrow" else "horoscope")
            await query.message.edit_text(
                "🔮 Выберите знак зодиака:" if day == "today" else "🌜 Выберите знак зодиака:",
                reply_markup=selected_markup
            )
            return

        # ✅ Обработка выбора знака
        if len(parts) == 4:
            _, sign, day, detailed = parts
            await send_horoscope(query, sign, day, detailed.lower() == "true")
        elif len(parts) == 2:
            # Например: horoscope:овен или horoscope_tomorrow:овен
            prefix, sign = parts
            day = "tomorrow" if prefix == "horoscope_tomorrow" else "today"
            await send_horoscope(query, sign, day, detailed=False)
        else:
            await query.message.edit_text("⚠️ Неверный формат данных гороскопа.", reply_markup=get_back_to_menu_inline())

    except Exception as e:
        logger.error(f"Ошибка в handle_zodiac_callback: {e}")
        await update.effective_message.reply_text("⚠️ Не удалось обработать запрос.", reply_markup=get_back_to_menu_inline())
