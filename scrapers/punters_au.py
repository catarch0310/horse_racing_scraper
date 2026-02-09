import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_relative_time(time_str):
    now = datetime.now()
    # 找尋數字 (例如 '10' hours ago)
    number = re.search(r'\d+', time_str)
    if not number: return now
    n = int(number.group())
    
    time_str = time_str.lower()
    if 'hour' in time_str: return now - timedelta(hours=n)
    if 'day' in time_str: return now - timedelta(days=n)
    if 'min' in time_str: return now - timedelta(minutes=n)
    return now

def scrape():
    base_url = "https://www.punters.com.au"
    news_url = "https://www.punters.com.au/news/latest-news/"
    # 36小時門檻
    threshold = datetime.now() - timedelta(hours=36)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,arm64e/v1,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print(f"--- 正在嘗試抓取 Punters 第一頁 ---")
    
    try:
        session = requests.Session()
        # 先造訪一次首頁建立 Session/Cookie
        session.get(base_url, headers=headers, timeout=10)
        
        # 真正抓取新聞頁
        res = session.get(news_url, headers=headers, timeout=15)
        
        if res.status_code != 200:
            print(f"    ❌ Punters 被擋 (HTTP {res.status_code})")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        # 尋找所有包含新聞的 a 標籤
        articles = soup.find_all('a', class_=re.compile(r'news-tile'))
        
        extracted_data = []
        for art in articles:
            # 抓標題 (通常在 .news-tile__title)
            title_node = art.find(['p', 'span', 'h3'], class_=re.compile(r'title'))
            # 抓時間文字 (包含 'ago' 的字串)
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
        
        if not extracted_data:
            # 如果抓不到，印出前 200 字原始碼 Debug
            print(f"    ⚠️ 抓不到標籤，網頁內容預覽: {res.text[:200]}")
            
        return extracted_data

    except Exception as e:
        print(f"    ❌ Punters 錯誤: {e}")
        return []
