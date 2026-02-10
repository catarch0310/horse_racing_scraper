import requests
import re
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta, timezone
import warnings
from bs4 import XMLParsedAsHTMLWarning

# 忽略警告
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def scrape():
    # --- 關鍵修正 1：優化搜尋指令 ---
    # 不再使用 inurl:，改用直接關鍵字搜尋，這在 Google RSS 中最穩定
    search_query = 'site:dailytelegraph.com.au "horse racing"'
    encoded_query = urllib.parse.quote(search_query)
    
    # 搜尋 36 小時內的新聞
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:36h&hl=en-AU&gl=AU&ceid=AU:en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Google 代理模式 (澳洲 Daily Telegraph 精準搜尋) ---")
    
    try:
        res = requests.get(rss_url, headers=headers, timeout=20)
        items = re.findall(r'<item>(.*?)</item>', res.text, re.DOTALL)
        print(f"    [Debug] Google 原始項目總數: {len(items)}")

        extracted_data = []
        seen_links = set()
        now_utc = datetime.now(timezone.utc)
        threshold = now_utc - timedelta(hours=36)

        # 關鍵修正 2：定義賽馬相關關鍵字，確保過濾掉政治/社會新聞
        racing_keywords = ['race', 'horse', 'jockey', 'trainer', 'bet', 'stakes', 'cup', 'racing', 'colt', 'filly', 'punters', 'mile', 'handicap']

        for item_content in items:
            t_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_content, re.S)
            l_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item_content, re.S)
            d_match = re.search(r'<pubDate>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</pubDate>', item_content, re.S)

            if t_match and l_match:
                raw_title = t_match.group(1).strip()
                title = raw_title.split(' - ')[0].strip()
                
                # --- 關鍵過濾邏輯 1：標題必須包含賽馬關鍵字 ---
                title_lower = title.lower()
                if not any(kw in title_lower for kw in racing_keywords):
                    continue

                # --- 關鍵過濾邏輯 2：標題長度與黑名單 ---
                if len(title) < 15 or 'dailytelegraph' in title_lower:
                    continue

                link = l_match.group(1).strip()
                pub_date_str = d_match.group(1).strip() if d_match else ""

                try:
                    article_date = pd.to_datetime(pub_date_str)
                    if article_date.tzinfo is None:
                        article_date = article_date.replace(tzinfo=timezone.utc)
                        
                    if article_date >= threshold:
                        if link not in seen_links:
                            seen_links.add(link)
                            extracted_data.append({
                                "title": title,
                                "link": link,
                                "time": article_date.strftime("%Y-%m-%d %H:%M")
                            })
                except:
                    continue

        print(f"    ✅ Daily Telegraph 解析完成，共 {len(extracted_data)} 則純賽馬新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Google 代理模式失敗: {e}")
        return []