import ephem
import logging
import json
import os
from datetime import datetime
import pytz
import asyncio  # Для async

from services.locales import get_text  # Импорт для переводов

logger = logging.getLogger(__name__)

# Путь к кэшу (из твоей структуры)
LUNAR_CACHE_FILE = "cache/lunar_cache.json"
CACHE_TTL = 3600  # 1 час в секундах

# Словари для фаз (по языкам)
PHASE_MAP = {
    'ru': {
        (0, 0.05): ("Новолуние", "🌑"),
        (0.05, 0.25): ("Растущий месяц", "🌒"),
        (0.25, 0.35): ("Первая четверть", "🌓"),
        (0.35, 0.45): ("Растущая луна", "🌔"),
        (0.45, 0.55): ("Полнолуние", "🌕"),
        (0.55, 0.65): ("Убывающая луна", "🌖"),
        (0.65, 0.75): ("Последняя четверть", "🌗"),
        (0.75, 1.0): ("Убывающий месяц", "🌘"),
        (0.95, 1.0): ("Новолуние", "🌑"),  # Для phase >0.95
    },
    'en': {
        (0, 0.05): ("New Moon", "🌑"),
        (0.05, 0.25): ("Waxing Crescent", "🌒"),
        (0.25, 0.35): ("First Quarter", "🌓"),
        (0.35, 0.45): ("Waxing Gibbous", "🌔"),
        (0.45, 0.55): ("Full Moon", "🌕"),
        (0.55, 0.65): ("Waning Gibbous", "🌖"),
        (0.65, 0.75): ("Last Quarter", "🌗"),
        (0.75, 1.0): ("Waning Crescent", "🌘"),
        (0.95, 1.0): ("New Moon", "🌑"),
    }
}

# Словари для знаков зодиака (по языкам)
ZODIAC_MAP = {
    'ru': {
        'Aries': '♈️ Овен',
        'Taurus': '♉️ Телец',
        'Gemini': '♊️ Близнецы',
        'Cancer': '♋️ Рак',
        'Leo': '♌️ Лев',
        'Virgo': '♍️ Дева',
        'Libra': '♎️ Весы',
        'Scorpius': '♏️ Скорпион',
        'Sagittarius': '♐️ Стрелец',
        'Capricornus': '♑️ Козерог',
        'Aquarius': '♒️ Водолей',
        'Pisces': '♓️ Рыбы'
    },
    'en': {
        'Aries': '♈️ Aries',
        'Taurus': '♉️ Taurus',
        'Gemini': '♊️ Gemini',
        'Cancer': '♋️ Cancer',
        'Leo': '♌️ Leo',
        'Virgo': '♍️ Virgo',
        'Libra': '♎️ Libra',
        'Scorpius': '♏️ Scorpio',
        'Sagittarius': '♐️ Sagittarius',
        'Capricornus': '♑️ Capricorn',
        'Aquarius': '♒️ Aquarius',
        'Pisces': '♓️ Pisces'
    }
}

def load_cache() -> dict:
    """Загрузка кэша из файла"""
    if os.path.exists(LUNAR_CACHE_FILE):
        with open(LUNAR_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(data: dict):
    """Сохранение кэша в файл"""
    os.makedirs(os.path.dirname(LUNAR_CACHE_FILE), exist_ok=True)
    with open(LUNAR_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def get_lunar_text(lang: str = 'ru', timezone: str = 'Europe/Moscow') -> str:
    """Получение информации о фазе луны (async, с кэшем и многоязычностью)"""
    cache = load_cache()
    cache_key = f"{lang}_{timezone}"
    now_timestamp = datetime.now().timestamp()

    # Проверяем кэш
    if cache_key in cache and (now_timestamp - cache.get(cache_key + '_timestamp', 0)) < CACHE_TTL:
        logger.info(f"📂 Lunar data loaded from cache for {lang}")
        return cache[cache_key]

    try:
        # Вычисляем данные
        moon = ephem.Moon()
        now = ephem.now()
        moon.compute(now)
        phase = moon.phase / 100.0

        # Определяем фазу и эмодзи (из словаря по lang)
        phase_map = PHASE_MAP.get(lang, PHASE_MAP['ru'])  # Fallback на ru
        phase_name, emoji = next((name, em) for (low, high), (name, em) in phase_map.items() if low <= phase < high)

        # Рост/убывание
        is_growing = phase < 0.5
        growth = get_text('moon_growing' if is_growing else 'moon_waning', lang)

        # Знак зодиака (из словаря по lang)
        moon_sign = ephem.constellation(moon)[1]
        zodiac_map = ZODIAC_MAP.get(lang, ZODIAC_MAP['ru'])
        moon_zodiac = zodiac_map.get(moon_sign, moon_sign)

        # Расстояние
        distance = int(moon.earth_distance * 149597870.7)  # AU to km

        # Время в указанном TZ
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
        tz_short = tz.zone.split('/')[-1]  # e.g., 'Moscow'

        # Формируем текст через get_text
        text = get_text('lunar_calendar', lang).format(
            emoji=emoji,
            phase_name=phase_name,
            illumination=round(moon.phase, 1),
            moon_zodiac=moon_zodiac,
            growth=growth,
            distance=distance,
            time=current_time,
            tz=tz_short
        )

        # Сохраняем в кэш
        cache[cache_key] = text
        cache[cache_key + '_timestamp'] = now_timestamp
        save_cache(cache)
        logger.info(f"✅ Lunar data calculated and cached for {lang}")

        return text

    except Exception as e:
        logger.error(f"❌ Error getting lunar data: {e}", exc_info=True)
        return get_text('lunar_error', lang)

if __name__ == "__main__":
    async def test():
        print(await get_lunar_text(lang='ru'))
        print(await get_lunar_text(lang='en'))  # Тест на английском

    asyncio.run(test())
