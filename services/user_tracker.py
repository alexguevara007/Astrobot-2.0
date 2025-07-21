import csv
import os
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

USER_FILE = "data/user_activity.csv"
os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)

DEFAULT_LANGUAGE = "ru"
CSV_FIELDS = ["user_id", "username", "first_seen", "language"]

def ensure_user_file():
    """Создаёт файл с заголовками, если он отсутствует"""
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()

def track_user(user_id: int, username: str = ""):
    """Добавляет пользователя, если он новый. Сохраняет username и язык."""
    user_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    ensure_user_file()

    updated = False
    user_found = False
    rows = []

    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["user_id"] == user_id:
                    user_found = True
                    # Обновим username, если он изменился
                    if username and row["username"] != username:
                        row["username"] = username
                        updated = True
                rows.append(row)

        if not user_found:
            rows.append({
                "user_id": user_id,
                "username": username or "",
                "first_seen": today,
                "language": DEFAULT_LANGUAGE
            })
            updated = True

        if updated:
            with open(USER_FILE, "w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

    except Exception as e:
        logger.exception(f"❌ Ошибка при записи клиента: {e}")

def get_user_count() -> int:
    """Общее количество пользователей"""
    ensure_user_file()
    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return sum(1 for _ in reader)
    except Exception as e:
        logger.exception(f"❌ Ошибка подсчёта пользователей: {e}")
    return 0

def get_user_stats_by_day() -> dict:
    """Количество новых пользователей по дате first_seen"""
    stats = defaultdict(int)
    ensure_user_file()

    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                stats[row.get("first_seen", "unknown")] += 1
        return dict(sorted(stats.items()))
    except Exception as e:
        logger.exception(f"❌ Ошибка чтения статистики: {e}")
        return {}

def get_user_language(user_id: int) -> str:
    """Возвращает язык пользователя по ID"""
    ensure_user_file()
    user_id = str(user_id)

    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["user_id"] == user_id:
                    return row.get("language", DEFAULT_LANGUAGE)
    except Exception as e:
        logger.exception(f"❌ Ошибка чтения языка пользователя: {e}")

    return DEFAULT_LANGUAGE

def toggle_user_language(user_id: int) -> str:
    """Переключает язык между 'ru' и 'en', сохраняет и возвращает новый язык"""
    ensure_user_file()
    user_id = str(user_id)
    new_lang = DEFAULT_LANGUAGE
    updated = False
    rows = []

    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["user_id"] == user_id:
                    current_lang = row.get("language", DEFAULT_LANGUAGE)
                    new_lang = "en" if current_lang == "ru" else "ru"
                    row["language"] = new_lang
                    updated = True
                rows.append(row)

        if updated:
            with open(USER_FILE, "w", encoding="utf-8", newline=True) as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

    except Exception as e:
        logger.exception(f"❌ Ошибка при переключении языка: {e}")

    return new_lang
