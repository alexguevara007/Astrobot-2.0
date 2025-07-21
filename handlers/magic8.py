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

from keyboards import get_main_menu_keyboard
from services.locales import get_text

logger = logging.getLogger(__name__)

MAGIC_8_BALL_ANSWERS = {
    'ru': [
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
    ],
    'en': [
        "🔮 It is certain!",
        "✨ Yes — definitely.",
        "🌟 You may rely on it.",
        "🟢 Yes.",
        "🙃 Most likely.",
        "💫 Signs point to yes.",
        "👍 Outlook good.",
        "🤔 Don't count on it.",
        "❌ My reply is no.",
        "🚫 No.",
        "🧘 Ask again later.",
        "😐 Reply hazy, try again.",
        "🔁 Better not tell you now.",
        "🤷 Cannot predict now.",
        "🤡 Very doubtful.",
        "🔥 Not today!"
    ]
}

async def start_magic_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        message = get_text('magic8_ask', lang)
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(get_text('magic8_button', lang), callback_data="magic_8ball_answer")
        ]])
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(message, reply_markup=markup, parse_mode="HTML")
        else:
            await update.message.reply_text(message, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        logger.error(f"[Magic8] Ошибка в start_magic_8ball: {e}")
        await update.effective_message.reply_text(get_text('error', lang), reply_markup=get_main_menu_keyboard(lang=lang))

async def show_magic_8ball_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id

        await query.message.edit_text(get_text('magic8_loading', lang))

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(2.5)

        answers = MAGIC_8_BALL_ANSWERS.get(lang, MAGIC_8_BALL_ANSWERS['ru'])
        answer = random.choice(answers)
        await query.message.edit_text(
            get_text('magic8_answer', lang, answer=answer),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text('magic8_repeat', lang), callback_data="magic_8ball_repeat")],
                [InlineKeyboardButton(get_text('back_to_menu', lang), callback_data="main_menu")]
            ])
        )
    except Exception as e:
        logger.exception(f"[Magic8] Ошибка при показе магического ответа: {e}")
        await update.effective_message.reply_text(get_text('magic8_error', lang), reply_markup=get_main_menu_keyboard(lang=lang))
