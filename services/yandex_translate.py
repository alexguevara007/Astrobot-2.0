import aiohttp
import os
import logging
import json

logger = logging.getLogger(__name__)

async def get_iam_token(oauth_token: str) -> str:
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    payload = {"yandexPassportOauthToken": oauth_token}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data["iamToken"]
    except Exception as e:
        logger.error(f"Ошибка получения IAM-токена: {e}")
        raise

async def translate_text(text: str, target_lang="ru", source_lang="en", use_iam=False):
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    if not folder_id:
        logger.error("Отсутствует YANDEX_FOLDER_ID в .env.")
        return text

    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    body = {
        "folderId": folder_id,
        "texts": [text],
        "targetLanguageCode": target_lang,
        "sourceLanguageCode": source_lang
    }

    if use_iam:
        oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
        if not oauth_token:
            logger.error("Отсутствует YANDEX_OAUTH_TOKEN для IAM в .env.")
            return text
        try:
            iam_token = await get_iam_token(oauth_token)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {iam_token}"
            }
        except Exception:
            return text
    else:
        api_key = os.getenv("YANDEX_API_KEY")
        if not api_key:
            logger.error("Отсутствует YANDEX_API_KEY в .env. Пробуем IAM как fallback.")
            return await translate_text(text, target_lang, source_lang, use_iam=True)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {api_key}"
        }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body, timeout=10) as response:
                response.raise_for_status()
                translated = (await response.json())["translations"][0]["text"]
                logger.info("Перевод успешен.")
                return translated
    except aiohttp.ClientResponseError as e:
        status = e.status
        if status == 401:
            logger.error("Ошибка 401: Unauthorized. Проверьте YANDEX_API_KEY/OAUTH_TOKEN, права доступа и биллинг в Yandex Cloud.")
            if not use_iam:
                logger.info("Пробуем fallback на IAM-токен.")
                return await translate_text(text, target_lang, source_lang, use_iam=True)
        elif status == 402:
            logger.error("Ошибка 402: Payment Required. Активируйте биллинг в Yandex Cloud.")
        elif status == 429:
            logger.error("Ошибка 429: Too Many Requests. Превышен лимит.")
        else:
            logger.error(f"HTTP-ошибка: {e}")
        return text
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        return text
translate = translate_text
