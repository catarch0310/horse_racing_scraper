import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def parse_ttr_date(date_str):
    """
    處理 TTR 的日期格式：'Tuesday 10th February' 或 'February 10th 2026'
    """
    if not date_str:
        return datetime.now()
    try:
        # 移除日期後的 st, nd, rd, th
        clean_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str.strip())
        
        # 情況 A: Tuesday 10 February (補上今年)
        if any(day in clean_date for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
            current_year = datetime.now().year
            return datetime.strptime(f"{clean_date} {current_year}", "%A %d %B %Y")
        
        # 情況 B: February 10 2026
        return datetime.strptime(clean_date, "%B %d %Y")
    except:
        return datetime.now()

def scrape():
    news_url = "https://www.ttrausnz.com.au"
    base_url = "https://www.ttrausnz.com.au"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 TTR AusNZ 廣域解析模式 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200: return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()
        
        # 策略：抓取所有連結，只要連結包含 /edition/ 且有日期格式
        # 例如: /edition/2026-02-10/sale-toppers-colts-take-charge...
        edition_links = soup.find_all('a', href=re.compile(r'^/edition/\d{4}-\d{2}-\d{2}/'))
        
        print(f"    [Debug] 發現 {len(edition_links)} 個符合格式的新聞連結")

        for a in edition_links:
            link = a.get('href', '')
            if not link: continue
            full_link = base_url + link if link.startswith('/') else link
            
            if full_link in seen_links: continue
            seen_links.add(full_link)

            # 1. 抓取標題
            # 優先找內部的 h4 或 h3，如果都沒有，則抓 a 標籤本身的 text
            title_node = a.find(['h4', 'h3', 'p'])
            title = title_node.get_text(strip=True) if title_node else a.get_text(strip=True)
            
            # 2. 抓取日期
            # 根據截圖，日期通常在 a 標籤內部的某個 div 裡
            date_text = ""
            date_node = a.find('div', class_=re.compile(r'date', re.I))
            if date_node:
                date_text = date_node.get_text(strip=True)
            
            # 3. 如果標題太短（可能是廣告或圖片文字），則跳過
            if len(title) < 10: continue

            pub_date = parse_ttr_date(date_text)
            
            extracted_data.append({
                "title": title,
                "link": full_link,
                "time": pub_date.strftime("%Y-%m-%d")
            })

        print(f"    ✅ TTR 抓取完成，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ TTR 失敗: {e}")
        return []