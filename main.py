import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- 1. AI 核心設定 ---
# 這裡會從 GitHub Secrets 讀取 Key
API_KEY = os.getenv("GEMINI_API_KEY")

def init_ai():
    """ 
    最簡化初始化：只要有 Key 就強行建立模型物件
    """
    if not API_KEY:
        print("❌ 錯誤：GEMINI_API_KEY 變數為空，請檢查 GitHub Secrets。")
        return None
    
    print(f"🔑 偵測到 API KEY，正在配置模型...")
    try:
        genai.configure(api_key=API_KEY)
        # 使用最穩定的模型路徑
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"❌ AI 配置出錯: {e}")
        return None

# 初始化
model_instance = init_ai()

# --- 2. 標題翻譯 (寫入標題後方) ---
def translate_titles_to_en(all_data):
    if not model_instance or not all_data:
        return all_data
    
    print(f"🌐 正在翻譯 {len(all_data)} 則標題...")
    raw_titles = [item['title'] for item in all_data]
    # 一次處理所有標題
    titles_blob = "\n".join(raw_titles)
    
    prompt = f"Translate the following racing headlines into English. Return ONLY the English text, one per line, strictly maintaining the order. If a line is already English, keep it as is:\n\n{titles_blob}"
    
    try:
        response = model_instance.generate_content(prompt)
        translated_lines = response.text.strip().split('\n')
        
        # 數量對齊才處理，防止資料錯位
        if len(translated_lines) >= len(all_data):
            for i in range(len(all_data)):
                orig = all_data[i]['title']
                en = translated_lines[i].strip()
                # 簡單判斷：如果翻譯內容跟原文不一樣（代表原文是中/日文），才附加
                if orig.lower() != en.lower():
                    all_data[i]['title'] = f"{orig} ({en})"
            print("✅ 標題英譯附加成功")
    except Exception as e:
        print(f"⚠️ 翻譯失敗: {e}")
    
    return all_data

# --- 3. 戰略分析報告 (英文) ---
def generate_strategic_report(all_headlines):
    if not model_instance:
        return "AI Model Not Ready. Please check GEMINI_API_KEY."

    news_text = ""
    for i, item in enumerate(all_headlines):
        news_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    prompt = f"""
    # Role
    You are a Strategic Industry Analyst for global horse racing.
    Analyze the following headlines and provide a brief in ENGLISH:

    # Input Data
    {news_text}

    # Task
    1. **TOP 5 STRATEGIC KEYWORDS**: List 5 most important themes from the data and briefly explain why they matter.
    2. **OUTLIER RADAR**: Identify 2-3 "unusual" or "niche" headlines that represent unique industry shifts or local incidents worth deeper investigation.

    Format with Markdown. Be concise and professional.
    """

    try:
        # 強制關閉安全性過濾，防止賽馬詞彙被擋
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model_instance.generate_content(
            prompt, 
            generation_config={"temperature": 0.2},
            safety_settings=safety
        )
        return response.text.strip()
    except Exception as e:
        return f"Report failed: {str(e)}"

# --- 4. 資料清洗 ---
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def deduplicate_data(all_data):
    if not all_data: return []
    unique_url_data = []
    seen_urls = set()
    for item in all_data:
        if item['link'] not in seen_urls:
            seen_urls.add(item['link'])
            unique_url_data.append(item)
    
    final_data = []
    for item in unique_url_data:
        is_duplicate = False
        for existing_item in final_data:
            if similarity(item['title'], existing_item['title']) > 0.85:
                is_duplicate = True
                break
        if not is_duplicate:
            final_data.append(item)
    return final_data

# --- 5. 執行流程 ---
def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 'the_straight', 'anz_bloodstock', 'ttr_ausnz', 'smh_racing', 'drf_news', 'racenet_news', 'daily_telegraph', 'equidia_racing']
    
    for site in SITES:
        try:
            print(f">>> Task: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
        except Exception as e:
            print(f"❌ {site} Error: {e}")

    if all_data:
        # 去重
        all_data = deduplicate_data(all_data)
        
        # 翻譯
        all_data = translate_titles_to_en(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # 儲存 CSV
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"💾 CSV Saved.")

        # 產出報告
        print(f"🤖 Generating Strategic Report...")
        ai_report = generate_strategic_report(all_data)
        with open(f"data/strategic_report_{date_str}.md", "w", encoding="utf-8") as f:
            f.write(ai_report)
        print(f"✨ Report Saved.")
    else:
        print("❌ No data.")

if __name__ == "__main__":
    run_all()
