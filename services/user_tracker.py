# services/user_tracker.py

import csv
import os
from datetime import datetime
from collections import defaultdict

USER_FILE = "data/user_activity.csv"
os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)

def track_user(user_id: int, username: str = ""):
    """Добавляет user_id и дату, если пользователь новый"""
    user_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    existing_users = set()

    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_users.add(row["user_id"])

    if user_id in existing_users:
        return

    try:
        is_new = not os.path.exists(USER_FILE)
        with open(USER_FILE, "a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            if is_new:
                writer.writerow(["user_id", "username", "first_seen"])
            writer.writerow([user_id, username or "", today])
    except Exception as e:
        print(f"❌ Ошибка записи пользователя: {e}")

def get_user_count() -> int:
    """Всего уникальных пользователей"""
    try:
        if not os.path.exists(USER_FILE):
            return 0
        with open(USER_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return sum(1 for _ in reader)
    except Exception:
        return 0

def get_user_stats_by_day() -> dict:
    """Возвращает словарь: {дата: количество новых юзеров}"""
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
