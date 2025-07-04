# Измените обработчик webhook_handler:
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
            
            logger.info(f"""
            Детали сообщения:
            Chat ID: {chat_id}
            Текст: {text}
            Это команда: {text.startswith('/')}
            """)
            
            # Отправляем тестовое сообщение
            try:
                if text == '/start':
                    await test_start(Update.de_json(update, application.bot), None)
                elif text == '/tarot':
                    await test_tarot(Update.de_json(update, application.bot), None)
                else:
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text=f"Получена команда: {text}"
                    )
                logger.info(f"Сообщение обработано для команды {text}")
            except Exception as e:
                logger.error(f"Ошибка обработки команды {text}: {e}")
                logger.exception("Стек ошибки:")

        # Обработка обновления через стандартный механизм
        try:
            await application.process_update(Update.de_json(update, application.bot))
            logger.info("✅ Обновление обработано стандартным обработчиком")
        except Exception as e:
            logger.error(f"Ошибка при обработке update: {e}")
            logger.exception("Стек ошибки:")
        
        return web.Response()
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        logger.exception("Полный стек ошибки:")
        return web.Response(status=500)

# Измените тестовые обработчики:
async def test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый обработчик команды /start"""
    try:
        user_id = update.effective_user.id if update.effective_user else "Неизвестно"
        logger.info(f"Вызвана команда /start пользователем {user_id}")
        
        await update.message.reply_text(
            "🌟 Добро пожаловать в AstroBot!\n\n"
            "Доступные команды:\n"
            "/start - Показать это сообщение\n"
            "/tarot - Расклад Таро"
        )
        logger.info("Ответ на /start отправлен успешно")
    except Exception as e:
        logger.error(f"Ошибка в обработчике test_start: {e}")
        logger.exception("Стек ошибки:")
        if update and update.message:
            await update.message.reply_text("Произошла ошибка")

async def test_tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый обработчик команды /tarot"""
    try:
        user_id = update.effective_user.id if update.effective_user else "Неизвестно"
        logger.info(f"Вызвана команда /tarot пользователем {user_id}")
        
        await update.message.reply_text(
            "🎴 Расклад Таро\n\n"
            "Идет подготовка расклада...\n"
            "Пожалуйста, подождите."
        )
        logger.info("Ответ на /tarot отправлен успешно")
    except Exception as e:
        logger.error(f"Ошибка в обработчике test_tarot: {e}")
        logger.exception("Стек ошибки:")
        if update and update.message:
            await update.message.reply_text("Произошла ошибка")
