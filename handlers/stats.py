# handlers/stats.py

from telegram import Update
from telegram.ext import ContextTypes
from services.user_tracker import get_user_stats_by_day, get_user_count
from locales import get_text

ADMIN_IDS = [306285013]  

async def new_users(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text(get_text('access_denied', lang))
        return

    stats = get_user_stats_by_day()
    total = get_user_count()

    if not stats:
        await update.message.reply_text(get_text('no_users', lang))
        return

    text = get_text('total_users', lang, count=total) + "\n\n"
    text += get_text('new_users_by_day', lang) + "\n\n"
    for date, count in stats.items():
        text += get_text('date_count', lang, date=date, count=count) + "\n"

    await update.message.reply_text(text, parse_mode="HTML")
