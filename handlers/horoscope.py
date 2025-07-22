import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from services.generate_horoscope import generate_horoscope
from keyboards import get_zodiac_inline_keyboard, get_back_to_menu_inline
from services.locales import get_text

logger = logging.getLogger(__name__)

# Списки знаков и отображаемые имена
ZODIAC_KEYS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

ZODIAC_DISPLAY = {
    'ru': {
        "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы", "cancer": "Рак",
        "leo": "Лев", "virgo": "Дева", "libra": "Весы", "scorpio": "Скорпион",
        "sagittarius": "Стрелец", "capricorn": "Козерог", "aquarius": "Водолей", "pisces": "Рыбы"
    },
    'en': {
        "aries": "Aries", "taurus": "Taurus", "gemini": "Gemini", "cancer": "Cancer",
        "leo": "Leo", "virgo": "Virgo", "libra": "Libra", "scorpio": "Scorpio",
        "sagittarius": "Sagittarius", "capricorn": "Capricorn", "aquarius": "Aquarius", "pisces": "Pisces"
    }
}

ZODIAC_INFO = {
    "aries":       {"emoji": "♈️", "element_ru": "🔥 Огонь", "planet_ru": "♂️ Марс", "element_en": "🔥 Fire", "planet_en": "♂️ Mars"},
    "taurus":      {"emoji": "♉️", "element_ru": "🌍 Земля", "planet_ru": "♀️ Венера", "element_en": "🌍 Earth", "planet_en": "♀️ Venus"},
    "gemini":      {"emoji": "♊️", "element_ru": "💨 Воздух", "planet_ru": "☿ Меркурий", "element_en": "💨 Air", "planet_en": "☿ Mercury"},
    "cancer":      {"emoji": "♋️", "element_ru": "💧 Вода", "planet_ru": "🌙 Луна", "element_en": "💧 Water", "planet_en": "🌙 Moon"},
    "leo":         {"emoji": "♌️", "element_ru": "🔥 Огонь", "planet_ru": "☀️ Солнце", "element_en": "🔥 Fire", "planet_en": "☀️ Sun"},
    "virgo":       {"emoji": "♍️", "element_ru": "🌍 Земля", "planet_ru": "☿ Меркурий", "element_en": "🌍 Earth", "planet_en": "☿ Mercury"},
    "libra":       {"emoji": "♎️", "element_ru": "💨 Воздух", "planet_ru": "♀️ Венера", "element_en": "💨 Air", "planet_en": "♀️ Venus"},
    "scorpio":     {"emoji": "♏️", "element_ru": "💧 Вода", "planet_ru": "♇ Плутон", "element_en": "💧 Water", "planet_en": "♇ Pluto"},
    "sagittarius": {"emoji": "♐️", "element_ru": "🔥 Огонь", "planet_ru": "♃ Юпитер", "element_en": "🔥 Fire", "planet_en": "♃ Jupiter"},
    "capricorn":   {"emoji": "♑️", "element_ru": "🌍 Земля", "planet_ru": "♄ Сатурн", "element_en": "🌍 Earth", "planet_en": "♄ Saturn"},
    "aquarius":    {"emoji": "♒️", "element_ru": "💨 Воздух", "planet_ru": "⛢ Уран", "element_en": "💨 Air", "planet_en": "⛢ Uranus"},
    "pisces":      {"emoji": "♓️", "element_ru": "💧 Вода", "planet_ru": "♆ Нептун", "element_en": "💧 Water", "planet_en": "♆ Neptune"}
}

# Кнопки под каждым гороскопом
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

# Основной вывод гороскопа
async def send_horoscope(update_or_query, context: ContextTypes.DEFAULT_TYPE, sign: str, day: str, detailed: bool = False, lang: str = 'ru'):
    if sign not in ZODIAC_INFO:
        text = get_text('invalid_sign', lang)
        reply_markup = get_zodiac_inline_keyboard("horoscope", lang=lang)
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update_or_query.edit_message_text(text, reply_markup=reply_markup)
        return

    sign_info = ZODIAC_INFO[sign]
    sign_display = ZODIAC_DISPLAY.get(lang, ZODIAC_DISPLAY['ru'])[sign]
    element = sign_info[f'element_{lang}']
    planet = sign_info[f'planet_{lang}']

    loading_text = get_text('horoscope_loading', lang, emoji=sign_info['emoji'], sign=sign_display,
                            element=element, planet=planet)

    if hasattr(update_or_query, 'message'):
        message = await update_or_query.message.reply_text(loading_text)
    else:
        message = await update_or_query.edit_message_text(loading_text)

    try:
        start_time = time.time()
        horoscope_text = await generate_horoscope(sign, day=day, detailed=detailed, lang=lang)
        duration = time.time() - start_time
        logger.info(f"✅ Гороскоп для {sign} сгенерирован за {duration:.2f} сек")
    except Exception as e:
        logger.exception(f"❌ Ошибка генерации гороскопа: {e}")
        await message.edit_text(
            get_text('horoscope_error', lang),
            reply_markup=get_back_to_menu_inline(lang=lang)
        )
        return

    day_text = get_text(f'day_{day}', lang)
    current_date = datetime.now().strftime("%d.%m.%Y")

    detailed_type = get_text('detailed_type_detailed' if detailed else 'detailed_type_short', lang)

    header = get_text('horoscope_header', lang, emoji=sign_info['emoji'], sign=sign_display,
                      element=element, planet=planet,
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

# Стартовое меню выбора знака — сегодня
async def horoscope_today(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        reply_markup = get_zodiac_inline_keyboard("horoscope", lang=lang)
        text = get_text('zodiac_select', lang)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"horoscope_today error: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_back_to_menu_inline(lang=lang))

# Стартовое меню выбора знака — завтра
async def horoscope_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        reply_markup = get_zodiac_inline_keyboard("horoscope_tomorrow", lang=lang)
        text = get_text('zodiac_select_tomorrow', lang)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"horoscope_tomorrow error: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_back_to_menu_inline(lang=lang))

# Обработка callback с выбором знака
async def handle_zodiac_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if ":" not in data:
            await query.message.edit_text(get_text('invalid_data', lang), reply_markup=get_back_to_menu_inline(lang=lang))
            return

        parts = data.split(":")

        if parts[0] == "horoscope_menu":
            day = parts[1] if len(parts) > 1 else "today"
            markup = get_zodiac_inline_keyboard("horoscope_tomorrow" if day == "tomorrow" else "horoscope", lang=lang)
            text = get_text('zodiac_select', lang) if day == "today" else get_text('zodiac_select_tomorrow', lang)
            await query.message.edit_text(text, reply_markup=markup)
            return

        if len(parts) == 4:
            _, sign, day, detailed = parts
            await send_horoscope(query, context, sign, day, detailed.lower() == "true", lang)
        elif len(parts) == 2:
            prefix, sign = parts
            day = "tomorrow" if prefix == "horoscope_tomorrow" else "today"
            await send_horoscope(query, context, sign, day, detailed=False, lang=lang)
        else:
            await query.message.edit_text(get_text('invalid_format', lang), reply_markup=get_back_to_menu_inline(lang=lang))

    except Exception as e:
        logger.exception(f"handle_zodiac_callback error: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_back_to_menu_inline(lang=lang))
