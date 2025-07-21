# services/locales.py
import logging
import json  # Для опциональной загрузки из JSON

logger = logging.getLogger(__name__)

# Поддерживаемые языки
LANGUAGES = {
    'ru': 'Русский',
    'en': 'English'
    # Добавьте больше: 'es': 'Español' и т.д.
}

# Словарь переводов (можно загрузить из JSON ниже)
TRANSLATIONS = {
    'ru': {
        # Общие
        'welcome': 'Добро пожаловать! Я — твой астролог. Выберите язык: /language',
        'language_set': 'Язык изменён на {lang}!',
        'error': '⚠️ Ошибка. Попробуйте позже.',
        'back_to_menu': '« Назад в меню',

        # Horoscope-specific
        'zodiac_select': '🔮 Выберите знак зодиака:',
        'horoscope_loading': '{emoji} Генерация гороскопа для {sign}\nСтихия: {element}\nУправитель: {planet}\n\n⏳ Пожалуйста, подождите...',
        'horoscope_header': '{emoji} <b>{sign}</b>\nСтихия: {element}\nПланета: {planet}\n<b>{detailed_type} гороскоп на {day_text} ({date})</b>\n{"─" * 30}\n\n',
        'horoscope_error': '⚠️ Ошибка при генерации гороскопа. Попробуйте позже.',
        'detailed_type_detailed': 'Подробный',
        'detailed_type_short': 'Краткий',

        # GPT prompts (для generate_horoscope.py или yandex_gpt.py)
        'system_prompt': 'Ты создаешь персональные гороскопы на русском языке. Пиши по-настоящему: искренне, без клише, без эзотерики. Текст должен быть интересным, человечным и легко воспринимаемым.',
        'user_prompt_template': 'Вот перевод гороскопа:\n\n\"\"\"{translated}\"\"\"\n\nПерепиши его в стиле — {tone}.\nИзбегай штампов и банальностей. Пиши по-человечески, как будто обращаешься к одному человеку.\nУчитывай этот контекст дня:\n\n- {moon_context}\n- {energy_context}',

        # Tarot (tarot.py, tarot3.py, tarot5.py)
        'tarot_draw': 'Разложим карты Таро...',
        'tarot_loading': '⏳ Тасуем колоду...',
        'tarot_card': 'Карта: {card_name}\nОписание: {description}',
        'tarot3_header': 'Расклад на 3 карты: Прошлое, Настоящее, Будущее',
        'tarot5_header': 'Расклад на 5 карт: Ситуация, Препятствия, Совет, Результат, Итог',
        'tarot_error': '⚠️ Ошибка при раскладе Таро.',

        # Moon (moon.py)
        'moon_phase': 'Фаза луны: {phase}\n{description}',
        'moon_loading': '⏳ Вычисляем фазу луны...',
        'moon_error': '⚠️ Ошибка при получении данных о луне.',

        # Compatibility (compatibility.py)
        'compatibility_select': 'Выберите знаки для совместимости:',
        'compatibility_result': 'Совместимость {sign1} и {sign2}:\n{percentage}% - {description}',
        'compatibility_error': '⚠️ Ошибка при расчёте совместимости.',

        # Subscribe (subscribe.py)
        'subscribe_success': '✅ Вы успешно подписаны на ежедневные гороскопы!',
        'unsubscribe_success': '❌ Подписка отменена.',
        'subscription_status': 'Ваш статус: {status}\nЗнак: {sign}',
        'subscribe_prompt': 'Выберите знак для подписки:',
        'subscribe_error': '⚠️ Ошибка при подписке.',

        # Magic8 (magic8.py) — предполагаю, это "волшебный шар"
        'magic8_ask': 'Задайте вопрос шару...',
        'magic8_answer': 'Шар говорит: {answer}',
        'magic8_error': '⚠️ Шар не отвечает.',

        # Stats (stats.py)
        'new_users': 'Новые пользователи: {count} за {period}',
        'stats_error': '⚠️ Ошибка при получении статистики.',

        # Scheduler (scheduler.py) — для уведомлений
        'daily_horoscope': 'Ваш ежедневный гороскоп на {date}:\n{text}',
        'scheduler_error': '⚠️ Ошибка в рассылке.'
    },
    'en': {
        # Общие
        'welcome': 'Welcome! I am your astrologer. Choose language: /language',
        'language_set': 'Language changed to {lang}!',
        'error': '⚠️ Error. Try again later.',
        'back_to_menu': '« Back to menu',

        # Horoscope-specific
        'zodiac_select': '🔮 Choose zodiac sign:',
        'horoscope_loading': '{emoji} Generating horoscope for {sign}\nElement: {element}\nRuler: {planet}\n\n⏳ Please wait...',
        'horoscope_header': '{emoji} <b>{sign}</b>\nElement: {element}\nPlanet: {planet}\n<b>{detailed_type} horoscope for {day_text} ({date})</b>\n{"─" * 30}\n\n',
        'horoscope_error': '⚠️ Error generating horoscope. Try later.',
        'detailed_type_detailed': 'Detailed',
        'detailed_type_short': 'Short',

        # GPT prompts
        'system_prompt': 'You create personal horoscopes in English. Write genuinely: sincerely, without clichés, without esoterics. The text should be interesting, human, and easy to read.',
        'user_prompt_template': 'Here is the horoscope translation:\n\n\"\"\"{translated}\"\"\"\n\nRewrite it in style — {tone}.\nAvoid stamps and banalities. Write humanly, as if addressing one person.\nConsider this day context:\n\n- {moon_context}\n- {energy_context}',

        # Tarot
        'tarot_draw': 'Drawing Tarot cards...',
        'tarot_loading': '⏳ Shuffling the deck...',
        'tarot_card': 'Card: {card_name}\nDescription: {description}',
        'tarot3_header': '3-Card Spread: Past, Present, Future',
        'tarot5_header': '5-Card Spread: Situation, Obstacles, Advice, Outcome, Summary',
        'tarot_error': '⚠️ Error in Tarot reading.',

        # Moon
        'moon_phase': 'Moon phase: {phase}\n{description}',
        'moon_loading': '⏳ Calculating moon phase...',
        'moon_error': '⚠️ Error fetching moon data.',

        # Compatibility
        'compatibility_select': 'Choose signs for compatibility:',
        'compatibility_result': 'Compatibility between {sign1} and {sign2}:\n{percentage}% - {description}',
        'compatibility_error': '⚠️ Error calculating compatibility.',

        # Subscribe
        'subscribe_success': '✅ You are successfully subscribed to daily horoscopes!',
        'unsubscribe_success': '❌ Subscription canceled.',
        'subscription_status': 'Your status: {status}\nSign: {sign}',
        'subscribe_prompt': 'Choose sign for subscription:',
        'subscribe_error': '⚠️ Error subscribing.',

        # Magic8
        'magic8_ask': 'Ask the magic ball a question...',
        'magic8_answer': 'The ball says: {answer}',
        'magic8_error': '⚠️ The ball is silent.',

        # Stats
        'new_users': 'New users: {count} in {period}',
        'stats_error': '⚠️ Error fetching stats.',

        # Scheduler
        'daily_horoscope': 'Your daily horoscope for {date}:\n{text}',
        'scheduler_error': '⚠️ Error in notification.'
    }
}

# Опционально: Загрузка из JSON (раскомментируйте, если используете файл)
# try:
#     with open('data/locales.json', 'r', encoding='utf-8') as f:
#         TRANSLATIONS = json.load(f)
# except FileNotFoundError:
#     logger.warning("locales.json не найден, используем встроенные переводы.")

def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
    """Получить текст на нужном языке с подстановкой переменных. Fallback на ru."""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['ru'])
    text = translations.get(key)
    if text is None:
        logger.warning(f"Missing translation for key '{key}' in lang '{lang}'")
        text = TRANSLATIONS['ru'].get(key, f"[Missing: {key}]")  # Fallback на ru или placeholder
    return text.format(**kwargs) if kwargs else text
