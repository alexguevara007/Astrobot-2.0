import logging

LANGUAGES = {
    'ru': 'Русский',
    'en': 'English'
}

TRANSLATIONS = {
    'ru': {
        # Общие
        'welcome': 'Добро пожаловать! Я — твой астролог. Выберите язык: /language',
        'language_set': 'Язык изменён на {lang}!',
        'language_button': '🌐 English 🇬🇧',
        'language_switch': '🌐 English 🇬🇧',
        'language_switched': '🌍 Язык переключён на русский 🇷🇺',
        'error': '⚠️ Ошибка. Попробуйте позже.',
        'back_to_menu': '« Назад в меню',
        'back_to_menu_button': '⬅️ Вернуться в меню',
        'repeat': '🔄 Повторить',
        'back': '⬅️ Назад',
        'main_menu': '🏠 Главное меню',

        # Меню
        'menu_horoscope': '🌞 Гороскопы',
        'menu_tarot': '🃏 Таро',
        'menu_moon': '🌝 Фаза луны',
        'menu_compatibility': '❤️ Совместимость',
        'menu_magic8': '🔮 Магический шар',
        'menu_subscribe': '🔔 Подписка',

        # Гороскоп
        'today_horoscope': '🌞 Гороскоп на сегодня',
        'tomorrow_horoscope': '🌜 Гороскоп на завтра',
        'zodiac_select': '🔮 Выберите знак зодиака:',
        'zodiac_select_tomorrow': '🔮 Завтрашний гороскоп: выберите знак зодиака',
        'invalid_sign': '⚠️ Неверно указан знак зодиака. Пожалуйста, выберите знак из списка.',
        'horoscope_loading': '{emoji} Генерация гороскопа для {sign}\nСтихия: {element}\nУправитель: {planet}\n\n⏳ Пожалуйста, подождите...',
        'horoscope_header': '{emoji} <b>{sign}</b>\nСтихия: {element}\nПланета: {planet}\n<b>{detailed_type} гороскоп на {day_text} ({date})</b>\n──────────────────────────────\n\n',
        'horoscope_error': '⚠️ Ошибка при генерации гороскопа. Попробуйте позже.',
        'detailed_type_detailed': 'Подробный',
        'detailed_type_short': 'Краткий',

        # AI
        'system_prompt': 'Ты создаешь персональные гороскопы... (коротко здесь)',
        'user_prompt_template': 'Вот перевод гороскопа:\n\n\"\"\"{translated}\"\"\"\n\nПерепиши его...',

        # Таро
        'tarot_one': '🃏 Таро-карта дня',
        'tarot_three': '🔮 Таро 3 карты',
        'tarot_five': '✨ Таро 5 карт',
        'tarot_draw': 'Разложим карты Таро...',
        'tarot_loading': '⏳ Тасуем колоду...',
        'tarot_card': 'Карта: {card_name}\nОписание: {description}',
        'tarot3_header': 'Расклад на 3 карты: Прошлое, Настоящее, Будущее',
        'tarot5_header': 'Расклад на 5 карт: Ситуация, Препятствия, Совет, Результат, Итог',
        'tarot_error': '⚠️ Ошибка при раскладе Таро.',

        # Луна
        'moon_loading': '⏳ Вычисляем фазу луны...',
        'moon_error': '⚠️ Ошибка при получении данных о луне.',
        'moon_growing': 'Луна растёт 🌒',
        'moon_waning': 'Луна убывает 🌘',
        'lunar_calendar': '{emoji} <b>{phase_name}</b> — освещенность {illumination}%\n'
                          'Знак зодиака: {moon_zodiac}\n'
                          '{growth}\n'
                          'Расстояние до Земли: {distance:,} км\n'
                          '🕒 {time} ({tz})',

        # Совместимость
        'compatibility': '❤️ Совместимость',
        'compatibility_select': 'Выберите знаки для совместимости:',
        'compatibility_result': 'Совместимость {sign1} и {sign2}:\n{percentage}% - {description}',
        'compatibility_error': '⚠️ Ошибка при расчёте совместимости.',

        # Подписка
        'subscribe': '🔔 Подписка',
        'subscribe_success': '✅ Вы успешно подписаны на гороскопы!',
        'unsubscribe_success': '❌ Подписка отменена.',
        'subscription_status': 'Ваш статус: {status}\nЗнак: {sign}',
        'subscribe_prompt': 'Выберите знак для подписки:',
        'subscribe_error': '⚠️ Ошибка при подписке.',

        # Магический шар
        'magic_ball': '🧿 Магический шар',
        'magic8_ask': 'Задайте вопрос шару...',
        'magic8_answer': 'Шар говорит: {answer}',
        'magic8_error': '⚠️ Шар не отвечает.',

        # Статистика
        'new_users': 'Новые пользователи: {count} за {period}',
        'stats_error': '⚠️ Ошибка при получении статистики.',

        # Рассылка
        'daily_horoscope': 'Ваш гороскоп на {date}:\n{text}',
        'scheduler_error': '⚠️ Ошибка в рассылке.'
    },

    'en': {
        # General
        'welcome': 'Welcome! I am your astrologer. Choose language: /language',
        'language_set': 'Language changed to {lang}!',
        'language_button': '🌐 Русский 🇷🇺',
        'language_switch': '🌐 Русский 🇷🇺',
        'language_switched': '🌍 Language switched to English 🇬🇧',
        'error': '⚠️ Error. Try again later.',
        'back_to_menu': '« Back to menu',
        'back_to_menu_button': '⬅️ Back to Menu',
        'repeat': '🔄 Repeat',
        'back': '⬅️ Back',
        'main_menu': '🏠 Main Menu',

        # Menu
        'menu_horoscope': '🌞 Horoscopes',
        'menu_tarot': '🃏 Tarot',
        'menu_moon': '🌝 Moon Phase',
        'menu_compatibility': '❤️ Compatibility',
        'menu_magic8': '🔮 Magic 8-Ball',
        'menu_subscribe': '🔔 Subscription',

        # Horoscope
        'today_horoscope': '🌞 Horoscope for Today',
        'tomorrow_horoscope': '🌜 Horoscope for Tomorrow',
        'zodiac_select': '🔮 Choose zodiac sign:',
        'zodiac_select_tomorrow': '🔮 Tomorrow\'s horoscope: choose your sign',
        'invalid_sign': '⚠️ Invalid zodiac sign. Please choose from the list.',
        'horoscope_loading': '{emoji} Generating horoscope for {sign}\nElement: {element}\nRuler: {planet}\n\n⏳ Please wait...',
        'horoscope_header': '{emoji} <b>{sign}</b>\nElement: {element}\nPlanet: {planet}\n<b>{detailed_type} horoscope for {day_text} ({date})</b>\n──────────────────────────────\n\n',
        'horoscope_error': '⚠️ Error generating horoscope. Try later.',
        'detailed_type_detailed': 'Detailed',
        'detailed_type_short': 'Short',

        # AI
        'system_prompt': 'You create personal horoscopes in English...',
        'user_prompt_template': 'Here is the horoscope translation:\n\n\"\"\"{translated}\"\"\"\n\nRewrite...',


        # Tarot
        'tarot_one': '🃏 Daily Tarot Card',
        'tarot_three': '🔮 Three Tarot Cards',
        'tarot_five': '✨ Five Tarot Cards',
        'tarot_draw': 'Drawing Tarot cards...',
        'tarot_loading': '⏳ Shuffling the deck...',
        'tarot_card': 'Card: {card_name}\nDescription: {description}',
        'tarot3_header': '3-Card Spread: Past, Present, Future',
        'tarot5_header': '5-Card Spread: Situation, Obstacles, Advice, Outcome, Summary',
        'tarot_error': '⚠️ Error in Tarot reading.',

        # Moon
        'moon_loading': '⏳ Calculating moon phase...',
        'moon_error': '⚠️ Error fetching moon data.',
        'moon_growing': 'Moon is waxing 🌒',
        'moon_waning': 'Moon is waning 🌘',
        'lunar_calendar': '{emoji} <b>{phase_name}</b> — illumination {illumination}%\n'
                          'Zodiac sign: {moon_zodiac}\n'
                          '{growth}\n'
                          'Distance to Earth: {distance:,} km\n'
                          '🕒 {time} ({tz})',

        # Compatibility
        'compatibility': '❤️ Compatibility',
        'compatibility_select': 'Choose signs for compatibility:',
        'compatibility_result': 'Compatibility between {sign1} and {sign2}:\n{percentage}% - {description}',
        'compatibility_error': '⚠️ Error calculating compatibility.',

        # Subscription
        'subscribe': '🔔 Subscription',
        'subscribe_success': '✅ You are successfully subscribed to horoscopes!',
        'unsubscribe_success': '❌ Subscription canceled.',
        'subscription_status': 'Your status: {status}\nSign: {sign}',
        'subscribe_prompt': 'Choose sign for subscription:',
        'subscribe_error': '⚠️ Error subscribing.',

        # Magic 8-ball
        'magic_ball': '🧿 Magic 8-Ball',
        'magic8_ask': 'Ask the magic ball a question...',
        'magic8_answer': 'The ball says: {answer}',
        'magic8_error': '⚠️ The ball is silent.',

        # Statistics
        'new_users': 'New users: {count} in {period}',
        'stats_error': '⚠️ Error fetching stats.',

        # Scheduler
        'daily_horoscope': 'Your horoscope for {date}:\n{text}',
        'scheduler_error': '⚠️ Error in notification.'
    }
}


def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
    """
    Получение строки перевода по ключу и языку.
    Автоматически логирует отсутствующие ключи.
    """
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['ru'])

    if key not in translations:
        logging.warning(f"[MISSING TRANSLATION] key='{key}' lang='{lang}'")

    text = translations.get(key, f"[Missing: {key}]")
    return text.format(**kwargs) if kwargs else text
