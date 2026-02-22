import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- 1. AI 核心設定與自動修復偵測 ---
API_KEY = os.getenv("GEMINI_API_KEY")

def get_best_model():
    """ 
    改良版偵測：確保不會回傳 None
    解決 'AI Model Not Ready' 與 '404 v1beta' 報錯
    """
    if not API_KEY:
        print("❌ 錯誤：找不到 GEMINI_API_KEY 環境變數")
        return None
    
    genai.configure(api_key=API_KEY)
    
    # 按照穩定度排序的候選名單
    candidate_names = [
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash', 
        'gemini-1.5-pro',
        'models/gemini-1.5-pro'
    ]
    
    print("🤖 正在初始化 AI 模型...")
    for name in candidate_names:
        try:
            model = genai.GenerativeModel(name)
            # 輕量測試：確認模型是否可用
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            print(f"✅ 成功啟用模型: {name}")
            return model
        except Exception as e:
            # print(f"   ℹ️ 跳過模型 {name}: {str(e)[:50]}")
            continue
    
    # 最終備援：強行指定，不進行預測試
    print("⚠️ 預測試失敗，強行掛載 gemini-1.5-flash...")
    return genai.GenerativeModel('gemini-1.5-flash')

# 確保模型實例被創建
model_instance = get_best_model()

# --- 2. 標題翻譯功能 ---
def translate_titles_to_en(all_data):
    """ 將標題英譯並附在後方，確保數據不亂掉 """
    if not model_instance or not all_data: 
        print("⚠️ AI 未就緒，跳過翻譯步驟")
        return all_data
    
    print(f"🌐 正在翻譯 {len(all_data)} 則標題...")
    raw_titles = [item['title'] for item in all_data]
    
    # 指令優化：確保 AI 乖乖逐行翻譯
    prompt = "Translate these racing headlines into English. ONLY English, one per line, no extra text. If it is already English, leave it:\n\n" + "\n".join(raw_titles)
    
    try:
        response = model_instance.generate_content(prompt)
        translated_lines = response.text.strip().split('\n')
        
        # 數量一致才進行合併
        if len(translated_lines) == len(all_data):
            for i in range(len(all_data)):
                orig = all_data[i]['title']
                en = translated_lines[i].strip()
                if orig.lower() != en.lower():
                    all_data[i]['title'] = f"{orig} ({en})"
            print("✅ 標題英譯附加成功")
        else:
            print(f"⚠️ 翻譯數量對位失敗 ({len(translated_lines)}/{len(all_data)})")
    except Exception as e:
        print(f"⚠️ 翻譯過程報錯: {e}")
    
    return all_data

# --- 3. 戰略型分析報告 (英文版) ---
def generate_strategic_report(all_headlines):
    """
    分析數據：Top 5 Keywords + 2-3 Outliers (針對資深編輯)
    """
    if not model_instance: return "AI Model Not Ready."

    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    prompt = f"""
    # Role
    You are a Strategic Industry Analyst for global horse racing. 
    Review the following raw data and produce a professional brief for senior editors.

    # Input Data
    {news_list_text}

    # Task (Output in ENGLISH only)
    1. **TOP 5 STRATEGIC KEYWORDS/THEMES**: 
       Identify 5 keywords/themes that dominate today's global headlines. Explain why they are trending (e.g., specific auction results, key stallion performance, or major race prep).

    2. **OUTLIER RADAR (2-3 Anomalies)**:
       Identify 2-3 headlines that are "unusual," "niche," or "out-of-the-ordinary." These stories may represent hidden industry shifts or unique local incidents worth deeper investigation. Explain why an editor should look closer.

    # Tone
    Analytical, professional, and concise. No fluff. Use Markdown.
    """

    try:
        # 關閉安全限制，防止賽馬相關詞彙被誤封
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
        return f"Report generation failed: {str(e)}"

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

# --- 5. 主執行流程 ---
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
        # A. 數據清洗
        all_data = deduplicate_data(all_data)
        
        # B. 翻譯標題 (存入 CSV 前完成)
        all_data = translate_titles_to_en(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # C. 儲存原始 CSV
        df = pd.DataFrame(all_data)
        csv_filename = f"data/raw_news_{date_str}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV saved: {csv_filename}")

        # D. 生成戰略報告
        print(f"\n🤖 Generating Strategic Report...")
        ai_report = generate_strategic_report(all_data)
        
        md_filename = f"data/strategic_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report)
        print(f"✨ Strategic Report saved: {md_filename}")
    else:
        print("\n❌ No data collected today.")

if __name__ == "__main__":
    run_all()
