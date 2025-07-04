from telegram import Update
from telegram.ext import ContextTypes
from services.database import (
    add_subscription,
    remove_subscription,
    is_subscribed
)
from keyboards import get_zodiac_subscribe_keyboard

SIGNS = [
    "овен", "телец", "близнецы", "рак", "лев", "дева",
    "весы", "скорпион", "стрелец", "козерог", "водолей", "рыбы"
]

# ✅ /subscribe — вызывает кнопки со знаками
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "🪐 Выбери свой знак зодиака для подписки:",
            reply_markup=get_zodiac_subscribe_keyboard()
        )

# ✅ обработка нажатия кнопки: "subscribe_<sign>"
async def handle_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    sign = data.replace("subscribe_", "").lower()

    if sign not in SIGNS:
        await query.message.reply_text("⚠️ Неизвестный знак зодиака.")
        return

    chat_id = query.message.chat_id
    add_subscription(chat_id, sign)

    await query.message.edit_text(
        f"✅ Подписка на знак *{sign.capitalize()}* оформлена!\n\n"
        "📬 Теперь ты будешь получать ежедневный гороскоп.",
        parse_mode="Markdown"
    )


# ❌ /unsubscribe — отмена подписки
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    success = remove_subscription(chat_id)

    if success:
        await update.message.reply_text(
            "❌ Подписка отменена.\n\n"
            "Если захочешь снова получать гороскоп — /subscribe"
        )
    else:
        await update.message.reply_text("ℹ️ У тебя пока нет активной подписки.")


# ℹ️ /status — статус подписки
async def subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if is_subscribed(chat_id):
        await update.message.reply_text("📮 У тебя есть активная подписка.")
    else:
        await update.message.reply_text("📭 У тебя пока нет подписки.")