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

def get_score(driver:webdriver):
    driver.get('https://www.bbc.com/sport/football/scores-fixtures/')
    
    driver.implicitly_wait(10)
    
    time.sleep(3)
    def fetch_scores(day:WebElement):
        sections = day.find_elements(By.XPATH,'//div[@class="ssrcss-1ox7t1a-Container ea54ukl1"]')
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
            
            try:
                title_section = section.find_element(By.XPATH,'./div')
            except:
                title_section = None
                
            try:
                title = title_section.find_element(By.XPATH,'.//h2')
            except:
                title = None
                
            
            try:
                title_href = title.find_element(By.XPATH,'./div/a').get_attribute('href')
            except:
                title_href = None
            if title.text:
                title_text = title.text
            else:
                title_text = None
            
            

            matches_section = section.find_element(By.XPATH,'./ul')
            matches = matches_section.find_elements(By.XPATH,'./li')
          
            
            for match in matches:

                match_data = match.find_element(By.XPATH,'.//div[@class="ssrcss-1bjtunb-GridContainer e1efi6g55"]')
                club1 = match_data.find_element(By.XPATH,'./div[@class="ssrcss-bon2fo-WithInlineFallback-TeamHome e1efi6g53"]')
                club1_name = club1.find_element(By.XPATH,'.//span[@class="ssrcss-1p14tic-DesktopValue emlpoi30"]')

                club2 =  match_data.find_element(By.XPATH,'./div[@class="ssrcss-nvj22c-WithInlineFallback-TeamAway e1efi6g52"]')
                club2_name = club2.find_element(By.XPATH,'.//span[@class="ssrcss-1p14tic-DesktopValue emlpoi30"]')

                
                
                try:   #check if still in future
                    timing = match_data.find_element(By.XPATH,'./div[@class="ssrcss-y5s079-WithInlineFallback-Scores e1efi6g51"]/div/time')
                except:
                    timing = None

                match_details = match_data.find_element(By.XPATH,'./div[@class="ssrcss-xxm013-MatchProgressContainer e1efi6g50"]')
                
                try:  #check if there is an agg score
                    agg = match_data.find_element(By.XPATH,'.//div[@data-testid="agg-score"]') 
                except:
                    agg = None

                try: #check if the match is over
                    score_home = match_data.find_element(By.XPATH,'.//div[@class="ssrcss-qsbptj-HomeScore e56kr2l2"]')
                    score_away = match_data.find_element(By.XPATH,'.//div[@class="ssrcss-fri5a2-AwayScore e56kr2l1"]')
                except:
                    score_home = score_away = None
                
                try:
                    minute = match_details.find_element(By.XPATH,'.//div[@class="ssrcss-1v84ueh-StyledPeriod e307mhr0"]')
                except Exception:
                    minute = None
                
                try:
                    postponed = match_details.find_element(By.XPATH,'.//div[@class="ssrcss-msb9pu-StyledPeriod e307mhr0"]')
                except:
                    postponed=None
                



                #append to the lists
                titles.append(title) 
                title_hrefs.append(title_href) 
                club1_names.append(club1_name) 
                club2_names.append(club2_name) 
                timings.append(timing) 
                aggs.append(agg) 
                home_scores.append(score_home) 
                away_scores.append(score_away) 
                minutes.append(minute) 
                postponeds.append(True if postponed else False) 
                print('match done')

            
        df = pd.DataFrame({
            "titles" : titles,
            "title_hrefs" : title_hrefs,
            "club1_names" : club1_names,
            "club2_names" : club2_names,
            "timings" : timings,
            "aggs" : aggs,
            "home_scores" : home_scores,
            "away_scores" : away_scores,
            "minutes" : minutes,
            "postponeds" : postponeds,
        })

        df.to_excel(f'mathces_{day}.xlsx')
            

        

        
    today = driver.find_element(By.XPATH,'//div[@data-content="Today"]')
    yesterday = driver.find_element(By.XPATH,'//div[@data-content="Today"]/../../../preceding-sibling::li[1]')
    tommorow  = driver.find_element(By.XPATH,'//div[@data-content="Today"]/../../../following-sibling::li[1]')

    #call with today
    fetch_scores(today)
    #move to yesterday
    chain = ActionChains(driver=driver)
    chain.move_to_element(yesterday)
    chain.click().perform()
    time.sleep(2)
    fetch_scores(yesterday)
    #move to tommorow
    chain = ActionChains(driver=driver)
    chain.move_to_element(tommorow)
    chain.click().perform()
    time.sleep(2)
    fetch_scores(tommorow)

    
            
        
            
get_score(driver)


time.sleep(5)


driver.quit()

