import requests
import re
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta, timezone
import warnings

def scrape():
    # 策略：向 Google 請求 The Straight 48 小時內的新聞
    search_query = "site:thestraight.com.au"
    encoded_query = urllib.parse.quote(search_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:48h&hl=en-AU&gl=AU&ceid=AU:en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Google 代理模式 (The Straight 終極調修) ---")
    
    try:
        res = requests.get(rss_url, headers=headers, timeout=15)
        # 1. 挖出所有項目塊
        items = re.findall(r'<item>(.*?)</item>', res.text, re.DOTALL)
        print(f"    [Debug] 原始項目總數: {len(items)}")

        extracted_data = []
        seen_links = set()
        
        # 門檻：48 小時
        now_utc = datetime.now(timezone.utc)
        threshold = now_utc - timedelta(hours=48)

        for i, item_content in enumerate(items):
            # 使用更強大的 Regex，處理大小寫與 CDATA 標籤
            t_match = re.search(r'<title>(.*?)</title>', item_content, re.I | re.S)
            l_match = re.search(r'<link>(.*?)</link>', item_content, re.I | re.S)
            d_match = re.search(r'<pubDate>(.*?)</pubDate>', item_content, re.I | re.S)

            if t_match and l_match:
                # 清洗內容，移除 CDATA
                title = t_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip()
                # 移除來源尾綴
                title = title.split(' - ')[0] if ' - ' in title else title
                link = l_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip()
                raw_date = d_match.group(1) if d_match else ""

                try:
                    # 使用 pandas 解析時間
                    article_date = pd.to_datetime(raw_date)
                    # 確保時區統一
                    if article_date.tzinfo is None:
                        article_date = article_date.replace(tzinfo=timezone.utc)
                    
                    # 診斷：前 3 則印出日期比對情況
                    if i < 3:
                        print(f"    [測試{i+1}] 標題: {title[:15]} | 文章日期: {article_date} | 當前門檻: {threshold}")

                    # 放寬條件：只要標題夠長就抓
                    if len(title) > 5:
                        # 如果日期太舊，在 Log 提醒但不一定要跳過（暫時放寬）
                        if article_date < threshold:
                            # 即使稍舊也保留，除非舊得離譜 (例如超過一週)
                            if article_date < (now_utc - timedelta(days=7)):
                                continue
                        
                        if link not in seen_links:
                            seen_links.add(link)
                            extracted_data.append({
                                "title": title,
                                "link": link,
                                "time": article_date.strftime("%Y-%m-%d %H:%M")
                            })
                except Exception as e:
                    continue

        print(f"    ✅ 最終成功擷取: {len(extracted_data)} 則")
        return extracted_data

    except Exception as e:
        print(f"    ❌ 執行錯誤: {e}")
        return []