import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time

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
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"⚠️ 使用系統自動發現模型: {m.name}")
                return genai.GenerativeModel(m.name)
    except: pass
    return None

model_instance = get_best_model()

# --- 新增功能：穩定版標題翻譯 ---
def translate_titles_to_en(all_data):
    """將非英文標題翻譯並附在後面，確保資料不亂掉"""
    if not model_instance or not all_data: return all_data
    
    print(f"🌐 正在翻譯 {len(all_data)} 則標題...")
    
    # 抽取標題
    raw_titles = [item['title'] for item in all_data]
    prompt = "Translate the following horse racing headlines into English. Reply with ONLY the English translations, one per line, no numbering, no extra text. If a line is already in English, keep it as is:\n\n" + "\n".join(raw_titles)

    try:
        response = model_instance.generate_content(prompt)
        translated_lines = response.text.strip().split('\n')
        
        # 核心檢查：如果 AI 回傳的行數跟原始標題一致，才進行合併
        if len(translated_lines) == len(all_data):
            for i in range(len(all_data)):
                orig = all_data[i]['title']
                en = translated_lines[i].strip()
                # 如果翻譯結果與原文明顯不同（即原文是中日文），才附加
                if orig.lower() != en.lower():
                    all_data[i]['title'] = f"{orig} ({en})"
            print("✅ 標題英譯成功並已附加")
        else:
            print(f"⚠️ 翻譯行數不符 ({len(translated_lines)} vs {len(all_data)})，為保安全放棄本次翻譯")
    except Exception as e:
        print(f"⚠️ 翻譯過程發生錯誤: {e}")
    
    return all_data

def generate_ai_report(all_headlines):
    """產出三語專業報告"""
    if not model_instance: return "AI 報告生成失敗：模型初始化失敗。"

    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

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
        # 在存檔與報名前，先進行翻譯
        all_data = translate_titles_to_en(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # 輸出 CSV (標題已附加翻譯)
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: data/raw_news_{date_str}.csv")

        # 產出 AI 報告
        print(f"\n🤖 啟動 AI 總編輯模式 (三語輸出)...")
        ai_report_content = generate_ai_report(all_data)
        with open(f"data/racing_report_{date_str}.md", "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        print(f"✨ AI 戰報已生成: racing_report_{date_str}.md")
    else:
        print("\n❌ 今日無新聞數據。")

if __name__ == "__main__":
    run_all()
