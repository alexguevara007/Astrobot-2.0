import requests
from bs4 import BeautifulSoup
from services.yandex_translate import translate_text  # создадим
from services.yandex_gpt import generate_text_with_system  # можно не использовать

# Соответствие имени знака и номера на сайте (1 — Aries, 2 — Taurus ...)
SIGN_MAP = {
    'aries': 1, 'taurus': 2, 'gemini': 3, 'cancer': 4,
    'leo': 5, 'virgo': 6, 'libra': 7, 'scorpio': 8,
    'sagittarius': 9, 'capricorn': 10, 'aquarius': 11, 'pisces': 12
}

def fetch_horoscope_text(sign: str, day: str = "today") -> str:
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
        return f"⚠️ Не удалось получить гороскоп: {e}"

def parse_and_translate(sign: str, day: str = "today") -> str:
    original = fetch_horoscope_text(sign, day)
    if original.startswith("⚠️") or original.startswith("🚫"):
        return original

    # Перевод через Yandex Translate
    translated = translate_text(original, target_lang="ru")

    # Перефразирование через GPT (необязательно)
    prompt = f"""
Ты переводишь астрологический гороскоп с английского языка. Вот перевод:
\"\"\"{translated}\"\"\"

Теперь перефразируй его красиво и лаконично на русском языке, избегая клише.
Сделай стиль душевным, осознанным и нативным.
"""
    try:
        final_text = generate_text_with_system(prompt, "")
        return final_text.strip()
    except Exception:
        return translated  # если GPT недоступен — покажем перевод
