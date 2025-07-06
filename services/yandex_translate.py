import requests
import os

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")  # клади ключ в .env

def translate_text(text: str, target_lang="ru"):
    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "targetLanguageCode": target_lang,
        "texts": [text],
        "folderId": os.getenv("YANDEX_FOLDER_ID")  # тоже в .env
    }

    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()["translations"][0]["text"]
    except Exception as e:
        return f"Ошибка перевода: {e}"
