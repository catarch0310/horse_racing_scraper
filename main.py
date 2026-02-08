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

def init_ai_model():
    if not API_KEY:
        print("❌ 找不到 API KEY")
        return None
    try:
        genai.configure(api_key=API_KEY)
        # 嘗試穩定版名稱，避開 v1beta 404 報錯
        # 建議使用 gemini-1.5-flash 或 gemini-2.0-flash-exp (最新)
        for model_name in ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-2.0-flash']:
            try:
                m = genai.GenerativeModel(model_name)
                # 測試一下模型是否可用
                m.generate_content("test", generation_config={"max_output_tokens": 1})
                print(f"✅ AI 成功啟用模型: {model_name}")
                return m
            except:
                continue
        return None
    except Exception as e:
        print(f"AI 初始化失敗: {e}")
        return None

model = init_ai_model()

def generate_summary_with_retry(title, content, retries=2):
    if not model: return "AI 模型未就緒"
    
    text_to_analyze = content[:2000] if len(content) > 50 else f"根據標題分析：{title}"
    prompt = f"你是賽馬專家，請用繁體中文將以下內容總結成一句50字內的精闢摘要：\n\n{text_to_analyze}"

    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                print(f"      ⏳ 觸發頻率限制，休息 10 秒後重試...")
                time.sleep(10)
            else:
                return f"摘要失敗: {str(e)[:50]}"
    return "摘要嘗試多次失敗"

def get_full_text(url, source):
    if source == 'on_cc_racing': return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        # 抓取 <p> 標籤內文
        paragraphs = soup.find_all('p')
        return "\n".join([p.get_text() for p in paragraphs if len(p.get_text()) > 30])[:2500]
    except:
        return ""

def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'on_cc_racing', 'punters_au']
    
    for site in SITES:
        try:
            print(f"\n>>> 爬取 {site}...")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ {site} 成功抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 錯誤: {e}")

    if all_data:
        print(f"\n🤖 進行 AI 摘要 (共 {len(all_data)} 則)...")
        results = []
        for i, item in enumerate(all_data):
            print(f"    ({i+1}/{len(all_data)}) 處理: {item['title'][:20]}")
            content = get_full_text(item['link'], item['source'])
            item['ai_summary'] = generate_summary_with_retry(item['title'], content)
            results.append(item)
            # 配合免費版限制，每則休息 5 秒
            time.sleep(5)

        df = pd.DataFrame(results)
        os.makedirs('data', exist_ok=True)
        filename = f"data/ai_racing_report_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 報告存檔: {filename}")

if __name__ == "__main__":
    run_all()
