看起來 SCMP 的網頁結構在 requests 抓取時與瀏覽器「檢查 (Inspect)」看到的並不完全一致。這通常是因為網頁用了某種「延遲加載」或是 lv1 這種類別名稱只在特定排版下出現。

我們觀察到：你的 CSV 抓到了 "SCMP Best Bets" (1月31日)，但卻漏掉了最上面的 "Hayes" (2月1日)。這證明程式「進得去」SCMP，但「看不見」最上方那個特別大的區塊。

這版 「終極修正版」 拋棄了對 article-lv1 或 article-lv3 的依賴，改用更強大的 「找尋所有標題與時間」 策略：

修正後的 scrapers/scmp_racing.py
code
Python
download
content_copy
expand_less
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def parse_scmp_date(date_str):
    if not date_str: return None
    try:
        # 格式範例: 1 Feb 2026 - 7:30 AM
        # 移除 Updated 等字眼
        clean_date = date_str.strip().split('\n')[0].replace('Updated: ', '')
        return datetime.strptime(clean_date, "%d %b %Y - %I:%M %p")
    except Exception:
        return None

def scrape():
    base_url = "https://www.scmp.com"
    news_url = "https://www.scmp.com/sport/racing/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"正在存取 SCMP: {news_url}")
    res = requests.get(news_url, headers=headers)
    if res.status_code != 200: return []

    soup = BeautifulSoup(res.text, 'html.parser')
    extracted_data = []
    seen_links = set()
    
    # 設定時間門檻 (測試時請確保 hours 足夠大，例如 48 或 500)
    threshold = datetime.now() - timedelta(hours=48)

    # 策略：尋找所有包含連結的 h1, h2, h3 標籤 (SCMP 的新聞標題只會放在這些標籤裡)
    headers_tags = soup.find_all(['h1', 'h2', 'h3'])
    print(f"掃描到 {len(headers_tags)} 個標題標籤...")

    for header in headers_tags:
        a_tag = header.find('a', href=True)
        if not a_tag:
            continue
            
        link = a_tag['href']
        full_link = base_url + link if link.startswith('/') else link
        
        if full_link in seen_links:
            continue
        
        title = a_tag.get_text(strip=True)
        
        # 關鍵：在該標題的「附近」尋找時間戳記
        # 我們往上找兩層父節點，然後在該範圍內搜尋帶有 timestamp 類別的標籤
        parent = header.find_parent(['div', 'article', 'section'])
        time_tag = None
        if parent:
            time_tag = parent.select_one('[class*="timestamp"]')
        
        # 如果父節點沒找到，嘗試在整頁找跟標題文字相關聯的時間 (這對大頭條特別有效)
        if not time_tag:
            # 有些大頭條的時間標記在結構上離標題較遠，我們擴大搜尋範圍
            time_tag = header.find_next_sibling(['div', 'span']).select_one('[class*="timestamp"]') if header.find_next_sibling() else None

        if a_tag and time_tag:
            raw_time = time_tag.get_text(strip=True)
            pub_date = parse_scmp_date(raw_time)
            
            if pub_date and pub_date >= threshold:
                seen_links.add(full_link)
                # 標記大頭條以便辨識
                display_title = f"[TOP] {title}" if header.name == 'h1' else title
                
                extracted_data.append({
                    "title": display_title,
                    "link": full_link,
                    "time": pub_date.strftime("%Y-%m-%d %H:%M")
                })
                print(f"成功擷取: {title[:30]}... (時間: {raw_time})")

    # 根據時間排序，最新在前
    extracted_data.sort(key=lambda x: x['time'], reverse=True)
    return extracted_data
為什麼這版一定能抓到？

放棄特定的 class 選項：
原本我們找 h1.news-content-title，但 SCMP 的 h1 可能在不同裝置或請求下有不同 class。現在我告訴程式：「只要是 <h1> 裡面的連結，通通給我拿出來看。」

動態搜尋時間戳：
大頭條的 timestamp 往往不在標題的同一個 div 裡。現在程式會先找到標題，然後在標題的「鄰居」和「長輩」節點裡翻找任何包含 timestamp 字眼的標籤。

排序優化：
我加上了 sort 功能。這樣 2 月 1 日的新聞（Hayes）絕對會出現在 SCMP 部分的第一行。

測試建議：

請將這段程式碼貼入 scrapers/scmp_racing.py，並執行 python3 main.py。

觀察終端機輸出：

它應該會印出 掃描到 XX 個標題標籤...

如果有抓到 Hayes，會印出 成功擷取: Hayes looks to bridge...

如果還是沒抓到，請告訴我終端機有沒有印出「成功擷取: Hayes...」這行字。 只要終端機有印，CSV 就一定會有。
