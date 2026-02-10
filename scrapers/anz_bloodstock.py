import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def extract_date_text(parent_node):
    """
    從父節點中挖出日期文字 (例如 February 10, 2026)
    """
    # 尋找月份關鍵字
    months_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)'
    text = parent_node.get_text(separator=" ", strip=True)
    match = re.search(rf'{months_pattern}\s+\d+,\s+\d{{4}}', text, re.I)
    return match.group(0) if match else "Latest"

def scrape():
    news_url = "https://www.anzbloodstocknews.com/category/latest-news/"
    base_url = "https://www.anzbloodstocknews.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 ANZ Bloodstock 寬鬆模式抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ ANZ 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()

        # 策略：直接抓取頁面上所有 h4.post-title
        headlines = soup.find_all('h4', class_='post-title')
        print(f"    [Debug] 頁面共掃描到 {len(headlines)} 個標題")

        for h4 in headlines:
            a_tag = h4.find('a')
            if not a_tag: continue
            
            title = a_tag.get_text(strip=True)
            link = a_tag.get('href', '')
            if not link.startswith('http'): link = base_url + link
            
            if link in seen_links: continue

            # 抓取日期 (僅供顯示用途，不再做為過濾條件)
            parent = h4.find_parent(['div', 'article'])
            date_display = "Latest"
            if parent:
                date_display = extract_date_text(parent)

            # 只要標題長度正常就加入
            if len(title) > 10:
                seen_links.add(link)
                extracted_data.append({
                    "title": title,
                    "link": link,
                    "time": date_display
                })
            
            # 達到 10 則就停止，防止抓到側邊欄無關內容
            if len(extracted_data) >= 10:
                break

        print(f"    ✅ ANZ 成功擷取 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ ANZ 執行出錯: {e}")
        return []