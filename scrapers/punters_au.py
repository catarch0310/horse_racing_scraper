import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_relative_time(time_str):
    now = datetime.now()
    num = re.search(r'\d+', time_str)
    if not num: return now
    n = int(num.group())
    if 'hour' in time_str: return now - timedelta(hours=n)
    if 'day' in time_str: return now - timedelta(days=n)
    return now

def scrape():
    base_url = "https://www.punters.com.au"
    news_url = "https://www.punters.com.au/news/latest-news/"
    threshold = datetime.now() - timedelta(hours=36)
    
    # 使用更完整的 Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,arm64e/v1,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache'
    }
    
    print(f"--- 啟動 Punters.com.au 穩定抓取 ---")
    
    try:
        session = requests.Session()
        res = session.get(news_url, headers=headers, timeout=20)
        
        if res.status_code != 200:
            print(f"   ❌ Punters 被阻擋，狀態碼: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        # 改用更寬鬆的 CSS 選擇器，尋找任何包含標題與連結的 a 標籤
        articles = soup.find_all('a', class_=re.compile(r'news-tile'))
        extracted_data = []

        for art in articles:
            # 尋找標題文字
            title_node = art.find(['p', 'span', 'h3'], class_=re.compile(r'title'))
            # 尋找時間文字
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
        
        print(f"   ✅ Punters 抓取成功，共 {len(extracted_data)} 則")
        return extracted_data
    except Exception as e:
        print(f"   ❌ Punters 失敗: {e}")
        return []
