import requests
import re
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta, timezone

def scrape():
    # 策略：搜尋 tospo-keiba.jp 且網址包含 breaking_news
    search_query = "site:tospo-keiba.jp inurl:breaking_news"
    encoded_query = urllib.parse.quote(search_query)
    
    # 向 Google 請求 36 小時內的新聞
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:36h&hl=ja&gl=JP&ceid=JP:ja"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Google 代理模式 (Tospo 日本精準版) ---")
    
    try:
        res = requests.get(rss_url, headers=headers, timeout=15)
        # 1. 拆解 item 區塊
        items = re.findall(r'<item>(.*?)</item>', res.text, re.DOTALL)
        print(f"    [Debug] Google 原始項目總數: {len(items)}")

        extracted_data = []
        seen_links = set()
        
        # 設定 36 小時門檻
        now_utc = datetime.now(timezone.utc)
        threshold = now_utc - timedelta(hours=36)

        for item_content in items:
            # 2. 使用更強大的 Regex 提取，並直接處理 CDATA 
            title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_content, re.S)
            link_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item_content, re.S)
            date_match = re.search(r'<pubDate>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</pubDate>', item_content, re.S)

            if title_match and link_match:
                raw_title = title_match.group(1).strip()
                # 移除來源尾綴，例如 " - 東スポ競馬" 或 " - 東スポ"
                title = re.split(r' - ', raw_title)[0].strip()
                
                link = link_match.group(1).strip()
                pub_date_str = date_match.group(1).strip() if date_match else ""

                try:
                    # 轉換時間
                    article_date = pd.to_datetime(pub_date_str)
                    if article_date.tzinfo is None:
                        article_date = article_date.replace(tzinfo=timezone.utc)
                    
                    # --- 核心過濾 ---
                    # 1. 檢查時間是否在 36 小時內
                    if article_date >= threshold:
                        # 2. 標題長度放寬到 6 個字（日文標題有時很精簡）
                        if len(title) > 6:
                            if link not in seen_links:
                                seen_links.add(link)
                                extracted_data.append({
                                    "title": title,
                                    "link": link,
                                    "time": article_date.strftime("%Y-%m-%d %H:%M")
                                })
                except:
                    continue

        print(f"    ✅ 解析完成，Tospo 有效新聞共 {len(extracted_data)} 則")
        return extracted_data

    except Exception as e:
        print(f"    ❌ 代理模式執行錯誤: {e}")
        return []