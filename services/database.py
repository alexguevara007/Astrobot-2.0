import sqlite3
import os

DB = "bot.db"

def init_db():
    """Создание SQLite-файла с таблицами"""
    os.makedirs("data", exist_ok=True)
    full_path = os.path.join("data", DB)
    with sqlite3.connect(full_path) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lang TEXT DEFAULT 'ru'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                chat_id INTEGER PRIMARY KEY,
                sign TEXT NOT NULL,
                lang TEXT DEFAULT 'ru'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                text TEXT NOT NULL,
                date TEXT DEFAULT CURRENT_DATE
            )
        """)
        conn.commit()

# ─────────────── Работа с пользователями ───────────────

def set_user_lang(user_id: int, lang: str):
    """Установить или обновить язык пользователя"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        conn.execute("REPLACE INTO users (user_id, lang) VALUES (?, ?)", (user_id, lang))
        conn.commit()

def get_user_lang(user_id: int) -> str:
    """Получить язык пользователя"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        cursor = conn.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'ru'

# ─────────────── Подписки ───────────────

def add_subscription(chat_id: int, sign: str, lang: str = 'ru'):
    """Добавить или обновить подписку"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        conn.execute(
            "REPLACE INTO subscriptions (chat_id, sign, lang) VALUES (?, ?, ?)",
            (chat_id, sign, lang)
        )
        conn.commit()

def remove_subscription(chat_id: int) -> bool:
    """Удалить подписку"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        cursor = conn.execute(
            "DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def is_subscribed(chat_id: int) -> bool:
    """Проверить, есть ли подписка"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        cursor = conn.execute(
            "SELECT 1 FROM subscriptions WHERE chat_id = ?", (chat_id,)
        )
        return cursor.fetchone() is not None

def get_all_subscriptions():
    """Получить все подписки (для рассылки)"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        return conn.execute("SELECT chat_id, sign, lang FROM subscriptions").fetchall()

# ─────────────── Предсказания / История ───────────────

def save_prediction(chat_id: int, text: str, prediction_type: str = "tarot"):
    """Сохранить предсказание (таро, gpt, и т.д.)"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        conn.execute(
            "INSERT INTO predictions (chat_id, type, text) VALUES (?, ?, ?)",
            (chat_id, prediction_type, text)
        )
        conn.commit()

def get_latest_predictions(chat_id: int, limit: int = 5):
    """Получить последние предсказания"""
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        return conn.execute(
            "SELECT type, text, date FROM predictions WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit)
        ).fetchall()
