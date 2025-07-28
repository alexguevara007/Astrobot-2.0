from telegram import Update
from telegram.ext import ContextTypes
from services.lunar import get_lunar_text
from keyboards import get_back_to_menu_inline

async def moon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды лунного календаря"""
    try:
        lunar_info = get_lunar_text()
        
        # Формируем сообщение
        message = (
            "🌙 *Лунный календарь*\n\n"
            f"{lunar_info}"
        )
        
        # Отправляем ответ
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=message,
                parse_mode="Markdown",
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                text=message,
                parse_mode="Markdown",
                reply_markup=get_back_to_menu_inline()
            )

    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=error_message,
                reply_markup=get_back_to_menu_inline()
            )
        else:
            await update.message.reply_text(
                text=error_message,
                reply_markup=get_back_to_menu_inline()
            )
