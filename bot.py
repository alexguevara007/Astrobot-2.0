import os
import logging
import asyncio
import aiohttp
import random
import psutil
import signal  # Для graceful shutdown
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode

# ─────── Импорты из приложения ───────
from handlers.menu import start as menu_start, button_handler, reply_command_handler
from handlers.horoscope import horoscope_today, horoscope_tomorrow
from handlers.subscribe import subscribe, unsubscribe, subscription_status
from handlers.moon import moon
from handlers.tarot import tarot, tarot3
from handlers.tarot5 import tarot5
from handlers.compatibility import compatibility
from handlers.stats import new_users

from services.database import init_db
from scheduler import setup_scheduler
from services.user_tracker import track_user
from services.locales import get_text, LANGUAGES

# ─────── Логирование (улучшено) ───────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Можно добавить FileHandler для файлов
)
logger = logging.getLogger(__name__)

# ─────── Переменные окружения ───────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env!")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = os.getenv("RENDER_URL", "https://astrobot.onrender.com")
KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", 840))  # Configurable
START_TIME = datetime.now()

# ─────── Вспомогательные функции ───────
def get_uptime():
    uptime = datetime.now() - START_TIME
    return f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"

def get_memory_usage():
    process = psutil.Process()
    mem = process.memory_info()
    return {
        "rss": f"{mem.rss / 1024 / 1024:.1f}MB",
        "vms": f"{mem.vms / 1024 / 1024:.1f}MB"
    }

async def keep_alive():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{RENDER_URL}/") as resp:
                    logger.info(f"🔁 Keep-alive ping: {resp.status}")
            except Exception as e:
                logger.warning(f"⚠️ Keep-alive error: {e}")
            await asyncio.sleep(KEEP_ALIVE_INTERVAL + random.randint(0, 30))

# ─────── Webhook-хендлер ───────
async def webhook_handler(request: web.Request):
    try:
        data = await request.json()
        logger.info(f"[WEBHOOK] 🔔 Обновление получено: {data}")
        bot_app = request.app["application"]
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return web.Response()
    except Exception as e:
        logger.exception("❌ Webhook обработка не удалась")
        return web.Response(status=500)

# ─────── Health Check (с try-except) ───────
async def health_check(request: web.Request):
    try:
        bot_app = request.app["application"]
        bot_info = await bot_app.bot.get_me()
        webhook = await bot_app.bot.get_webhook_info()

        return web.json_response({
            "status": "ok",
            "bot": {
                "username": bot_info.username,
                "id": bot_info.id,
                "webhook": webhook.url,
                "pending": webhook.pending_update_count
            },
            "timestamp": datetime.now().isoformat(),
            "uptime": get_uptime(),
            "memory": get_memory_usage()
        })
    except Exception as e:
        logger.exception("❌ Ошибка health_check")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

# ─────── Обработка ошибок Telegram ───────
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Telegram error: %s", context.error, exc_info=True)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ Ошибка. Попробуйте позже.")
        except Exception:
            logger.exception("Не удалось отправить сообщение об ошибке.")

# ─────── Обработка /start ───────
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang_code = user.language_code or 'ru'
    lang = lang_code if lang_code in LANGUAGES else 'ru'
    context.user_data['lang'] = lang

    track_user(user.id, user.username or "")  # TODO: Сделать async, если пишет в БД
    await update.message.reply_text(get_text("welcome", lang))

# ─────── Обработка выбора языка ───────
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")]
                for code, name in LANGUAGES.items()]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌍 Choose language:", reply_markup=markup)

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    await query.edit_message_text(get_text('language_set', lang, lang=LANGUAGES[lang]))

# ─────── Основной запуск ───────
async def main():
    init_db()
    app = web.Application()

    # Telegram Application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .build()
    )

    app["application"] = application

    # AIOHTTP маршруты
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)
    app.router.add_get("/", health_check)

    # Telegram хендлеры (без изменений)
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("menu", menu_start))
    application.add_handler(CommandHandler("help", menu_start))
    application.add_handler(CommandHandler("language", language_handler))
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
    application.add_handler(CommandHandler("newusers", new_users))

    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))
    application.add_error_handler(error_handler)

    await application.initialize()
    await application.bot.delete_webhook()
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    await application.bot.set_webhook(webhook_url)  # TODO: Добавить проверку успеха
    await application.start()

    logger.info(f"🤖 Бот запущен по webhook: {webhook_url}")
    logger.info(f"⏱ Uptime: {get_uptime()}")

    setup_scheduler(application)
    asyncio.create_task(keep_alive())

    # Запускаем web-сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Graceful shutdown (на SIGTERM/SIGINT)
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_handler(signum):
        logger.info(f"📴 Получен сигнал {signum}. Остановка...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_handler, sig)

    await stop_event.wait()

    # Cleanup
    await application.stop()
    await application.shutdown()
    await runner.cleanup()
    logger.info("🛑 Бот остановлен gracefully.")

# ─────── Точка входа ───────
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"❌ Ошибка запуска: {e}", exc_info=True)
