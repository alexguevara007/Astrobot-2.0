import os
import json
import logging
import random
from datetime import date, timedelta
from services.lunar import get_lunar_text
from services.yandex_gpt import generate_text_with_system
from services.parsed_horoscope import parse_and_translate  # 🆕

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
    return random.choices(
        ["positive", "neutral", "negative"],
        weights=[0.5, 0.25, 0.25],
        k=1
    )[0]

def generate_horoscope(
    sign: str,
    day: str = "today",
    detailed: bool = False,
    hybrid: bool = True,
    use_scraped: bool = False  # ✅ новый параметр
):
    try:
        today = date.today()
        target = today if day == "today" else today + timedelta(days=1)
        date_str = str(target)
        sign = sign.lower()

        cache = load_cache()
        cache_key = f"{'detailed' if detailed else 'brief'}_{sign}_{day}"
        
        if sign in cache and cache_key in cache[sign] and cache[sign][cache_key]["date"] == date_str:
            logger.info(f"Из кэша: {sign} на {day}")
            return cache[sign][cache_key]["text"]

        # ✅ Режим: парсинг внешнего текста + перевод
        if use_scraped:
            logger.info(f"📰 Используется парсинг для {sign} на {day}")
            result_text = parse_and_translate(sign, day)
            if sign not in cache:
                cache[sign] = {}
            cache[sign][cache_key] = {
                "date": date_str,
                "text": result_text,
                "tone": "parsed"
            }
            save_cache(cache)
            return result_text

        # ✅ Режим: гибрид (GPT + лунная инфа)
        if hybrid:
            from services.gpt_horoscope_hybrid import generate_hybrid_horoscope
            logger.info(f"✨ Генерация гибридного гороскопа: sign={sign}, day={day}, detailed={detailed}")
            result_text = generate_hybrid_horoscope(sign, day, detailed)

            if sign not in cache:
                cache[sign] = {}
            cache[sign][cache_key] = {
                "date": date_str,
                "text": result_text,
                "tone": "hybrid"
            }
            save_cache(cache)
            return result_text

        # ℹ️ Классическая генерация через GPT
        tone = pick_tone()
        tone_instruction = {
            "positive": "в целом благоприятный, вдохновляющий, но реалистичный",
            "neutral": "сбалансированный, спокойный, с акцентом на самонаблюдение",
            "negative": "сдержанный, с конструктивным предупреждением, не драматизируя"
        }

        system_prompt = f"""Ты — опытный астролог.
Твой стиль — {tone_instruction[tone]}.
Пиши честно, без шаблонов, по-человечески."""

        label = 'сегодня' if day == 'today' else 'завтра'

        # 🌐 Пользовательский prompt
        if detailed:
            user_prompt = f"""Составь подробный гороскоп на {label} для знака {sign.title()}.

Структура:
1. Общая энергия дня
2. Отношения
3. Работа и финансы
4. Эмоциональное состояние
5. Совет
"""
        else:
            user_prompt = f"""Краткий гороскоп на {label} для {sign.title()}:
- Ощущения дня
- Личный совет
- Когда принимать решения

Без клише, по-живому, с уважением.
"""

        logger.info(f"🧠 Классическая генерация: {sign}, день: {day}, тон: {tone}")
        gpt_text = generate_text_with_system(system_prompt, user_prompt)

        # ➕ Добавление лунных данных
        if detailed:
            try:
                lunar = get_lunar_text()
                full_text = f"{gpt_text}\n\n🌙 <b>Лунный календарь:</b>\n{lunar}"
            except Exception as e:
                logger.warning(f"Не удалось добавить луну: {e}")
                full_text = gpt_text
        else:
            full_text = gpt_text

        # 💾 Сохраняем результат в кэш
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
        logger.exception(f"Ошибка при генерации гороскопа: {e}")
        return "⚠️ Не удалось сгенерировать гороскоп. Попробуйте позже."

def clear_old_cache():
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
        logger.info("🧹 Старый кэш очищен.")
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")
