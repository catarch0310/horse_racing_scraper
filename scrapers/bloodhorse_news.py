import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_bloodhorse_time(time_str):
    """
    處理 BloodHorse 的時間格式：
    'Today, 7:34 PM', 'Yesterday, 9:01 PM', 'Feb 7, 6:34 PM'
    """
    now = datetime.now()
    time_str = time_str.strip()
    
    try:
        if 'Today' in time_str:
            # 提取時間部分 (7:34 PM)
            t_part = time_str.split(', ')[1]
            t_obj = datetime.strptime(t_part, "%I:%M %p")
            return now.replace(hour=t_obj.hour, minute=t_obj.minute, second=0, microsecond=0)
        
        elif 'Yesterday' in time_str:
            t_part = time_str.split(', ')[1]
            t_obj = datetime.strptime(t_part, "%I:%M %p")
            yest = now - timedelta(days=1)
            return yest.replace(hour=t_obj.hour, minute=t_obj.minute, second=0, microsecond=0)
        
        else:
            # 處理其他格式如 'Feb 7, 6:34 PM'
            # 補上年份以利解析
            current_year = now.year
            full_date_str = f"{time_str}, {current_year}"
            return datetime.strptime(full_date_str, "%b %d, %I:%M %p, %Y")
    except:
        return now

def scrape():
    news_url = "https://www.bloodhorse.com/horse-racing/articles"
    base_url = "https://www.bloodhorse.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 BloodHorse 美國新聞抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ BloodHorse 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()
        threshold = datetime.now() - timedelta(hours=36)

        # 根據截圖，新聞在 article.summary 中
        articles = soup.select('article.summary')
        print(f"    找到 {len(articles)} 個新聞區塊，開始時間過濾...")

        for art in articles:
            # 1. 抓取標題與連結 (在 h4 a 內)
            title_node = art.select_one('h4 a')
            if not title_node: continue
            
            title = title_node.get_text(strip=True)
            link = title_node.get('href', '')
            if link.startswith('/'): link = base_url + link
            
            # 2. 抓取時間 (在 ul.article-meta 內)
            meta_node = art.select_one('.article-meta')
            time_text = ""
            if meta_node:
                # 通常時間是 meta 裡面的最後一項文字，或者是包含 Today/Yesterday 的文字
                time_text = meta_node.get_text(strip=True)
                # 清洗文字：移除 "By Olivia Newman | " 這種作者資訊
                if '|' in time_text:
                    time_text = time_text.split('|')[-1].strip()
                elif 'By ' in time_text:
                    # 使用 Regex 尋找 Today, Yesterday 或 月份開頭的日期
                    match = re.search(r'(Today|Yesterday|[A-Z][a-z]{2}\s\d+).*', time_text)
                    if match:
                        time_text = match.group(0)

            if title and time_text:
                pub_date = parse_bloodhorse_time(time_text)
                
                if pub_date >= threshold:
                    if link not in seen_links:
                        seen_links.add(link)
                        extracted_data.append({
                            "title": title,
                            "link": link,
                            "time": pub_date.strftime("%Y-%m-%d %H:%M") + f" ({time_text})"
                        })

        print(f"    ✅ BloodHorse 抓取成功，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ BloodHorse 執行錯誤: {e}")
        return []
