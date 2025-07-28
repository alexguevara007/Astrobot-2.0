import json
import random
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from services.database import save_prediction
from keyboards import get_back_to_menu_inline

# Загрузка данных карт
with open("data/tarot_cards.json", encoding="utf-8") as f:
    CARDS = json.load(f)

# Позиции для 3-картного расклада
POSITIONS_3 = ["Прошлое", "Настоящее", "Будущее"]

def draw_card(used_names: set = None) -> dict:
    if used_names is None:
        used_names = set()
        
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

async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        card = draw_card()

        message = f"🃏 Карта дня\n\n{card['name']}\n{card['meaning']}"

        # Разбиваем текст на части
        text_parts = split_text(message)

        # Сохраняем в БД
        save_prediction(update.effective_chat.id, message, "tarot")

        # Определяем метод отправки
        if update.callback_query:
            send_photo = update.callback_query.message.reply_photo
            send_text = update.callback_query.message.reply_text
        else:
            send_photo = update.message.reply_photo
            send_text = update.message.reply_text

        # Отправляем карту с первой частью текста
        await send_photo(
            photo=card["image"],
            caption=text_parts[0]
        )

        # Отправляем остальные части текста
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

async def tarot3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        used = set()
        cards = []
        all_images = []
        message = "🃏 Расклад из трёх карт\n\n"

        # Вытягиваем карты
        for i in range(3):
            card = draw_card(used)
            cards.append(card)
            all_images.append(card["image"])
            message += f"{POSITIONS_3[i]}\n→ {card['name']}\n{card['meaning']}\n\n"

        # Сохраняем в БД
        save_prediction(update.effective_chat.id, message, "tarot3")

        # Разбиваем текст
        text_parts = split_text(message)

        # Определяем метод отправки
        if update.callback_query:
            send_media = update.callback_query.message.reply_media_group
            send_text = update.callback_query.message.reply_text
        else:
            send_media = update.message.reply_media_group
            send_text = update.message.reply_text

        # Формируем media group
        media_group = [
            InputMediaPhoto(media=img) for img in all_images[:-1]
        ]
        # Последняя карта — с подписью
        media_group.append(
            InputMediaPhoto(
                media=all_images[-1],
                caption=text_parts[0]
            )
        )

        # Отправляем изображения
        await send_media(media=media_group)

        # Остаток текста
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