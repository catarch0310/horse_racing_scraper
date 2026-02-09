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

def get_ai_response(title, content):
    if not API_KEY:
        return "AI 失敗: 找不到 API KEY"
    
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        text = content[:2000] if len(content) > 50 else f"根據標題分析：{title}"
        prompt = f"請用繁體中文將以下賽馬新聞縮寫成一句約 50 字的摘要：\n\n{text}"
        
        # 加上安全設定，防止 AI 拒絕生成
        response = model.generate_content(prompt, safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ])
        return response.text.strip()
    except Exception as e:
        if "429" in str(e):
            return "AI 失敗: 請求過快 (429)"
        return f"AI 失敗: {str(e)[:50]}"

def get_full_text(url, source):
    if source == 'on_cc_racing': return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return "\n".join([p.get_text() for p in paragraphs if len(p.get_text()) > 30])[:2500]
    except:
        return ""

def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'on_cc_racing', 'punters_au']
    
    for site in SITES:
        try:
            print(f"\n>>> 任務: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    成功抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ 執行錯誤: {e}")

    if all_data:
        print(f"\n🤖 啟動 AI 摘要 (共 {len(all_data)} 則)...")
        for i, item in enumerate(all_data):
            print(f"    ({i+1}/{len(all_data)}) 處理: {item['title'][:20]}")
            # 獲取內文
            full_text = get_full_text(item['link'], item['source'])
            # 產生摘要
            item['ai_summary'] = get_ai_response(item['title'], full_text)
            # 延遲 5 秒以符合免費版限制
            time.sleep(5)

        df = pd.DataFrame(all_data)
        os.makedirs('data', exist_ok=True)
        filename = f"data/racing_report_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✅ 任務完成！檔案存至: {filename}")

if __name__ == "__main__":
    run_all()
