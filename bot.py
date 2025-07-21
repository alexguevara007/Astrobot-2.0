import os
import logging
import asyncio
import aiohttp
import psutil
import random  # Добавлено для случайной задержки
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # Добавлены импорты для клавиатур
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

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_URL = "https://astrobot-2-0.onrender.com"
KEEP_ALIVE_INTERVAL = 840  # Базовый интервал

START_TIME = datetime.now()
application = None

if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN не найден в .env")
    raise SystemExit("BOT_TOKEN отсутствует. Выход.")

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
            await asyncio.sleep(KEEP_ALIVE_INTERVAL + random.randint(0, 60))  # Случайная задержка

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ Ошибка: %s", context.error, exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")
    except Exception:
        logger.exception("Ошибка отправки сообщения об ошибке.")

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

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = update.effective_user.language_code or 'ru'
    if user_lang not in LANGUAGES:
        user_lang = 'ru'
    context.user_data['lang'] = user_lang
    
    await track_user(update.effective_user)  # Пример интеграции трекинга
    
    text = get_text('welcome', user_lang)
    await update.message.reply_text(text)

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(LANGUAGES[lang_code], callback_data=f"lang_{lang_code}")]
                for lang_code in LANGUAGES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose language / Выберите язык:", reply_markup=reply_markup)

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    text = get_text('language_set', lang, lang=LANGUAGES[lang])
    await query.edit_message_text(text)

async def horoscope_today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await horoscope_today(update, context, lang=lang)

async def horoscope_tomorrow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await horoscope_tomorrow(update, context, lang=lang)

async def setup_bot():
    global application

    try:
        init_db()
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

        await application.initialize()
        await application.start()

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

        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_command_handler))

        application.add_handler(CommandHandler("language", language_handler))
        application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))

        application.add_error_handler(error_handler)
        setup_scheduler(application)

        bot_info = await application.bot.get_me()
        logger.info(f"""
        === Бот подключен ===
        🤖 Имя: {bot_info.first_name}
        🆔 ID: {bot_info.id}
        📛 Юзернейм: @{bot_info.username}
        """)

        webhook_path = f"/webhook/{BOT_TOKEN}"
        webhook_url = f"{RENDER_URL}{webhook_path}"
        await application.bot.delete_webhook()
        success = await application.bot.set_webhook(webhook_url)
        if success:
            logger.info(f"🌐 Webhook установлен: {webhook_url}")
        else:
            logger.error("❌ Не удалось установить webhook")

    except Exception as e:
        logger.error(f"Ошибка при старте бота: {e}", exc_info=True)
        raise

def main():  # Сделали синхронной
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_bot())  # Запускаем асинхронную настройку

    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)

    loop.create_task(keep_alive())  # Запускаем keep_alive как задачу

    return app

if __name__ == "__main__":
    try:
        app = main()  # Получаем app синхронно
        web.run_app(app, port=PORT)  # Запускаем сервер
    except Exception as e:
        logger.critical(f"❌ Ошибка запуска: {e}", exc_info=True)
