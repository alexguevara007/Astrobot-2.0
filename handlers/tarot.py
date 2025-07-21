import json
import random
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from services.database import save_prediction
from keyboards import get_back_to_menu_inline
from services.locales import get_text
from services.yandex_translate import translate

# Загрузка данных карт
with open("data/tarot_cards.json", encoding="utf-8") as f:
    CARDS = json.load(f)

# Позиции для 3-картного расклада
POSITIONS_3 = {
    'ru': ["Прошлое", "Настоящее", "Будущее"],
    'en': ["Past", "Present", "Future"]
}

async def draw_card(lang: str = 'ru', used_names: set = None) -> dict:
    if used_names is None:
        used_names = set()
        
    while True:
        card = random.choice(CARDS)
        if card["name"] not in used_names:
            used_names.add(card["name"])
            is_reversed = random.choice([True, False])
            name = card["name"] + (" (перевёрнутая)" if is_reversed else "")
            meaning = card["reversed_meaning"] if is_reversed else card["meaning"]
            
            if lang == 'en':
                name = await translate(name, 'en')
                meaning = await translate(meaning, 'en')
            
            return {
                "name": name,
                "meaning": meaning,
                "image": card["image"]
            }

def split_text(text: str, limit: int = 1000) -> list:
    if len(text) <= limit:
        return [text]
    
    parts = []
    current_part = ""
    
    for paragraph in text.split('\n\n'):
        if len(current_part) + len(paragraph) + 2 <= limit:
            current_part += (paragraph + '\n\n')
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = paragraph + '\n\n'
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts

async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        card = await draw_card(lang)

        message = get_text('tarot_card', lang, card_name=card['name'], description=card['meaning'])

        text_parts = split_text(message)

        save_prediction(update.effective_chat.id, message, "tarot")

        if update.callback_query:
            send_photo = update.callback_query.message.reply_photo
            send_text = update.callback_query.message.reply_text
        else:
            send_photo = update.message.reply_photo
            send_text = update.message.reply_text

        await send_photo(
            photo=card["image"],
            caption=text_parts[0]
        )

        for part in text_parts[1:]:
            await send_text(part)

        await send_text(
            "🃏",
            reply_markup=get_back_to_menu_inline(lang=lang)
        )

    except Exception as e:
        error_message = get_text('tarot_error', lang)
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)

async def tarot3(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        used = set()
        cards = []
        all_images = []
        message = get_text('tarot3_header', lang) + "\n\n"

        positions = POSITIONS_3.get(lang, POSITIONS_3['ru'])

        for i in range(3):
            card = await draw_card(lang, used)
            cards.append(card)
            all_images.append(card["image"])
            message += f"{positions[i]}\n→ {card['name']}\n{card['meaning']}\n\n"

        save_prediction(update.effective_chat.id, message, "tarot3")

        text_parts = split_text(message)

        if update.callback_query:
            send_media = update.callback_query.message.reply_media_group
            send_text = update.callback_query.message.reply_text
        else:
            send_media = update.message.reply_media_group
            send_text = update.message.reply_text

        media_group = [
            InputMediaPhoto(media=img) for img in all_images[:-1]
        ]
        media_group.append(
            InputMediaPhoto(
                media=all_images[-1],
                caption=text_parts[0]
            )
        )

        await send_media(media=media_group)

        for part in text_parts[1:]:
            await send_text(part)

        await send_text(
            "🃏",
            reply_markup=get_back_to_menu_inline(lang=lang)
        )

    except Exception as e:
        error_message = get_text('tarot_error', lang)
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)
