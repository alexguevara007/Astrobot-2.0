import os
import json
import logging
import random
from datetime import date, timedelta
from services.lunar import get_lunar_text
from services.yandex_gpt import generate_text_with_system

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_FILE = "cache/horoscope_cache.json"
os.makedirs("cache", exist_ok=True)

def load_cache():
    try:
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении кэша: {e}")

def pick_tone():
    """Выбирает тон прогноза с заданной вероятностью"""
    return random.choices(
        ["positive", "neutral", "negative"],
        weights=[0.5, 0.25, 0.25],
        k=1
    )[0]

def generate_horoscope(sign: str, day: str = "today", detailed: bool = False):
    try:
        today = date.today()
        target = today if day == "today" else today + timedelta(days=1)
        date_str = str(target)
        sign = sign.lower()

        cache = load_cache()
        cache_key = f"{'detailed' if detailed else 'brief'}_{sign}_{day}"

        # 📌 Проверка: если в кэше уже есть — возвращаем
        if sign in cache and cache_key in cache[sign] and cache[sign][cache_key]["date"] == date_str:
            logger.info(f"Из кэша: {sign} на {day}")
            return cache[sign][cache_key]["text"]

        # 🔮 Выбираем тон прогноза (эмоциональный окрас)
        tone = pick_tone()

        # 🧠 Системный промпт в зависимости от тона
        tone_instruction = {
            "positive": "в целом благоприятный, вдохновляющий, но реалистичный",
            "neutral": "сбалансированный, спокойный, с акцентом на самонаблюдение",
            "negative": "сдержанный, с конструктивным предупреждением, не драматизируя"
        }

        system_prompt = f"""Ты — опытный астролог и консультант.
Твой стиль — {tone_instruction[tone]}. 
Пиши живо, честно, без клише, с уважением к выбору человека. Избегай пустых обещаний и банальностей, но сохраняй сочувствие и заботу."""

        label = 'сегодня' if day == 'today' else 'завтра'

        if detailed:
            user_prompt = f"""Составь подробный гороскоп на {label} для знака зодиака {sign.title()}.

Учитывай, что стиль должен быть {tone_instruction[tone]}.

⛅ Структура гороскопа:
1. 🌟 Общая энергия дня
2. ❤️ Отношения и семья
3. 💼 Работа и финансы
4. 🏥 Физическое и ментальное здоровье
5. 💡 Главный совет дня
6. ☀️ Благоприятные цвета, числа и часы
7. 🚫 Потенциальные риски и как их избежать
8. 👥 Взаимодействие с окружающими
9. 🎯 Эмоциональный вектор дня

Используй эмодзи и делай текст живым и не как робот."""
        else:
            user_prompt = f"""Напиши краткий гороскоп на {label} для знака зодиака {sign.title()}.
Тон: {tone_instruction[tone]}.

💡 Включи 3 пункта:
1. Главное ощущение и фон дня
2. Короткий совет
3. Когда лучше всего принять важные решения

Не используй общий стиль для всех — сделай уникально и жизненно."""

        # ✅ Генерация текста с GPT
        logger.info(f"Генерация гороскопа: {sign}, {day}, тон: {tone}")
        gpt_text = generate_text_with_system(system_prompt, user_prompt)

        if detailed:
            try:
                lunar = get_lunar_text()
                full_text = f"{gpt_text}\n\n🌙 <b>Лунный календарь:</b>\n{lunar}"
            except Exception as e:
                logger.warning(f"Не удалось добавить лунный календарь: {e}")
                full_text = gpt_text
        else:
            full_text = gpt_text

        # ✅ Сохраняем результат в кэш
        if sign not in cache:
            cache[sign] = {}
        cache[sign][cache_key] = {
            "date": date_str,
            "text": full_text,
            "tone": tone
        }

        save_cache(cache)
        return full_text

    except Exception as e:
        logger.exception("Ошибка при генерации гороскопа")
        return "⚠️ Не удалось сгенерировать гороскоп. Попробуйте позже."

def clear_old_cache():
    """Удаляет устаревшие гороскопы"""
    try:
        cache = load_cache()
        today = str(date.today())

        for sign in list(cache.keys()):
            for key in list(cache[sign].keys()):
                if cache[sign][key]["date"] < today:
                    del cache[sign][key]
            if not cache[sign]:
                del cache[sign]

        save_cache(cache)
        logger.info("✅ Старые кэшированные гороскопы удалены")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")
