import requests
import re
import urllib.parse
import warnings
from bs4 import XMLParsedAsHTMLWarning

# 忽略警告
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def scrape():
    # 策略：直接在 Google 搜尋指令中指定要 news_view 網址
    # site:news.netkeiba.com 只找這網站
    # inurl:news_view 網址必須包含這個關鍵字 (確保是新聞內文)
    search_query = "site:news.netkeiba.com inurl:news_view"
    encoded_query = urllib.parse.quote(search_query)
    
    # 搜尋過去 36 小時的新聞
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:36h&hl=ja&gl=JP&ceid=JP:ja"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Google 代理模式 (Netkeiba 指令優化) ---")
    
    try:
        res = requests.get(rss_url, headers=headers, timeout=15)
        
        # 使用 Regex 切割 <item>，這最穩定
        items = re.findall(r'<item>(.*?)</item>', res.text, re.DOTALL)
        print(f"    [Debug] 原始項目總數: {len(items)}")

        extracted_data = []
        seen_links = set()

        # 過濾關鍵字黑名單
        blacklist = ['検索結果', 'コラム検索', 'のニュース', 'のコラム', '一覧']

        for item_content in items:
            title_match = re.search(r'<title>(.*?)</title>', item_content)
            link_match = re.search(r'<link>(.*?)</link>', item_content)
            date_match = re.search(r'<pubDate>(.*?)</pubDate>', item_content)

            if title_match and link_match:
                raw_title = title_match.group(1)
                # 移除 Google 自動加上的來源尾綴
                title = raw_title.split(' - ')[0] if ' - ' in raw_title else raw_title
                link = link_match.group(1)
                pub_date = date_match.group(1) if date_match else ""

                # 核心過濾邏輯：
                # 1. 標題不能包含黑名單關鍵字
                # 2. 標題長度必須大於 12 個字元 (排除純馬名、純地名)
                # 3. 不再檢查 link 內容，因為 Google 已經幫我們過濾好了
                
                if not any(word in title for word in blacklist):
                    if len(title) > 12:
                        if link not in seen_links:
                            seen_links.add(link)
                            extracted_data.append({
                                "title": title.strip(),
                                "link": link.strip(),
                                "time": pub_date
                            })

        print(f"    ✅ 過濾完成，精確新聞共 {len(extracted_data)} 則")
        return extracted_data

    except Exception as e:
        print(f"    ❌ 代理模式執行錯誤: {e}")
        return []
