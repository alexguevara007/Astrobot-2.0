import os
import logging
import asyncio
import aiohttp
import psutil
import random
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode

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

# ─────────────── Логирование ───────────────
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────── Загрузка переменных ───────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = os.getenv("RENDER_URL", "https://astrobot-2-0.onrender.com")
KEEP_ALIVE_INTERVAL = 840  # ~14 минут

START_TIME = datetime.now()
application = None

if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN не найден в .env")
    raise SystemExit("❌ BOT_TOKEN отсутствует. Завершение работы.")

# ─────────────── Статистика ───────────────
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

# ─────────────── Keep Alive ───────────────
async def keep_alive():
    logger.info("✅ Keep-alive запущен")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{RENDER_URL}/") as resp:
                    logger.info(f"🔁 Keep-alive: {resp.status} @ {datetime.now().isoformat()}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка ping: {e}")
            await asyncio.sleep(KEEP_ALIVE_INTERVAL + random.randint(0, 60))

# ─────────────── Обработка ошибок ───────────────
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Ошибка: %s", context.error, exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")
    except Exception:
        logger.exception("Ошибка отправки сообщения об ошибке.")

# ─────────────── Webhook ───────────────
async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка webhook_handler: {e}", exc_info=True)
        return web.Response(status=500)

# ─────────────── Healthcheck ───────────────
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
        logger.error(f"❌ Ошибка health_check: {e}", exc_info=True)
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

# ─────────────── /start с сохранением языка и трекингом ───────────────
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = update.effective_user.language_code or 'ru'
    user_lang = user_lang if user_lang in LANGUAGES else 'ru'
    context.user_data['lang'] = user_lang

    # ❗ Трекинг пользователя — 🍀 синхронно, без await!
    track_user(update.effective_user.id, update.effective_user.username)

    await update.message.reply_text(get_text('welcome', user_lang))

# ─────────────── Смена языка ───────────────
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(LANGUAGES[code], callback_data=f"lang_{code}")]
                for code in LANGUAGES]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose language / Выберите язык:", reply_markup=markup)

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    await query.edit_message_text(get_text('language_set', lang, lang=LANGUAGES[lang]))

# ─────────────── Обработчики гороскопов ───────────────
async def horoscope_today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await horoscope_today(update, context, lang=lang)

async def horoscope_tomorrow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await horoscope_tomorrow(update, context, lang=lang)

# ─────────────── Инициализация бота и webhook ───────────────
async def setup_bot():
    global application
    init_db()
    defaults = Defaults(parse_mode=ParseMode.HTML)

    application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

    # Старт
    await application.initialize()
    await application.start()

    # 🔁 Команды
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("help", start))

    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("status", subscription_status))

    application.add_handler(CommandHandler("horoscope", horoscope_today_handler))
    application.add_handler(CommandHandler("tomorrow", horoscope_tomorrow_handler))
    application.add_handler(CommandHandler("moon", moon))

    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("tarot3", tarot3))
    application.add_handler(CommandHandler("tarot5", tarot5))
    application.add_handler(CommandHandler("compatibility", compatibility))

    application.add_handler(CommandHandler("newusers", new_users))

    # 👇 Обработка кнопок и обычных текстов
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))

    # Языковая команда
    application.add_handler(CommandHandler("language", language_handler))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))

    application.add_error_handler(error_handler)

    # Планировщик (гороскопы и т.п.)
    setup_scheduler(application)

    # Webhook
    webhook_path = f"/webhook/{BOT_TOKEN}"
    webhook_url = f"{RENDER_URL}{webhook_path}"
    await application.bot.delete_webhook()
    success = await application.bot.set_webhook(webhook_url)
    if success:
        logger.info(f"🌐 Webhook установлен: {webhook_url}")
    else:
        logger.error("❌ Не удалось установить webhook")

    bot = await application.bot.get_me()
    logger.info(f"🤖 Бот запущен: @{bot.username} ({bot.id})")

# ─────────────── Точка входа ───────────────
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_bot())

    # Web приложение (aiohttp)
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)

    # Keep-alive Loop
    loop.create_task(keep_alive())

    return app

# 🚀 Запуск
if __name__ == "__main__":
    try:
        app = main()
        web.run_app(app, port=PORT)
    except Exception as e:
        logger.critical(f"❌ Ошибка запуска: {e}", exc_info=True)
