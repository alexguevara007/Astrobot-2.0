import requests
import os
import logging
import json

logger = logging.getLogger(__name__)

def get_iam_token(oauth_token: str) -> str:
    """Получаем IAM-токен по OAuth-токену (для альтернативы Api-Key)"""
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    payload = {"yandexPassportOauthToken": oauth_token}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["iamToken"]
    except Exception as e:
        logger.error(f"Ошибка получения IAM-токена: {e}")
        raise

def translate_text(text: str, target_lang="ru", source_lang="en", use_iam=False):
    """
    Перевод текста с использованием Yandex Translate API.
    :param use_iam: Если True, используем IAM-токен вместо Api-Key (для fallback).
    """
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    if not folder_id:
        logger.error("Отсутствует YANDEX_FOLDER_ID в .env.")
        return text  # Fallback: оригинальный текст

    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    body = {
        "folderId": folder_id,
        "texts": [text],
        "targetLanguageCode": target_lang,
        "sourceLanguageCode": source_lang
    }

    if use_iam:
        # Альтернатива: IAM-токен
        oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
        if not oauth_token:
            logger.error("Отсутствует YANDEX_OAUTH_TOKEN для IAM в .env.")
            return text
        try:
            iam_token = get_iam_token(oauth_token)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {iam_token}"
            }
        except Exception:
            return text
    else:
        # Основной: Api-Key
        api_key = os.getenv("YANDEX_API_KEY")
        if not api_key:
            logger.error("Отсутствует YANDEX_API_KEY в .env. Пробуем IAM как fallback.")
            return translate_text(text, target_lang, source_lang, use_iam=True)  # Рекурсивно пробуем IAM
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {api_key}"
        }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        translated = response.json()["translations"][0]["text"]
        logger.info("Перевод успешен.")
        return translated
    except requests.exceptions.HTTPError as e:
        status = response.status_code
        if status == 401:
            logger.error("Ошибка 401: Unauthorized. Проверьте YANDEX_API_KEY/OAUTH_TOKEN, права доступа и биллинг в Yandex Cloud.")
            if not use_iam:
                logger.info("Пробуем fallback на IAM-токен.")
                return translate_text(text, target_lang, source_lang, use_iam=True)
        elif status == 402:
            logger.error("Ошибка 402: Payment Required. Активируйте биллинг в Yandex Cloud.")
        elif status == 429:
            logger.error("Ошибка 429: Too Many Requests. Превышен лимит.")
        else:
            logger.error(f"HTTP-ошибка: {e}")
        return text  # Fallback: оригинальный текст
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        return text  # Fallback
