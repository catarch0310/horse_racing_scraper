import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- AI 設定與自動偵測 (完全保留你的穩定邏輯) ---
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
        except Exception: continue
    return None

model_instance = get_best_model()

# --- 標題英譯功能 (保留，幫助 AI 在處理時有統一的語言基礎) ---
def translate_titles_to_en(all_data):
    if not model_instance or not all_data: return all_data
    print(f"🌐 正在翻譯 {len(all_data)} 則標題...")
    raw_titles = [item['title'] for item in all_data]
    prompt = "Translate these racing headlines into English. ONLY the English, one per line:\n\n" + "\n".join(raw_titles)
    try:
        response = model_instance.generate_content(prompt)
        translated_lines = response.text.strip().split('\n')
        if len(translated_lines) == len(all_data):
            for i in range(len(all_data)):
                orig = all_data[i]['title']
                en = translated_lines[i].strip()
                if orig.lower() != en.lower():
                    all_data[i]['title'] = f"{orig} ({en})"
            print("✅ 標題英譯附加成功")
    except: print("⚠️ 翻譯跳過")
    return all_data

# --- 重頭戲：產出針對資深編輯的英文分析報告 ---
def generate_strategic_report(all_headlines):
    """
    分析數據，找出 Top 5 關鍵詞與 2-3 個異常值 (Outliers)
    """
    if not model_instance: return "AI Model Not Ready."

    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    prompt = f"""
    # Role
    You are a Strategic Industry Analyst for the global horse racing media. 
    Review the following raw news data and produce a professional brief for senior editors and investigative journalists.

    # Input Data
    {news_list_text}

    # Task
    Perform a cross-check analysis and output the report in ENGLISH only:
    
    1. **TOP 5 STRATEGIC KEYWORDS/THEMES**: 
       Identify the 5 most frequent or significant keywords/themes currently saturating the global headlines. Briefly explain why they are trending (e.g., specific stallion names, upcoming major sales, or regulatory shifts).

    2. **OUTLIER RADAR (2-3 Anomalies)**:
       Identify 2-3 specific headlines that are "unusual," "niche," or "out-of-the-ordinary." These are stories that don't fit the main trends but might represent a hidden shift, a unique human interest story, or a local incident with potential global implications. Explain why an editor should look deeper into these.

    # Tone
    Authoritative, analytical, and concise. No fluff. 
    Use professional Markdown formatting.
    """

    try:
        # 強制關閉安全過濾，確保分析不受限
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model_instance.generate_content(
            prompt, 
            generation_config={"temperature": 0.3},
            safety_settings=safety
        )
        return response.text.strip()
    except Exception as e:
        return f"Strategic Report generation failed: {str(e)}"

def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 'the_straight', 'anz_bloodstock', 'ttr_ausnz', 'smh_racing', 'drf_news', 'racenet_news', 'daily_telegraph', 'equidia_racing']
    
    for site in SITES:
        try:
            print(f"\n>>> Task: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ Captured {len(data)} items")
        except Exception as e:
            print(f"    ❌ {site} Error: {e}")

    if all_data:
        # 1. 附加翻譯 (協助 CSV 閱讀)
        all_data = translate_titles_to_en(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # 2. 儲存原始數據 CSV
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')

        # 3. 生成戰略分析報告 (MD)
        print(f"\n🤖 Generating Strategic Insight Report...")
        ai_report = generate_strategic_report(all_data)
        
        md_filename = f"data/strategic_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report)
        print(f"✨ Report completed: {md_filename}")
    else:
        print("\n❌ No data today.")

if __name__ == "__main__":
    run_all()
