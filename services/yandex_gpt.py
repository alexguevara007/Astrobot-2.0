import os
import aiohttp
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")

API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
MODEL_URI = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite"


async def get_iam_token() -> str:
    """Получение IAM-токена из OAuth"""
    if not YANDEX_OAUTH_TOKEN:
        raise ValueError("Отсутствует YANDEX_OAUTH_TOKEN в .env")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                json={"yandexPassportOauthToken": YANDEX_OAUTH_TOKEN},
                timeout=10
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data["iamToken"]
    except Exception as e:
        logger.error(f"Ошибка получения IAM-токена: {e}")
        raise


async def _make_request(messages: list[dict], temperature: float, max_tokens: int, use_iam: bool) -> str:
    """Внутренняя функция отправки запроса к YandexGPT"""
    
    if not YANDEX_FOLDER_ID:
        logger.error("Отсутствует YANDEX_FOLDER_ID в .env.")
        return ""

    # Подготовка заголовков
    try:
        if use_iam:
            iam_token = await get_iam_token()
            headers = {
                "Authorization": f"Bearer {iam_token}",
                "x-folder-id": YANDEX_FOLDER_ID
            }
        else:
            if not YANDEX_GPT_API_KEY:
                if YANDEX_OAUTH_TOKEN:
                    logger.warning("Нет API-ключа, используем IAM fallback.")
                    return await _make_request(messages, temperature, max_tokens, use_iam=True)
                logger.error("Нет YANDEX_GPT_API_KEY и YANDEX_OAUTH_TOKEN.")
                return ""
            headers = {
                "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
                "x-folder-id": YANDEX_FOLDER_ID
            }

        payload = {
            "modelUri": MODEL_URI,
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens)
            },
            "messages": messages
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["result"]["alternatives"][0]["message"]["text"]
                else:
                    body = await response.text()
                    logger.warning(f"❌ Ошибка GPT API {response.status}: {body}")

                    # Обработка ошибок
                    if response.status == 401 and not use_iam and YANDEX_OAUTH_TOKEN:
                        logger.info("Пробуем IAM fallback (401)")
                        return await _make_request(messages, temperature, max_tokens, use_iam=True)
                    if response.status == 402:
                        logger.error("❌ Ошибка 402: Payment Required — подключите биллинг.")
                    if response.status == 429:
                        logger.error("❌ Ошибка 429: Превышен лимит.")
                    return ""
    except Exception as e:
        logger.error(f"❌ Ошибка при обращении к YandexGPT: {e}")
        if not use_iam and YANDEX_OAUTH_TOKEN:
            logger.info("⏪ Retry через IAM fallback")
            return await _make_request(messages, temperature, max_tokens, use_iam=True)
        return ""


async def generate_text_yandex(prompt: str, temperature: float = 0.6, max_tokens: int = 2000, use_iam: bool = False) -> str:
    """Запрос к YandexGPT с одним сообщением от пользователя"""
    messages = [{"role": "user", "text": prompt}]
    return await _make_request(messages, temperature, max_tokens, use_iam)


async def generate_text_with_system(system_prompt: str, user_prompt: str, temperature: float = 0.6, max_tokens: int = 2000, use_iam: bool = False) -> str:
    """Запрос к YandexGPT с system + user prompt"""
    messages = [
        {"role": "system", "text": system_prompt},
        {"role": "user", "text": user_prompt}
    ]
    return await _make_request(messages, temperature, max_tokens, use_iam)
