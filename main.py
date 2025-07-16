from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta
import pandas as pd
import re
from dateutil import parser

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


service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service)


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

time.sleep(5)


driver.quit()

