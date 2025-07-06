from datetime import date, timedelta
from services.astro_data import get_lunar_info            # создадим ниже
from services.astroseek_scraper import get_day_energy_description  # тоже создадим
from services.yandex_gpt import generate_text_with_system         # уже есть

def generate_hybrid_horoscope(sign: str, day: str = "today", detailed: bool = False):
    target_date = date.today() if day == "today" else date.today() + timedelta(days=1)
    sign = sign.capitalize()

    lunar_info = get_lunar_info(target_date)
    energy = get_day_energy_description()

    label = "сегодня" if day == "today" else "завтра"

    lunar_part = (
        f"🌙 <b>Луна в знаке:</b> {lunar_info['moon_sign']} "
        f"({lunar_info['phase_text']}, фаза: {lunar_info['moon_phase']}%)\n"
    )

    if detailed:
        user_prompt = f"""
Составь подробный астрологический гороскоп для знака {sign} на {label}.

Луна находится в знаке {lunar_info['moon_sign']} ({lunar_info['phase_text']}, {lunar_info['moon_phase']}%).  
Энергия дня: {energy or 'не определена'}

Структура:
1. Общая энергия дня
2. Отношения
3. Работа и финансы
4. Эмоции и здоровье
5. Совет

Стиль - заботливый, в духе ASTROSTYLE, без штампов и пустых фраз.
        """
    else:
        user_prompt = f"""
Напиши краткий гороскоп для знака {sign} на {label}, с учётом фазы Луны ({lunar_info['phase_text']}) 
и общей астрологической атмосферы.

Энергия дня: {energy or 'не определена'}

Пиши коротко, без банальностей, но с вдохновением. Стиль ближе к ASTROSTYLE.
        """

    system_prompt = "Ты опытный астролог. Пиши красиво, человечно и мудро, в духе ASTROSTYLE. Избегай банальных формулировок."

    result = generate_text_with_system(system_prompt, user_prompt.strip())
    return f"{lunar_part}\n{result}"
