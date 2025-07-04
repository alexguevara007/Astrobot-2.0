"""
AstroBot — Telegram ассистент по гороскопам, Таро и Луне 🌙
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from aiohttp import web

from handlers.menu import start, button_handler, reply_command_handler
from handlers.horoscope import horoscope_today, horoscope_tomorrow
from handlers.subscribe import subscribe, unsubscribe, subscription_status
from handlers.moon import moon
from handlers.tarot import tarot, tarot3
from handlers.tarot5 import tarot5
from handlers.compatibility import compatibility
from services.database import init_db
from scheduler import setup_scheduler

# === 🔐 Загрузка токена и настроек ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = "https://astrobot-2-0.onrender.com"

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

# Создаем глобальную переменную для приложения
application = None

# === Обработчик webhook ===
async def webhook_handler(request):
    try:
        update = await request.json()
        await application.process_update(update)
        return web.Response()
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return web.Response(status=500)

# === main ===
async def main():
    global application
    
    # 📂 Подготовка
    init_db()

    # ✅ Настройки по умолчанию (HTML)
    defaults = Defaults(parse_mode=ParseMode.HTML)

    # 🤖 Приложение
    application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()
    await application.initialize()  # Инициализируем приложение
    await application.start()  # Запускаем приложение

    # === 📌 Команды ===
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("help", start))

    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("status", subscription_status))

    application.add_handler(CommandHandler("horoscope", horoscope_today))
    application.add_handler(CommandHandler("tomorrow", horoscope_tomorrow))
    application.add_handler(CommandHandler("moon", moon))

    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("tarot3", tarot3))
    application.add_handler(CommandHandler("tarot5", tarot5))
    application.add_handler(CommandHandler("compatibility", compatibility))

    # ✅ Callback кнопки
    application.add_handler(CallbackQueryHandler(button_handler))

    # ✅ Текст клавиатуры (Reply-кнопки)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))

    # 🛑 Глобальный обработчик ошибок
    application.add_error_handler(error_handler)

    # ⏰ Планировщик
    setup_scheduler(application)

    # ▶️ Настройка webhook
    webhook_path = f"/webhook/{BOT_TOKEN}"
    webhook_url = f"{RENDER_URL}{webhook_path}"
    
    await application.bot.set_webhook(webhook_url)
    logger.info(f"🚀 Webhook установлен на {webhook_url}")

    # Настройка веб-приложения
    app = web.Application()
    app.router.add_post(webhook_path, webhook_handler)
    
    return app

# === Точка входа ===
if __name__ == "__main__":
    web.run_app(main(), port=PORT)
