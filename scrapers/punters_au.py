from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re, time

def parse_relative_time(time_str):
    now = datetime.now()
    number = re.search(r'\d+', time_str)
    if not number: return now
    n = int(number.group())
    if 'hour' in time_str: return now - timedelta(hours=n)
    if 'day' in time_str: return now - timedelta(days=n)
    return now

def scrape():
    base_url = "https://www.punters.com.au"
    news_url = f"{base_url}/news/latest-news/"
    threshold = datetime.now() - timedelta(hours=36)
    
    extracted_data = []
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # 增加 timeout 到 60 秒
            page.goto(news_url, timeout=60000)
            
            # 多捲動幾次確保內容載入
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3) 

            soup = BeautifulSoup(page.content(), 'html.parser')
            articles = soup.select('a.news-tile')
            
            for art in articles:
                title_node = art.select_one('.news-tile__title')
                time_node = art.find(string=re.compile(r'ago'))
                if title_node and time_node:
                    title = title_node.get_text(strip=True)
                    pub_date = parse_relative_time(time_node.strip())
                    if pub_date >= threshold:
                        link = art.get('href', '')
                        extracted_data.append({
                            "title": title,
                            "link": base_url + link if link.startswith('/') else link,
                            "time": pub_date.strftime("%Y-%m-%d %H:%M")
                        })
            browser.close()
        except Exception as e:
            print(f"Punters Playwright 錯誤: {e}")
            
    return extracted_data
