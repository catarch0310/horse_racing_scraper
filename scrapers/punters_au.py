import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json

def parse_relative_time(time_str):
    now = datetime.now()
    num = re.search(r'\d+', time_str)
    if not num: return now
    n = int(num.group())
    time_str = time_str.lower()
    if 'hour' in time_str: return now - timedelta(hours=n)
    if 'day' in time_str: return now - timedelta(days=n)
    if 'min' in time_str: return now - timedelta(minutes=n)
    return now

def scrape():
    base_url = "https://www.punters.com.au"
    news_url = "https://www.punters.com.au/news/latest-news/"
    threshold = datetime.now() - timedelta(hours=36)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Punters 廣域掃描 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200: return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()

        # 策略：尋找所有連結，只要連結網址包含 '/news/' 且結尾有數字 ID 的，通常就是新聞
        # 例如: /news/straight-arron-goes-for-gold-20260206/
        all_links = soup.find_all('a', href=re.compile(r'/news/.+-\d+/?$'))
        
        print(f"    找到 {len(all_links)} 個潛在連結，開始比對...")

        for a in all_links:
            link = a.get('href', '')
            full_link = base_url + link if link.startswith('/') else link
            
            if full_link in seen_links: continue
            
            # 嘗試在該標籤內或附近找標題
            # 優先找裡面有沒有 <p> 或 <span> 包含文字
            title = a.get_text(strip=True)
            
            # 如果標題太短，試著找它父容器裡的文字
            if len(title) < 10:
                parent = a.find_parent('div')
                if parent:
                    title = parent.get_text(strip=True)

            # 尋找時間文字 (包含 'ago' 的文字)
            # 在 a 標籤周圍搜尋
            time_text = "0 hours ago"
            parent_container = a.find_parent(['div', 'article'])
            if parent_container:
                time_node = parent_container.find(string=re.compile(r'ago'))
                if time_node:
                    time_text = time_node.strip()

            pub_date = parse_relative_time(time_text)
            
            if pub_date >= threshold and len(title) > 10:
                seen_links.add(full_link)
                # 清洗標題，去掉可能抓到的重複時間文字
                clean_title = title.split('ago')[-1] if 'ago' in title else title
                
                extracted_data.append({
                    "title": clean_title[:150], # 限制長度
                    "link": full_link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M")
                })

        return extracted_data

    except Exception as e:
        print(f"    ❌ Punters 執行錯誤: {e}")
        return []
