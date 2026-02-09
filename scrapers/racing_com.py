import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_racing_com_time(time_str):
    """
    處理 Racing.com 的時間格式：
    '25 MINS AGO', '3 HRS AGO', 'YESTERDAY'
    """
    now = datetime.now()
    time_str = time_str.upper().strip()
    
    try:
        if 'MINS AGO' in time_str or 'MIN AGO' in time_str:
            num = re.search(r'\d+', time_str)
            return now - timedelta(minutes=int(num.group())) if num else now
        
        elif 'HRS AGO' in time_str or 'HR AGO' in time_str:
            num = re.search(r'\d+', time_str)
            return now - timedelta(hours=int(num.group())) if num else now
        
        elif 'YESTERDAY' in time_str:
            return now - timedelta(days=1)
        
        else:
            # 處理其他可能的日期格式
            return now
    except:
        return now

def scrape():
    news_url = "https://www.racing.com/news/latest-news"
    base_url = "https://www.racing.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Racing.com (澳洲) 新聞抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ Racing.com 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()
        threshold = datetime.now() - timedelta(hours=36)

        # 根據截圖，新聞在 article-card 中
        # 我們尋找所有的新聞卡片容器
        articles = soup.select('.component.article-card')
        print(f"    找到 {len(articles)} 個新聞區塊，開始解析...")

        for art in articles:
            # 1. 抓取標題 (h4.article-card__title)
            title_node = art.select_one('.article-card__title')
            # 2. 抓取連結 (a.link)
            link_node = art.select_one('a.link')
            # 3. 抓取時間 (通常在 .article-card__brand-tags 附近或包含 AGO 的文字)
            # 觀察圖一，時間文字通常在標籤下方
            time_node = art.find(string=re.compile(r'AGO|YESTERDAY', re.I))

            if title_node and link_node:
                title = title_node.get_text(strip=True)
                link = link_node.get('href', '')
                if link.startswith('/'): link = base_url + link
                
                if link in seen_links: continue
                
                time_text = time_node.strip() if time_node else "0 MINS AGO"
                pub_date = parse_racing_com_time(time_text)
                
                if pub_date >= threshold:
                    seen_links.add(link)
                    extracted_data.append({
                        "title": title,
                        "link": link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M") + f" ({time_text})"
                    })

        print(f"    ✅ Racing.com 抓取成功，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Racing.com 執行錯誤: {e}")
        return []
