import pandas as pd
from datetime import datetime
import os
import importlib
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# --- 1. AI 核心設定與自動偵測 ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ 錯誤：請先在終端機執行 export GEMINI_API_KEY='你的KEY'")
    exit()

genai.configure(api_key=API_KEY)

def init_ai_model():
    """ 自動尋找當前 API Key 可用的模型名稱 """
    print("🤖 正在偵測可用 AI 模型...")
    try:
        # 獲取所有可用模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"   系統發現可用模型: {available_models}")
        
        # 優先順序：flash -> pro -> 其他
        target_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        
        for target in target_models:
            if target in available_models:
                print(f"✅ 成功鎖定最佳模型: {target}")
                return genai.GenerativeModel(target)
        
        # 如果都沒在清單裡，就拿清單第一個
        if available_models:
            print(f"⚠️ 未發現首選模型，嘗試使用: {available_models[0]}")
            return genai.GenerativeModel(available_models[0])
            
    except Exception as e:
        print(f"❌ 無法獲取模型清單: {e}")
    return None

# 初始化模型
model = init_ai_model()

# --- 2. 工具函式 ---

def get_full_text(url, source):
    """ 抓取新聞全文 """
    if source == 'on_cc_racing': return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        paras = soup.find_all('p')
        content = "\n".join([p.get_text() for p in paras if len(p.get_text()) > 25])
        return content[:2500]
    except:
        return ""

def summarize(title, content):
    """ 產生摘要 """
    if not model: return "AI 模型未就緒"
    
    if len(content) < 80:
        prompt = f"這是一則賽馬標題：『{title}』。請用繁體中文寫出一句約 40 字的簡短分析。"
    else:
        prompt = f"請將以下新聞總結成一句約 50 字的繁體中文摘要：\n\n{content}"

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # 在終端機印出具體錯誤，方便除錯
        print(f"      AI 呼叫失敗: {e}")
        return f"摘要失敗: {str(e)}"

# --- 3. 執行流程 ---

def run():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'on_cc_racing', 'punters_au']
    
    # A. 抓取標題
    for site in SITES:
        try:
            print(f"\n[1/2] 正在爬取 {site}...")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"      成功抓到 {len(data)} 則")
        except Exception as e:
            print(f"      ❌ {site} 錯誤: {e}")

    # B. AI 處理 (全量)
    if all_data:
        total = len(all_data)
        print(f"\n[2/2] 正在進行 AI 摘要 (總共 {total} 則)...")
        
        results = []
        for i, item in enumerate(all_data):
            # 每 15 則顯示一次進度，避免洗版
            print(f"      ({i+1}/{total}) 處理中: {item['title'][:20]}...")
            
            full_content = get_full_text(item['link'], item['source'])
            item['ai_summary'] = summarize(item['title'], full_content)
            results.append(item)
            
            # 配合免費版 15 RPM 限制
            time.sleep(4.2)

        # C. 存檔
        df = pd.DataFrame(results)
        os.makedirs('data', exist_ok=True)
        filename = f"data/ai_report_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✨ 完成！請查看: {filename}")
    else:
        print("\n❌ 失敗：未抓到資料")

if __name__ == "__main__":
    run()
