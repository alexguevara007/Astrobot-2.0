import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from services.database import get_all_subscriptions
from services.gpt_horoscope import load_cache
from datetime import datetime

def setup_scheduler(application):
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")  # Укажите свою зону, если нужно

    @scheduler.scheduled_job("cron", hour=8)
    def send_horoscopes():
        print(f"[{datetime.now()}] 🔔 Начинаем рассылку гороскопов...")

        # Загружаем гороскопы из кэша
        cache = load_cache()
        users = get_all_subscriptions()

        # Переносим в асинхронность
        asyncio.run(send_messages(application, users, cache))

    scheduler.start()


async def send_messages(app, users, cache):
    for chat_id, sign in users:
        user_data = cache.get(sign.lower(), {}).get("today")
        full_date = str(datetime.today().date())

        if user_data and user_data.get("date") == full_date:
            text = f"🔮 *Гороскоп на сегодня для {sign.capitalize()}*\n\n{user_data['text']}"

            try:
                await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                print(f"✅ Отправлено → {chat_id} ({sign})")
            except Exception as e:
                print(f"❌ Ошибка у {chat_id}: {e}")
        else:
            print(f"⚠️ Пропуск → Нет гороскопа в кэше для {sign}")