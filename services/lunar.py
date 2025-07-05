import logging
from datetime import datetime
import pytz
from skyfield.api import load, Topos
from skyfield.almanac import moon_phase
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LunarCalendar:
    def __init__(self):
        self.ts = load.timescale()
        self.eph = load('de421.bsp')
        self.earth = self.eph['earth']
        self.moon = self.eph['moon']
        self.sun = self.eph['sun']

    def get_moon_info(self) -> Dict[str, Any]:
        """Получение детальной информации о луне"""
        try:
            now = self.ts.now()
            
            # Фаза луны (0-1)
            phase = moon_phase(self.eph, now)
            
            # Определение фазы
            phase_info = self._get_phase_name(phase)
            
            # Расчет расстояния до луны
            moon_distance = self._calculate_moon_distance(now)
            
            # Определение знака зодиака
            zodiac_sign = self._get_moon_zodiac(now)
            
            return {
                "phase": phase_info["name"],
                "emoji": phase_info["emoji"],
                "illumination": phase * 100,
                "distance": moon_distance,
                "zodiac": zodiac_sign,
                "growing": phase < 0.5,
                "timestamp": datetime.now(pytz.UTC)
            }
        except Exception as e:
            logger.error(f"Ошибка при получении данных о луне: {e}")
            raise

    def _get_phase_name(self, phase: float) -> Dict[str, str]:
        """Определение названия и эмодзи фазы луны"""
        if 0 <= phase < 0.05 or phase > 0.95:
            return {"name": "Новолуние", "emoji": "🌑"}
        elif 0.05 <= phase < 0.25:
            return {"name": "Растущий месяц", "emoji": "🌒"}
        elif 0.25 <= phase < 0.35:
            return {"name": "Первая четверть", "emoji": "🌓"}
        elif 0.35 <= phase < 0.45:
            return {"name": "Растущая луна", "emoji": "🌔"}
        elif 0.45 <= phase < 0.55:
            return {"name": "Полнолуние", "emoji": "🌕"}
        elif 0.55 <= phase < 0.65:
            return {"name": "Убывающая луна", "emoji": "🌖"}
        elif 0.65 <= phase < 0.75:
            return {"name": "Последняя четверть", "emoji": "🌗"}
        else:
            return {"name": "Убывающий месяц", "emoji": "🌘"}

    def _calculate_moon_distance(self, time) -> float:
        """Расчет расстояния до луны в километрах"""
        moon_pos = self.moon.at(time)
        earth_pos = self.earth.at(time)
        distance = moon_pos - earth_pos
        return distance.km

    def _get_moon_zodiac(self, time) -> str:
        """Определение знака зодиака луны"""
        moon_pos = self.moon.at(time)
        ecliptic = moon_pos.ecliptic_latlon()
        lon = ecliptic[1].degrees
        
        zodiac_signs = [
            "♈️ Овен", "♉️ Телец", "♊️ Близнецы", "♋️ Рак",
            "♌️ Лев", "♍️ Дева", "♎️ Весы", "♏️ Скорпион",
            "♐️ Стрелец", "♑️ Козерог", "♒️ Водолей", "♓️ Рыбы"
        ]
        
        sign_index = int(lon / 30) % 12
        return zodiac_signs[sign_index]

def get_lunar_text() -> str:
    """Получение текстовой информации о луне"""
    try:
        calendar = LunarCalendar()
        moon_info = calendar.get_moon_info()
        
        moscow_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y %H:%M")
        
        return (
            f"{moon_info['emoji']} Лунный календарь\n\n"
            f"Фаза: {moon_info['phase']}\n"
            f"Освещенность: {moon_info['illumination']:.1f}%\n"
            f"Луна в знаке: {moon_info['zodiac']}\n"
            f"Луна {'растущая' if moon_info['growing'] else 'убывающая'}\n"
            f"Расстояние: {moon_info['distance']:,.0f} км\n\n"
            f"Время: {moscow_time} (МСК)"
        )

    except Exception as e:
        logger.error(f"Ошибка при формировании лунного календаря: {e}")
        return "⚠️ Извините, не удалось получить данные о луне"

if __name__ == "__main__":
    print(get_lunar_text())
