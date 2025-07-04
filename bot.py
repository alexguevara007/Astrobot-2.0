"""
AstroBot — Telegram ассистент по гороскопам, Таро и Луне 🌙
"""

import os
import time
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

# Создаем глобальную переменную для приложения
application = None

async def webhook_handler(request):
    """Обработчик webhook запросов от Telegram"""
    try:
        update = await request.json()
        logger.info("==================== НОВОЕ ОБНОВЛЕНИЕ ====================")
        logger.info(f"📥 Получено обновление: {update}")
        
        # Подробный анализ обновления
        if 'message' in update:
            message = update['message']
            logger.info(f"От: {message.get('from', {}).get('username', 'Неизвестно')}")
            logger.info(f"Текст: {message.get('text', 'Нет текста')}")
            logger.info(f"Chat ID: {message.get('chat', {}).get('id', 'Неизвестно')}")
            
        elif 'callback_query' in update:
            callback = update['callback_query']
            logger.info(f"Callback data: {callback.get('data', 'Нет данных')}")
            logger.info(f"От: {callback.get('from', {}).get('username', 'Неизвестно')}")

        # Обработка обновления
        logger.info("Начинаем обработку обновления...")
        await application.process_update(update)
        logger.info("✅ Обновление успешно обработано")
        
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        logger.exception("Полный стек ошибки:")
        return web.Response(status=500)

async def health_check(request):
    """Расширенный обработчик для проверки работоспособности"""
    try:
        webhook_info = await application.bot.get_webhook_info()
        bot_info = await application.bot.get_me()
        return web.json_response({
            "status": "running",
            "bot_username": bot_info.username,
            "webhook_url": webhook_info.url,
            "webhook_pending_update_count": webhook_info.pending_update_count,
            "timestamp": time.time(),
            "service": "AstroBot",
            "version": "2.0"
        })
    except Exception as e:
        logger.error(f"Ошибка в health_check: {e}")
        return web.json_response({"status": "error", "error": str(e)}, status=500)

async def setup_bot():
    """Настройка бота"""
    global application
    
    try:
        # 📂 Подготовка
        init_db()
        logger.info("База данных инициализирована")

        # ✅ Настройки по умолчанию (HTML)
        defaults = Defaults(parse_mode=ParseMode.HTML)

        # 🤖 Приложение
        application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()
        
        # Инициализация и запуск
        await application.initialize()
        await application.start()

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

        # Проверка подключения к Telegram
        bot_info = await application.bot.get_me()
        logger.info(f"=== Информация о боте ===")
        logger.info(f"Имя: {bot_info.first_name}")
        logger.info(f"Username: @{bot_info.username}")
        logger.info(f"ID: {bot_info.id}")

        # ▶️ Настройка webhook
        webhook_path = f"/webhook/{BOT_TOKEN}"
        webhook_url = f"{RENDER_URL}{webhook_path}"
        
        await application.bot.delete_webhook()
        await application.bot.set_webhook(webhook_url)
        
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"=== Информация о webhook ===")
        logger.info(f"URL: {webhook_info.url}")
        logger.info(f"Pending updates: {webhook_info.pending_update_count}")

        logger.info("✅ Бот успешно настроен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке бота: {e}")
        raise

async def main():
    """Основная функция"""
    try:
        await setup_bot()
        
        app = web.Application()
        webhook_path = f"/webhook/{BOT_TOKEN}"
        
        # Добавляем обработчики путей
        app.router.add_get("/", health_check)
        app.router.add_post(webhook_path, webhook_handler)
        
        logger.info("🌐 Веб-сервер настроен")
        return app
        
    except Exception as e:
        logger.error(f"❌ Ошибка в main: {e}")
        raise

if __name__ == "__main__":
    try:
        web.run_app(main(), port=PORT)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
