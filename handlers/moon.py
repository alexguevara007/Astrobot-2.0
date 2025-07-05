from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import logging
from services.lunar import get_lunar_text
from keyboards import get_back_to_menu_inline

logger = logging.getLogger(__name__)

async def moon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды лунного календаря"""
    try:
        # Показываем статус загрузки
        loading_message = "🔮 Получаем данные о луне..."
        if update.callback_query:
            message = await update.callback_query.message.edit_text(
                text=loading_message,
                parse_mode="Markdown"
            )
            await update.callback_query.answer()
        else:
            message = await update.message.reply_text(
                text=loading_message,
                parse_mode="Markdown"
            )

        # Получаем информацию о луне
        lunar_info = get_lunar_text()
        
        # Формируем сообщение
        response = (
            "🌙 *Лунный календарь*\n\n"
            f"{lunar_info}"
        )
        
        # Отправляем ответ
        try:
            await message.edit_text(
                text=response,
                parse_mode="Markdown",
                reply_markup=get_back_to_menu_inline()
            )
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise

    except Exception as e:
        logger.error(f"Ошибка в обработчике moon: {e}")
        error_message = (
            "⚠️ *Ошибка при получении данных*\n\n"
            "Пожалуйста, попробуйте позже."
        )
        try:
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    text=error_message,
                    parse_mode="Markdown",
                    reply_markup=get_back_to_menu_inline()
                )
            else:
                await update.message.reply_text(
                    text=error_message,
                    parse_mode="Markdown",
                    reply_markup=get_back_to_menu_inline()
                )
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке сообщения об ошибке: {e}")
