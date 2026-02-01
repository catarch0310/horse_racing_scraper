import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def scrape():
    # 這是東方馬經新聞選單真實存在的內部網址
    # 我們嘗試兩個可能的路徑，確保萬無一失
    urls = [
        "https://racing.on.cc/racing/new/curr/index.html",
        "https://racing.on.cc/racing/new/lastwin/index.html"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    extracted_data = []
    seen_titles = set()
    
    # 取得今天與昨天的日期字串 (格式: 20260201)
    today_str = datetime.now().strftime("%Y%m%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    target_dates = [today_str, yesterday_str]

    for url in urls:
        try:
            print(f"嘗試抓取東方選單: {url}")
            res = requests.get(url, headers=headers)
            res.encoding = 'cp950' # 東方網頁使用 Big5 編碼
            
            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 尋找類別為 rac_news_selection 的 select
            select_tag = soup.find('select', class_='rac_news_selection')
            
            # 如果找不到特定的 select，就抓取頁面上所有的 option
            options = select_tag.find_all('option') if select_tag else soup.find_all('option')
            
            for opt in options:
                val = opt.get('value', '')
                title = opt.get_text(strip=True)
                
                # 判斷日期 (value 內包含日期字串)
                if any(date in val for date in target_dates):
                    if title and "請選擇" not in title and title not in seen_titles:
                        seen_titles.add(title)
                        extracted_data.append({
                            "title": f"[東方] {title}",
                            "link": "https://racing.on.cc/news.html",
                            "time": datetime.now().strftime("%Y-%m-%d") # 東方選單無細分小時，標註今日
                        })
            
            # 如果在這個 URL 抓到了東西，就不用跑下一個 URL 了
            if extracted_data:
                break

        except Exception as e:
            print(f"抓取 {url} 時發生錯誤: {e}")

    if extracted_data:
        print(f"成功從東方馬經選單抓取 {len(extracted_data)} 則標題")
    return extracted_data
