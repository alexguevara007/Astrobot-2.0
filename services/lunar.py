import ephem
import logging
import json
import os
from datetime import datetime
import pytz
import asyncio

from services.locales import get_text

logger = logging.getLogger(__name__)

LUNAR_CACHE_FILE = "cache/lunar_cache.json"
CACHE_TTL = 3600  # 1 час

PHASE_MAP = {
    'ru': {
        (0, 0.05): ("Новолуние", "🌑"),
        (0.05, 0.25): ("Растущий месяц", "🌒"),
        (0.25, 0.35): ("Первая четверть", "🌓"),
        (0.35, 0.45): ("Растущая луна", "🌔"),
        (0.45, 0.55): ("Полнолуние", "🌕"),
        (0.55, 0.65): ("Убывающая луна", "🌖"),
        (0.65, 0.75): ("Последняя четверть", "🌗"),
        (0.75, 0.95): ("Убывающий месяц", "🌘"),
        (0.95, 1.0): ("Новолуние", "🌑"),
    },
    'en': {
        (0, 0.05): ("New Moon", "🌑"),
        (0.05, 0.25): ("Waxing Crescent", "🌒"),
        (0.25, 0.35): ("First Quarter", "🌓"),
        (0.35, 0.45): ("Waxing Gibbous", "🌔"),
        (0.45, 0.55): ("Full Moon", "🌕"),
        (0.55, 0.65): ("Waning Gibbous", "🌖"),
        (0.65, 0.75): ("Last Quarter", "🌗"),
        (0.75, 0.95): ("Waning Crescent", "🌘"),
        (0.95, 1.0): ("New Moon", "🌑"),
    }
}

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
    if os.path.exists(LUNAR_CACHE_FILE):
        with open(LUNAR_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(data: dict):
    os.makedirs(os.path.dirname(LUNAR_CACHE_FILE), exist_ok=True)
    with open(LUNAR_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def get_lunar_text(lang: str = 'ru', timezone: str = 'Europe/Moscow') -> str:
    cache = load_cache()
    cache_key = f"{lang}_{timezone}"
    now_ts = datetime.now().timestamp()

    if cache_key in cache and (now_ts - cache.get(f"{cache_key}_timestamp", 0)) < CACHE_TTL:
        logger.info(f"📂 Lunar data from cache: {lang}")
        return cache[cache_key]

    try:
        moon = ephem.Moon()
        moon.compute(ephem.now())
        phase = moon.phase / 100.0

        # Фаза луны
        phase_map = PHASE_MAP.get(lang, PHASE_MAP['ru'])
        phase_name, emoji = next(
            (name, emj) for (low, high), (name, emj) in phase_map.items()
            if low <= phase < high
        )

        is_growing = phase < 0.5
        growth = get_text('moon_growing' if is_growing else 'moon_waning', lang)

        # Знак зодиака
        moon_sign_key = ephem.constellation(moon)[1]
        moon_zodiac = ZODIAC_MAP.get(lang, ZODIAC_MAP['ru']).get(moon_sign_key, moon_sign_key)

        # Расстояние
        distance_km = int(moon.earth_distance * 149_597_870.7)

        # Время
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        formatted_time = now.strftime("%d.%m.%Y %H:%M")
        tz_label = tz.zone.split("/")[-1]

        # Формирование текста
        text = get_text('lunar_calendar', lang).format(
            emoji=emoji,
            phase_name=phase_name,
            illumination=round(moon.phase, 1),
            moon_zodiac=moon_zodiac,
            growth=growth,
            distance=distance_km,
            time=formatted_time,
            tz=tz_label
        )

        cache[cache_key] = text
        cache[f"{cache_key}_timestamp"] = now_ts
        save_cache(cache)

        logger.info(f"✅ Lunar data updated for lang={lang}")
        return text

    except Exception as e:
        logger.error(f"❌ Ошибка получения данных о луне: {e}", exc_info=True)
        return get_text('lunar_error', lang)


# 👇 Запуск для теста
if __name__ == "__main__":
    async def test():
        print(await get_lunar_text(lang='ru'))
        print(await get_lunar_text(lang='en'))

    asyncio.run(test())
