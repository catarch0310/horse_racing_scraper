import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time

# --- AI 設定與自動偵測 ---
API_KEY = os.getenv("GEMINI_API_KEY")

def get_best_model():
    if not API_KEY: return None
    genai.configure(api_key=API_KEY)
    candidate_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-pro']
    for name in candidate_names:
        try:
            model = genai.GenerativeModel(name)
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            return model
        except: continue
    return None

model_instance = get_best_model()

def generate_ai_report(all_headlines):
    """將所有標題投給 AI 生成英、中、日三語報告"""
    if not model_instance:
        return "AI 報告生成失敗：模型初始化失敗。"

    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    # --- 強化版三語 Prompt ---
    prompt = f"""
    You are a high-level Global Horse Racing Chief Editor. Below is today's headlines from UK, HK, AU, JP, and US:
    
    {news_list_text}
    
    Please generate a comprehensive "Global Horse Racing Intelligence Report" in THREE distinct languages in the following order:
    1. ENGLISH VERSION
    2. TRADITIONAL CHINESE VERSION (HONG KONG)
    3. JAPANESE VERSION

    For EACH language section, include:
    - **Top 5 Priority News**: Select the most important 5 stories globally and explain their significance in one sentence.
    - **Categorized Summaries**: Group remaining news into "HK Racing", "International Racing", "Tips & Analysis", and "Breeding & Sales".
    - **Global Trend Analysis**: A 100-word analysis of today's global racing atmosphere.

    --- CRITICAL INSTRUCTIONS ---
    - For the CHINESE version: 
        - Use Traditional Chinese (Hong Kong).
        - **MANDATORY**: All horse names, jockeys, trainers, and race titles MUST follow official Hong Kong Jockey Club (HKJC) translations. 
        - Examples: 'Aidan O'Brien' -> '岳伯仁', 'David Hayes' -> '希斯', 'Classic Mile' -> '香港經典一哩賽', 'Sha Tin' -> '沙田'.
    - For the JAPANESE version: 
        - Use professional Japanese racing terminology (e.g., 追い切り, リーディング, 重賞).
    - Format: Use professional Markdown with clear, bold headers for each language.
    """

    try:
        # 由於需要生成三種語言，內容較長，我們稍微調高輸出長度限制
        response = model_instance.generate_content(
            prompt,
            generation_config={"max_output_tokens": 4096, "temperature": 0.7}
        )
        return response.text.strip()
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

def run_all():
    all_data = []
    # 執行所有媒體模組
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'netkeiba_news', 'bloodhorse_news']
    
    for site in SITES:
        try:
            print(f"\n>>> 正在抓取: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ 抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 錯誤: {e}")

    if all_data:
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # 1. 儲存原始 CSV
        df = pd.DataFrame(all_data)
        csv_filename = f"data/raw_news_{date_str}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: {csv_filename}")

        # 2. 產出 AI 三語報告
        print(f"\n🤖 啟動 AI 三語總編輯模式 (英/中/日)...")
        ai_report_content = generate_ai_report(all_data)
        
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        
        print(f"✨ 三語 AI 戰報已完成: {md_filename}")
    else:
        print("\n❌ 今日無新聞數據。")

if __name__ == "__main__":
    run_all()
