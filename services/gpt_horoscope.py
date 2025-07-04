import os
import json
from datetime import date, timedelta
from services.lunar import get_lunar_text
from services.yandex_gpt import generate_text_with_system

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
        print(f"Ошибка при сохранении кэша: {e}")

def generate_horoscope(sign: str, day: str = "today"):
    """
    Генерирует гороскоп для указанного знака зодиака
    :param sign: Знак зодиака
    :param day: День (today/tomorrow)
    :return: Текст гороскопа
    """
    from dotenv import load_dotenv
    load_dotenv()

    today = date.today()
    target = today if day == "today" else today + timedelta(days=1)
    date_str = str(target)
    sign = sign.lower()

    # Проверяем кэш
    cache = load_cache()
    if sign in cache and day in cache[sign] and cache[sign][day]["date"] == date_str:
        return cache[sign][day]["text"]

    # Системный промпт для установки роли
    system_prompt = """Ты - профессиональный астролог с глубоким пониманием астрологии. 
    Твоя задача - составлять точные и полезные гороскопы, которые помогают людям 
    лучше понять свой день и принять правильные решения. Используй позитивный 
    и конструктивный тон, избегай негативных предсказаний."""

    # Пользовательский промпт
    user_prompt = f"""Составь детальный гороскоп на {'сегодня' if day == 'today' else 'завтра'} 
    для знака зодиака {sign.capitalize()}.

    Включи следующие аспекты:
    1. Общая атмосфера и энергетика дня
    2. Личная жизнь и отношения
    3. Работа и карьера
    4. Здоровье и самочувствие
    5. Практический совет на день
    6. Благоприятные цвета
    7. Лучшие часы для важных дел

    Формат: структурированный текст с эмодзи для каждого раздела."""

    try:
        # Генерируем гороскоп
        gpt_text = generate_text_with_system(system_prompt, user_prompt)
        
        # Получаем лунный календарь
        try:
            lunar = get_lunar_text()
            full_text = f"{gpt_text}\n\n🌙 Лунный календарь:\n{lunar}"
        except Exception as e:
            print(f"Ошибка при получении лунного календаря: {e}")
            full_text = gpt_text

        # Сохраняем в кэш
        if sign not in cache:
            cache[sign] = {}
        cache[sign][day] = {"date": date_str, "text": full_text}
        save_cache(cache)

        return full_text

    except Exception as e:
        print(f"Ошибка при генерации гороскопа: {e}")
        return "Извините, произошла ошибка при генерации гороскопа. Пожалуйста, попробуйте позже."