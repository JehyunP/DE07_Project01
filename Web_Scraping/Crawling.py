# import Libraries
# for Crawling
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait as ww
from selenium.webdriver.support import expected_conditions as ec
import re

# for data fram
import pandas as pd

# Target URL and YEAR selection
URL = 'https://flixpatrol.com/most-watched/'
YEAR = ['2023-1', '2023-2', '2023', '2024-1', '2024-2', '2024', '2025-1']


# crawled data will be stored into list then 
temporary_can = []


# Set options for webdriver
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')
options.add_argument('--disable-extensions')
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-background-networking')
options.add_argument('--disable-default-apps')
options.add_argument('--disable-sync')
options.add_argument('--disable-translate')
options.add_argument('--metrics-recording-only')
options.add_argument('--mute-audio')
options.add_argument('--no-first-run')
options.add_argument('--disable-features=IsolateOrigins,site-per-process')
options.add_argument('--log-level=3')          
options.add_experimental_option('excludeSwitches', ['enable-logging']) 


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# loop through all years
for year in YEAR:

    # Loop for 10 pages: 1-10
    # try except block to handle any errors during scraping
    try:
        for i in range(1, 7):
            page_url = URL + year + '/page-' + str(i) + '/'
            driver.get(page_url)
    
            try:
                ww(driver, 3).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
                )
            except Exception as e:
                print(f"Timeout waiting for page {page_url}: {e}")
                continue


            print(f'Scraping page: {page_url}')
            
            # parse the page source with BeautifulSoup
            soup = bs(driver.page_source, 'html.parser')
            
            # Find each TR element in the table body
            for row in soup.find('tbody').find_all('tr'):
                cols = row.find_all('td')
                if not cols:
                    continue  # Skip if no columns found

                # Extract data from each column
                try:
                    rank = cols[0].get_text(strip=True).replace(".", "")
                    title = cols[1].select_one("span.group-hover\\:underline").get_text(strip=True)
                    type = cols[2].get_text(strip=True)
                    premiere = cols[3].get_text(strip=True)
                    genre = cols[4].get_text(strip=True)
                    country = cols[5].find("span")["title"]
                    hours = cols[6].find("div").get_text(strip=True)
                    runtime = cols[7].get_text(strip=True)
                    views = cols[8].find("div").get_text(strip=True)
                except Exception as e:
                    print(f'Error Occured at mainpage with {e}')

                # Navigate to the detail page to get more information     
                link = cols[1].find("a")["href"]
                detail_url = "https://flixpatrol.com" + link
                
                driver.execute_script('window.open(arguments[0]);', detail_url)
                driver.switch_to.window(driver.window_handles[1])
                ww(driver, 3).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, 'body > div:nth-child(4)'))
                )


                detail_soup = bs(driver.page_source, 'html.parser')

                # Extract additional details

                try:
                    description_elem = detail_soup.select_one(
                        "div.card.-mx-content > div:not(:has(table))"
                    )
                    description = description_elem.get_text(strip=True) if description_elem else None
                except Exception as e:
                    print(f'Error extracting description for {title}: {e}')
                    description = None

                dl_block = detail_soup.select_one(
                    "div.card.-mx-content > dl"
                )

                info_dict = {}
                if dl_block:
                    rows = dl_block.select("div") 
                    for row in rows:
                        label_elem = row.select_one("dt.w-24") 
                        value_elem = row.select_one("dt.grow") 
                        if label_elem and value_elem:
                            label = label_elem.get_text(strip=True)
                            value = value_elem.get_text(strip=True)
                            info_dict[label] = value
                
                starring = info_dict.get('Starring', None)
                directors = info_dict.get('Directed by', None)
                produced_by = info_dict.get('Produced by', None)

                try:
                    ott = None

                    ott_elem_span = detail_soup.select_one(
                        "div.flex.gap-x-1.items-center span[title] + span"
                    )
                    if ott_elem_span:
                        ott = ott_elem_span.get_text(strip=True).rstrip('|')

                    if not ott:
                        ott_elem_div = detail_soup.select_one(
                            "div.flex.flex-wrap.gap-x-1.text-sm > div:nth-child(4)"
                        )
                        if ott_elem_div:
                            text = ott_elem_div.get_text(strip=True).rstrip('|')
                            if text != genre:
                                ott = text

                except Exception as e:
                    print(f'Error extracting ott for {title}: {e}')
                    ott = None

                try:
                    genre_position = 6 if ott else 5
                    specific_genre = detail_soup.select_one(
                        f"div.flex.flex-wrap.gap-x-1.text-sm.leading-6.text-gray-500 > div:nth-child({genre_position})"
                    ).get_text(strip=True).rstrip('|')
                except Exception as e:
                    print(f'Error extracting specific_genre for {title}: {e}')
                    specific_genre = None


                imdb = detail_soup.select_one(
                    "div.flex.flex-wrap.justify-around.text-center > div.px-2.py-4.w-32 > div.mb-1.text-2xl.text-gray-400"
                ).get_text(strip=True).rstrip('/10')
                


                rotten_tomatos = detail_soup.select_one(
                    "div.flex.flex-wrap.justify-around.text-center > div.px-2.py-4.w-40 > div.mb-1.text-2xl.text-gray-400"
                ).get_text(strip=True).rstrip('%')

                
                try:
                    poster_elem = driver.find_element(
                        By.XPATH,
                        "/html/body/div[4]/div/div[1]/div/picture/img"
                    )
                    poster = poster_elem.get_attribute("src")  
                except Exception as e:
                    print(f"Error extracting poster for {title}: {e}")
                    poster = None

                # Click "Streaming" to get Streaming services
                tabs = driver.find_elements(By.CSS_SELECTOR, "div.flex a")
                streaming_btn = None
                streamings = []

                for tab in tabs:
                    if "Streaming" in tab.text:
                        streaming_btn = tab
                        break

                if streaming_btn:
                    driver.execute_script("arguments[0].click();", streaming_btn)
                    try:
                        ww(driver, 2).until(
                            ec.any_of(
                                ec.presence_of_element_located((By.CSS_SELECTOR, "div[id^=toc-] > h2")),
                                ec.presence_of_element_located((By.CSS_SELECTOR, "div[id^=toc-]"))
                            )
                        )
                    except Exception as e:
                        print(f"Timeout waiting for Streaming section: {e}")

                    updated_soup = bs(driver.page_source, 'html.parser')
                    for h2 in updated_soup.select("div[id^=toc-] > h2"):
                        span = h2.select_one("span:nth-of-type(2)")
                        if span:
                            text = span.get_text(strip=True)
                            match = text.rsplit("on", 1)[-1].strip()
                            if match:
                                streamings.append(match)
                else:
                    print(f"No Streaming tab for {title}")
                
                # Store the crawled data into data frame
                data = {
                    'Rank':rank,
                    'Title' : title, 
                    'Type' : type, 
                    'Premiere' : premiere, 
                    'Genre' : genre, 
                    'Country' : country, 
                    'Hours' : hours, 
                    'Runtime' : runtime, 
                    'Views' : views, 
                    'Description' : description,
                    'Starring' : starring,
                    'Directors' : directors, 
                    'Produced_by' : produced_by, 
                    'Specific_genre' : specific_genre, 
                    'IMDB' : imdb, 
                    'Rotten_Tomatoes' : rotten_tomatos,
                    'Poster' : poster, 
                    'Year' : year, 
                    'Streaming' : streamings, 
                    'OTT': ott
                }
                temporary_can.append(data)
                print(f'rank: {rank}\tdata: {title}')
                
                # back to the main page
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
                
    except Exception as e:
        print(f'Error while scraping page: {i} - {e}')

df = pd.DataFrame(temporary_can)
df.to_csv('output.csv', index=False)