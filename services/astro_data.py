import ephem
from datetime import date

def get_lunar_info(target_date=None, lang: str = 'ru'):
    """
    Возвращает фазу Луны (%), имя фазы и знак зодиака, в котором находится Луна.
    :param target_date: объект date, если None — берём текущую дату
    :param lang: 'ru' или 'en'
    :return: dict с полями: moon_phase, moon_sign, phase_text
    """
    if target_date is None:
        target_date = date.today()

    date_str = target_date.strftime("%Y/%m/%d")
    moon = ephem.Moon(date_str)
    moon.compute(date_str)

    phase = moon.phase
    phase_pct = round(phase, 1)

    # Карта фаз
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

    # Карта знаков зодиака
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

    # Безопасный доступ по языку
    phase_map = phases.get(lang, phases['ru'])
    sign_map = signs.get(lang, signs['ru'])

    if phase < 1:
        phase_text = phase_map['new']
    elif phase > 99:
        phase_text = phase_map['full']
    elif phase < 50:
        phase_text = phase_map['waxing']
    else:
        phase_text = phase_map['waning']

    sign_eng = ephem.constellation(moon)[1]
    moon_sign = sign_map.get(sign_eng, sign_eng)

    return {
        "moon_phase": phase_pct,
        "moon_sign": moon_sign,
        "phase_text": phase_text
    }
