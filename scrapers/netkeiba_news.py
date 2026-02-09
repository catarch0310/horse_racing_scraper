import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_japanese_time(time_str):
    """
    處理日文相對時間：'12分前', '5時間前', '1日前'
    """
    now = datetime.now()
    # 提取數字
    number_match = re.search(r'\d+', time_str)
    if not number_match:
        return now
    
    n = int(number_match.group())
    
    if '分前' in time_str:
        return now - timedelta(minutes=n)
    elif '時間前' in time_str:
        return now - timedelta(hours=n)
    elif '日前' in time_str:
        return now - timedelta(days=n)
    
    return now

def scrape():
    # Netkeiba 新聞清單頁面
    news_url = "https://news.netkeiba.com/?pid=news_list&type=a"
    base_url = "https://news.netkeiba.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Netkeiba 日本新聞抓取 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        # Netkeiba 有時使用 EUC-JP，讓 requests 自動偵測編碼防止亂碼
        res.encoding = res.apparent_encoding
        
        if res.status_code != 200:
            print(f"    ❌ Netkeiba 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        
        # 設定 36 小時門檻 (或視需求調整)
        threshold = datetime.now() - timedelta(hours=36)

        # 根據截圖，新聞項目在 a.ArticleLink 中
        # 我們抓取所有帶有 ArticleLink 類別的 a 標籤
        articles = soup.select('a.ArticleLink')
        print(f"    找到 {len(articles)} 個新聞連結，開始解析日文時間...")

        for art in articles:
            # 1. 抓取標題 (在 class="NewsTitle" 內)
            title_node = art.select_one('.NewsTitle')
            if not title_node:
                continue
            title = title_node.get_text(strip=True)
            
            # 2. 抓取連結
            link = art.get('href', '')
            if link.startswith('//'):
                link = 'https:' + link
            elif link.startswith('/'):
                link = base_url + link
                
            # 3. 抓取時間 (在 class="NewsData" 內，可能包含 12分前)
            time_node = art.select_one('.NewsData')
            time_text = time_node.get_text(strip=True) if time_node else ""
            
            # 4. 處理時間與過濾
            pub_date = parse_japanese_time(time_text)
            
            if pub_date >= threshold:
                extracted_data.append({
                    "title": title,
                    "link": link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M") + f" ({time_text})"
                })

        print(f"    ✅ Netkeiba 抓取完成，符合時間內的新聞共 {len(extracted_data)} 則")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Netkeiba 執行錯誤: {e}")
        return []
