import os
import json
from datetime import date
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = "cache/horoscope_cache.json"

def load_cache() -> dict:
    """Загрузка всех данных кэша"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки кэша: {e}")
    return {}

def save_cache(data: dict):
    """Сохраняет данные в кэш-файл"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("✅ Кэш успешно сохранён")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения кэша: {e}")

def get_cache_key(sign: str, lang: str = 'ru') -> str:
    """Возвращает ключ кэша по знаку и языку"""
    return f"brief_{sign.lower()}_today_{lang}"

def save_horoscope_to_cache(sign: str, text: str, lang: str = 'ru'):
    """
    Сохраняет гороскоп на сегодня в кэш по знаку и языку
    """
    try:
        today = str(date.today())
        sign_lower = sign.lower()
        key = get_cache_key(sign, lang)

        # Загружаем и обновляем кэш
        cache = load_cache()
        if sign_lower not in cache:
            cache[sign_lower] = {}

        cache[sign_lower][key] = {
            "date": today,
            "text": text
        }

        save_cache(cache)
        logger.info(f"💾 Гороскоп для '{sign_lower}' ({lang}) на {today} сохранён в кэш.")

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в кэш: {e}")

def clear_old_cache():
    """
    Очищает данные, отличные от сегодняшней даты
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
        logger.info("🧹 Устаревшие записи кэша удалены.")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кэша: {e}")
