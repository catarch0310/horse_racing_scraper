import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def parse_scmp_date(date_str):
    if not date_str: return None
    try:
        # SCMP 格式: 31 Jan 2026 - 4:53 PM
        clean_date = date_str.strip()
        # 有些時間會包含 "Updated:" 字樣，需移除
        clean_date = clean_date.replace('Updated: ', '')
        return datetime.strptime(clean_date, "%d %b %Y - %I:%M %p")
    except Exception:
        return None

def scrape():
    base_url = "https://www.scmp.com"
    news_url = "https://www.scmp.com/sport/racing/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    res = requests.get(news_url, headers=headers)
    if res.status_code != 200: return []

    soup = BeautifulSoup(res.text, 'html.parser')
    extracted_data = []
    seen_links = set()
    
    # 48 小時過濾 (測試時可自行改回 500)
    threshold = datetime.now() - timedelta(hours=48)

    # 策略：抓取所有帶有時間戳記的文章區塊
    # SCMP 的文章區塊通常包裹在含有 "article" 關鍵字的 div 或 article 標籤中
    # 我們直接尋找所有包含連結且旁邊有時間戳的容器
    
    # 先處理最上方的大頭條 (通常在 h1)
    hero_title_node = soup.find('h1')
    if hero_title_node:
        a_tag = hero_title_node.find('a')
        # 尋找與 h1 最近的時間標籤 (可能是 article-lv1__timestamp)
        time_tag = soup.select_one('[class*="timestamp"]') 
        if a_tag and time_tag:
            title = a_tag.get_text(strip=True)
            link = base_url + a_tag['href'] if a_tag['href'].startswith('/') else a_tag['href']
            pub_date = parse_scmp_date(time_tag.get_text(strip=True))
            
            if pub_date and pub_date >= threshold:
                seen_links.add(link)
                extracted_data.append({
                    "title": title,
                    "link": link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M")
                })

    # 處理其餘列表新聞 (通常在 h3)
    # 尋找所有包含時間戳的文章容器
    containers = soup.select('div[class*="article"], article')
    for container in containers:
        a_tag = container.find('a', href=True)
        # 尋找該容器內的標題 (可能是 h2 或 h3)
        title_node = container.find(['h2', 'h3'])
        # 尋找該容器內的時間戳
        time_node = container.select_one('[class*="timestamp"]')
        
        if title_node and time_node and a_tag:
            title = title_node.get_text(strip=True)
            link = a_tag['href']
            link = base_url + link if link.startswith('/') else link
            
            if link not in seen_links:
                pub_date = parse_scmp_date(time_node.get_text(strip=True))
                if pub_date and pub_date >= threshold:
                    seen_links.add(link)
                    extracted_data.append({
                        "title": title,
                        "link": link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M")
                    })

    # 按時間排序 (最新在前面)
    extracted_data.sort(key=lambda x: x['time'], reverse=True)
    return extracted_data
