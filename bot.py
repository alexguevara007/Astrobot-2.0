"""
AstroBot — Telegram ассистент по гороскопам, Таро и Луне 🌙
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

from handlers.menu import start, button_handler, reply_command_handler
from handlers.horoscope import horoscope_today, horoscope_tomorrow
from handlers.subscribe import subscribe, unsubscribe, subscription_status
from handlers.moon import moon
from handlers.tarot import tarot, tarot3
from handlers.tarot5 import tarot5
from handlers.compatibility import compatibility
from services.database import init_db
from scheduler import setup_scheduler


# === 🔐 Загрузка токена ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logging.critical("❌ BOT_TOKEN не найден в .env")
    raise SystemExit("BOT_TOKEN отсутствует. Выход.")


# === 📝 Логгирование ===
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# === ⛑ Глобальный обработчик ошибок ===
async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Ошибка: %s", context.error, exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")
    except Exception:
        logger.exception("Не удалось отправить сообщение об ошибке.")


# === main ===
def main():
    # 📂 Подготовка
    init_db()

    # ✅ Настройки по умолчанию (HTML)
    defaults = Defaults(parse_mode=ParseMode.HTML)

    # 🤖 Приложение
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(defaults).build()

    # === 📌 Команды ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("help", start))

    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("status", subscription_status))

    app.add_handler(CommandHandler("horoscope", horoscope_today))
    app.add_handler(CommandHandler("tomorrow", horoscope_tomorrow))
    app.add_handler(CommandHandler("moon", moon))

    app.add_handler(CommandHandler("tarot", tarot))
    app.add_handler(CommandHandler("tarot3", tarot3))
    app.add_handler(CommandHandler("tarot5", tarot5))
    app.add_handler(CommandHandler("compatibility", compatibility))

    # ✅ Callback кнопки
    app.add_handler(CallbackQueryHandler(button_handler))

    # ✅ Текст клавиатуры (Reply-кнопки)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))

    # 🛑 Глобальный обработчик ошибок
    app.add_error_handler(error_handler)

    # ⏰ Планировщик
    setup_scheduler(app)

    # ▶️ Запуск
    logger.info("🚀 AstroBot стартует...")
    print("🤖 AstroBot запущен. Polling начат.")
    app.run_polling()


# === Точка входа ===
if __name__ == "__main__":
    main()