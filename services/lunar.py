import ephem
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def get_lunar_text() -> str:
    """Получение информации о фазе луны"""
    try:
        # Создаем объект луны
        moon = ephem.Moon()
        
        # Текущее время
        now = ephem.now()
        
        # Вычисляем фазу луны
        moon.compute(now)
        
        # Получаем фазу как число от 0 до 1
        phase = moon.phase / 100.0
        
        # Определяем фазу луны и эмодзи
        if 0 <= phase < 0.05 or phase > 0.95:
            phase_name = "Новолуние"
            emoji = "🌑"
        elif 0.05 <= phase < 0.25:
            phase_name = "Растущий месяц"
            emoji = "🌒"
        elif 0.25 <= phase < 0.35:
            phase_name = "Первая четверть"
            emoji = "🌓"
        elif 0.35 <= phase < 0.45:
            phase_name = "Растущая луна"
            emoji = "🌔"
        elif 0.45 <= phase < 0.55:
            phase_name = "Полнолуние"
            emoji = "🌕"
        elif 0.55 <= phase < 0.65:
            phase_name = "Убывающая луна"
            emoji = "🌖"
        elif 0.65 <= phase < 0.75:
            phase_name = "Последняя четверть"
            emoji = "🌗"
        else:
            phase_name = "Убывающий месяц"
            emoji = "🌘"

        # Определяем растущая/убывающая
        is_growing = phase < 0.5
        
        # Вычисляем знак зодиака
        moon_sign = ephem.constellation(moon)[1]
        zodiac_map = {
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
        }
        moon_zodiac = zodiac_map.get(moon_sign, moon_sign)
        
        # Текущее время МСК
        moscow_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y %H:%M")
        
        # Формируем ответ
        return (
            f"{emoji} Лунный календарь\n\n"
            f"Фаза: {phase_name}\n"
            f"Освещенность: {moon.phase:.1f}%\n"
            f"Луна в знаке: {moon_zodiac}\n"
            f"Луна {'растущая' if is_growing else 'убывающая'}\n"
            f"Расстояние: {int(moon.earth_distance * 149597870.7):,} км\n\n"
            f"Время: {moscow_time} (МСК)"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении данных о луне: {e}")
        return "⚠️ Извините, не удалось получить данные о луне"

if __name__ == "__main__":
    print(get_lunar_text())
