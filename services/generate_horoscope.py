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

# Кэш для гороскопов (max 1000 записей, TTL зависит от day)
horoscope_cache = TTLCache(maxsize=1000, ttl=86400)  # Default TTL 24 часа

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
    - перефразируем через GPT
    - добавляем лунный и энергетический контекст
    """
    # Ключ для кэша
    cache_key = f"{sign.lower()}_{day}_{detailed}"

    # Установка TTL в зависимости от day
    if day == "week":
        horoscope_cache.ttl = 604800  # 7 дней
    else:
        horoscope_cache.ttl = 86400  # 24 часа

    # Проверка кэша
    if cache_key in horoscope_cache:
        logger.info(f"Гороскоп для {sign} ({day}, detailed={detailed}) взят из кэша.")
        return horoscope_cache[cache_key]

    try:
        # 1. Парсинг оригинала
        original_text_en = fetch_horoscope_from_site(sign, day)
        if original_text_en.startswith("⚠️") or original_text_en.startswith("🚫"):
            return original_text_en

        # 2. Перевод
        translated_text = translate_text(original_text_en, target_lang="ru")

        # 3. Дополнительный контекст — Луна и энергия дня
        target_date = date.today() if day == "today" else date.today() + timedelta(days=1)
        lunar_info = get_lunar_info(target_date)
        energy = get_day_energy_description()

        moon_context = f"Луна в {lunar_info['moon_sign']}, фаза: {lunar_info['phase_text']}, {lunar_info['moon_phase']}%"
        energy_context = f"Энергия дня: {energy or 'не определена'}"

        # 4. Генерация стиля и интро
        tone = random.choice(REPHRASE_TONES)
        intro = random.choice(START_INTROS)

        # 5. Формируем promt
        system_prompt = (
            "Ты создаешь персональные гороскопы на русском языке. "
            "Пиши по-настоящему: искренне, без клише, без эзотерики. "
            "Текст должен быть интересным, человечным и легко воспринимаемым."
        )

        user_prompt = f"""
Вот перевод гороскопа:

\"\"\"{translated_text}\"\"\"

Перепиши его в стиле — {tone}.
Избегай штампов и банальностей. Пиши по-человечески, как будто обращаешься к одному человеку.
Учитывай этот контекст дня:

- {moon_context}
- {energy_context}
"""

        # 6. Генерация финального текста с ограничением temperature [0.9, 1.0]
        temperature = random.uniform(0.9, 1.0)  # Ограничено до 1.0, чтобы избежать ошибки 400 в Yandex GPT
        logger.info(f"Генерация GPT с temperature={temperature:.2f}")

        try:
            gpt_response = generate_text_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt.strip(),
                temperature=temperature,  # Уже ограничено
                max_tokens=1000 if detailed else 500  # Контроль длины в зависимости от detailed
            )
            if not gpt_response:  # Если GPT вернул пустую строку (fallback)
                raise ValueError("GPT вернул пустой ответ")
            final_text = f"{intro}\n\n{gpt_response.strip()}"
        except Exception as e:
            logger.warning(f"GPT недоступен. Используем перевод. {e}")
            final_text = f"{intro}\n\n{translated_text.strip()}"

        # Кэшируем результат
        horoscope_cache[cache_key] = final_text
        logger.info(f"Гороскоп для {sign} ({day}, detailed={detailed}) сгенерирован и закеширован.")

        return final_text

    except Exception as e:
        logger.exception("Ошибка при генерации гороскопа")
        return "⚠️ Не удалось сгенерировать гороскоп. Попробуйте позже."
