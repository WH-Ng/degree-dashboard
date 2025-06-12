
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

    return bachelor_degrees

def ba_links(url):
    options = Options()
    options.add_argument("--headless")  # Run in background, no browser window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    html = driver.page_source
    soup = BS(html, "html.parser")
    
    ba_degree_links = []
    degree_anchors = soup.find_all("a", class_="degree-card-title-container-row")

    for anchor in degree_anchors:
        title_div = anchor.find("div", class_="degree-card-title-container-row-title")
        title = title_div.get_text(strip=True) if title_div else ""
        href = anchor.get("href")

        if href and title.startswith("Bachelor"):
            full_url = href
            ba_degree_links.append((title, full_url))

    return ba_degree_links


def get_data(degree_links):
    all_data = []

    options = Options()
    options.add_argument("--headless")  # Run in background, no browser window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    for url in degree_links:
        
        driver.get(url[1])
        html = driver.page_source
        page_soup = BS(html, "html.parser")
    
        block1 = page_soup.find_all("div", class_="degree-details-content-section-icon-list-top")
    
        for i in block1:
            spans = i.find_all('span')
            #print(spans)
        
            if spans: # shorthand for if len(spans) > 0:
                name = spans[0].get_text(strip=True)
                if name == 'Entry scores':
                    value = spans[-2].get_text(strip=True)
                else: 
                    value = spans[-1].get_text(strip=True)
    
                all_data.append({
                    "Degree Name": url[0],    # Degree name from ba_degree_links
                    "Degree URL": url[1],     # Degree link from ba_degree_links
                    "Field": name,            # Field name e.g. "Mode"
                    "Value": value            # Field value e.g. "100% Online"
                })
    
    data_list = pd.DataFrame(all_data)
    
    return data_list



def data_pivot(data_list):
    
    data_list = data_list.pivot_table(
        index=['Degree Name', 'Degree URL'],  # 1 row per degree
        columns='Field',                      # Field names become columns
        values='Value',                       # Field values go into cells
        aggfunc='first'                       # In case of duplicates
    ).reset_index()

    data_list.columns.name = None
    data_list.columns = [str(col) for col in data_list.columns]

    return data_list

def clean_up(data_list):

    columns_to_drop = ['Check your eligibility', 'Program code', 'Indicative annual fees', 'Time commitment']
    data_list = data_list.drop(columns=[col for col in columns_to_drop if col in data_list.columns])
    
    if 'Entry scores' in data_list.columns:
        data_list.rename(columns={'Entry scores': 'Guaranteed ATAR score'}, inplace=True)

        def extract_number(text):
            str_text = str(text)
            match = re.search(r'(\d+\.?\d*)$', str_text)  # Match integers and decimals
            return float(match.group(1)) if match else None  # Return the number or None

        data_list['Guaranteed ATAR score'] = data_list['Guaranteed ATAR score'].apply(extract_number)

    column_order = ['Degree Name', 'Guaranteed ATAR score', 'Prerequisite', 'Assumed knowledge', 'Mode', 'Campus', 'Study as', 'Duration', 'Start date', 'Degree URL']
    existing_columns = [col for col in column_order if col in data_list.columns]
    
    data_list = data_list[existing_columns]

    return data_list

def save_file(data_list, file_name):
    data_list.to_csv(file_name, index=False)

def merge_csv(folder_path, output_file):
    import pandas as pd
    import glob
    
    csv_files = glob.glob(f"{folder_path}/*.csv")
    dfs = [pd.read_csv(file) for file in csv_files]
    merged_df = pd.concat(dfs, ignore_index=True, sort=False)

    if 'Degree Name' in merged_df.columns and 'Degree URL' in merged_df.columns:
        before_count = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['Degree Name', 'Degree URL']).reset_index(drop=True)
    
    if 'Degree Name' in merged_df.columns:
        merged_df = merged_df.sort_values(by='Degree Name').reset_index(drop=True)
        
    merged_df.to_csv(output_file, index=False)
    return merged_df
