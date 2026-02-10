import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_racenet_time(time_str):
    """
    處理 Racenet 的時間格式：
    '2 hours ago', '7 hours ago', 'a day ago', '30 mins ago'
    """
    now = datetime.now()
    time_str = time_str.lower().strip()
    
    try:
        num_match = re.search(r'\d+', time_str)
        num = int(num_match.group()) if num_match else 1
        
        if 'min' in time_str:
            return now - timedelta(minutes=num)
        elif 'hour' in time_str:
            return now - timedelta(hours=num)
        elif 'day' in time_str:
            return now - timedelta(days=num)
    except:
        pass
    return now

def scrape():
    news_url = "https://www.racenet.com.au/news"
    base_url = "https://www.racenet.com.au"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Racenet (澳洲) 新聞抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ Racenet 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()
        threshold = datetime.now() - timedelta(hours=36)

        # 根據截圖，新聞項目通常是包含 news-item 類別的 a 標籤
        articles = soup.find_all('a', class_=re.compile(r'news-item'))
        
        if not articles:
            # 備援：搜尋所有包含標題類別的 div，再往上找連結
            title_nodes = soup.select('.news-item__title')
            articles = [node.find_parent('a') for node in title_nodes if node.find_parent('a')]

        print(f"    找到 {len(articles)} 個潛在新聞區塊，開始解析...")

        for a in articles:
            link = a.get('href', '')
            if not link: continue
            full_link = base_url + link if link.startswith('/') else link
            
            if full_link in seen_links: continue
            
            # 抓取標題 (div.news-item__title)
            title_node = a.select_one('.news-item__title')
            title = title_node.get_text(strip=True) if title_node else a.get_text(strip=True)
            
            # 抓取時間 (通常在標題下方的作者旁，包含 'ago' 的文字)
            time_node = a.find(string=re.compile(r'ago|day', re.I))
            time_text = time_node.strip() if time_node else "0 hours ago"
            
            if len(title) > 10:
                pub_date = parse_racenet_time(time_text)
                
                if pub_date >= threshold:
                    seen_links.add(full_link)
                    extracted_data.append({
                        "title": title,
                        "link": full_link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M")
                    })

        print(f"    ✅ Racenet 抓取成功，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Racenet 執行錯誤: {e}")
        return []