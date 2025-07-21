from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
import json
import random
from keyboards import get_back_to_menu_inline
from services.database import save_prediction
from locales import get_text
from services.yandex_translate import translate

# Загрузка колоды
with open("data/tarot_cards.json", encoding="utf-8") as f:
    CARDS = json.load(f)

# Названия позиций 5-карточного расклада
POSITIONS_5 = {
    'ru': [
        "1. Суть ситуации",
        "2. Что помогает / мешает",
        "3. Глубинная мотивация",
        "4. Опыт прошлого",
        "5. Возможный исход"
    ],
    'en': [
        "1. Core of the situation",
        "2. What helps / hinders",
        "3. Deep motivation",
        "4. Past experience",
        "5. Possible outcome"
    ]
}

async def draw_card(lang: str = 'ru', used_names: set = set()) -> dict:
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

async def tarot5(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = 'ru'):
    try:
        chat_id = update.effective_chat.id
        used = set()
        cards = []
        all_images = []
        message = get_text('tarot5_header', lang) + "\n\n"

        positions = POSITIONS_5.get(lang, POSITIONS_5['ru'])

        for i in range(5):
            card = await draw_card(lang, used)
            cards.append(card)
            all_images.append(card['image'])
            message += f"{positions[i]}\n→ {card['name']}\n{card['meaning']}\n\n"

        message += get_text('tarot_think', lang)

        save_prediction(chat_id, message, "tarot5")

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
