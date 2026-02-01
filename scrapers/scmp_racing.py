import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def parse_scmp_date(date_str):
    if not date_str: return None
    try:
        # SCMP 格式範例: 1 Feb 2026 - 7:30 AM
        clean_date = date_str.strip().replace('Updated: ', '')
        return datetime.strptime(clean_date, "%d %b %Y - %I:%M %p")
    except Exception:
        return None

def scrape():
    base_url = "https://www.scmp.com"
    news_url = "https://www.scmp.com/sport/racing/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    print(f"正在存取 SCMP: {news_url}")
    res = requests.get(news_url, headers=headers)
    if res.status_code != 200:
        print(f"SCMP 請求失敗: {res.status_code}")
        return []

    soup = BeautifulSoup(res.text, 'html.parser')
    extracted_data = []
    seen_links = set()
    threshold = datetime.now() - timedelta(hours=48) # 測試時可改成 500

    # --- 1. 抓取大頭條 (Hero Story) ---
    # 根據截圖，大頭條標題在 h1.news-content-title a
    # 時間在 .article-lv1__timestamp
    hero_title_a = soup.select_one('h1.news-content-title a')
    hero_time_span = soup.select_one('.article-lv1__timestamp')
    
    if hero_title_a:
        title = hero_title_a.get_text(strip=True)
        link = hero_title_a.get('href', '')
        full_link = base_url + link if link.startswith('/') else link
        
        # 取得時間
        raw_time = hero_time_span.get_text(strip=True) if hero_time_span else "未知時間代碼"
        pub_date = parse_scmp_date(raw_time)
        
        print(f"找到大頭條: {title} (時間: {raw_time})")
        
        if pub_date and pub_date >= threshold:
            seen_links.add(full_link)
            extracted_data.append({
                "title": f"[HEADLINE] {title}",
                "link": full_link,
                "time": pub_date.strftime("%Y-%m-%d %H:%M")
            })

    # --- 2. 抓取列表新聞 (Article List) ---
    # 每個列表新聞通常在一個特定容器內，我們直接抓取所有文章連結
    articles = soup.select('.article-lv3, [class*="article-lv"]')
    
    for art in articles:
        # 尋找標題連結
        a_tag = art.select_one('h2 a, h3 a, .article-lv3__header a')
        # 尋找時間戳
        t_tag = art.select_one('[class*="__timestamp"]')
        
        if a_tag and t_tag:
            title = a_tag.get_text(strip=True)
            link = a_tag.get('href', '')
            full_link = base_url + link if link.startswith('/') else link
            
            if full_link in seen_links:
                continue
            
            raw_time = t_tag.get_text(strip=True)
            pub_date = parse_scmp_date(raw_time)
            
            if pub_date and pub_date >= threshold:
                seen_links.add(full_link)
                extracted_data.append({
                    "title": title,
                    "link": full_link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M")
                })

    # 按時間排序
    extracted_data.sort(key=lambda x: x['time'], reverse=True)
    return extracted_data
