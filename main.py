from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement
import time
from datetime import datetime, timedelta
import pandas as pd
import re
from dateutil import parser
import os
from concurrent.futures import ThreadPoolExecutor
now = datetime.now()

#a helper function to parse messing dates into meaningful data
def parse_timestamp(ts):
    if not isinstance(ts, str):
        return pd.NaT

    ts = ts.strip().lower()

    # Relative formats
    if 'min' in ts:
        num = int(re.search(r'\d+', ts).group())
        return now - timedelta(minutes=num)
    elif 'h' in ts:
        num = int(re.search(r'\d+', ts).group())
        return now - timedelta(hours=num)
    elif 'd' in ts:
        num = int(re.search(r'\d+', ts).group())
        return now - timedelta(days=num)

    # Try parsing fixed dates (e.g., 8 Jul or 27 Jul 2024)
    try:
        dt = parser.parse(ts, default=now.replace(month=1, day=1))
        
        # If year is missing, parser fills it with 1900, so update it
        if dt.year == 1900:
            dt = dt.replace(year=now.year)
        
        return dt
    except Exception:
        return pd.NaT

options = Options()
options.add_argument('--log-level=3')       # Reduce browser logs
#options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress DevTools log
#options.add_argument('--headless')  # No UI
options.add_argument('--disable-gpu')  # Optional on Windows
options.add_argument('--window-size=1920,1080')  # Needed by some sites
service = Service(executable_path='chromedriver.exe')  #hide logs
driver = webdriver.Chrome(service=service,options=options)

def get_news(driver:webdriver):

    driver.get('https://www.bbc.com/sport/football')
    headlines = []
    links = []
    category_names = []
    category_links = []
    time_stamps = []


    news = driver.find_elements(By.XPATH,'//div[@class="ssrcss-k49uhy-PromoContent exn3ah912"]')
    for el in news:
        try:
            title = el.find_element(By.TAG_NAME, 'a')
            link = title.get_attribute('href')
            headline = title.find_element(By.XPATH, './span/p/span').text

            details = el.find_element(By.XPATH, './/div[@class="ssrcss-1j1rzn0-Stack e1y4nx260"]/div/ul') 
            detail_section = details.find_element(By.XPATH, './li')

            try:
                category = detail_section.find_element(By.XPATH, './div/span/a')
                category_link = category.get_attribute('href')
                category_name = category.text
            except:
                category = None
                category_link = None
                category_name = None
                
            
            time_stamp = details.find_element(By.XPATH,'.//span[@aria-hidden="true"]').text.strip()
            
            time_stamp = parse_timestamp(time_stamp)   #parse the time format
        


            headlines.append(headline)
            links.append(link)
            category_names.append(category_name)
            category_links.append(category_link)
            time_stamps.append(time_stamp)

        
        except Exception as e:
            continue


            
    df = pd.DataFrame(
        {
            'headline' : headlines,
            'link' : links,
            'category_name' : category_names,
            'category_link' : category_links,
            'time_stamp' : time_stamps
        }
    )

    df.sort_values(by='time_stamp')
    df.sort_values(by='time_stamp',ascending=False)

    print(df.head())
    report_date =  datetime.now().strftime("%Y-%m-%d_%H-%M")
    df.to_csv(f'football_news_report-{report_date}.csv')


    
