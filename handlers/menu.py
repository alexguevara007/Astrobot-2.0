import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from keyboards import (
    get_main_menu_keyboard,
    get_zodiac_inline_keyboard,
    get_back_to_menu_inline
)
from services.lunar import get_lunar_text
from services.user_tracker import track_user, get_user_language, toggle_user_language
from locales import get_text

# Импорты обработчиков
from handlers.horoscope import horoscope_today, horoscope_tomorrow, handle_zodiac_callback
from handlers.tarot import tarot, tarot3
from handlers.tarot5 import tarot5
from handlers.compatibility import compatibility
from handlers.subscribe import subscribe
from handlers.magic8 import start_magic_8ball, show_magic_8ball_answer

logger = logging.getLogger(__name__)

def get_main_menu_inline_keyboard(lang: str = 'ru'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text('menu_horoscope', lang), callback_data="horoscope_menu")],
        [InlineKeyboardButton(get_text('menu_tarot', lang), callback_data="tarot_menu")],
        [InlineKeyboardButton(get_text('menu_moon', lang), callback_data="moon")],
        [InlineKeyboardButton(get_text('menu_compatibility', lang), callback_data="compatibility")],
        [InlineKeyboardButton(get_text('menu_magic8', lang), callback_data="magic_8ball")],
        [InlineKeyboardButton(get_text('menu_subscribe', lang), callback_data="subscribe")]
    ])

def get_horoscope_menu_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text('horoscope_today', lang), callback_data="horoscope_today")],
        [InlineKeyboardButton(get_text('horoscope_tomorrow', lang), callback_data="horoscope_tomorrow")],
        [InlineKeyboardButton(get_text('back_to_menu', lang), callback_data="main_menu")]
    ])

def get_tarot_menu_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text('tarot_one', lang), callback_data="tarot")],
        [InlineKeyboardButton(get_text('tarot_three', lang), callback_data="tarot3")],
        [InlineKeyboardButton(get_text('tarot_five', lang), callback_data="tarot5")],
        [InlineKeyboardButton(get_text('back_to_menu', lang), callback_data="main_menu")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    track_user(user.id, user.username)

    lang = get_user_language(user.id)
    message = get_text('welcome', lang)

    try:
        if update.callback_query:
            try:
                await update.callback_query.message.edit_text(
                    text=message,
                    reply_markup=get_main_menu_keyboard(lang=lang)
                )
            except BadRequest:
                await update.callback_query.message.reply_text(
                    text=message,
                    reply_markup=get_main_menu_keyboard(lang=lang)
                )
            await update.callback_query.answer()
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=get_main_menu_keyboard(lang=lang)
            )

    except Exception as e:
        logger.exception("Ошибка в /start")
        await update.effective_message.reply_text(
            get_text('error', lang)
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    lang = get_user_language(user_id)

    try:
        await query.answer()

        match data:
            case "horoscope_menu":
                await query.message.edit_text(get_text('zodiac_select', lang), reply_markup=get_horoscope_menu_inline(lang))

            case "tarot_menu":
                await query.message.edit_text(get_text('tarot_menu_title', lang), reply_markup=get_tarot_menu_inline(lang))

            case "moon":
                text = get_lunar_text(lang=lang)
                await query.message.edit_text(
                    text,
                    reply_markup=get_back_to_menu_inline(lang=lang)
                )

            case "subscribe":
                await subscribe(update, context, lang=lang)

            case "magic_8ball":
                await start_magic_8ball(update, context, lang=lang)

            case "magic_8ball_answer" | "magic_8ball_repeat":
                await show_magic_8ball_answer(update, context, lang=lang)

            case "main_menu" | "back_to_menu":
                await start(update, context)

            case "horoscope_today":
                await query.message.edit_text(
                    get_text('zodiac_select', lang),
                    reply_markup=get_zodiac_inline_keyboard("horoscope", lang=lang)
                )

            case "horoscope_tomorrow":
                await query.message.edit_text(
                    get_text('zodiac_select_tomorrow', lang),
                    reply_markup=get_zodiac_inline_keyboard("horoscope_tomorrow", lang=lang)
                )

            case _ if data.startswith("horoscope:") or data.startswith("horoscope_tomorrow:"):
                await handle_zodiac_callback(update, context, lang=lang)

            case "tarot":
                await tarot(update, context, lang=lang)
            case "tarot3":
                await tarot3(update, context, lang=lang)
            case "tarot5":
                await tarot5(update, context, lang=lang)

            case _ if data.startswith("compatibility"):
                await compatibility(update, context, lang=lang)

            case _ if data.startswith("subscribe_"):
                from handlers.subscribe import handle_subscription_callback
                await handle_subscription_callback(update, context, lang=lang)

            case _:
                await query.message.edit_text(
                    get_text('error', lang),
                    reply_markup=get_back_to_menu_inline(lang=lang)
                )

    except Exception:
        logger.exception("Ошибка в button_handler")
        await query.message.reply_text(
            get_text('error', lang),
            reply_markup=get_back_to_menu_inline(lang=lang)
        )

async def reply_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    track_user(user_id, user.username)

    lang = get_user_language(user_id)

    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip().lower()

        # Обработка команды переключения языка
        if "🌐" in text or "/language" in text:
            new_lang = toggle_user_language(user_id)
            await update.message.reply_text(
                get_text('language_switched', new_lang),
                reply_markup=get_main_menu_keyboard(lang=new_lang)
            )
            return

        # Обработка обычных команд
        match text:
            # RU
            case "🌞 гороскоп на сегодня" | "🌞 horoscope for today":
                await horoscope_today(update, context, lang=lang)
            case "🌜 гороскоп на завтра" | "🌜 horoscope for tomorrow":
                await horoscope_tomorrow(update, context, lang=lang)
            case "🃏 таро-карта дня" | "🃏 daily tarot card":
                await tarot(update, context, lang=lang)
            case "🔮 таро 3 карты" | "🔮 three tarot cards":
                await tarot3(update, context, lang=lang)
            case "✨ таро 5 карт" | "✨ five tarot cards":
                await tarot5(update, context, lang=lang)
            case "❤️ совместимость" | "❤️ compatibility":
                await compatibility(update, context, lang=lang)
            case "🔔 подписка" | "🔔 subscription":
                await subscribe(update, context, lang=lang)
            case "🧿 магический шар" | "🧿 magic 8-ball":
                await start_magic_8ball(update, context, lang=lang)
            case "🏠 главное меню" | "🏠 main menu" | "/menu" | "/start":
                await start(update, context)
            case _:
                await update.message.reply_text(
                    get_text('error', lang),
                    reply_markup=get_main_menu_keyboard(lang=lang)
                )

    except Exception:
        logger.exception("Ошибка в reply_command_handler")
        await update.message.reply_text(
            get_text('error', lang),
            reply_markup=get_main_menu_keyboard(lang=lang)
        )
