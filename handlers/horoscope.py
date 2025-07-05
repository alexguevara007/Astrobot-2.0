from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
import time
from datetime import datetime
from services.gpt_horoscope import generate_horoscope
from keyboards import get_zodiac_inline_keyboard, get_back_to_menu_inline

logger = logging.getLogger(__name__)

# Карта знаков зодиака с эмодзи и описанием стихий
ZODIAC_SIGNS = {
    "овен": {
        "eng": "aries",
        "emoji": "♈️",
        "element": "🔥 Огонь",
        "planet": "♂️ Марс"
    },
    "телец": {
        "eng": "taurus",
        "emoji": "♉️",
        "element": "🌍 Земля",
        "planet": "♀️ Венера"
    },
    "близнецы": {
        "eng": "gemini",
        "emoji": "♊️",
        "element": "💨 Воздух",
        "planet": "☿ Меркурий"
    },
    "рак": {
        "eng": "cancer",
        "emoji": "♋️",
        "element": "💧 Вода",
        "planet": "🌙 Луна"
    },
    "лев": {
        "eng": "leo",
        "emoji": "♌️",
        "element": "🔥 Огонь",
        "planet": "☀️ Солнце"
    },
    "дева": {
        "eng": "virgo",
        "emoji": "♍️",
        "element": "🌍 Земля",
        "planet": "☿ Меркурий"
    },
    "весы": {
        "eng": "libra",
        "emoji": "♎️",
        "element": "💨 Воздух",
        "planet": "♀️ Венера"
    },
    "скорпион": {
        "eng": "scorpio",
        "emoji": "♏️",
        "element": "💧 Вода",
        "planet": "♇ Плутон"
    },
    "стрелец": {
        "eng": "sagittarius",
        "emoji": "♐️",
        "element": "🔥 Огонь",
        "planet": "♃ Юпитер"
    },
    "козерог": {
        "eng": "capricorn",
        "emoji": "♑️",
        "element": "🌍 Земля",
        "planet": "♄ Сатурн"
    },
    "водолей": {
        "eng": "aquarius",
        "emoji": "♒️",
        "element": "💨 Воздух",
        "planet": "⛢ Уран"
    },
    "рыбы": {
        "eng": "pisces",
        "emoji": "♓️",
        "element": "💧 Вода",
        "planet": "♆ Нептун"
    }
}

def get_horoscope_actions_keyboard(sign: str, day: str, detailed: bool = False):
    """Создает клавиатуру с действиями для гороскопа"""
    buttons = []
    
    if not detailed:
        buttons.append([
            InlineKeyboardButton("📝 Подробнее", callback_data=f"horoscope:{sign}:{day}:true"),
            InlineKeyboardButton("🔄 Обновить", callback_data=f"horoscope:{sign}:{day}:false")
        ])
    
    buttons.extend([
        [InlineKeyboardButton("🔮 Другой знак", callback_data=f"horoscope_menu:{day}")],
        [InlineKeyboardButton("« Назад в меню", callback_data="main_menu")]
    ])
    
    return InlineKeyboardMarkup(buttons)

