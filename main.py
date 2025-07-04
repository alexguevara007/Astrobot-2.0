import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)
from menu import start, button_handler

# Включаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔒 Вставь свой токен
BOT_TOKEN = "7636508766:AAGozCbG5JYdGyVaPAYB1eU_eFMSWg5Tp38"

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler("start", start))

    # Callback-кнопки из меню
    app.add_handler(CallbackQueryHandler(button_handler))

    # ✅ Здесь ты можешь добавить хендлеры для /tarot, /subscribe и т.д.

    # Запуск бота
    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()