import requests
from bs4 import BeautifulSoup
from django.conf import settings
import httpx

url = settings.PARALLEL_RATE_WEB_LINK

def get_parallel_rate() -> str:
    """This get parallel rate from wise.com/gb/currency-converter/usd-to-ngn-rate at the start of the code....If it breaks hold the plaftorm responsible ooooo. wait you can let me know sha"""
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup wiht html parser sha
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the element containing the exchange rate
        # Note: The class name or structure might change over time, so you may need to inspect the page and update this accordingly.
        rate_element = soup.find('span', {'class': 'text-success'})
        
        if rate_element:
            # Extract the exchange rate text
            naira_rate = rate_element.text.strip()
            print(f"Current USD to NGN rate: {naira_rate}")
            return naira_rate.replace(",", "")
        else:
            print("Could not find the exchange rate on the page.")
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")


def get_official_exchange_rate() -> float:
    # Make a request to a reliable source (e.g., a central bank (relaiable for where????) or financial institution) to get the current official exchange rate
    url = f"{settings.OFFICIAL_RATE_WEB_LINK}?app_id={settings.OPEN_EXCHANGE_API_KEY}"
    response = httpx.get(url)
    if response.status_code == 200:
        data = response.json()
        rate = data["rates"].get("NGN")
        return rate