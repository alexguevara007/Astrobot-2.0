import os
import json
from datetime import date
import logging

logger = logging.getLogger(__name__)

# 📁 Путь к кэшу
CACHE_FILE = "cache/horoscope_cache.json"

# Создать папку /cache, если её нет
os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)


def load_cache() -> dict:
    """Загрузить текущий кэш из файла"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки кэша: {e}")
    return {}


def save_cache(data: dict):
    """Сохранить кэш в файл"""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("✅ Кэш успешно сохранён")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения кэша: {e}")


def save_horoscope_to_cache(sign: str, text: str):
    """
    Сохранить гороскоп на сегодня в кэш
    :param sign: знак зодиака, на английском (например, "aries")
    :param text: текст гороскопа
    """
    try:
        today = str(date.today())
        sign_lower = sign.lower()
        key = f"brief_{sign_lower}_today"

        cache = load_cache()
        if sign_lower not in cache:
            cache[sign_lower] = {}

        cache[sign_lower][key] = {
            "date": today,
            "text": text
        }

        save_cache(cache)
        logger.info(f"💾 Гороскоп для {sign_lower} на {today} сохранён в кэш")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в кэш: {e}")


def clear_old_cache():
    """
    Очистить устаревшие записи в кэше (оставить только на текущую дату)
    """
    try:
        today = str(date.today())
        cache = load_cache()
        cleaned = {}

        for sign, entries in cache.items():
            fresh_entries = {
                key: value for key, value in entries.items()
                if value.get("date") == today
            }

            if fresh_entries:
                cleaned[sign] = fresh_entries

        save_cache(cleaned)
        logger.info("🧹 Старый кэш успешно очищен")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кэша: {e}")
