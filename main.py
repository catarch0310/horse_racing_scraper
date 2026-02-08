import pandas as pd
from datetime import datetime
import os
import importlib
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# --- AI 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-1.5-flash')
else:
    model = None

def generate_summary_with_retry(title, content, retries=3):
    """具備自動重試功能的摘要產生器"""
    if not model: return "未設定 API KEY"
    
    prompt = f"請用繁體中文將以下賽馬新聞縮短為一句約 50 字的智能摘要：\n\n標題：{title}\n內容：{content[:2000]}"
    
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                print(f"      ⚠️ 觸發頻率限制，等待 15 秒後重試 ({i+1}/{retries})...")
                time.sleep(15) # 遇到 429 等久一點
            else:
                return f"摘要失敗: {err_msg}"
    return "摘要失敗: 已達最大重試次數 (429)"

def get_full_text(url, source):
    if source == 'on_cc_racing': return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return "\n".join([p.get_text() for p in paragraphs if len(p.get_text()) > 25])[:2500]
    except:
        return ""

def run_all():
    all_data = []
    # 確保 punters_au 在清單中
    SITES = ['racing_post', 'scmp_racing', 'on_cc_racing', 'punters_au']
    
    for site in SITES:
        try:
            print(f"\n>>> 爬取 {site}...")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ 抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 錯誤: {e}")

    if all_data:
        total = len(all_data)
        print(f"\n🤖 進行 AI 摘要 (總共 {total} 則)...")
        results = []
        for i, item in enumerate(all_data):
            print(f"    ({i+1}/{total}) 處理: {item['title'][:20]}...")
            
            # 取得內文並摘要
            text = get_full_text(item['link'], item['source'])
            item['ai_summary'] = generate_summary_with_retry(item['title'], text)
            results.append(item)
            
            # 基礎延遲：免費版限制 15RPM，每則至少要間隔 4.5 秒
            time.sleep(4.5)

        df = pd.DataFrame(results)
        os.makedirs('data', exist_ok=True)
        filename = f"data/ai_racing_report_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✨ 存檔成功: {filename}")

if __name__ == "__main__":
    run_all()
