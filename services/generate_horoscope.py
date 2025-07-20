import random
from datetime import date, timedelta
import logging
import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache

from services.yandex_translate import translate_text
from services.yandex_gpt import generate_text_with_system
from services.astro_data import get_lunar_info
from services.astroseek_scraper import get_day_energy_description
from locales import get_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

daily_cache = TTLCache(maxsize=1000, ttl=86400)
weekly_cache = TTLCache(maxsize=1000, ttl=604800)

SIGN_MAP = {
    'aries': 1, 'taurus': 2, 'gemini': 3, 'cancer': 4,
    'leo': 5, 'virgo': 6, 'libra': 7, 'scorpio': 8,
    'sagittarius': 9, 'capricorn': 10, 'aquarius': 11, 'pisces': 12
}

def fetch_horoscope_from_site(sign: str, day: str = "today") -> str:
    sign_id = SIGN_MAP.get(sign.lower())
    if not sign_id:
        return "🚫 Неверный знак зодиака"

    url = f"https://www.horoscope.com/us/horoscopes/general/horoscope-general-daily-{day}.aspx?sign={sign_id}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        box = soup.find("div", class_="main-horoscope")
        p = box.find("p")
        text = p.get_text(strip=True)
        return text
    except Exception as e:
        logger.error(f"Ошибка парсинга гороскопа: {e}")
        return f"⚠️ Не удалось получить гороскоп: {e}"

def generate_horoscope(sign: str, day: str = "today", detailed: bool = False, lang: str = 'ru') -> str:
    if day == "week":
        cache = weekly_cache
    else:
        cache = daily_cache

    cache_key = f"{sign.lower()}_{day}_{detailed}_{lang}"

    if cache_key in cache:
        logger.info(f"Гороскоп для {sign} ({day}, detailed={detailed}, lang={lang}) взят из кэша.")
        return cache[cache_key]

    try:
        original_text_en = fetch_horoscope_from_site(sign, day)
        if original_text_en.startswith("⚠️") or original_text_en.startswith("🚫"):
            return original_text_en

        if lang == 'en':
            translated_text = original_text_en
        else:
            translated_text = translate_text(original_text_en, target_lang=lang)

        target_date = date.today() if day == "today" else date.today() + timedelta(days=1)
        lunar_info = get_lunar_info(target_date)
        energy = get_day_energy_description()

        moon_context = get_text('moon_context', lang, sign=lunar_info['moon_sign'], phase=lunar_info['phase_text'], percent=lunar_info['moon_phase'])
        energy_context = get_text('energy_context', lang, energy=energy or get_text('energy_undefined', lang))

        tone = random.choice(get_text('rephrase_tones', lang))  # Добавьте список в locales.py
        intro = random.choice(get_text('start_intros', lang))  # Добавьте список в locales.py

        system_prompt = get_text('system_prompt', lang)

        user_prompt = get_text('user_prompt_template', lang, translated=translated_text, tone=tone,
                               moon_context=moon_context, energy_context=energy_context)

        temperature = random.uniform(0.9, 1.0)
        logger.info(f"Генерация GPT с temperature={temperature:.2f}")

        try:
            gpt_response = generate_text_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt.strip(),
                temperature=temperature,
                max_tokens=1000 if detailed else 500
            )
            if not gpt_response:
                raise ValueError("GPT вернул пустой ответ")
            final_text = f"{intro}\n\n{gpt_response.strip()}"
        except Exception as e:
            logger.warning(f"GPT недоступен. Используем перевод. {e}")
            final_text = f"{intro}\n\n{translated_text.strip()}"

        cache[cache_key] = final_text
        logger.info(f"Гороскоп для {sign} ({day}, detailed={detailed}, lang={lang}) сгенерирован и закеширован.")

        return final_text

    except Exception as e:
        logger.exception("Ошибка при генерации гороскопа")
        return get_text('generation_error', lang)
