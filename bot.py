import os
import logging
import asyncio
import aiohttp
import random
import psutil
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode

# Импорты из приложения
from handlers.menu import start, button_handler, reply_command_handler
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

# ────────── Настройка логов ──────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ────────── Переменные ──────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = os.getenv("RENDER_URL", "https://astrobot-2-0.onrender.com")
KEEP_ALIVE_INTERVAL = 840
START_TIME = datetime.now()

# ────────── Вспомогательные функции ──────────
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
                    logger.info(f"🔁 Keep-alive: {resp.status}")
            except Exception as e:
                logger.warning(f"⚠️ Keep-alive ошибка: {e}")
            await asyncio.sleep(KEEP_ALIVE_INTERVAL + random.randint(0, 30))

# ────────── Webhook / Healthcheck ──────────
async def webhook_handler(request: web.Request):
    try:
        data = await request.json()
        bot_app = request.app["application"]  # Получаем application из aiohttp
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return web.Response()
    except Exception as e:
        logger.exception("❌ Ошибка webhook_handler")
        return web.Response(status=500)

async def health_check(request: web.Request):
    try:
        app = request.app["application"]
        bot = app.bot
        start_time = datetime.now()
        bot_info = await bot.get_me()
        webhook = await bot.get_webhook_info()
        elapsed = (datetime.now() - start_time).total_seconds()

        return web.json_response({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "bot": {
                "username": bot_info.username,
                "id": bot_info.id,
                "webhook_url": webhook.url,
                "pending_updates": webhook.pending_update_count
            },
            "uptime": get_uptime(),
            "memory": get_memory_usage(),
            "response_time": f"{elapsed:.3f}s"
        })
    except Exception as e:
        logger.exception("❌ Ошибка health_check")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

# ────────── Ошибки Telegram ──────────
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Ошибка в Telegram: %s", context.error, exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ Ошибка. Попробуйте позже.")

# ────────── /start с трекингом ──────────
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.effective_user.language_code or 'ru'
    lang = lang_code if lang_code in LANGUAGES else 'ru'
    context.user_data['lang'] = lang

    track_user(update.effective_user.id, update.effective_user.username)
    await update.message.reply_text(get_text("welcome", lang))

# ────────── /language команды ──────────
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(LANGUAGES[lang], callback_data=f"lang_{lang}")] for lang in LANGUAGES]
    await update.message.reply_text("🌍 Choose language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    await query.edit_message_text(get_text('language_set', lang, lang=LANGUAGES[lang]))

# ────────── Инициализация приложения ──────────
async def main():
    init_db()
    app = web.Application()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .build()
    )
    app["application"] = application  # Для доступа внутри aiohttp

    # ➕ ROUTES
    app.router.add_get("/", health_check)
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)

    # 🔘 HANDLERS
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("language", language_handler))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))

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

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))

    application.add_error_handler(error_handler)

    # Запуск
    await application.initialize()
    await application.bot.delete_webhook()
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    await application.bot.set_webhook(webhook_url)
    await application.start()

    logging.info(f"🤖 Бот запущен по webhook: {webhook_url}")
    logging.info(f"📊 Uptime: {get_uptime()}")

    # Планировщик и keep_alive
    setup_scheduler(application)
    asyncio.create_task(keep_alive())

    # Запуск aiohttp web-сервера
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Удержание процесса
    await application.updater.wait()

# ────────── Старт ──────────
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"❌ Ошибка запуска: {e}", exc_info=True)
