import requests
from bs4 import BeautifulSoup

def get_day_energy_description():
    try:
        url = "https://horoscopes.astro-seek.com/daily-horoscope"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        desc_block = soup.find("div", class_="horoBoxBoxText")
        if not desc_block:
            return ""
        return desc_block.get_text(strip=True)

    except:
        return ""
