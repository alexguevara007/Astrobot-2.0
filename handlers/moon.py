from telegram import Update
from telegram.ext import ContextTypes
from services.lunar import get_lunar_text
from keyboards import get_back_to_menu_inline
from services.locales import get_text

async def moon(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        lunar_info = get_lunar_text(lang=lang)
        
        message = get_text('moon_phase', lang, phase=lunar_info)
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=message,
                parse_mode="Markdown",
                reply_markup=get_back_to_menu_inline(lang=lang)
            )
        else:
            await update.message.reply_text(
                text=message,
                parse_mode="Markdown",
                reply_markup=get_back_to_menu_inline(lang=lang)
            )

    except Exception as e:
        error_message = get_text('moon_error', lang)
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=error_message,
                reply_markup=get_back_to_menu_inline(lang=lang)
            )
        else:
            await update.message.reply_text(
                text=error_message,
                reply_markup=get_back_to_menu_inline(lang=lang)
            )
