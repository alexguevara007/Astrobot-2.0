# === Обработчики путей ===
async def health_check(request):
    """Расширенный обработчик для проверки работоспособности"""
    try:
        webhook_info = await application.bot.get_webhook_info()
        bot_info = await application.bot.get_me()
        return web.json_response({
            "status": "running",
            "bot_username": bot_info.username,
            "webhook_url": webhook_info.url,
            "webhook_has_custom_certificate": webhook_info.has_custom_certificate,
            "webhook_pending_update_count": webhook_info.pending_update_count,
            "timestamp": time.time(),
            "service": "AstroBot",
            "version": "2.0"
        })
    except Exception as e:
        logger.error(f"Ошибка в health_check: {e}")
        return web.json_response({"status": "error", "error": str(e)}, status=500)

async def webhook_handler(request):
    """Обработчик webhook запросов от Telegram"""
    try:
        update = await request.json()
        logger.info(f"📥 Получено обновление: {update}")
        
        # Проверяем тип обновления
        if 'message' in update:
            logger.info(f"Получено сообщение: {update['message'].get('text', '')}")
        elif 'callback_query' in update:
            logger.info(f"Получен callback: {update['callback_query'].get('data', '')}")
        
        # Обрабатываем обновление
        await application.process_update(update)
        logger.info("✅ Обновление обработано успешно")
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}", exc_info=True)
        return web.Response(status=500)

# === main ===
async def main():
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
        logger.info("Приложение инициализировано и запущено")

        # Проверяем подключение к API Telegram
        bot_info = await application.bot.get_me()
        logger.info(f"Бот @{bot_info.username} успешно подключен")

        # === 📌 Добавляем обработчики... ===
        # (оставьте весь код обработчиков как есть)

        # ▶️ Настройка webhook
        webhook_path = f"/webhook/{BOT_TOKEN}"
        webhook_url = f"{RENDER_URL}{webhook_path}"
        
        # Удаляем старый webhook и устанавливаем новый
        await application.bot.delete_webhook()
        await application.bot.set_webhook(webhook_url)
        
        # Проверяем установку webhook
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"🚀 Webhook установлен на {webhook_info.url}")
        logger.info(f"Pending updates: {webhook_info.pending_update_count}")

        # Настройка веб-приложения
        app = web.Application()
        
        # Добавляем обработчики путей
        app.router.add_get("/", health_check)
        app.router.add_post(webhook_path, webhook_handler)
        
        logger.info(f"🌐 Веб-сервер настроен на порту {PORT}")
        
        return app

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации: {e}", exc_info=True)
        raise

# === Точка входа ===
if __name__ == "__main__":
    try:
        web.run_app(main(), port=PORT)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
