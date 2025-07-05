from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
from services.gpt_horoscope import generate_horoscope
from keyboards import get_zodiac_inline_keyboard, get_back_to_menu_inline

logger = logging.getLogger(__name__)

# Карта знаков зодиака с эмодзи
ZODIAC_SIGNS = {
    "овен": ("aries", "♈️"),
    "телец": ("taurus", "♉️"),
    "близнецы": ("gemini", "♊️"),
    "рак": ("cancer", "♋️"),
    "лев": ("leo", "♌️"),
    "дева": ("virgo", "♍️"),
    "весы": ("libra", "♎️"),
    "скорпион": ("scorpio", "♏️"),
    "стрелец": ("sagittarius", "♐️"),
    "козерог": ("capricorn", "♑️"),
    "водолей": ("aquarius", "♒️"),
    "рыбы": ("pisces", "♓️")
}

# Кнопки действий для гороскопа
def get_horoscope_actions_keyboard(sign: str, day: str):
    """Создает клавиатуру с действиями для гороскопа"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Подробнее", callback_data=f"horoscope:{sign}:{day}:true"),
            InlineKeyboardButton("🔄 Обновить", callback_data=f"horoscope:{sign}:{day}:false")
        ],
        [InlineKeyboardButton("🔮 Другой знак", callback_data=f"horoscope_menu:{day}")],
        [InlineKeyboardButton("« Назад в меню", callback_data="main_menu")]
    ])

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

        sign_eng, sign_emoji = ZODIAC_SIGNS[sign_lower]
        
        # Сообщение о генерации
        loading_text = f"🔮 Генерируется гороскоп для {sign_emoji} {sign.title()}..."
        if hasattr(update_or_query, 'message'):
            message = await update_or_query.message.reply_text(loading_text)
        else:
            message = await update_or_query.edit_message_text(loading_text)

        # Получаем гороскоп
        try:
            horoscope_text = generate_horoscope(sign_eng, day=day, detailed=detailed)
        except Exception as e:
            logger.error(f"Ошибка генерации гороскопа: {e}")
            await message.edit_text(
                "⚠️ Произошла ошибка при генерации гороскопа. Попробуйте позже.",
                reply_markup=get_back_to_menu_inline()
            )
            return

        # Формируем ответ
        day_text = "сегодня" if day == "today" else "завтра"
        response = f"{sign_emoji} {'Подробный' if detailed else 'Краткий'} гороскоп для {sign.title()} на {day_text}:\n\n{horoscope_text}"

        # Добавляем клавиатуру с действиями
        keyboard = get_horoscope_actions_keyboard(sign, day) if not detailed else InlineKeyboardMarkup([
            [InlineKeyboardButton("🔮 Другой знак", callback_data=f"horoscope_menu:{day}")],
            [InlineKeyboardButton("« Назад в меню", callback_data="main_menu")]
        ])

        # Отправляем ответ
        try:
            await message.edit_text(
                text=response,
                reply_markup=keyboard
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
                    reply_markup=keyboard
                )
            else:
                raise

    except Exception as e:
        logger.error(f"Ошибка отправки гороскопа: {e}")
        error_message = "⚠️ Произошла ошибка. Попробуйте позже."
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
        error_message = "⚠️ Произошла ошибка. Попробуйте позже."
        if update.callback_query:
            await update.callback_query.message.reply_text(
                error_message,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                error_message,
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
        error_message = "⚠️ Произошла ошибка. Попробуйте позже."
        if update.callback_query:
            await update.callback_query.message.reply_text(
                error_message,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                error_message,
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
        try:
            await update.callback_query.message.edit_text(
                "⚠️ Произошла ошибка. Попробуйте позже.",
                reply_markup=get_back_to_menu_inline()
            )
        except:
            await update.callback_query.message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте позже.",
                reply_markup=get_back_to_menu_inline()
            )
