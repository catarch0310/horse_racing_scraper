import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re

def scrape_racing_post():
    base_url = "https://www.racingpost.com"
    news_url = "https://www.racingpost.com/news/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    print(f"正在存取: {news_url}")
    res = requests.get(news_url, headers=headers)
    if res.status_code != 200:
        print(f"存取失敗: {res.status_code}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 根據圖二，目標是 data-testid 包含 "Link__" 且包含 "__Article" 的 a 標籤
    # 使用正規表達式匹配
    article_links = soup.find_all('a', attrs={'data-testid': re.compile(r'Link__.*__Article')})
    
    extracted_data = []
    seen_titles = set()

    for a in article_links:
        link = a.get('href', '')
        if not link.startswith('http'):
            link = base_url + link
            
        # 提取標題邏輯：
        # 1. 優先找 <a> 標籤內 <img> 的 alt 屬性（這通常是最完整的頭條標題，如圖二所示）
        img = a.find('img')
        title = ""
        if img and img.get('alt'):
            title = img.get('alt').strip()
        
        # 2. 如果沒有圖片 alt，則抓取標籤內的純文字
        if not title:
            title = a.get_text(strip=True)
            
        # 過濾掉太短的文字或重複的標題
        if title and len(title) > 10 and title not in seen_titles:
            seen_titles.add(title)
            extracted_data.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title": title,
                "link": link
            })

    if extracted_data:
        df = pd.DataFrame(extracted_data)
        os.makedirs('data', exist_ok=True)
        filename = f"data/racing_post_headlines_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"成功抓取 {len(extracted_data)} 條頭條標題")
        print(df.head()) # 在 Log 中顯示前幾筆
    else:
        print("未能抓取到任何內容，請檢查 data-testid 是否變更")

if __name__ == "__main__":
    scrape_racing_post()
