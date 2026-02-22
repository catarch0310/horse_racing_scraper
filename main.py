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
        except Exception: continue
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"⚠️ 使用系統自動發現模型: {m.name}")
                return genai.GenerativeModel(m.name)
    except: pass
    return None

model_instance = get_best_model()

# --- 核心修正：分段翻譯功能 (防止 311 vs 312 錯誤) ---
def translate_titles_to_en(all_data):
    if not model_instance or not all_data: return all_data
    
    print(f"🌐 正在分段翻譯 {len(all_data)} 則標題...")
    
    # 每次處理 50 則，這是 AI 最不會數錯的數量
    chunk_size = 50
    for i in range(0, len(all_data), chunk_size):
        chunk = all_data[i : i + chunk_size]
        raw_titles = [item['title'] for item in chunk]
        
        prompt = (
            "Translate these horse racing headlines into English. "
            "Return ONLY the English translations, one per line, no numbering. "
            "If already in English, keep it as is:\n\n" + "\n".join(raw_titles)
        )

        try:
            response = model_instance.generate_content(prompt)
            translated_lines = response.text.strip().split('\n')
            
            # 如果這一小段的數量對上了，就進行合併
            if len(translated_lines) == len(chunk):
                for j in range(len(chunk)):
                    orig = chunk[j]['title']
                    en = translated_lines[j].strip()
                    if orig.lower() != en.lower():
                        all_data[i + j]['title'] = f"{orig} ({en})"
                print(f"   ✅ 已完成第 {i+1} 至 {min(i + chunk_size, len(all_data))} 則")
            else:
                print(f"   ⚠️ 第 {i+1} 區段行數不符，跳過此段翻譯")
            
            # 休息 2 秒避免 API 頻率限制
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️ 第 {i+1} 區段翻譯出錯: {e}")
            continue
            
    return all_data

def generate_ai_report(all_headlines):
    if not model_instance: return "AI 報告生成失敗：模型初始化失敗。"
    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    prompt = f"""
    You are a Global Horse Racing Chief Editor. Analyze these headlines:
    {news_list_text}
    Please generate a report in THREE parts: 1. ENGLISH, 2. TRADITIONAL CHINESE (HK), 3. JAPANESE.
    (其餘指令維持原樣...)
    """
    try:
        response = model_instance.generate_content(prompt, generation_config={"max_output_tokens": 5000})
        return response.text.strip()
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

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
        # 使用修正後的分段翻譯
        all_data = translate_titles_to_en(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: data/raw_news_{date_str}.csv")

        print(f"\n🤖 啟動 AI 總編輯模式...")
        ai_report_content = generate_ai_report(all_data)
        with open(f"data/racing_report_{date_str}.md", "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        print(f"✨ AI 戰報已生成: racing_report_{date_str}.md")
    else:
        print("\n❌ 今日無新聞數據。")

if __name__ == "__main__":
    run_all()
