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
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode

# === 🧩 Хендлеры ===
from handlers.menu import start, button_handler, reply_command_handler
from handlers.horoscope import horoscope_today, horoscope_tomorrow
from handlers.subscribe import subscribe, unsubscribe, subscription_status
from handlers.moon import moon
from handlers.tarot import tarot, tarot3
from handlers.tarot5 import tarot5
from handlers.compatibility import compatibility
from handlers.stats import new_users  # ✅ <--- NEW

# === 💾 Базы и планировщик ===
from services.database import init_db
from scheduler import setup_scheduler

# === 👀 Аналитика пользователей ===
from services.user_tracker import track_user  # <--- Новый трекер

# === 📝 Логгирование ===
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === 🔐 Загрузка переменных окружения ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = "https://astrobot-2-0.onrender.com"  # замените на ваш URL
KEEP_ALIVE_INTERVAL = 840  # 14 минут

START_TIME = datetime.now()
application = None  # Глобальное приложение

if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN не найден в .env")
    raise SystemExit("BOT_TOKEN отсутствует. Выход.")

# === Системные функции ===

def get_memory_usage():
    process = psutil.Process()
    mem = process.memory_info()
    return {
        "rss": f"{mem.rss / 1024 / 1024:.1f}MB",
        "vms": f"{mem.vms / 1024 / 1024:.1f}MB"
    }

def get_uptime():
    uptime = datetime.now() - START_TIME
    days = uptime.days
    hours, rem = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

async def keep_alive():
    logger.info("Keep-alive механизм активен")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{RENDER_URL}/") as resp:
                    logger.info(f"✅ Keep-alive статус: {resp.status} @ {datetime.now()}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка ping: {e}")
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)

# === Обработка ошибок ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Ошибка: %s", context.error, exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")
    except Exception:
        logger.exception("Ошибка отправки сообщения об ошибке.")

# === Обработчик Webhook ===
async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        logger.info("✅ Обновление обработано")
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook_handler: {e}", exc_info=True)
        return web.Response(status=500)

# === Health Check ===
async def health_check(request):
    try:
        start_time = datetime.now()
        bot_info = await application.bot.get_me()
        webhook_info = await application.bot.get_webhook_info()
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
                "memory": get_memory_usage(),
                "response_time": f"{response_time:.3f}s"
            },
            "uptime": get_uptime(),
            "version": "2.0"
        })
    except Exception as e:
        logger.error(f"❌ Ошибка в health_check: {e}", exc_info=True)
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

# === Настройка приложения Telegram Bot ===
async def setup_bot():
    global application

    try:
        init_db()
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

        await application.initialize()
        await application.start()

        # === Команды ===
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

        application.add_handler(CommandHandler("newusers", new_users))  # ✅ Аналитика

        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))

        application.add_error_handler(error_handler)
        setup_scheduler(application)

        # === Инфо о боте
        bot_info = await application.bot.get_me()
        logger.info(f"""
        === Бот подключен ===
        🤖 Имя: {bot_info.first_name}
        🆔 ID: {bot_info.id}
        📛 Юзернейм: @{bot_info.username}
        """)

        # === Устанавливаем webhook
        webhook_path = f"/webhook/{BOT_TOKEN}"
        webhook_url = f"{RENDER_URL}{webhook_path}"
        await application.bot.delete_webhook()
        await application.bot.set_webhook(webhook_url)

        logger.info(f"🌐 Webhook установлен: {webhook_url}")

    except Exception as e:
        logger.error(f"Ошибка при старте бота: {e}", exc_info=True)
        raise

# === Точка входа ===
async def main():
    await setup_bot()

    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)

    asyncio.create_task(keep_alive())  # Пинг every 14 min
    return app

if __name__ == "__main__":
    try:
        web.run_app(main(), port=PORT)
    except Exception as e:
        logger.critical(f"❌ Ошибка запуска: {e}", exc_info=True)
