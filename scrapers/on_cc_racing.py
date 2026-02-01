import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def scrape():
    # 這是東方馬經「選單與內容」真正存在的後端網址
    # 根據以往經驗與截圖結構，這個網址最有可能包含 rac_news_selection
    target_url = "https://racing.on.cc/racing/new/curr/index.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://racing.on.cc/news.html'
    }
    
    print(f"--- 嘗試存取東方馬經數據源: {target_url} ---")
    
    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        # 東方馬經是老牌網站，使用 Big5 (cp950) 編碼
        res.encoding = 'cp950' 
        
        if res.status_code != 200:
            print(f"東方馬經請求失敗，代碼: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        
        # 1. 建立目標日期字串（對應截圖中的 optgroup label "1/2/2026"）
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # 格式：D/M/YYYY (例如 1/2/2026)
        date_formats = [
            f"{now.day}/{now.month}/{now.year}",
            f"{yesterday.day}/{yesterday.month}/{yesterday.year}"
        ]
        print(f"尋找日期標籤: {date_formats}")

        # 2. 尋找目標 select
        select_tag = soup.find('select', class_='rac_news_selection')
        
        if not select_tag:
            # 如果找不到 select，嘗試直接找 optgroup
            optgroups = soup.find_all('optgroup')
        else:
            optgroups = select_tag.find_all('optgroup')

        for group in optgroups:
            label = group.get('label', '')
            # 檢查 label 是否匹配今天或昨天的日期 (如 "1/2/2026")
            if any(fmt in label for fmt in date_formats):
                options = group.find_all('option')
                print(f"在日期 {label} 下找到 {len(options)} 則新聞")
                
                for opt in options:
                    title = opt.get_text(strip=True)
                    # 排除掉預設的提示文字
                    if title and "請選擇" not in title:
                        extracted_data.append({
                            "title": f"[東方] {title}",
                            "link": "https://racing.on.cc/news.html",
                            "time": label
                        })
        
        # 3. 備援方案：如果 optgroup 沒抓到，抓取所有 option 看看
        if not extracted_data:
            print("嘗試備援方案：抓取所有 option...")
            all_options = soup.find_all('option')
            for opt in all_options:
                title = opt.get_text(strip=True)
                if len(title) > 5 and "請選擇" not in title:
                    extracted_data.append({
                        "title": f"[東方-備援] {title}",
                        "link": "https://racing.on.cc/news.html",
                        "time": now.strftime("%Y-%m-%d")
                    })

        return extracted_data

    except Exception as e:
        print(f"東方馬經執行失敗: {e}")
        return []
