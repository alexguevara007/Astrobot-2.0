from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging

# 📥 Импорт клавиатур
from keyboards import (
    get_main_menu_keyboard,
    get_zodiac_inline_keyboard,
    get_back_to_menu_inline
)

# 📥 Импорт обработчиков/сценариев
from services.lunar import get_lunar_text
from handlers.horoscope import horoscope_today, horoscope_tomorrow, handle_zodiac_callback
from handlers.tarot import tarot, tarot3
from handlers.tarot5 import tarot5
from handlers.compatibility import compatibility
from handlers.subscribe import subscribe

logger = logging.getLogger(__name__)

# 🏠 Inline клавиатура главного меню
def get_main_menu_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌞 Гороскоп", callback_data="horoscope_menu")],
        [InlineKeyboardButton("🃏 Таро", callback_data="tarot_menu")],
        [InlineKeyboardButton("🌙 Лунный календарь", callback_data="moon")],
        [InlineKeyboardButton("❤️ Совместимость", callback_data="compatibility")],
        [InlineKeyboardButton("🔔 Подписка", callback_data="subscribe")]
    ])


# 🔮 Меню гороскопов
def get_horoscope_menu_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Сегодня", callback_data="horoscope_today")],
        [InlineKeyboardButton("🌘 Завтра", callback_data="horoscope_tomorrow")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])


# 🃏 Меню раскладов Таро
def get_tarot_menu_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 Карта дня", callback_data="tarot")],
        [InlineKeyboardButton("🔮 Расклад из 3", callback_data="tarot3")],
        [InlineKeyboardButton("🔮 Расклад из 5", callback_data="tarot5")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])


# 🔹 Команда /start и стартовое меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "👋 Привет! Это меню AstroBot. Выберите действие:"
    try:
        if update.callback_query:
            try:
                await update.callback_query.message.edit_text(
                    text=message,
                    reply_markup=get_main_menu_inline_keyboard()
                )
            except BadRequest:
                await update.callback_query.message.reply_text(
                    text=message,
                    reply_markup=get_main_menu_keyboard()
                )
            await update.callback_query.answer()
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=get_main_menu_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        err = f"Произошла ошибка: {e}"
        if update.callback_query:
            await update.callback_query.message.reply_text(err)
        else:
            await update.message.reply_text(err)


# 🔘 Inline кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    try:
        # Сразу отвечаем на callback query
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Ошибка ответа на callback query: {e}")

        match data:
            case "horoscope_menu":
                try:
                    await query.message.edit_text(
                        "🔮 Выберите тип гороскопа:",
                        reply_markup=get_horoscope_menu_inline()
                    )
                except BadRequest as e:
                    if "message is not modified" in str(e):
                        pass
                    else:
                        await query.message.reply_text(
                            "🔮 Выберите тип гороскопа:",
                            reply_markup=get_horoscope_menu_inline()
                        )

            case "tarot_menu":
                try:
                    await query.message.edit_text(
                        "🃏 Таро-расклады:",
                        reply_markup=get_tarot_menu_inline()
                    )
                except BadRequest as e:
                    if "message is not modified" not in str(e):
                        await query.message.reply_text(
                            "🃏 Таро-расклады:",
                            reply_markup=get_tarot_menu_inline()
                        )

            case "moon":
                text = get_lunar_text()
                try:
                    await query.message.edit_text(
                        f"🌙 Лунный календарь:\n\n{text}",
                        reply_markup=get_back_to_menu_inline()
                    )
                except BadRequest:
                    await query.message.reply_text(
                        f"🌙 Лунный календарь:\n\n{text}",
                        reply_markup=get_back_to_menu_inline()
                    )

            case "subscribe":
                await subscribe(update, context)

            case _ if data.startswith("subscribe_"):
                from handlers.subscribe import handle_subscription_callback
                await handle_subscription_callback(update, context)

            case "compatibility" | _ if data.startswith("compatibility_"):
                await compatibility(update, context)

            case "main_menu" | "back_to_menu":
                try:
                    await start(update, context)
                except BadRequest:
                    if update.callback_query:
                        await update.callback_query.message.reply_text(
                            "👋 Главное меню:",
                            reply_markup=get_main_menu_inline_keyboard()
                        )

            case "horoscope_today":
                try:
                    await query.message.edit_text(
                        "🔮 Выберите знак зодиака:",
                        reply_markup=get_zodiac_inline_keyboard("horoscope")
                    )
                except BadRequest:
                    await query.message.reply_text(
                        "🔮 Выберите знак зодиака:",
                        reply_markup=get_zodiac_inline_keyboard("horoscope")
                    )

            case "horoscope_tomorrow":
                try:
                    await query.message.edit_text(
                        "🌜 Выберите знак зодиака:",
                        reply_markup=get_zodiac_inline_keyboard("horoscope_tomorrow")
                    )
                except BadRequest:
                    await query.message.reply_text(
                        "🌜 Выберите знак зодиака:",
                        reply_markup=get_zodiac_inline_keyboard("horoscope_tomorrow")
                    )

            case "tarot":
                await tarot(update, context)
            case "tarot3":
                await tarot3(update, context)
            case "tarot5":
                await tarot5(update, context)

            case _ if data.startswith("horoscope:") or data.startswith("horoscope_tomorrow:"):
                await handle_zodiac_callback(update, context)

            case _:
                try:
                    await query.message.edit_text(
                        "⚠️ Неизвестная команда. Вернитесь в главное меню:",
                        reply_markup=get_back_to_menu_inline()
                    )
                except BadRequest:
                    await query.message.reply_text(
                        "⚠️ Неизвестная команда. Вернитесь в главное меню:",
                        reply_markup=get_back_to_menu_inline()
                    )

    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        try:
            await query.message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте вернуться в главное меню:",
                reply_markup=get_back_to_menu_inline()
            )
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке ошибки: {e}")


# 💬 Reply-кнопки
async def reply_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip().lower()

        match text:
            case "🌞 гороскоп на сегодня":
                await horoscope_today(update, context)
            case "🌜 гороскоп на завтра":
                await horoscope_tomorrow(update, context)
            case "🃏 таро-карта дня":
                await tarot(update, context)
            case "🔮 таро 3 карты":
                await tarot3(update, context)
            case "✨ таро 5 карт":
                await tarot5(update, context)
            case "❤️ совместимость":
                await compatibility(update, context)
            case "🔔 подписка":
                await subscribe(update, context)
            case "🏠 главное меню" | "/menu":
                await start(update, context)
            case _:
                await update.message.reply_text(
                    "🤔 Неизвестная команда. Напишите /menu или нажмите кнопку ниже.",
                    reply_markup=get_main_menu_keyboard()
                )

    except Exception as e:
        logger.error(f"Ошибка в обработчике текстовых команд: {e}")
        await update.message.reply_text(f"Произошла ошибка: {e}")
