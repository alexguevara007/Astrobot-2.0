import os
import json
import logging
from datetime import date, timedelta
from services.lunar import get_lunar_text
from services.yandex_gpt import generate_text_with_system

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Путь к файлу кэша
CACHE_FILE = "cache/horoscope_cache.json"

# Создаем директорию cache, если её нет
os.makedirs("cache", exist_ok=True)

def load_cache():
    """Загружает кэш гороскопов"""
    try:
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(data):
    """Сохраняет кэш гороскопов"""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении кэша: {e}")

def clear_old_cache():
    """Очищает устаревшие записи из кэша"""
    try:
        cache = load_cache()
        today = str(date.today())
        
        for sign in list(cache.keys()):
            for key in list(cache[sign].keys()):
                if cache[sign][key]["date"] < today:
                    del cache[sign][key]
            if not cache[sign]:
                del cache[sign]
        
        save_cache(cache)
        logger.info("Очистка кэша завершена")
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")

def generate_horoscope(sign: str, day: str = "today", detailed: bool = False):
    """
    Генерирует гороскоп для указанного знака зодиака
    :param sign: Знак зодиака на английском
    :param day: День (today/tomorrow)
    :param detailed: Подробный или краткий формат
    :return: Текст гороскопа
    """
    try:
        today = date.today()
        target = today if day == "today" else today + timedelta(days=1)
        date_str = str(target)
        sign = sign.lower()

        # Проверяем кэш
        cache = load_cache()
        cache_key = f"{'detailed' if detailed else 'brief'}_{sign}_{day}"
        
        if sign in cache and cache_key in cache[sign] and cache[sign][cache_key]["date"] == date_str:
            logger.info(f"Возвращаем кэшированный гороскоп для {sign} на {date_str}")
            return cache[sign][cache_key]["text"]

        # Системный промпт для установки роли
        system_prompt = """Ты - профессиональный астролог с глубоким пониманием астрологии. 
        Твоя задача - составлять точные и полезные гороскопы, которые помогают людям 
        лучше понять свой день и принять правильные решения. Используй позитивный 
        и конструктивный тон, избегай негативных предсказаний."""

        # Выбор промпта в зависимости от формата
        if detailed:
            user_prompt = f"""Составь детальный гороскоп на {'сегодня' if day == 'today' else 'завтра'} 
            для знака зодиака {sign.capitalize()}.

            Включи следующие аспекты:
            1. 🌟 Общая атмосфера и энергетика дня
            2. ❤️ Личная жизнь и отношения
            3. 💼 Работа и карьера
            4. 🏥 Здоровье и самочувствие
            5. 💡 Практический совет
            6. 🎨 Благоприятные цвета
            7. ⏰ Лучшие часы для важных дел
            8. 💰 Финансовые перспективы
            9. 🎯 Творческий потенциал
            10. 👥 Взаимодействие с окружающими

            Используй эмодзи для каждого раздела."""
        else:
            user_prompt = f"""Составь краткий гороскоп на {'сегодня' if day == 'today' else 'завтра'} 
            для знака зодиака {sign.capitalize()}.

            Включи только самое важное в 3 коротких пункта:
            1. 🌟 Общий настрой дня (1-2 предложения)
            2. 💡 Главный совет дня (1 предложение)
            3. ⏰ Лучшее время для важных дел

            Текст должен быть кратким, но информативным."""

        # Генерируем гороскоп
        logger.info(f"Генерация гороскопа для {sign} на {date_str}")
        gpt_text = generate_text_with_system(system_prompt, user_prompt)
        
        # Добавляем лунный календарь для подробного гороскопа
        if detailed:
            try:
                lunar = get_lunar_text()
                full_text = f"{gpt_text}\n\n🌙 Лунный календарь:\n{lunar}"
            except Exception as e:
                logger.error(f"Ошибка при получении лунного календаря: {e}")
                full_text = gpt_text
        else:
            full_text = gpt_text

        # Сохраняем в кэш
        if sign not in cache:
            cache[sign] = {}
        cache[sign][cache_key] = {
            "date": date_str,
            "text": full_text
        }
        save_cache(cache)

        return full_text

    except Exception as e:
        logger.error(f"Ошибка при генерации гороскопа: {e}", exc_info=True)
        return "Извините, произошла ошибка при генерации гороскопа. Пожалуйста, попробуйте позже."
