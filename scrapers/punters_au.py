import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_relative_time(time_str):
    """
    將 '10 hours ago', '1 day ago', '30 mins ago' 轉換為 datetime
    """
    now = datetime.now()
    time_str = time_str.lower().strip()
    
    # 提取數字
    number = re.search(r'\d+', time_str)
    if not number:
        return now
    
    n = int(number.group())
    
    if 'min' in time_str:
        return now - timedelta(minutes=n)
    elif 'hour' in time_str:
        return now - timedelta(hours=n)
    elif 'day' in time_str:
        return now - timedelta(days=n)
    
    return now

def scrape():
    base_url = "https://www.punters.com.au"
    news_url = "https://www.punters.com.au/news/latest-news/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Punters.com.au 抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Punters 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        
        # 設定 36 小時門檻
        threshold = datetime.now() - timedelta(hours=36)

        # 根據截圖，新聞項目在 a.news-tile 標籤中
        articles = soup.select('a.news-tile')
        print(f"找到 {len(articles)} 個新聞區塊，進行時間檢查...")

        for art in articles:
            # 1. 抓取標題
            title_node = art.select_one('.news-tile__title')
            if not title_node:
                continue
            title = title_node.get_text(strip=True)
            
            # 2. 抓取連結
            link = art.get('href', '')
            if link.startswith('/'):
                link = base_url + link
                
            # 3. 抓取時間並轉換 (通常在 .news-tile__meta 或包含 'ago' 的文字中)
            # 根據截圖，時間通常在標題下方的 meta 資訊中
            time_node = art.select_one('.news-tile__date, .news-tile__meta, span')
            # 如果上面的 selector 沒抓到，我們找包含 'ago' 文字的標籤
            if not time_node:
                time_node = art.find(string=re.compile(r'ago'))
            
            time_text = time_node.get_text(strip=True) if time_node else "0 hours ago"
            pub_date = parse_relative_time(time_text)
            
            # 4. 36 小時過濾
            if pub_date >= threshold:
                extracted_data.append({
                    "title": title,
                    "link": link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M") + f" ({time_text})"
                })

        print(f"Punters 抓取完成，符合 36 小時內的新聞共 {len(extracted_data)} 則")
        return extracted_data

    except Exception as e:
        print(f"Punters 執行失敗: {e}")
        return []
