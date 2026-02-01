import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time

def scrape_racing_post():
    base_url = "https://www.racingpost.com"
    news_url = "https://www.racingpost.com/news/"
    
    # 模擬真人瀏覽器，否則會被阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"正在存取: {news_url}")
    response = requests.get(news_url, headers=headers)
    if response.status_code != 200:
        print(f"無法存取網頁，狀態碼: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Racing Post 的新聞標題通常在具有特定 class 的 <a> 標籤內
    # 這裡使用 select 尋找含有 /news/ 路徑的連結
    links = []
    for a in soup.select('a[href*="/news/"]'):
        href = a['href']
        # 排除掉純 /news/ 首頁連結與重複項
        if href != '/news/' and href not in links:
            if href.startswith('/'):
                links.append(base_url + href)
            elif href.startswith('http'):
                links.append(href)
    
    # 只取前 5 則新聞避免執行過久
    links = list(dict.fromkeys(links))[:5] 
    print(f"找到 {len(links)} 則新聞連結")

    results = []
    for link in links:
        try:
            print(f"正在抓取全文: {link}")
            res = requests.get(link, headers=headers)
            detail_soup = BeautifulSoup(res.text, 'html.parser')
            
            # 抓取標題：通常在 <h1>
            title = detail_soup.find('h1').get_text(strip=True) if detail_soup.find('h1') else "無標題"
            
            # 抓取全文：Racing Post 的內文通常在 p 標籤中
            # 我們尋找包含文章內容的容器，通常是 article 或特定的 div
            paragraphs = detail_soup.find_all('p')
            # 過濾掉太短或不相關的文字（可根據需求調整）
            content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 30])
            
            results.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title": title,
                "link": link,
                "full_text": content
            })
            
            # 休息 2 秒，避免被封鎖
            time.sleep(2)
            
        except Exception as e:
            print(f"抓取 {link} 時發生錯誤: {e}")

    if results:
        df = pd.DataFrame(results)
        os.makedirs('data', exist_ok=True)
        # 檔名包含日期
        filename = f"data/racing_post_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"成功儲存至 {filename}")
    else:
        print("未抓取到任何資料")

if __name__ == "__main__":
    scrape_racing_post()
