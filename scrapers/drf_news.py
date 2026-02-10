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
    # 策略：透過 Google News 搜尋 drf.com 過去 36 小時的新聞
    search_query = "site:drf.com"
    encoded_query = urllib.parse.quote(search_query)
    
    # 搜尋 36 小時內的新聞
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:36h&hl=en-US&gl=US&ceid=US:en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    print(f"--- 啟動 Google 代理模式 (美國 DRF) ---")
    
    try:
        # 向 Google 請求數據，Google 的連線通常不會超時
        res = requests.get(rss_url, headers=headers, timeout=20)
        
        # 使用 Regex 直接切割 <item> 區塊，這是最穩定的解析方式
        items = re.findall(r'<item>(.*?)</item>', res.text, re.DOTALL)
        print(f"    [Debug] Google 代理掃描到 {len(items)} 則原始項目")

        extracted_data = []
        seen_links = set()
        
        # 設定 36 小時門檻 (Google RSS 是 UTC 時間)
        now_utc = datetime.now(timezone.utc)
        threshold = now_utc - timedelta(hours=36)

        for item_content in items:
            # 使用 Regex 提取標題、連結與日期，並處理 CDATA 標籤
            t_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_content, re.S)
            l_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item_content, re.S)
            d_match = re.search(r'<pubDate>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</pubDate>', item_content, re.S)

            if t_match and l_match:
                raw_title = t_match.group(1).strip()
                # 移除來源尾綴，例如 " - Daily Racing Form"
                title = raw_title.split(' - ')[0] if ' - ' in raw_title else raw_title
                
                link = l_match.group(1).strip()
                pub_date_str = d_match.group(1).strip() if d_match else ""

                try:
                    # 轉換時間並檢查門檻
                    article_date = pd.to_datetime(pub_date_str)
                    if article_date.tzinfo is None:
                        article_date = article_date.replace(tzinfo=timezone.utc)
                        
                    if article_date >= threshold:
                        if link not in seen_links and len(title) > 10:
                            seen_links.add(link)
                            extracted_data.append({
                                "title": title.strip(),
                                "link": link.strip(),
                                "time": article_date.strftime("%Y-%m-%d %H:%M")
                            })
                except:
                    continue

        print(f"    ✅ DRF 抓取成功，共 {len(extracted_data)} 則新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Google 代理模式失敗: {e}")
        return []