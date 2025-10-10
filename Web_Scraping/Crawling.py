# import Libraries for Crawling
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait as ww
from selenium.webdriver.support import expected_conditions as ec

# for data frame
import pandas as pd

# Target URL and YEAR selection
URL = 'https://flixpatrol.com/most-watched/'
#YEAR = ['2023-1', '2023-2', '2023', '2024-1', '2024-2', '2024', '2025-1']
YEAR = ['2025-1']

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

# driver setup via Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# loop through all years
for half_year in YEAR:

    # Loop for 10 pages: 1-7 : 300 data
    # try except block to handle any errors during scraping
    try:
        for i in range(1, 7):
            page_url = URL + half_year + '/page-' + str(i) + '/'
            driver.get(page_url)

            # Wait for web loading
            try:
                ww(driver, 3).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
                )
            except Exception as e:
                print(f"Timeout waiting for page {page_url}: {e}")
                continue

            # Debug check each pages
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
                    title_elem = cols[1].select_one("span.group-hover\\:underline")
                    series_elem = cols[1].select_one("span.text-sm.text-gray-500.whitespace-nowrap")     
                    title = title_elem.get_text(strip=True) if title_elem else None
                    if series_elem:
                        title = f"{title} {series_elem.get_text(strip=True)}"
                    type = cols[2].get_text(strip=True)
                    release = cols[3].get_text(strip=True)
                    genre = cols[4].get_text(strip=True)
                    country = cols[5].find("span")["title"]
                    hours = cols[6].find("div").get_text(strip=True)
                    runtime = cols[7].get_text(strip=True)
                    views = cols[8].find("div").get_text(strip=True)
                except Exception as e: # Debuger for each column 
                    print(f'Error Occured at mainpage with {e}')
                print(title)

                # Navigate to the detail page to get more information     
                link = cols[1].find("a")["href"]
                detail_url = "https://flixpatrol.com" + link

                # Open new window with detail page
                driver.execute_script('window.open(arguments[0]);', detail_url)
                driver.switch_to.window(driver.window_handles[1])
                ww(driver, 3).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, 'body > div:nth-child(4)'))
                )


                detail_soup = bs(driver.page_source, 'html.parser')

                # Extract additional details

                # Description
                try:
                    description_elem = detail_soup.select_one(
                        "div.card.-mx-content > div:not(:has(table))"
                    )
                    description = description_elem.get_text(strip=True) if description_elem else None
                except Exception as e:
                    print(f'Error extracting description for {title}: {e}')
                    description = None

                # Persons info : Starring, directors an d producer
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

                # Production
                try:
                    production = None

                    production_elem_span = detail_soup.select_one(
                        "div.flex.gap-x-1.items-center span[title] + span"
                    )
                    if production_elem_span:
                        production = production_elem_span.get_text(strip=True).rstrip('|')

                    if not production:
                        production_elem_div = detail_soup.select_one(
                            "div.flex.flex-wrap.gap-x-1.text-sm > div:nth-child(4)"
                        )
                        if production_elem_div:
                            text = production_elem_div.get_text(strip=True).rstrip('|')
                            if text != genre:
                                production = text

                except Exception as e:
                    print(f'Error extracting production for {title}: {e}')
                    production = None

                # Sub genre : check production exists -> to determine production location
                try:
                    genre_position = 6 if production else 5
                    sub_genre = detail_soup.select_one(
                        f"div.flex.flex-wrap.gap-x-1.text-sm.leading-6.text-gray-500 > div:nth-child({genre_position})"
                    ).get_text(strip=True).rstrip('|')
                except Exception as e:
                    print(f'Error extracting sub_genre for {title}: {e}')
                    sub_genre = None

                # IMDB
                imdb = detail_soup.select_one(
                    "div.flex.flex-wrap.justify-around.text-center > div.px-2.py-4.w-32 > div.mb-1.text-2xl.text-gray-400"
                ).get_text(strip=True).split('/')[0]
                

                # Rotten Tomatoes
                rotten_tomatos = detail_soup.select_one(
                    "div.flex.flex-wrap.justify-around.text-center > div.px-2.py-4.w-40 > div.mb-1.text-2xl.text-gray-400"
                ).get_text(strip=True).rstrip('%')

                # Get poster URL
                try:
                    poster_elem = driver.find_element(
                        By.XPATH,
                        "/html/body/div[4]/div/div[1]/div/div/picture/img"
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
                            # Get OTT name after 'on'
                            text = span.get_text(strip=True)
                            match = text.rsplit(" on ", 1)[-1].strip()
                            if match:
                                streamings.append(match)
                else:
                    print(f"No Streaming tab for {title}")
                
                # Store the crawled data into data frame
                data = {
                    'Rank':rank,
                    'Title' : title, 
                    'Type' : type, 
                    'Release' : release, 
                    'Genre' : genre, 
                    'Country' : country, 
                    'Hours' : hours, 
                    'Runtime' : runtime, 
                    'Views' : views, 
                    'Description' : description,
                    'Starring' : starring,
                    'Directors' : directors, 
                    'Produced_by' : produced_by, 
                    'Sub_genre' : sub_genre, 
                    'IMDB' : imdb, 
                    'Rotten_Tomatoes' : rotten_tomatos,
                    'Poster' : poster, 
                    'Half_Year' : half_year, 
                    'Streaming' : streamings, 
                    'Production': production
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