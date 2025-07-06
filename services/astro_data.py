import ephem
from datetime import date
import pytz

def get_lunar_info(target_date=None):
    if target_date is None:
        target_date = date.today()

    date_str = target_date.strftime("%Y/%m/%d")
    moon = ephem.Moon(date_str)
    moon.compute(date_str)

    phase = moon.phase
    phase_pct = round(phase, 1)

    if phase < 1 or phase > 99:
        phase_text = "Новолуние" if phase < 1 else "Полнолуние"
    elif phase < 50:
        phase_text = "Растущая Луна"
    else:
        phase_text = "Убывающая Луна"

    sign_eng = ephem.constellation(moon)[1]
    signs = {
        'Aries': '♈️ Овен', 'Taurus': '♉️ Телец', 'Gemini': '♊️ Близнецы', 'Cancer': '♋️ Рак',
        'Leo': '♌️ Лев', 'Virgo': '♍️ Дева', 'Libra': '♎️ Весы', 'Scorpius': '♏️ Скорпион',
        'Sagittarius': '♐️ Стрелец', 'Capricornus': '♑️ Козерог', 'Aquarius': '♒️ Водолей', 'Pisces': '♓️ Рыбы'
    }

    return {
        "moon_phase": phase_pct,
        "moon_sign": signs.get(sign_eng, sign_eng),
        "phase_text": phase_text
    }
