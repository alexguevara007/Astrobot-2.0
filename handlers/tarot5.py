from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
import json
import random
from keyboards import get_back_to_menu_inline
from services.database import save_prediction

# Загрузка колоды
with open("data/tarot_cards.json", encoding="utf-8") as f:
    CARDS = json.load(f)

# Названия позиций 5-карточного расклада
POSITIONS_5 = [
    "1. Суть ситуации",
    "2. Что помогает / мешает",
    "3. Глубинная мотивация",
    "4. Опыт прошлого",
    "5. Возможный исход"
]

def draw_card(used_names: set) -> dict:
    while True:
        card = random.choice(CARDS)
        if card["name"] not in used_names:
            used_names.add(card["name"])
            is_reversed = random.choice([True, False])
            name = card["name"] + (" (перевёрнутая)" if is_reversed else "")
            meaning = card["reversed_meaning"] if is_reversed else card["meaning"]
            return {
                "name": name,
                "meaning": meaning,
                "image": card["image"]
            }

def split_text(text: str, limit: int = 1000) -> list:
    """Разделяет текст на части с учетом ограничения длины"""
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

async def tarot5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        used = set()
        cards = []
        all_images = []
        message = "🃏 Пятикарточный расклад Таро\n\n"

        # Вытягиваем карты и формируем текст
        for i in range(5):
            card = draw_card(used)
            cards.append(card)
            all_images.append(card['image'])
            message += f"{POSITIONS_5[i]}\n→ {card['name']}\n{card['meaning']}\n\n"

        # Добавляем финальное сообщение без AI
        message += "💬 Подумайте, как каждая карта отражает вашу ситуацию. Ответ может быть внутри вас."

        # Сохраняем в БД
        save_prediction(chat_id, message, "tarot5")

        # Разбиваем текст на части
        text_parts = split_text(message)

        # Определяем методы отправки
        if update.callback_query:
            send_media = update.callback_query.message.reply_media_group
            send_text = update.callback_query.message.reply_text
        else:
            send_media = update.message.reply_media_group
            send_text = update.message.reply_text

        # MediaGroup для карт — 4 без caption, последняя — с caption
        media_group = [
            InputMediaPhoto(media=img) for img in all_images[:-1]
        ]
        media_group.append(
            InputMediaPhoto(
                media=all_images[-1],
                caption=text_parts[0]
            )
        )

        # Отправка карт
        await send_media(media=media_group)

        # Остальной текст
        for part in text_parts[1:]:
            await send_text(part)

        # Кнопка возврата в меню
        await send_text(
            "🃏",
            reply_markup=get_back_to_menu_inline()
        )

    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)