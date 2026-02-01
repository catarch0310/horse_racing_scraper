import requests
from bs4 import BeautifulSoup
import re

def scrape():
    base_url = "https://www.racingpost.com"
    news_url = "https://www.racingpost.com/news/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    res = requests.get(news_url, headers=headers)
    if res.status_code != 200:
        return []

    soup = BeautifulSoup(res.text, 'html.parser')
    # 使用你之前成功的正規表達式
    article_links = soup.find_all('a', attrs={'data-testid': re.compile(r'Link__.*__Article')})
    
    extracted_data = []
    seen_titles = set()

    for a in article_links:
        link = a.get('href', '')
        full_link = base_url + link if link.startswith('/') else link
        img = a.find('img')
        title = img.get('alt', '').strip() if img and img.get('alt') else a.get_text(strip=True)
            
        if title and len(title) > 10 and title not in seen_titles:
            seen_titles.add(title)
            extracted_data.append({
                "title": title,
                "link": full_link
            })
    return extracted_data # 這裡回傳 list，交給 main.py 處理
