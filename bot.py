"""
AstroBot — Telegram ассистент по гороскопам, Таро и Луне 🌙
"""

import os
import time
import logging
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters
)
from telegram.constants import ParseMode

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

if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN не найден в .env")
    raise SystemExit("BOT_TOKEN отсутствует. Выход.")

# Создаем глобальную переменную для приложения
application = None

# === Тестовые обработчики команд ===
async def test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый обработчик команды /start"""
    try:
        logger.info(f"Вызвана команда /start пользователем {update.effective_user.id}")
        await update.message.reply_text(
            "🌟 Тестовый ответ на команду /start\n"
            "Бот работает!"
        )
        logger.info("Ответ на /start отправлен успешно")
    except Exception as e:
        logger.error(f"Ошибка в обработчике test_start: {e}")
        await update.message.reply_text("Произошла ошибка")

async def test_tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый обработчик команды /tarot"""
    try:
        logger.info(f"Вызвана команда /tarot пользователем {update.effective_user.id}")
        await update.message.reply_text(
            "🎴 Тестовый ответ на команду /tarot\n"
            "Идет обработка..."
        )
        logger.info("Ответ на /tarot отправлен успешно")
    except Exception as e:
        logger.error(f"Ошибка в обработчике test_tarot: {e}")
        await update.message.reply_text("Произошла ошибка")

# === Обработчик webhook ===
async def webhook_handler(request):
    """Обработчик webhook запросов от Telegram"""
    try:
        update = await request.json()
        logger.info("\n=================НОВОЕ ОБНОВЛЕНИЕ=================")
        logger.info(f"RAW UPDATE: {update}")

        if 'message' in update:
            message = update['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            # Отправляем тестовое сообщение до обработки команды
            try:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=f"Получена команда: {text}"
                )
                logger.info(f"Тестовое сообщение отправлено в чат {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки тестового сообщения: {e}")

        # Обработка обновления
        try:
            await application.process_update(update)
            logger.info("✅ Обновление обработано")
        except Exception as e:
            logger.error(f"Ошибка при обработке update: {e}")
            logger.exception("Стек ошибки:")
        
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        logger.exception("Полный стек ошибки:")
        return web.Response(status=500)

# === Health check ===
async def health_check(request):
    """Проверка работоспособности сервиса"""
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

# === Настройка бота ===
async def setup_bot():
    """Настройка бота"""
    global application
    
    try:
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()
        
        await application.initialize()
        await application.start()

        # Тестовые обработчики
        application.add_handler(CommandHandler("start", test_start))
        application.add_handler(CommandHandler("tarot", test_tarot))
        
        # Базовый обработчик текста
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            lambda update, context: update.message.reply_text("Получено текстовое сообщение")
        ))

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
