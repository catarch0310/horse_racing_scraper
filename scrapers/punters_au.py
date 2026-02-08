import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_relative_time(time_str):
    now = datetime.now()
    time_str = time_str.lower().strip()
    number = re.search(r'\d+', time_str)
    if not number: return now
    n = int(number.group())
    if 'hour' in time_str: return now - timedelta(hours=n)
    if 'day' in time_str: return now - timedelta(days=n)
    return now

def scrape():
    base_url = "https://www.punters.com.au"
    news_url = "https://www.punters.com.au/news/latest-news/"
    # 設定 36 小時門檻
    threshold = datetime.now() - timedelta(hours=36)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Punters.com.au 簡單抓取 (第一頁) ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Punters 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        # 標題與連結通常在帶有 news-tile 類別的 a 標籤或 div 內
        articles = soup.select('a.news-tile')
        extracted_data = []

        for art in articles:
            title_node = art.select_one('.news-tile__title')
            time_node = art.find(string=re.compile(r'ago'))
            
            if title_node and time_node:
                title = title_node.get_text(strip=True)
                time_text = time_node.strip()
                pub_date = parse_relative_time(time_text)
                
                if pub_date >= threshold:
                    link = art.get('href', '')
                    extracted_data.append({
                        "title": title,
                        "link": base_url + link if link.startswith('/') else link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M")
                    })
        
        print(f"Punters 成功抓取 {len(extracted_data)} 則新聞。")
        return extracted_data
    except Exception as e:
        print(f"Punters 失敗: {e}")
        return []
