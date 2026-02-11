import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time

# --- AI 設定與自動偵測 (完全保留你的穩定邏輯) ---
API_KEY = os.getenv("GEMINI_API_KEY")

def get_best_model():
    """ 自動偵測可用的模型名稱，解決 404 v1beta 錯誤 """
    if not API_KEY:
        return None
    
    genai.configure(api_key=API_KEY)
    
    candidate_names = [
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash', 
        'gemini-1.5-pro',
        'models/gemini-1.5-pro'
    ]
    
    print("🤖 正在偵測可用 AI 模型...")
    for name in candidate_names:
        try:
            model = genai.GenerativeModel(name)
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            print(f"✅ 成功啟用模型: {name}")
            return model
        except Exception:
            continue
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"⚠️ 使用系統自動發現模型: {m.name}")
                return genai.GenerativeModel(m.name)
    except:
        pass
        
    return None

# 初始化模型
model_instance = get_best_model()

def generate_ai_report(all_headlines):
    """強化版 AI 總編輯報告生成：結構更專業、分析更透徹"""
    if not model_instance:
        return "AI 報告生成失敗：模型初始化失敗，請檢查 API Key 或模型權限。"

    # 整理標題清單，加入 ID 方便 AI 比對
    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    # --- 改造後的專業編輯 Prompt ---
    prompt = f"""
    # Role
    You are the Executive Chief Editor of a global premium horse racing news agency. Analyze the following headlines from UK, HK, AU, JP, US, and FRANCE:
    
    {news_list_text}
    
    # Task
    Generate a "Global Racing Strategic Intelligence Report" in THREE languages: 1. ENGLISH, 2. TRADITIONAL CHINESE (HK), 3. JAPANESE.

    # Format & Structure (Apply to EACH language version)
    
    ## 1. Top 5 Priority News (Breaking & Strategic)
    - Identify the 5 most critical stories globally.
    - Instead of just summarizing, explain their **Strategic Impact** (e.g., "This injury changes the G1 field hierarchy" or "The auction results indicate a strong market for Japanese bloodlines").

    ## 2. Regional Intelligence Matrix (Desk Summaries)
    Group and summarize the remaining news into these professional desks:
    - **Hong Kong Desk**: Local trainer/jockey moves, betting sentiment, and race updates.
    - **Oceania Desk (AU/NZ)**: Sales (Inglis/Magic Millions), industry politics, and carnival previews.
    - **Japan & Asian-Pacific Desk**: JRA updates, Japanese raiders abroad, and key workouts.
    - **EMEA & Americas Desk**: US Triple Crown preps, UK/France major stakes, and breeding news.

    ## 3. The "Global Pulse" (Cross-Border Connections)
    - A 100-word expert analysis identifying trends connecting different regions (e.g., European jockeys riding in Australia, or the impact of global currency on bloodstock sales).

    ## 4. Editor's Watchlist
    - 3 key events or horses to track in the next 48 hours.

    # Mandatory Terminology & Translation Instructions
    - **Traditional Chinese (Hong Kong)**: MUST follow official Hong Kong Jockey Club (HKJC) translations.
        - Names: David Hayes -> 希斯, James McDonald -> 麥道朗, Zac Purton -> 潘頓, Ryan Moore -> 莫雅, Aidan O'Brien -> 岳伯仁.
        - Races/Places: Sha Tin -> 沙田, Classic Mile -> 經典一哩賽, G1 -> 一級賽, Bloodstock -> 血統/育馬.
    - **Japanese**: Use professional terminology (重賞, 追い切り, ワークアウト, リーディング).

    # Style
    - Authoritative, concise, and structured with professional Markdown headers and bullet points.
    """

    try:
        # 修正：加入安全設定防止「賭博相關內容」過濾，並增加輸出長度
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model_instance.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 8000, # 增加長度確保三語不被切斷
                "temperature": 0.4,       # 降低隨機性，確保譯名精確穩定
            },
            safety_settings=safety_settings
        )
        return response.text.strip()
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

def run_all():
    all_data = []
    # 媒體清單
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 'the_straight', 'anz_bloodstock', 'ttr_ausnz', 'smh_racing', 'drf_news', 'racenet_news', 'daily_telegraph', 'equidia_racing']
    
    # 1. 執行爬蟲
    for site in SITES:
        try:
            print(f"\n>>> 任務開始: {site}")
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

        # --- 輸出文件 1：CSV ---
        df = pd.DataFrame(all_data)
        csv_filename = f"data/raw_news_{date_str}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: {csv_filename}")

        # --- 輸出文件 2：AI Markdown ---
        print(f"\n🤖 啟動 AI 總編輯模式 (三語/專業結構)...")
        ai_report_content = generate_ai_report(all_data)
        
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        
        print(f"✨ AI 戰報已生成: {md_filename}")
    else:
        print("\n❌ 今日無新聞數據，不生成報告。")

if __name__ == "__main__":
    run_all()
