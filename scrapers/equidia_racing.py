import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def extract_french_date(art_node):
    """
    從文章節點中提取法語時間文字
    """
    try:
        # 尋找帶有 date 類別的 p 標籤
        date_node = art_node.select_one('.article-infos-date')
        if date_node:
            return date_node.get_text(strip=True)
        
        # 備援：搜尋包含 'Publié' 或 'il y a' 的文字
        text_node = art_node.find(string=re.compile(r'Publié|il y a|Hier', re.I))
        if text_node:
            return text_node.strip()
    except:
        pass
    return "Latest"

def scrape():
    news_url = "https://www.equidia.fr/actualites"
    base_url = "https://www.equidia.fr"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'fr-FR,fr;q=0.9',
    }
    
    print(f"--- 啟動 Equidia (法國) 全量掃描模式 ---")
    
    try:
        res = requests.get(news_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"    ❌ Equidia 請求失敗: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        extracted_data = []
        seen_links = set()

        # 策略：尋找所有 article 標籤
        articles = soup.find_all('article', class_=re.compile(r'article'))
        print(f"    [Debug] 頁面原始掃描到 {len(articles)} 個新聞區塊")

        for art in articles:
            # 1. 抓取標題與連結
            title_node = art.select_one('.article-infos-title a') or art.find('a')
            if not title_node: continue
            
            title = title_node.get_text(strip=True)
            link = title_node.get('href', '')
            
            if not link or link in seen_links:
                continue
                
            full_link = base_url + link if link.startswith('/') else link
            
            # 2. 獲取時間文字 (僅供顯示，不參與過濾)
            time_text = extract_french_date(art)

            # 3. 只要標題夠長就抓 (過濾掉純分類標籤)
            if len(title) > 10:
                seen_links.add(full_link)
                extracted_data.append({
                    "title": title,
                    "link": full_link,
                    "time": time_text
                })
            
            # 限制單次抓取數量，防止抓到過舊的底部內容
            if len(extracted_data) >= 20:
                break

        print(f"    ✅ Equidia 成功擷取 {len(extracted_data)} 則法語新聞")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Equidia 執行錯誤: {e}")
        return []