from datetime import date, timedelta
import random
from services.astro_data import get_lunar_info
from services.astroseek_scraper import get_day_energy_description
from services.yandex_gpt import generate_text_with_system

def generate_hybrid_horoscope(sign: str, day: str = "today", detailed: bool = False) -> str:
    """
    Генерация гибридного гороскопа на основе реальных астрологических данных
    и генерации текста через YandexGPT, со стилем в духе ASTROSTYLE.
    """

    # Получаем дату и читаем контекст
    target_date = date.today() if day == "today" else date.today() + timedelta(days=1)
    sign = sign.capitalize()

    lunar_info = get_lunar_info(target_date)
    energy = get_day_energy_description()
    label = "сегодня" if day == "today" else "завтра"

    # Рандомные стильные заголовки перед гороскопом
    start_intro_options = [
        "🌟 Космические подсказки на день:",
        "🪐 Астрология подсказывает:",
        "🎯 День с характером — вот он:",
        "💫 Послание звёзд:",
        "🌕 Предчувствие дня:",
        "✨ Не просто день — а момент:"
    ]
    intro = random.choice(start_intro_options)

    # ---------- ПРОМПТ: КРАТКИЙ ----------
    if not detailed:
        user_prompt = f"""
Ты — мудрый и человечный астролог. Напиши краткий, но сильный гороскоп на {label} для знака {sign}.

Контекст, на основе которого следует строить настроение и советы:
- Луна: {lunar_info['moon_sign']}, фаза: {lunar_info['phase_text']}, {lunar_info['moon_phase']}%
- Энергия дня: {energy or 'неизвестна'}

❗️Не описывай Луну напрямую. Используй её как фон — для атмосферы, эмоционального вектора, окраса.

Сохраняй стиль ASTROSTYLE: мудро, живо, современно, без эзотерики. Не используй клише.

Структура:
1. Главный вектор дня (эмоциональный и жизненный)
2. Личный вызов и возможность
3. Полезный и прикладной совет
"""
    # ---------- ПРОМПТ: ПОДРОБНЫЙ ----------
    else:
        user_prompt = f"""
Ты — астролог с опытом и ясным языком. Напиши стильный и содержательный подробный гороскоп на {label} для знака зодиака {sign}.

Контекст:
- Луна в знаке: {lunar_info['moon_sign']}
- Фаза Луны: {lunar_info['phase_text']} ({lunar_info['moon_phase']}%)
- Энергия дня: {energy or 'не указана'}

Используй эти данные как эмоциональный и смысловой фон, но не называй их напрямую. Вдохновляйся, а не цитируй.

Структура:
1. Тема и настрой дня (сфера, ощущение)
2. Отношения и личная жизнь
3. Работа, бытовое, цели
4. Подводный камень дня (что может сбивать)
5. Сила дня — что работает в плюс
6. Конечный вывод — что важно не упустить

Без клише, без эзотерики. Сохрани теплую и близкую подачу.
"""

    # ---------- SYSTEM PROMPT (авторский стиль) ----------
    system_prompt = """Ты пишешь гороскопы в стиле ASTROSTYLE: с чувством, мудро, современно.
Без банальностей, без приукрашиваний. Стиль — искренний, рассудительный, вдохновляющий и конкретный.
Ты не учишь — ты предлагаешь. Не прогнозируешь, а подсказываешь человеку, на что опереться."""

    # ---------- Генерация текста через GPT ----------
    gpt_response = generate_text_with_system(system_prompt, user_prompt.strip())

    final_text = f"{intro}\n\n{gpt_response.strip()}"
    return final_text
