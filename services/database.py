import sqlite3
import os

DB = "bot.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    full_path = os.path.join("data", DB)
    with sqlite3.connect(full_path) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS subscriptions (chat_id INTEGER PRIMARY KEY, sign TEXT)")
        c.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                type TEXT,
                text TEXT,
                date TEXT DEFAULT CURRENT_DATE
            )
        """)
        conn.commit()

# ➕ подписка
def add_subscription(chat_id, sign):
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        conn.execute("REPLACE INTO subscriptions (chat_id, sign) VALUES (?, ?)", (chat_id, sign))
        conn.commit()

# ➖ отписка
def remove_subscription(chat_id: int) -> bool:
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        cursor = conn.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
        conn.commit()
        return cursor.rowcount > 0

# 🔎 проверка подписки
def is_subscribed(chat_id: int) -> bool:
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        cursor = conn.execute("SELECT 1 FROM subscriptions WHERE chat_id = ?", (chat_id,))
        return cursor.fetchone() is not None

# 📬 получить всех подписчиков
def get_all_subscriptions():
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        return conn.execute("SELECT chat_id, sign FROM subscriptions").fetchall()

# 📝 сохранить предсказание
def save_prediction(chat_id: int, text: str, prediction_type: str = "tarot"):
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        conn.execute(
            "INSERT INTO predictions (chat_id, type, text) VALUES (?, ?, ?)",
            (chat_id, prediction_type, text)
        )
        conn.commit()

# 📖 получить последние n предсказаний
def get_latest_predictions(chat_id: int, limit: int = 5):
    with sqlite3.connect(os.path.join("data", DB)) as conn:
        return conn.execute(
            "SELECT type, text, date FROM predictions WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit)
        ).fetchall()