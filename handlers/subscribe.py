from telegram import Update
from telegram.ext import ContextTypes
from services.database import (
    add_subscription,
    remove_subscription,
    is_subscribed
)
from keyboards import get_zodiac_subscribe_keyboard
from locales import get_text

ZODIAC_KEYS = [
    "aries", "taurus", "gemini",
    "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius",
    "capricorn", "aquarius", "pisces"
]

ZODIAC_DISPLAY = {
    'ru': {
        "aries": "Овен",
        "taurus": "Телец",
        "gemini": "Близнецы",
        "cancer": "Рак",
        "leo": "Лев",
        "virgo": "Дева",
        "libra": "Весы",
        "scorpio": "Скорпион",
        "sagittarius": "Стрелец",
        "capricorn": "Козерог",
        "aquarius": "Водолей",
        "pisces": "Рыбы"
    },
    'en': {
        "aries": "Aries",
        "taurus": "Taurus",
        "gemini": "Gemini",
        "cancer": "Cancer",
        "leo": "Leo",
        "virgo": "Virgo",
        "libra": "Libra",
        "scorpio": "Scorpio",
        "sagittarius": "Sagittarius",
        "capricorn": "Capricorn",
        "aquarius": "Aquarius",
        "pisces": "Pisces"
    }
}

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    if update.message:
        await update.message.reply_text(
            get_text('subscribe_prompt', lang),
            reply_markup=get_zodiac_subscribe_keyboard(lang=lang)
        )

async def handle_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    query = update.callback_query
    await query.answer()

    data = query.data
    sign_key = data.replace("subscribe_", "")

    if sign_key not in ZODIAC_KEYS:
        await query.message.reply_text(get_text('invalid_sign', lang))
        return

    chat_id = query.message.chat_id
    add_subscription(chat_id, sign_key)

    sign_display = ZODIAC_DISPLAY.get(lang, ZODIAC_DISPLAY['ru'])[sign_key]

    await query.message.edit_text(
        get_text('subscribe_success', lang, sign=sign_display),
        parse_mode="Markdown"
    )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    chat_id = update.effective_chat.id
    success = remove_subscription(chat_id)

    if success:
        await update.message.reply_text(
            get_text('unsubscribe_success', lang)
        )
    else:
        await update.message.reply_text(get_text('unsubscribe_no', lang))

async def subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    chat_id = update.effective_chat.id
    if is_subscribed(chat_id):
        await update.message.reply_text(get_text('status_yes', lang))
    else:
        await update.message.reply_text(get_text('status_no', lang))
