# locales.py

# Поддерживаемые языки
LANGUAGES = {
    'ru': 'Русский',
    'en': 'English'
}

# Словарь переводов (добавьте все нужные строки из бота)
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

        # GPT prompts (для gpt_horoscope.py)
        'system_prompt': 'Ты создаешь персональные гороскопы на русском языке. Пиши по-настоящему: искренне, без клише, без эзотерики. Текст должен быть интересным, человечным и легко воспринимаемым.',
        'user_prompt_template': 'Вот перевод гороскопа:\n\n\"\"\"{translated}\"\"\"\n\nПерепиши его в стиле — {tone}.\nИзбегай штампов и банальностей. Пиши по-человечески, как будто обращаешься к одному человеку.\nУчитывай этот контекст дня:\n\n- {moon_context}\n- {energy_context}',

        # Добавьте для других модулей (таро, шар и т.д.)
        'tarot_draw': 'Разложим карты Таро...',
        # ... другие
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

        # Добавьте для других модулей
        'tarot_draw': 'Drawing Tarot cards...',
        # ... другие
    }
}

def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
    """Получить текст на нужном языке с подстановкой переменных. Fallback на ru."""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['ru'])
    text = translations.get(key, key)  # Если ключ не найден, вернуть сам ключ
    return text.format(**kwargs) if kwargs else text
