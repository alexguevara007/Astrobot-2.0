import aiohttp
from bs4 import BeautifulSoup
from services.yandex_translate import translate

async def get_day_energy_description(lang: str = 'ru'):
    try:
        url = "https://horoscopes.astro-seek.com/daily-horoscope"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                text = await response.text()

        soup = BeautifulSoup(text, "html.parser")
        desc_block = soup.find("div", class_="horoBoxBoxText")
        if not desc_block:
            return ""

        description = desc_block.get_text(strip=True)

        if lang == 'ru':
            description = await translate(description, 'ru')

        return description

    except Exception as e:
        print(f"Error in scraper: {e}")
        return ""
