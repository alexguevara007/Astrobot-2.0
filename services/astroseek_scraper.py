import aiohttp
import logging
from bs4 import BeautifulSoup
from services.yandex_translate import translate

logger = logging.getLogger(__name__)

async def get_day_energy_description(lang: str = 'ru') -> str:
    """
    Получает краткое описание энергетики дня с astro-seek.com.
    При необходимости переведёт на русский.
    """
    try:
        url = "https://horoscopes.astro-seek.com/daily-horoscope"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                text = await response.text()

        # Парсинг HTML
        soup = BeautifulSoup(text, "html.parser")
        desc_block = soup.find("div", class_="horoBoxBoxText")
        if not desc_block:
            logger.warning("⚠️ Блок с описанием энергии не найден.")
            return ""

        description = desc_block.get_text(strip=True)

        # Перевод, если нужен
        if lang == 'ru':
            description = await translate(description, 'ru')

        if not description or len(description) < 30:
            logger.warning("⚠️ Получено слишком короткое описание дневной энергии.")
            return ""

        return description

    except Exception as e:
        logger.error(f"❌ Ошибка парсера astro-seek: {e}", exc_info=True)
        return ""
