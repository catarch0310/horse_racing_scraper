import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_scmp_date(date_str):
    if not date_str: return None
    try:
        # 處理格式: 1 Feb 2026 - 7:30 AM
        clean_date = date_str.strip().replace('Updated: ', '').split('\n')[0]
        return datetime.strptime(clean_date, "%d %b %Y - %I:%M %p")
    except Exception:
        return None

def scrape():
    base_url = "https://www.scmp.com"
    news_url = "https://www.scmp.com/sport/racing/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    res = requests.get(news_url, headers=headers)
    if res.status_code != 200: return []

    soup = BeautifulSoup(res.text, 'html.parser')
    extracted_data = []
    seen_links = set()
    threshold = datetime.now() - timedelta(hours=100) # 先放寬到 100 小時測試

    # --- 1. 專攻大頭條 (Hero Section) ---
    # SCMP 的頭條連結通常在 h1 裡面
    hero_h1 = soup.find('h1')
    if hero_h1:
        a_tag = hero_h1.find('a', href=True)
        if a_tag:
            title = a_tag.get_text(strip=True)
            link = base_url + a_tag['href'] if a_tag['href'].startswith('/') else a_tag['href']
            # 頭條的時間通常在同一個父容器的 .article-lv1__timestamp 或 .timestamp 裡
            # 我們直接搜尋整頁的第一個 timestamp
            time_tag = soup.select_one('[class*="timestamp"]')
            
            if time_tag:
                pub_date = parse_scmp_date(time_tag.get_text(strip=True))
                if pub_date and pub_date >= threshold:
                    seen_links.add(link)
                    extracted_data.append({
                        "title": f"[HEADLINE] {title}",
                        "link": link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M")
                    })
                    print(f"成功抓到頭條: {title}")

    # --- 2. 抓取其他所有馬經新聞連結 ---
    # 尋找所有包含馬經文章路徑的 a 標籤
    article_links = soup.find_all('a', href=re.compile(r'/sport/racing/article/'))
    
    for a in article_links:
        link = a.get('href', '')
        full_link = base_url + link if link.startswith('/') else link
        if full_link in seen_links: continue
        
        # 往上找父容器來獲取標題與時間
        container = a.find_parent(['div', 'article'])
        if not container: continue
        
        title_node = container.find(['h2', 'h3'])
        time_node = container.select_one('[class*="timestamp"]')
        
        if title_node and time_node:
            title = title_node.get_text(strip=True)
            pub_date = parse_scmp_date(time_node.get_text(strip=True))
            
            if pub_date and pub_date >= threshold:
                seen_links.add(full_link)
                extracted_data.append({
                    "title": title,
                    "link": full_link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M")
                })
    
    return extracted_data
