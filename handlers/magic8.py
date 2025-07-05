# handlers/magic8.py

import random
import asyncio
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from keyboards import get_main_menu_keyboard, get_main_menu_inline_keyboard

logger = logging.getLogger(__name__)

# 🎱 Варианты ответов магического шара
MAGIC_8_BALL_ANSWERS = [
    "🔮 Бесспорно!",
    "✨ Да — определённо.",
    "🌟 Можешь рассчитывать на это.",
    "🟢 Думаю, да.",
    "🙃 Скорее всего.",
    "💫 Знаки говорят: да.",
    "👍 Перспективы хорошие.",
    "🤔 Пожалуй, нет.",
    "❌ Не рассчитывай на это.",
    "🚫 Ответ — нет.",
    "🧘 Спроси позже.",
    "😐 Пока туманно. Попробуй позже.",
    "🔁 Всё может измениться. Повтори позже.",
    "🤷 Я не могу сказать сейчас.",
    "🤡 Очень сомнительно.",
    "🔥 Не сегодня!"
]


# 🔘 Старт: кнопка "🧿 Магический шар"
async def start_magic_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает приглашение к магическому шару"""
    try:
        message = (
            "🧿 <b>Задайте мысленно свой вопрос Вселенной</b>\n\n"
            "Когда будете готовы — нажмите кнопку ниже 🎱"
        )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("Узнать ответ у шара 🎱", callback_data="magic_8ball_answer")
        ]])
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(message, reply_markup=markup, parse_mode="HTML")
        else:
            await update.message.reply_text(message, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        logger.error(f"[Magic8] Ошибка в start_magic_8ball: {e}")
        await update.effective_message.reply_text("⚠️ Произошла ошибка.", reply_markup=get_main_menu_keyboard())


# 🔮 Показать ответ шара
async def show_magic_8ball_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает случайный ответ от шара"""
    try:
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id

        # Шаг 1: «Шар вращается...»
        await query.message.edit_text("🌀 Шар вращается...\nСилы Вселенной собираются... 🔮")

        # Шаг 2: typing...
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(2.5)

        # Шаг 3: показать случайный ответ
        answer = random.choice(MAGIC_8_BALL_ANSWERS)
        await query.message.edit_text(
            f"<b>🎱 Магический шар говорит:</b>\n\n{answer}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌀 Ещё раз", callback_data="magic_8ball_repeat")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ])
        )
    except Exception as e:
        logger.exception(f"[Magic8] Ошибка при показе магического ответа: {e}")
        await update.effective_message.reply_text("⚠️ Не удалось получить ответ.", reply_markup=get_main_menu_inline_keyboard())
