import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def scrape():
    # 東方馬經新聞主頁
    news_url = "https://racing.on.cc/news.html"
    base_url = "https://racing.on.cc"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://racing.on.cc/'
    }
    
    print(f"正在存取東方馬經: {news_url}")
    
    try:
        res = requests.get(news_url, headers=headers)
        # on.cc 有時使用 utf-8，有時需要自動偵測
        res.encoding = res.apparent_encoding 
        
        if res.status_code != 200:
            print(f"東方馬經請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        
        # 設定要抓取的日期範圍 (48小時內)
        # on.cc 的日期格式在 option value 裡是 20260201 這種格式
        today_str = datetime.now().strftime("%Y%m%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        target_dates = [today_str, yesterday_str]
        
        print(f"目標日期: {target_dates}")

        # 策略：尋找所有的 <option> 標籤
        options = soup.find_all('option')
        seen_titles = set()

        for opt in options:
            val = opt.get('value', '')
            title = opt.get_text(strip=True)
            
            # 過濾邏輯：
            # 1. value 裡面必須包含我們的目標日期 (如 20260201)
            # 2. 標題不能是空的，且不是預設的提示文字
            if any(date in val for date in target_dates):
                if title and "請選擇" not in title and title not in seen_titles:
                    seen_titles.add(title)
                    
                    # 構造連結
                    # on.cc 的連結通常可以透過其 ID 組合，但最簡單的方法是導向新聞主頁
                    # 因為它是透過 JS 切換內容，這裡提供主頁連結
                    extracted_data.append({
                        "title": title,
                        "link": news_url, 
                        "time": f"{val[7:11]}-{val[11:13]}-{val[13:15]}" if len(val) > 15 else today_str
                    })

        if not extracted_data:
            print("未能從下拉選單抓取到任何當日新聞標題。")

        return extracted_data

    except Exception as e:
        print(f"東方馬經執行錯誤: {e}")
        return []
