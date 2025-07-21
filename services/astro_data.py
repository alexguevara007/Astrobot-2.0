import ephem
from datetime import date
import pytz

def get_lunar_info(target_date=None, lang: str = 'ru'):
    if target_date is None:
        target_date = date.today()

    date_str = target_date.strftime("%Y/%m/%d")
    moon = ephem.Moon(date_str)
    moon.compute(date_str)

    phase = moon.phase
    phase_pct = round(phase, 1)

    phases = {
        'ru': {
            'new': "Новолуние",
            'waxing': "Растущая Луна",
            'full': "Полнолуние",
            'waning': "Убывающая Луна"
        },
        'en': {
            'new': "New Moon",
            'waxing': "Waxing Moon",
            'full': "Full Moon",
            'waning': "Waning Moon"
        }
    }

    if phase < 1:
        phase_text = phases[lang]['new']
    elif phase > 99:
        phase_text = phases[lang]['full']
    elif phase < 50:
        phase_text = phases[lang]['waxing']
    else:
        phase_text = phases[lang]['waning']

    sign_eng = ephem.constellation(moon)[1]
    signs = {
        'ru': {
            'Aries': '♈️ Овен', 'Taurus': '♉️ Телец', 'Gemini': '♊️ Близнецы', 'Cancer': '♋️ Рак',
            'Leo': '♌️ Лев', 'Virgo': '♍️ Дева', 'Libra': '♎️ Весы', 'Scorpius': '♏️ Скорпион',
            'Sagittarius': '♐️ Стрелец', 'Capricornus': '♑️ Козерог', 'Aquarius': '♒️ Водолей', 'Pisces': '♓️ Рыбы'
        },
        'en': {
            'Aries': '♈️ Aries', 'Taurus': '♉️ Taurus', 'Gemini': '♊️ Gemini', 'Cancer': '♋️ Cancer',
            'Leo': '♌️ Leo', 'Virgo': '♍️ Virgo', 'Libra': '♎️ Libra', 'Scorpius': '♏️ Scorpio',
            'Sagittarius': '♐️ Sagittarius', 'Capricornus': '♑️ Capricorn', 'Aquarius': '♒️ Aquarius', 'Pisces': '♓️ Pisces'
        }
    }

    return {
        "moon_phase": phase_pct,
        "moon_sign": signs.get(lang, signs['ru']).get(sign_eng, sign_eng),
        "phase_text": phase_text
    }