async def send_horoscope(update_or_query, sign: str, day: str, detailed: bool = False):
    """Отправляет гороскоп пользователю"""
    try:
        # Проверка знака
        sign_lower = sign.lower()
        if sign_lower not in ZODIAC_SIGNS:
            text = "🚫 Неверный знак зодиака. Попробуйте ещё раз."
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(
                    text,
                    reply_markup=get_zodiac_inline_keyboard("horoscope")
                )
            else:
                await update_or_query.edit_message_text(
                    text,
                    reply_markup=get_zodiac_inline_keyboard("horoscope")
                )
            return

        sign_info = ZODIAC_SIGNS[sign_lower]
        
        # Сообщение о генерации с предупреждением и информацией о знаке
        loading_text = (
            f"{sign_info['emoji']} Генерируется гороскоп для {sign.title()}\n"
            f"Стихия: {sign_info['element']}\n"
            f"Управитель: {sign_info['planet']}\n\n"
            "⚠️ Первый запрос может занять до минуты из-за особенностей хостинга.\n"
            "Пожалуйста, подождите..."
        )
        
        if hasattr(update_or_query, 'message'):
            message = await update_or_query.message.reply_text(loading_text)
        else:
            message = await update_or_query.edit_message_text(loading_text)

        # Получаем гороскоп
        try:
            start_time = time.time()
            horoscope_text = generate_horoscope(sign_info['eng'], day=day, detailed=detailed)
            generation_time = time.time() - start_time
            logger.info(f"Время генерации гороскопа для {sign}: {generation_time:.2f} секунд")
        except Exception as e:
            logger.error(f"Ошибка генерации гороскопа: {e}")
            error_text = (
                f"{sign_info['emoji']} Ошибка при генерации гороскопа\n\n"
                "Это может быть связано с перезапуском сервера.\n"
                "Пожалуйста, попробуйте через минуту."
            )
            await message.edit_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )
            return

        # Формируем ответ
        day_text = "сегодня" if day == "today" else "завтра"
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        header = (
            f"{sign_info['emoji']} {sign.title()}\n"
            f"Стихия: {sign_info['element']}\n"
            f"Управитель: {sign_info['planet']}\n"
            f"{'Подробный' if detailed else 'Краткий'} гороскоп на {day_text} ({current_date})\n"
            f"{'_' * 30}\n\n"
        )
        
        response = header + horoscope_text

        # Отправляем ответ
        try:
            await message.edit_text(
                text=response,
                reply_markup=get_horoscope_actions_keyboard(sign, day, detailed)
            )
        except BadRequest as e:
            if "Message is too long" in str(e):
                # Разделяем длинное сообщение
                parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
                for i, part in enumerate(parts):
                    if i == 0:
                        await message.edit_text(part)
                    else:
                        await message.reply_text(part)
                # Добавляем клавиатуру к последнему сообщению
                await message.reply_text(
                    "Выберите действие:",
                    reply_markup=get_horoscope_actions_keyboard(sign, day, detailed)
                )
            else:
                logger.error(f"Ошибка отправки сообщения: {e}")
                raise

    except Exception as e:
        logger.error(f"Ошибка отправки гороскопа: {e}")
        error_text = (
            "⚠️ Произошла ошибка\n\n"
            "Возможно, сервер перезапускается.\n"
            "Пожалуйста, попробуйте через минуту."
        )
        try:
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(
                    error_text,
                    reply_markup=get_back_to_menu_inline()
                )
            else:
                await update_or_query.edit_message_text(
                    error_text,
                    reply_markup=get_back_to_menu_inline()
                )
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке сообщения об ошибке: {e}")

async def horoscope_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды гороскопа на сегодня"""
    try:
        if update.callback_query:
            await update.callback_query.answer()
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
        logger.error(f"Ошибка в horoscope_today: {e}")
        error_text = (
            "⚠️ Произошла ошибка\n"
            "Пожалуйста, попробуйте позже."
        )
        if update.callback_query:
            await update.callback_query.message.reply_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )

async def horoscope_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды гороскопа на завтра"""
    try:
        if update.callback_query:
            await update.callback_query.answer()
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
        logger.error(f"Ошибка в horoscope_tomorrow: {e}")
        error_text = (
            "⚠️ Произошла ошибка\n"
            "Пожалуйста, попробуйте позже."
        )
        if update.callback_query:
            await update.callback_query.message.reply_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )

async def handle_zodiac_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки выбора знака зодиака"""
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if ":" not in data:
            await query.message.edit_text(
                "⚠️ Неверный формат данных. Вернитесь в главное меню:",
                reply_markup=get_back_to_menu_inline()
            )
            return

        parts = data.split(":")
        
        # Обработка меню выбора знака
        if parts[0] == "horoscope_menu":
            day = parts[1] if len(parts) > 1 else "today"
            await query.message.edit_text(
                "🔮 Выберите знак зодиака:",
                reply_markup=get_zodiac_inline_keyboard(f"horoscope{'_tomorrow' if day == 'tomorrow' else ''}")
            )
            return

        # Обработка выбора знака
        if len(parts) == 4:  # horoscope:sign:day:detailed
            prefix, sign, day, detailed = parts
            detailed = detailed.lower() == "true"
        else:
            prefix, sign = parts
            day = "today"
            detailed = False

        if prefix == "horoscope":
            await send_horoscope(query, sign, day, detailed)
        elif prefix == "horoscope_tomorrow":
            await send_horoscope(query, sign, "tomorrow", detailed)
        else:
            await query.message.edit_text(
                "⚠️ Неизвестный тип гороскопа. Вернитесь в главное меню:",
                reply_markup=get_back_to_menu_inline()
            )

    except Exception as e:
        logger.error(f"Ошибка в handle_zodiac_callback: {e}")
        error_text = (
            "⚠️ Произошла ошибка\n"
            "Пожалуйста, попробуйте позже."
        )
        try:
            await update.callback_query.message.edit_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )
        except:
            await update.callback_query.message.reply_text(
                error_text,
                reply_markup=get_back_to_menu_inline()
            )
