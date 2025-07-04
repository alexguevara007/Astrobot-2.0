# services/yandex_gpt.py

import os
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем ключи API
YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

def generate_text_yandex(prompt: str, temperature: float = 0.6, max_tokens: int = 2000) -> str:
    """
    Генерирует текст используя YandexGPT API
    :param prompt: Текст запроса
    :param temperature: Температура генерации (0.0 - 1.0)
    :param max_tokens: Максимальное количество токенов
    :return: Сгенерированный текст
    """
    try:
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
                "x-folder-id": YANDEX_FOLDER_ID
            },
            json={
                "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens)
                },
                "messages": [
                    {
                        "role": "user",
                        "text": prompt
                    }
                ]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["result"]["alternatives"][0]["message"]["text"]
        else:
            print(f"Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return "Извините, произошла ошибка при генерации текста."
            
    except Exception as e:
        print(f"Ошибка при запросе к YandexGPT: {e}")
        return "Извините, произошла ошибка при обращении к сервису."

def generate_text_with_system(system_prompt: str, user_prompt: str, temperature: float = 0.6) -> str:
    """
    Генерирует текст с учетом системного промпта
    :param system_prompt: Системный промпт для установки роли
    :param user_prompt: Пользовательский запрос
    :param temperature: Температура генерации
    :return: Сгенерированный текст
    """
    try:
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
                "x-folder-id": YANDEX_FOLDER_ID
            },
            json={
                "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": "2000"
                },
                "messages": [
                    {
                        "role": "system",
                        "text": system_prompt
                    },
                    {
                        "role": "user",
                        "text": user_prompt
                    }
                ]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["result"]["alternatives"][0]["message"]["text"]
        else:
            print(f"Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return "Извините, произошла ошибка при генерации текста."
            
    except Exception as e:
        print(f"Ошибка при запросе к YandexGPT: {e}")
        return "Извините, произошла ошибка при обращении к сервису."