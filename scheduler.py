import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from services.database import get_all_subscriptions
from services.cache_utils import load_cache, clear_old_cache

logger = logging.getLogger(__name__)

def setup_scheduler(application):
    """Настройка фонового планировщика задач"""
    try:
        scheduler = BackgroundScheduler(timezone="Europe/Moscow")

        @scheduler.scheduled_job("cron", hour=10, minute=0)
        def send_daily_horoscopes():
            """Ежедневная рассылка гороскопов подписчикам в 10:00"""
            logger.info("🔔 Запуск утренней рассылки гороскопов...")

            try:
                cache = load_cache()
                users = get_all_subscriptions()

                # ✅ Создаём задачу ВНУТРИ loop'а бота
                application.create_task(send_messages(application, users, cache))

            except Exception as e:
                logger.error(f"❌ Ошибка в рассылке гороскопов: {e}")

        @scheduler.scheduled_job("cron", hour=0, minute=1)
        def clear_cache_job():
            """Очистка старого кэша каждый день в 00:01"""
            try:
                clear_old_cache()
                logger.info("✅ Старый кэш очищен")
            except Exception as e:
                logger.error(f"❌ Ошибка при очистке кэша: {e}")

        scheduler.start()
        logger.info("✅ Планировщик запущен")
        logger.info("📅 Задачи:")
        logger.info("   • Рассылка гороскопов — ежедневно в 10:00")
        logger.info("   • Очистка кэша — ежедневно в 00:01")

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске планировщика: {e}")


# ───────── ASYNC SEND MESSAGES ─────────

async def send_messages(application, users, cache):
    """Отправляет гороскопы подписчикам"""
    current_date = str(datetime.today().date())
    sent_count = 0
    error_count = 0

    for chat_id, sign in users:
        try:
            sign_lower = sign.lower()
            key = f"brief_{sign_lower}_today"

            sign_cache = cache.get(sign_lower, {})
            user_data = sign_cache.get(key)

            if user_data and user_data.get("date") == current_date:
                message = (
                    f"🌟 <b>Ваш гороскоп на сегодня</b> ({current_date})\n"
                    f"Знак: {sign.capitalize()}\n"
                    f"{'─' * 30}\n\n"
                    f"{user_data['text']}"
                )
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML"
                )
                sent_count += 1
                logger.info(f"✅ Отправлен: chat_id={chat_id}, sign={sign}")
            else:
                logger.warning(f"⚠️ Нет данных в кэше для: {sign} / {chat_id}")
                error_count += 1

        except Exception as e:
            logger.error(f"❌ Ошибка отправки: chat_id={chat_id}, sign={sign} — {e}")
            error_count += 1

    logger.info(
        f"📊 Статистика рассылки на {current_date}:\n"
        f"👥 Пользователей: {len(users)}\n"
        f"📩 Успешно: {sent_count}\n"
        f"⚠️ Ошибок: {error_count}"
    )
