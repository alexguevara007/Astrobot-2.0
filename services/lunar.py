from datetime import datetime
import ephem
from math import floor
import pytz

def get_moon_day() -> int:
    """Получает текущий лунный день"""
    # Используем московское время
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)
    
    # Создаем объект Observer для расчета с учетом локации (примерный центр России)
    obs = ephem.Observer()
    obs.lat = '55.7522'  # Широта Москвы
    obs.long = '37.6156'  # Долгота Москвы
    obs.date = now
    
    # Получаем время предыдущего новолуния
    previous_new_moon = ephem.previous_new_moon(now.strftime('%Y/%m/%d'))
    
    # Вычисляем количество дней, прошедших с новолуния
    moon_day = int(now.date().strftime('%d')) - int(previous_new_moon.datetime().strftime('%d'))
    if moon_day <= 0:
        moon_day += 30
    
    return moon_day

def get_moon_phase() -> float:
    """Получает текущую фазу луны (0-1)"""
    moon = ephem.Moon()
    # Используем московское время
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)
    moon.compute(now)
    return moon.phase / 100.0

def get_moon_phase_name(phase: float) -> str:
    """Получает название фазы луны"""
    if phase < 0.05:
        return "🌑 Новолуние"
    elif phase < 0.25:
        return "🌒 Растущая луна"
    elif phase < 0.45:
        return "🌓 Первая четверть"
    elif phase < 0.55:
        return "🌕 Полнолуние"
    elif phase < 0.75:
        return "🌗 Последняя четверть"
    elif phase < 0.95:
        return "🌘 Убывающая луна"
    else:
        return "🌑 Новолуние"

def get_moon_sign() -> str:
    """Получает знак зодиака, в котором находится луна"""
    moon = ephem.Moon()
    # Используем московское время
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)
    moon.compute(now)
    
    # Получаем эклиптическую долготу
    ecl_long = float(moon.hlong) * 180 / ephem.pi
    
    # Определяем знак зодиака
    zodiac_signs = [
        "♈️ Овен", "♉️ Телец", "♊️ Близнецы", "♋️ Рак",
        "♌️ Лев", "♍️ Дева", "♎️ Весы", "♏️ Скорпион",
        "♐️ Стрелец", "♑️ Козерог", "♒️ Водолей", "♓️ Рыбы"
    ]
    
    sign_index = int(ecl_long / 30)
    return zodiac_signs[sign_index % 12]

def get_lunar_recommendations(phase_name: str) -> str:
    """Получает рекомендации в зависимости от фазы луны"""
    recommendations = {
        "🌑 Новолуние": (
            "• Идеальное время для новых начинаний\n"
            "• Составляйте планы и ставьте цели\n"
            "• Хорошо начинать диету или новые привычки"
        ),
        "🌒 Растущая луна": (
            "• Благоприятное время для роста и развития\n"
            "• Начинайте новые проекты\n"
            "• Хорошо для обучения и инвестиций"
        ),
        "🌓 Первая четверть": (
            "• Время активных действий\n"
            "• Преодолевайте препятствия\n"
            "• Хорошо для важных решений"
        ),
        "🌕 Полнолуние": (
            "• Пик энергии и эмоций\n"
            "• Завершайте важные дела\n"
            "• Будьте осторожны и внимательны"
        ),
        "🌗 Последняя четверть": (
            "• Время для анализа и подведения итогов\n"
            "• Хорошо для планирования\n"
            "• Избегайте важных начинаний"
        ),
        "🌘 Убывающая луна": (
            "• Завершайте проекты\n"
            "• Хорошо для очищения и отдыха\n"
            "• Избавляйтесь от ненужного"
        )
    }
    return recommendations.get(phase_name, "Наблюдайте за своим состоянием.")

def get_lunar_text() -> str:
    """Формирует текст о текущем состоянии луны"""
    try:
        phase = get_moon_phase()
        phase_name = get_moon_phase_name(phase)
        moon_day = get_moon_day()
        moon_sign = get_moon_sign()
        recommendations = get_lunar_recommendations(phase_name)
        
        text = (
            f"*Фаза луны:* {phase_name}\n"
            f"*Лунный день:* {moon_day}\n"
            f"*Луна в знаке:* {moon_sign}\n\n"
            f"*Рекомендации:*\n{recommendations}"
        )
        
        return text
    except Exception as e:
        return f"Ошибка при получении лунных данных: {str(e)}"