def fetch_scores(day: WebElement,label:str):
    start_time = time.time()

    # Reduce implicit wait to speed up "optional" elements
    driver.implicitly_wait(1)

    sections = day.find_elements(By.XPATH, '//div[@class="ssrcss-1ox7t1a-Container ea54ukl1"]')
    print("here")
    print(day.text)

    titles = []
    title_hrefs = []
    club1_names = []
    club2_names = []
    timings = []
    aggs = []
    home_scores = []
    away_scores = []
    minutes = []
    postponeds = []

    for section in sections:
        # Title
        title_section = section.find_elements(By.XPATH, './div')
        title_section = title_section[0] if title_section else None

        title = title_section.find_elements(By.XPATH, './/h2') if title_section else []
        title = title[0] if title else None
        title_text = title.text if title else None

        # Href
        title_href_elem = title.find_elements(By.XPATH, './div/a') if title else []
        title_href = title_href_elem[0].get_attribute('href') if title_href_elem else None

        # Matches
        matches_section = section.find_elements(By.XPATH, './ul')
        if not matches_section:
            continue
        matches = matches_section[0].find_elements(By.XPATH, './li')

        for match in matches:
            match_data = match.find_elements(By.XPATH, './/div[@class="ssrcss-1bjtunb-GridContainer e1efi6g55"]')
            if not match_data:
                continue
            match_data = match_data[0]

            # Clubs
            club1 = match_data.find_elements(By.XPATH, './div[@class="ssrcss-bon2fo-WithInlineFallback-TeamHome e1efi6g53"]')
            club1_name = club1[0].find_element(By.XPATH, './/span[@class="ssrcss-1p14tic-DesktopValue emlpoi30"]').text if club1 else None

            club2 = match_data.find_elements(By.XPATH, './div[@class="ssrcss-nvj22c-WithInlineFallback-TeamAway e1efi6g52"]')
            club2_name = club2[0].find_element(By.XPATH, './/span[@class="ssrcss-1p14tic-DesktopValue emlpoi30"]').text if club2 else None

            # Timing (optional)
            timing = match_data.find_elements(By.XPATH, './div[@class="ssrcss-y5s079-WithInlineFallback-Scores e1efi6g51"]/div/time')
            timing = timing[0].text if timing else None

            # Match detail block
            match_details = match_data.find_elements(By.XPATH, './div[@class="ssrcss-xxm013-MatchProgressContainer e1efi6g50"]')
            match_details = match_details[0] if match_details else None

            # Aggregate score
            agg = match_data.find_elements(By.XPATH, './/div[@data-testid="agg-score"]')
            agg = agg[0].text if agg else None

            # Fulltime scores
            home_score_elem = match_data.find_elements(By.XPATH, './/div[@class="ssrcss-qsbptj-HomeScore e56kr2l2"]')
            away_score_elem = match_data.find_elements(By.XPATH, './/div[@class="ssrcss-fri5a2-AwayScore e56kr2l1"]')
            score_home = home_score_elem[0].text if home_score_elem else None
            score_away = away_score_elem[0].text if away_score_elem else None

            # Minute and Postponed
            minute_elem = match_details.find_elements(By.XPATH, './/div[@class="ssrcss-1v84ueh-StyledPeriod e307mhr0"]') if match_details else []
            minute = minute_elem[0].text if minute_elem else None

            postponed_elem = match_details.find_elements(By.XPATH, './/div[@class="ssrcss-msb9pu-StyledPeriod e307mhr0"]') if match_details else []
            postponed = True if postponed_elem else False

            # Append data
            titles.append(title_text)
            title_hrefs.append(title_href)
            club1_names.append(club1_name)
            club2_names.append(club2_name)
            timings.append(timing)
            aggs.append(agg)
            home_scores.append(score_home)
            away_scores.append(score_away)
            minutes.append(minute)
            postponeds.append(postponed)

            print('match done')

    print("heeeeeeeere")
    df = pd.DataFrame({
        "titles": titles,
        "title_hrefs": title_hrefs,
        "club1_names": club1_names,
        "club2_names": club2_names,
        "timings": timings,
        "aggs": aggs,
        "home_scores": home_scores,
        "away_scores": away_scores,
        "minutes": minutes,
        "postponeds": postponeds,
    })

    formatted_date = datetime.now().strftime("%d_%m_%Y")

    df.to_csv(f'matches_{label}_relative_{formatted_date}.csv',index=False)
    print(f"Time taken: {time.time() - start_time:.2f}s")
        



def scrape_day(label):
    driver = webdriver.Chrome()
    driver.get("https://www.bbc.com/sport/football/scores-fixtures/")
    time.sleep(3)  # Let the page load

    today_tab = driver.find_element(By.XPATH, '//div[@data-content="Today"]')
    
    if label == "Today":
        tab = today_tab
    elif label == "Yesterday":
        tab = driver.find_element(By.XPATH, '//div[@data-content="Today"]/../../../preceding-sibling::li[1]')
    elif label == "Tomorrow":
        tab = driver.find_element(By.XPATH, '//div[@data-content="Today"]/../../../following-sibling::li[1]')
    else:
        driver.quit()
        return

    # Click the correct tab (except Today)
    if label != "Today":
        ActionChains(driver).move_to_element(tab).click().perform()
        time.sleep(2)

    fetch_scores(tab,label)
    driver.quit()



def scrape_all_days():
    labels = ["Yesterday", "Today", "Tomorrow"]
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(scrape_day, labels)
            
        
            
scrape_all_days()


time.sleep(5)


driver.quit()

