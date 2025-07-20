# handlers/stats.py

from telegram import Update
from telegram.ext import ContextTypes
from services.user_tracker import get_user_stats_by_day, get_user_count

ADMIN_IDS = [123456789]  # 👉 Замени на свой Telegram user_id

async def new_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Доступ запрещён.")
        return

    stats = get_user_stats_by_day()
    total = get_user_count()

    if not stats:
        await update.message.reply_text("👥 Пока нет пользователей.")
        return

    text = f"<b>📊 Всего пользователей:</b> <code>{total}</code>\n\n"
    text += "<b>📅 Новые пользователи по дням:</b>\n\n"
    for date, count in stats.items():
        text += f"🗓 <b>{date}</b>: {count}\n"

    await update.message.reply_text(text, parse_mode="HTML")
