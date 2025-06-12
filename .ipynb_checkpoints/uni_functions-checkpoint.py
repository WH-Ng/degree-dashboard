
def libraries():
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup as BS
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import time
    import re

def set_up(url):
    options = Options()
    options.add_argument("--headless")  # Run in background, no browser window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    html = driver.page_source
    soup = BS(html, "html.parser")

    degree_cards = soup.find_all("div", class_="degree-card-title-container-row-title")

    bachelor_degrees = []

    for card in degree_cards:
        title = card.get_text(strip=True)
    
        if title.startswith('Bachelor'):
            bachelor_degrees.append(title)

    print(bachelor_degrees)
