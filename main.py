import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- 1. AI 核心設定與自動偵測 ---
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
    return None

# 初始化模型實例
model_instance = get_best_model()

# --- 2. 資料清洗工具：標題相似度比對 ---
def similarity(a, b):
    """ 計算兩個標題之間的相似度比例 """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def deduplicate_data(all_data):
    """ 進行原始數據清洗：1.網址去重 2.標題模糊去重 """
    if not all_data: return []
    
    print(f"\n🧹 開始資料清洗 (原始總數: {len(all_data)} 則)...")
    
    # 步驟 1: 網址唯一化 (URL De-duplication)
    unique_url_data = []
    seen_urls = set()
    for item in all_data:
        if item['link'] not in seen_urls:
            seen_urls.add(item['link'])
            unique_url_data.append(item)
    
    # 步驟 2: 標題相似度過濾 (Fuzzy Matching)
    final_data = []
    for item in unique_url_data:
        is_duplicate = False
        current_title = item['title']
        
        for existing_item in final_data:
            # 如果相似度超過 0.75，視為重複報導
            if similarity(current_title, existing_item['title']) > 0.75:
                is_duplicate = True
                break
        
        if not is_duplicate:
            final_data.append(item)
            
    print(f"✨ 清洗完成: 最終保留 {len(final_data)} 則精華新聞 (過濾掉 {len(all_data) - len(final_data)} 則重複)")
    return final_data

# --- 3. AI 報告生成 ---
def generate_ai_report(cleaned_headlines):
    """ 將清洗過的標題投給 AI 進行分類、排序與三語摘要 """
    if not model_instance:
        return "AI 報告生成失敗：模型未就緒。"

    # 格式化新聞清單供 AI 閱讀
    news_list_text = ""
    for i, item in enumerate(cleaned_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    prompt = f"""
    You are a professional Global Horse Racing Chief Editor. 
    Below is today's cleaned headlines from UK, HK, AU, JP, and US:
    
    {news_list_text}
    
    Please generate a comprehensive "Global Horse Racing Intelligence Report" in THREE languages in this exact order:
    1. ENGLISH VERSION
    2. TRADITIONAL CHINESE VERSION (HONG KONG)
    3. JAPANESE VERSION

    Each language section must include:
    - **Top 5 Priority News**: Select the 5 most critical stories globally and explain their significance in one sentence.
    - **Categorized Highlights**: Group remaining news into "HK & Asia Racing", "International Majors", "Bloodstock & Sales", and "Expert Analysis".
    - **Global Market Sentiment**: A 100-word summary of today's global racing trend.

    --- MANDATORY INSTRUCTIONS FOR CHINESE ---
    - Use Traditional Chinese (Hong Kong).
    - CRITICAL: Horse names, Trainers, Jockeys, and Race titles MUST follow official Hong Kong Jockey Club (HKJC) translations.
    - Examples: 'James McDonald' -> '麥道朗', 'David Hayes' -> '希斯', 'Classic Mile' -> '香港經典一哩賽', 'Caulfield' -> '考菲爾德'.

    --- MANDATORY INSTRUCTIONS FOR JAPANESE ---
    - Use professional Japanese racing terminology (e.g., 重賞, 追い切り, ワークアウト).

    Format with professional Markdown headers.
    """

    try:
        # 增加 output tokens 確保完整生成三種語言
        response = model_instance.generate_content(
            prompt,
            generation_config={"max_output_tokens": 4000, "temperature": 0.7}
        )
        return response.text.strip()
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

# --- 4. 主執行流程 ---
def run_all():
    raw_collected_data = []
    # 完整 11 個站點清單
    SITES = [
        'racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 
        'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 
        'the_straight', 'anz_bloodstock', 'ttr_ausnz'
    ]
    
    # A. 抓取階段
    for site in SITES:
        try:
            print(f"\n>>> 任務開始: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                raw_collected_data.extend(data)
                print(f"    ✅ 抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 執行錯誤: {e}")

    # B. 資料清洗 (去重)
    cleaned_data = deduplicate_data(raw_collected_data)

    if cleaned_data:
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # C. 輸出文件 1: 清洗後的原始數據 (CSV)
        df = pd.DataFrame(cleaned_data)
        csv_filename = f"data/global_news_{date_str}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 原始數據 (CSV) 已存至: {csv_filename}")

        # D. 輸出文件 2: AI 三語報告 (Markdown)
        print(f"\n🤖 啟動 AI 總編輯模式，正在分析全球情報...")
        ai_report = generate_ai_report(cleaned_data)
        
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report)
        
        print(f"✨ 三語 AI 戰情報告已完成: {md_filename}")
    else:
        print("\n❌ 今日未發現符合時間條件的新聞。")

if __name__ == "__main__":
    run_all()
