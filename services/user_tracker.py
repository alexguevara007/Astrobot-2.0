# services/user_tracker.py

import csv
import os
from datetime import datetime
from collections import defaultdict

USER_FILE = "data/user_activity.csv"
os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)

DEFAULT_LANGUAGE = "ru"

def ensure_user_file():
    """Создаёт файл при необходимости с заголовками"""
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["user_id", "username", "first_seen", "language"])

def track_user(user_id: int, username: str = ""):
    """Добавляет пользователя, если новый"""
    user_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    exists = False
    rows = []

    ensure_user_file()

    with open(USER_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["user_id"] == user_id:
                exists = True
                return  # уже есть
            rows.append(row)

    if not exists:
        with open(USER_FILE, "a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([user_id, username or "", today, DEFAULT_LANGUAGE])

def get_user_count() -> int:
    """Общее число пользователей"""
    if not os.path.exists(USER_FILE):
        return 0
    with open(USER_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return sum(1 for _ in reader)

def get_user_stats_by_day() -> dict:
    """Сколько новых пользователей по датам"""
    stats = defaultdict(int)
    if not os.path.exists(USER_FILE):
        return {}

    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                stats[row["first_seen"]] += 1
        return dict(sorted(stats.items()))
    except Exception as e:
        print(f"❌ Ошибка чтения статистики: {e}")
        return {}

def get_user_language(user_id: int) -> str:
    """Получить язык пользователя"""
    user_id = str(user_id)
    if not os.path.exists(USER_FILE):
        return DEFAULT_LANGUAGE

    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["user_id"] == user_id:
                    return row.get("language", DEFAULT_LANGUAGE)
    except Exception as e:
        print(f"❌ Ошибка чтения языка: {e}")
    
    return DEFAULT_LANGUAGE

def toggle_user_language(user_id: int) -> str:
    """
    Меняет язык пользователя (ru <-> en) и сохраняет в CSV.
    Возвращает новый язык.
    """
    user_id_str = str(user_id)
    new_rows = []
    new_lang = DEFAULT_LANGUAGE
    changed = False

    ensure_user_file()

    with open(USER_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["user_id"] == user_id_str:
                current_lang = row.get("language", DEFAULT_LANGUAGE)
                new_lang = "en" if current_lang == "ru" else "ru"
                row["language"] = new_lang
                changed = True
            new_rows.append(row)

    if changed:
        with open(USER_FILE, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["user_id", "username", "first_seen", "language"])
            writer.writeheader()
            writer.writerows(new_rows)

    return new_lang
