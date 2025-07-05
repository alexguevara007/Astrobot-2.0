"""
AstroBot — Telegram ассистент по гороскопам, Таро и Луне 🌙
"""

import os
import time
import logging
import asyncio
import aiohttp
import psutil
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
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

# === 📝 Логгирование ===
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === 🔐 Загрузка токена и настроек ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = "https://astrobot-2-0.onrender.com"
KEEP_ALIVE_INTERVAL = 840  # 14 минут
START_TIME = datetime.now()

if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN не найден в .env")
    raise SystemExit("BOT_TOKEN отсутствует. Выход.")

# Создаем глобальную переменную для приложения
application = None

def get_memory_usage():
    """Получение информации об использовании памяти"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss": f"{memory_info.rss / 1024 / 1024:.1f}MB",
        "vms": f"{memory_info.vms / 1024 / 1024:.1f}MB"
    }

def get_uptime():
    """Получение времени работы сервера"""
    uptime = datetime.now() - START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

async def keep_alive():
    """Функция для поддержания активности сервера"""
    logger.info("Keep-alive механизм запущен")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{RENDER_URL}/") as response:
                    if response.status == 200:
                        logger.info(f"Keep-alive пинг успешен: {datetime.now()}")
                    else:
                        logger.warning(f"Keep-alive пинг вернул статус {response.status}")
            except Exception as e:
                logger.error(f"Ошибка keep-alive пинга: {e}")
            
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)

# === ⛑ Глобальный обработчик ошибок ===
async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Ошибка: %s", context.error, exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")
    except Exception:
        logger.exception("Не удалось отправить сообщение об ошибке.")

# === Обработчик webhook ===
async def webhook_handler(request):
    """Обработчик webhook запросов от Telegram"""
    try:
        update_data = await request.json()
        logger.info("\n=================НОВОЕ ОБНОВЛЕНИЕ=================")
        logger.info(f"RAW UPDATE: {update_data}")

        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        logger.info("✅ Обновление обработано")
        
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        logger.exception("Полный стек ошибки:")
        return web.Response(status=500)

# === Health check ===
async def health_check(request):
    """Расширенный health check"""
    try:
        start_time = datetime.now()
        webhook_info = await application.bot.get_webhook_info()
        bot_info = await application.bot.get_me()
        response_time = (datetime.now() - start_time).total_seconds()

        return web.json_response({
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "bot": {
                "username": bot_info.username,
                "id": bot_info.id,
                "webhook_url": webhook_info.url,
                "pending_updates": webhook_info.pending_update_count
            },
            "performance": {
                "response_time": f"{response_time:.3f}s",
                "memory_usage": get_memory_usage()
            },
            "uptime": get_uptime(),
            "version": "2.0"
        })
    except Exception as e:
        logger.error(f"Ошибка в health check: {e}")
        return web.json_response({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

# === Настройка бота ===
async def setup_bot():
    """Настройка бота"""
    global application
    
    try:
        # 📂 Подготовка
        init_db()

        # ✅ Настройки по умолчанию (HTML)
        defaults = Defaults(parse_mode=ParseMode.HTML)

        # 🤖 Приложение
        application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()
        
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

        # 🛑 Глобальный обработчик ошибок
        application.add_error_handler(error_handler)

        # ⏰ Планировщик
        setup_scheduler(application)

        # Проверка подключения
        bot_info = await application.bot.get_me()
        logger.info(f"""
        === Информация о боте ===
        Имя: {bot_info.first_name}
        Username: @{bot_info.username}
        ID: {bot_info.id}
        """)

        # Настройка webhook
        webhook_path = f"/webhook/{BOT_TOKEN}"
        webhook_url = f"{RENDER_URL}{webhook_path}"
        
        await application.bot.delete_webhook()
        await application.bot.set_webhook(webhook_url)
        
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"""
        === Информация о webhook ===
        URL: {webhook_info.url}
        Pending updates: {webhook_info.pending_update_count}
        """)

        logger.info("✅ Бот успешно настроен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке бота: {e}")
        logger.exception("Полный стек ошибки:")
        raise

# === Основная функция ===
async def main():
    """Основная функция"""
    try:
        await setup_bot()
        
        app = web.Application()
        webhook_path = f"/webhook/{BOT_TOKEN}"
        
        app.router.add_get("/", health_check)
        app.router.add_post(webhook_path, webhook_handler)
        
        # Запускаем keep-alive в отдельной таске
        asyncio.create_task(keep_alive())
        
        logger.info("🌐 Веб-сервер настроен")
        return app
        
    except Exception as e:
        logger.error(f"❌ Ошибка в main: {e}")
        raise

# === Точка входа ===
if __name__ == "__main__":
    try:
        web.run_app(main(), port=PORT)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
