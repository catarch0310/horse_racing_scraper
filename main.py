import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- 1. AI 核心設定 (保留你的成功邏輯) ---
API_KEY = os.getenv("GEMINI_API_KEY")

def get_best_model():
    if not API_KEY: return None
    genai.configure(api_key=API_KEY)
    candidate_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-pro', 'models/gemini-1.5-pro']
    print("🤖 正在偵測可用 AI 模型...")
    for name in candidate_names:
        try:
            model = genai.GenerativeModel(name)
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            print(f"✅ 成功啟用模型: {name}")
            return model
        except: continue
    return None

model_instance = get_best_model()

# --- 2. 資料清洗 ---
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

# --- 3. AI 報告生成 (強化穩定性) ---
def generate_ai_report(cleaned_headlines):
    if not model_instance:
        return "AI 報告生成失敗：模型初始化失敗。"

    news_list_text = ""
    for i, item in enumerate(cleaned_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    prompt = f"""
    You are a Global Horse Racing Chief Editor. Analyze these headlines:
    {news_list_text}
    
    Please generate a report in THREE parts in this exact order:
    1. ENGLISH VERSION
    2. TRADITIONAL CHINESE VERSION (HONG KONG)
    3. JAPANESE VERSION

    For each language:
    - **Top 5 Priority**: 5 most important global stories + one-sentence significance.
    - **Categorized Highlights**: Group others into "HK Racing", "International Racing", and "Analysis".
    - **Global Trend**: 100-word analysis of today's atmosphere.

    --- MANDATORY INSTRUCTIONS ---
    - CHINESE: Use Traditional Chinese (Hong Kong). Horse/Person/Race names MUST match official Hong Kong Jockey Club (HKJC) translations.
    - JAPANESE: Use professional terminology (e.g., 追い切り, 重賞).
    - FORMAT: Use professional Markdown.
    """

    try:
        # 強制關閉安全過濾
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model_instance.generate_content(
            prompt, 
            generation_config={"max_output_tokens": 4000, "temperature": 0.7},
            safety_settings=safety
        )
        
        # 穩定獲取文本的方法：檢查 candidates
        if response.candidates and response.candidates[0].content.parts:
            return response.text.strip()
        else:
            return f"AI 拒絕回覆。原因: {response.prompt_feedback}"
            
    except Exception as e:
        return f"AI 生成時發生錯誤: {str(e)}"

# --- 4. 主執行流程 ---
def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 'the_straight', 'anz_bloodstock', 'ttr_ausnz']
    
    for site in SITES:
        try:
            print(f"\n>>> 執行: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ 抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 錯誤: {e}")

    # A. 數據清洗
    cleaned_data = deduplicate_data(all_data)

    if cleaned_data:
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # B. 儲存原始 CSV (無論如何都會先存這個)
        df = pd.DataFrame(cleaned_data)
        csv_filename = f"data/raw_news_{date_str}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"💾 CSV 已更新: {csv_filename}")

        # C. 生成 AI 報告
        print(f"🤖 正在請求 AI 生成報告...")
        ai_report_content = generate_ai_report(cleaned_data)
        
        # D. 強制寫入 MD 檔案 (即使內容是錯誤訊息也會寫入)
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        
        print(f"✨ MD 報告已存檔: {md_filename}")
    else:
        print("\n❌ 今日無新聞。")

if __name__ == "__main__":
    run_all()
