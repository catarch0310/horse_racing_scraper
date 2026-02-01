import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

def scrape_news():
    base_url = "https://www.tattersalls.com/news/"  # 替換成目標網站
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    data = []
    
    # 1. 假設頭條標題在 <h3> 標籤內，且裡面有 <a> 連結
    articles = soup.select('h3 a')[:5]  # 只抓前 5 則做範例
    
    for article in articles:
        title = article.get_text(strip=True)
        link = article['href']
        if not link.startswith('http'):
            link = base_url + link
            
        # 2. 進入全文頁面抓取內容
        detail_res = requests.get(link, headers=headers)
        detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
        
        # 假設全文在 <div class="article-body"> 內
        content_tag = detail_soup.select_one('.article-body')
        content = content_tag.get_text(strip=True) if content_tag else "找不到全文"
        
        data.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": title,
            "link": link,
            "content": content
        })
    
    # 3. 儲存成 CSV
    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    filename = f"data/news_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"成功儲存: {filename}")

if __name__ == "__main__":
    scrape_news()
