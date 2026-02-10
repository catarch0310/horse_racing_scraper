import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def extract_smh_date(a_tag):
    """
    從新聞連結附近搜尋日期文字 (Best effort)
    """
    try:
        # 往上找父容器
        parent = a_tag.find_parent(['div', 'article', 'section'])
        if parent:
            # 尋找包含月份或 'ago' 的文字
            pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|ago|updated)'
            time_node = parent.find(string=re.compile(pattern, re.I))
            if time_node:
                return time_node.strip()
    except:
        pass
    return "Latest"

def scrape():
    news_url = "https://www.smh.com.au/sport/racing"
    base_url = "https://www.smh.com.au"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 SMH 全量掃描模式 ---")
    
    extracted_data = []
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ SMH 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        seen_links = set()

        # 策略：尋找所有 data-testid 為 article-link 的 a 標籤
        articles = soup.find_all('a', attrs={'data-testid': 'article-link'})
        print(f"    [Debug] 頁面原始掃描到 {len(articles)} 個連結標籤")

        for a in articles:
            link = a.get('href', '')
            if not link or 'sport/racing' not in link:
                continue
            
            full_link = base_url + link if link.startswith('/') else link
            if full_link in seen_links:
                continue
            
            # 抓取標題
            title = a.get_text(strip=True)
            
            # 如果標題太短，可能是抓到圖片連結，嘗試找附近的 h2/h3/h4
            if len(title) < 10:
                parent = a.find_parent(['div', 'article'])
                if parent:
                    h_node = parent.find(['h2', 'h3', 'h4'])
                    if h_node:
                        title = h_node.get_text(strip=True)

            # 只要標題長度正常 (過濾掉單純的 'Horse racing' 標籤)
            if title and len(title) > 12:
                time_text = extract_smh_date(a)
                seen_links.add(full_link)
                extracted_data.append({
                    "title": title,
                    "link": full_link,
                    "time": time_text
                })
            
            # 限制抓取數量
            if len(extracted_data) >= 25:
                break

        print(f"    ✅ SMH 成功擷取 {len(extracted_data)} 則新聞")

    except Exception as e:
        print(f"    ❌ SMH 執行錯誤: {e}")
        
    return extracted_data