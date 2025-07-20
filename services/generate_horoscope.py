import random
from datetime import date, timedelta
import logging
import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache  # Для кэширования с TTL

from services.yandex_translate import translate_text
from services.yandex_gpt import generate_text_with_system
from services.astro_data import get_lunar_info
from services.astroseek_scraper import get_day_energy_description

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Кэши для гороскопов с разными TTL (max 1000 записей каждый)
daily_cache = TTLCache(maxsize=1000, ttl=86400)  # 24 часа для today/tomorrow
weekly_cache = TTLCache(maxsize=1000, ttl=604800)  # 7 дней для week

# Соответствие имени знака и id на сайте
SIGN_MAP = {
    'aries': 1, 'taurus': 2, 'gemini': 3, 'cancer': 4,
    'leo': 5, 'virgo': 6, 'libra': 7, 'scorpio': 8,
    'sagittarius': 9, 'capricorn': 10, 'aquarius': 11, 'pisces': 12
}

# Стилевые варианты перефразировки
REPHRASE_TONES = [
    "по-дружески и с поддержкой, без пафоса",
    "анализируя, как хороший коуч или психолог",
    "человечно, с теплотой и вниманием",
    "с лёгким философским тоном и образами",
    "в спокойном и уверенном стиле, как зрелый наставник"
]

# Варианты вступлений
START_INTROS = [
    "🔮 Сегодня важно:",
    "🌌 Главные сигналы от звёзд:",
    "💫 Общий вектор для дня:",
    "🪐 Атмосфера и путь:",
    "✨ Небо рекомендует:"
]


def fetch_horoscope_from_site(sign: str, day: str = "today") -> str:
    """Парсинг текста гороскопа с сайта horoscope.com"""
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


def generate_horoscope(sign: str, day: str = "today", detailed: bool = False) -> str:
    """
    Финальная генерация гороскопа с кэшированием:
    - парсим гороскоп
    - переводим
    - 
