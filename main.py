import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time

# --- AI 核心設定 (修正模型初始化失敗問題) ---
API_KEY = os.getenv("GEMINI_API_KEY")

def get_model():
    if not API_KEY:
        print("❌ 找不到 API KEY")
        return None
    try:
        genai.configure(api_key=API_KEY)
        # 直接使用官方最穩定的名稱
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"❌ AI 配置失敗: {e}")
        return None

# 直接初始化，不要做檢測請求
model_instance = get_model()

def generate_ai_report(all_headlines):
    """ 生成英、中、日三語報告 """
    if not model_instance:
        return "AI 報告生成失敗：模型未就緒。請檢查環境變數 GEMINI_API_KEY。"

    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    prompt = f"""
    You are a Global Horse Racing Chief Editor. 
    Analyze these headlines from UK, HK, AU, JP, and US:
    
    {news_list_text}
    
    Please generate a report in THREE parts in this exact order:
    1. ENGLISH VERSION
    2. TRADITIONAL CHINESE VERSION (HONG KONG)
    3. JAPANESE VERSION

    Requirements for each language:
    - **Top 5 Priority**: Choose the 5 most important global news and explain why in one sentence.
    - **Categorized Summaries**: Summarize others into "HK Racing", "International Racing", and "Analysis".
    - **Global Trend**: A 100-word analysis of today's atmosphere.

    --- SPECIAL INSTRUCTIONS FOR CHINESE ---
    - Use Traditional Chinese (Hong Kong).
    - **MANDATORY**: Use official Hong Kong Jockey Club (HKJC) translations for names.
    - Examples: 'David Hayes' -> '希斯', 'Aidan O'Brien' -> '岳伯仁', 'Sha Tin' -> '沙田', 'Happy Valley' -> '跑馬地'.

    --- SPECIAL INSTRUCTIONS FOR JAPANESE ---
    - Use professional Japanese horse racing terminology (e.g., 重賞, 追い切り).

    Format with professional Markdown headers.
    """

    try:
        # 增加輸出 token 限制以容納三種語言
        response = model_instance.generate_content(
            prompt, 
            generation_config={"max_output_tokens": 4000, "temperature": 0.7}
        )
        return response.text.strip()
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

def run_all():
    all_data = []
    # 媒體清單
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'netkeiba_news', 'bloodhorse_news']
    
    for site in SITES:
        try:
            print(f"\n>>> 任務開始: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ 成功抓取 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 錯誤: {e}")

    if all_data:
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # 1. 原始 CSV
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')

        # 2. AI 三語報告
        print(f"\n🤖 正在生成英/中/日三語戰報...")
        report = generate_ai_report(all_data)
        with open(f"data/racing_report_{date_str}.md", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✨ 任務完成！")
    else:
        print("\n❌ 未抓取到任何資料。")

if __name__ == "__main__":
    run_all()
