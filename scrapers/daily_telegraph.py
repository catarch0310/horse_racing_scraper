import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_dt_time(time_str):
    """
    處理 Daily Telegraph 的時間格式：
    '15 minutes ago', '3 hours ago', 'February 9, 2026'
    """
    now = datetime.now()
    t = time_str.lower().strip()
    try:
        if 'minute' in t or 'min' in t:
            num = re.search(r'\d+', t)
            return now - timedelta(minutes=int(num.group())) if num else now
        elif 'hour' in t or 'hr' in t:
            num = re.search(r'\d+', t)
            return now - timedelta(hours=int(num.group())) if num else now
        elif 'yesterday' in t:
            return now - timedelta(days=1)
        else:
            # 處理 February 9, 2026
            # 移除可能的前綴如 "Updated"
            clean_date = re.sub(r'updated|published', '', t).strip()
            return datetime.strptime(clean_date, "%B %d, %Y")
    except:
        return now

def scrape():
    news_url = "https://www.dailytelegraph.com.au/sport/horse-racing"
    base_url = "https://www.dailytelegraph.com.au"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Daily Telegraph (澳洲大報) 抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ Daily Telegraph 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()
        threshold = datetime.now() - timedelta(hours=36)

        # 策略：抓取所有 class 包含 storyblock_title_link 或 storyblock_standfirst_link 的 a 標籤
        # 這些是你在截圖中識別出的關鍵標籤
        articles = soup.find_all('a', class_=re.compile(r'storyblock_(title|standfirst)_link'))
        print(f"    找到 {len(articles)} 個潛在新聞標籤，開始解析...")

        for a in articles:
            link = a.get('href', '')
            if not link: continue
            full_link = base_url + link if link.startswith('/') else link
            
            if full_link in seen_links: continue
            
            # 標題抓取
            title = a.get_text(strip=True)
            
            # 抓取時間：通常在同一個 storyblock 容器內的 span 或 div 中
            # 往上找父節點，再搜尋包含時間資訊的文字
            time_text = ""
            parent = a.find_parent(['div', 'article'])
            if parent:
                # 尋找包含 'ago' 或 月份單字的文字
                time_node = parent.find(string=re.compile(r'ago|minutes|hours|January|February|March|April|May|June|July|August|September|October|November|December', re.I))
                if time_node:
                    time_text = time_node.strip()

            # 只要標題夠長且網址正確 (排除重複)
            if len(title) > 10 and '/sport/horse-racing/' in full_link:
                pub_date = parse_dt_time(time_text)
                
                if pub_date >= threshold:
                    seen_links.add(full_link)
                    extracted_data.append({
                        "title": title,
                        "link": full_link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M")
                    })

        print(f"    ✅ Daily Telegraph 抓取成功，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Daily Telegraph 執行錯誤: {e}")
        return []
