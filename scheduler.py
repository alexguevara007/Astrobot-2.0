import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
from services.database import get_all_subscriptions
from services.gpt_horoscope import load_cache, clear_old_cache

logger = logging.getLogger(__name__)

def setup_scheduler(application):
    """Настройка планировщика задач"""
    try:
        scheduler = BackgroundScheduler(timezone="Europe/Moscow")

        @scheduler.scheduled_job("cron", hour=10)  # Изменено время на 10:00
        def send_daily_horoscopes():
            """Ежедневная рассылка гороскопов подписчикам в 10:00"""
            logger.info("🔔 Начинаем рассылку гороскопов...")

            try:
                # Загружаем гороскопы из кэша
                cache = load_cache()
                users = get_all_subscriptions()

                # Переносим в асинхронность
                asyncio.run(send_messages(application, users, cache))
            except Exception as e:
                logger.error(f"Ошибка при запуске рассылки: {e}")

        @scheduler.scheduled_job("cron", hour=0, minute=1)
        def clear_cache_job():
            """Ежедневная очистка устаревшего кэша"""
            try:
                clear_old_cache()
                logger.info("✅ Плановая очистка кэша завершена")
            except Exception as e:
                logger.error(f"Ошибка при очистке кэша: {e}")

        # Запускаем планировщик
        scheduler.start()
        logger.info("✅ Планировщик задач успешно запущен")
        logger.info("📅 Расписание:")
        logger.info("   • Рассылка гороскопов: 10:00")
        logger.info("   • Очистка кэша: 00:01")

    except Exception as e:
        logger.error(f"❌ Ошибка при настройке планировщика: {e}")

async def send_messages(app, users, cache):
    """Отправка гороскопов пользователям"""
    current_date = str(datetime.today().date())
    sent_count = 0
    error_count = 0

    for chat_id, sign in users:
        try:
            # Получаем данные из кэша
            sign_lower = sign.lower()
            user_data = cache.get(sign_lower, {}).get("brief_" + sign_lower + "_today")

            if user_data and user_data.get("date") == current_date:
                # Формируем сообщение
                message = (
                    f"🌟 Ваш гороскоп на сегодня ({current_date})\n"
                    f"Знак: {sign.capitalize()}\n"
                    f"{'_' * 30}\n\n"
                    f"{user_data['text']}"
                )

                # Отправляем сообщение
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML"
                )
                sent_count += 1
                logger.info(f"✅ Гороскоп отправлен: {chat_id} ({sign})")
            else:
                logger.warning(f"⚠️ Нет актуального гороскопа в кэше для {sign}")
                error_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"❌ Ошибка отправки для {chat_id} ({sign}): {e}")

    # Итоговая статистика
    logger.info(
        f"📊 Статистика рассылки:\n"
        f"Всего пользователей: {len(users)}\n"
        f"Успешно отправлено: {sent_count}\n"
        f"Ошибок: {error_count}"
    )
