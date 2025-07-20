from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
import time
from datetime import datetime

from services.generate_horoscope import generate_horoscope
from keyboards import get_zodiac_inline_keyboard, get_back_to_menu_inline
from locales import get_text

logger = logging.getLogger(__name__)

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


def get_horoscope_actions_keyboard(sign: str, day: str, detailed: bool = False, lang: str = 'ru'):
    buttons = []

    if not detailed:
        buttons.append([
            InlineKeyboardButton(get_text('detailed_button', lang), callback_data=f"horoscope:{sign}:{day}:true")
        ])

    buttons.extend([
        [InlineKeyboardButton(get_text('another_sign', lang), callback_data=f"horoscope_menu:{day}")],
        [InlineKeyboardButton(get_text('back_to_menu', lang), callback_data="main_menu")]
    ])
    
    return InlineKeyboardMarkup(buttons)


async def send_horoscope(update_or_query, context: ContextTypes.DEFAULT_TYPE, sign: str, day: str, detailed: bool = False):
    lang = context.user_data.get('lang', 'ru')
    sign_lower = sign.lower()

    if sign_lower not in ZODIAC_SIGNS:
        text = get_text('invalid_sign', lang)
        reply_markup = get_zodiac_inline_keyboard("horoscope")
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update_or_query.edit_message_text(text, reply_markup=reply_markup)
        return

    sign_info = ZODIAC_SIGNS[sign_lower]

    loading_text = get_text('horoscope_loading', lang, emoji=sign_info['emoji'], sign=sign.title(),
                            element=sign_info['element'], planet=sign_info['planet'])

    if hasattr(update_or_query, 'message'):
        message = await update_or_query.message.reply_text(loading_text)
    else:
        message = await update_or_query.edit_message_text(loading_text)

    try:
        start_time = time.time()
        horoscope_text = generate_horoscope(sign_info["eng"], day=day, detailed=detailed, lang=lang)
        duration = time.time() - start_time
        logger.info(f"Гороскоп для {sign} сгенерирован за {duration:.2f} сек")
    except Exception as e:
        logger.error(f"Ошибка генерации гороскопа: {e}")
        await message.edit_text(
            get_text('horoscope_error', lang),
            reply_markup=get_back_to_menu_inline()
        )
        return

    day_text = get_text(f'day_{day}', lang)
    current_date = datetime.now().strftime("%d.%m.%Y")

    detailed_type = get_text('detailed_type_detailed' if detailed else 'detailed_type_short', lang)

    header = get_text('horoscope_header', lang, emoji=sign_info['emoji'], sign=sign.title(),
                      element=sign_info['element'], planet=sign_info['planet'],
                      detailed_type=detailed_type, day_text=day_text, date=current_date)

    response = header + horoscope_text

    try:
        await message.edit_text(
            text=response,
            reply_markup=get_horoscope_actions_keyboard(sign, day, detailed, lang),
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
            await message.reply_text(get_text('choose_action', lang), reply_markup=get_horoscope_actions_keyboard(sign, day, detailed, lang))
        else:
            raise


async def horoscope_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    try:
        reply_markup = get_zodiac_inline_keyboard("horoscope")
        text = get_text('zodiac_select', lang)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"horoscope_today error: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_back_to_menu_inline())


async def horoscope_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    try:
        reply_markup = get_zodiac_inline_keyboard("horoscope_tomorrow")
        text = get_text('zodiac_select_tomorrow', lang)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"horoscope_tomorrow error: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_back_to_menu_inline())


async def handle_zodiac_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if ":" not in data:
            await query.message.edit_text(get_text('invalid_data', lang), reply_markup=get_back_to_menu_inline())
            return

        parts = data.split(":")

        if parts[0] == "horoscope_menu":
            day = parts[1] if len(parts) > 1 else "today"
            markup = get_zodiac_inline_keyboard("horoscope_tomorrow" if day == "tomorrow" else "horoscope")
            text = get_text('zodiac_select', lang) if day == "today" else get_text('zodiac_select_tomorrow', lang)
            await query.message.edit_text(text, reply_markup=markup)
            return

        if len(parts) == 4:
            _, sign, day, detailed = parts
            await send_horoscope(query, context, sign, day, detailed.lower() == "true")
        elif len(parts) == 2:
            prefix, sign = parts
            day = "tomorrow" if prefix == "horoscope_tomorrow" else "today"
            await send_horoscope(query, context, sign, day, detailed=False)
        else:
            await query.message.edit_text(get_text('invalid_format', lang), reply_markup=get_back_to_menu_inline())

    except Exception as e:
        logger.error(f"handle_zodiac_callback error: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_back_to_menu_inline())
