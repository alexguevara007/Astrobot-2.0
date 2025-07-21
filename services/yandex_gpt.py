import os
import aiohttp
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")

async def get_iam_token() -> str:
    if not YANDEX_OAUTH_TOKEN:
        raise ValueError("Отсутствует YANDEX_OAUTH_TOKEN в .env для IAM fallback.")
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    payload = {"yandexPassportOauthToken": YANDEX_OAUTH_TOKEN}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                return data["iamToken"]
    except Exception as e:
        logger.error(f"Ошибка получения IAM-токена: {e}")
        raise

async def generate_text_yandex(prompt: str, temperature: float = 0.6, max_tokens: int = 2000, use_iam: bool = False) -> str:
    if not YANDEX_FOLDER_ID:
        logger.error("Отсутствует YANDEX_FOLDER_ID в .env.")
        return ""

    if use_iam:
        try:
            iam_token = await get_iam_token()
            headers = {
                "Authorization": f"Bearer {iam_token}",
                "x-folder-id": YANDEX_FOLDER_ID
            }
        except Exception as e:
            logger.error(f"IAM fallback провалился: {e}")
            return ""
    else:
        if not YANDEX_GPT_API_KEY:
            if YANDEX_OAUTH_TOKEN:
                logger.warning("Отсутствует YANDEX_GPT_API_KEY. Пробуем IAM fallback.")
                return await generate_text_yandex(prompt, temperature, max_tokens, use_iam=True)
            else:
                logger.error("Отсутствует YANDEX_GPT_API_KEY и YANDEX_OAUTH_TOKEN.")
                return ""
        headers = {
            "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
            "x-folder-id": YANDEX_FOLDER_ID
        }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json={
                    "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
                    "completionOptions": {
                        "stream": False,
                        "temperature": temperature,
                        "maxTokens": str(max_tokens)
                    },
                    "messages": [
                        {"role": "user", "text": prompt}
                    ]
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["result"]["alternatives"][0]["message"]["text"]
                else:
                    logger.warning(f"Ошибка API: {response.status}. Ответ: {await response.text()}")
                    if response.status == 401 and not use_iam and YANDEX_OAUTH_TOKEN:
                        logger.info("Пробуем IAM fallback для 401.")
                        return await generate_text_yandex(prompt, temperature, max_tokens, use_iam=True)
                    elif response.status == 402:
                        logger.error("Ошибка 402: Payment Required. Активируйте биллинг в Yandex Cloud.")
                    elif response.status == 429:
                        logger.error("Ошибка 429: Too Many Requests. Превышен лимит.")
                    return ""
            
    except Exception as e:
        logger.error(f"Ошибка при запросе к YandexGPT: {e}")
        if not use_iam and YANDEX_OAUTH_TOKEN:
            return await generate_text_yandex(prompt, temperature, max_tokens, use_iam=True)
        return ""

async def generate_text_with_system(system_prompt: str, user_prompt: str, temperature: float = 0.6, max_tokens: int = 2000, use_iam: bool = False) -> str:
    if not YANDEX_FOLDER_ID:
        logger.error("Отсутствует YANDEX_FOLDER_ID в .env.")
        return ""

    if use_iam:
        try:
            iam_token = await get_iam_token()
            headers = {
                "Authorization": f"Bearer {iam_token}",
                "x-folder-id": YANDEX_FOLDER_ID
            }
        except Exception as e:
            logger.error(f"IAM fallback провалился: {e}")
            return ""
    else:
        if not YANDEX_GPT_API_KEY:
            if YANDEX_OAUTH_TOKEN:
                logger.warning("Отсутствует YANDEX_GPT_API_KEY. Пробуем IAM fallback.")
                return await generate_text_with_system(system_prompt, user_prompt, temperature, max_tokens, use_iam=True)
            else:
                logger.error("Отсутствует YANDEX_GPT_API_KEY и YANDEX_OAUTH_TOKEN.")
                return ""
        headers = {
            "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
            "x-folder-id": YANDEX_FOLDER_ID
        }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json={
                    "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
                    "completionOptions": {
                        "stream": False,
                        "temperature": temperature,
                        "maxTokens": str(max_tokens)
                    },
                    "messages": [
                        {"role": "system", "text": system_prompt},
                        {"role": "user", "text": user_prompt}
                    ]
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["result"]["alternatives"][0]["message"]["text"]
                else:
                    logger.warning(f"Ошибка API: {response.status}. Ответ: {await response.text()}")
                    if response.status == 401 and not use_iam and YANDEX_OAUTH_TOKEN:
                        logger.info("Пробуем IAM fallback для 401.")
                        return await generate_text_with_system(system_prompt, user_prompt, temperature, max_tokens, use_iam=True)
                    elif response.status == 402:
                        logger.error("Ошибка 402: Payment Required. Активируйте биллинг.")
                    elif response.status == 429:
                        logger.error("Ошибка 429: Too Many Requests. Превышен лимит.")
                    return ""
            
    except Exception as e:
        logger.error(f"Ошибка при запросе к YandexGPT: {e}")
        if not use_iam and YANDEX_OAUTH_TOKEN:
            return await generate_text_with_system(system_prompt, user_prompt, temperature, max_tokens, use_iam=True)
        return ""
