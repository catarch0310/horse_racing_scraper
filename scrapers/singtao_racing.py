import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_singtao_time(time_str):
    """
    處理星島的相對時間：'11小時前', '昨日', '2分鐘前'
    """
    now = datetime.now()
    time_str = time_str.strip()
    
    if '分鐘前' in time_str:
        num = re.search(r'\d+', time_str)
        return now - timedelta(minutes=int(num.group())) if num else now
    elif '小時前' in time_str:
        num = re.search(r'\d+', time_str)
        return now - timedelta(hours=int(num.group())) if num else now
    elif '昨日' in time_str:
        return now - timedelta(days=1)
    elif '前日' in time_str:
        return now - timedelta(days=2)
    elif '-' in time_str: # 處理日期格式如 2026-02-09
        try:
            return datetime.strptime(time_str, "%Y-%m-%d")
        except:
            return now
    return now

def scrape():
    # 馬圈快訊網址
    news_url = "https://www.stheadline.com/realtime-racing/%E9%A6%AC%E5%9C%88%E5%BF%AB%E8%A8%8A"
    base_url = "https://www.stheadline.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動星島頭條 (馬圈快訊) 抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        
        if res.status_code != 200:
            print(f"    ❌ 星島請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()
        threshold = datetime.now() - timedelta(hours=48)

        # 根據截圖二，新聞內容在 class="news-detail" 內
        # 我們尋找所有的新聞區塊
        articles = soup.select('.news-detail')
        print(f"    找到 {len(articles)} 個新聞區塊，開始解析...")

        for art in articles:
            # 1. 抓取標題 (在 class="title" 內)
            title_node = art.select_one('.title')
            # 2. 抓取連結 (向上或向下找 a 標籤)
            link_node = art.find_previous('a') or art.find('a') or art.parent
            # 3. 抓取時間 (在 class="time" 內)
            time_node = art.select_one('.time')

            if title_node and link_node and time_node:
                title = title_node.get_text(strip=True)
                link = link_node.get('href', '')
                time_text = time_node.get_text(strip=True)
                
                # 補全連結
                if link.startswith('/'):
                    link = base_url + link
                
                if link in seen_links or not title:
                    continue
                
                pub_date = parse_singtao_time(time_text)
                
                if pub_date >= threshold:
                    seen_links.add(link)
                    extracted_data.append({
                        "title": title,
                        "link": link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M") + f" ({time_text})"
                    })

        print(f"    ✅ 星島抓取完成，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ 星島執行出錯: {e}")
        return []
