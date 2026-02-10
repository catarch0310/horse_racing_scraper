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
    if not API_KEY: return None
    genai.configure(api_key=API_KEY)
    
    # 嘗試多個模型名稱格式
    candidate_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-pro']
    
    print("🤖 正在偵測可用 AI 模型...")
    for name in candidate_names:
        try:
            model = genai.GenerativeModel(name)
            # 測試請求
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            print(f"✅ 成功啟用模型: {name}")
            return model
        except:
            continue
    return None

model_instance = get_best_model()

# --- 2. 資料清洗工具 ---
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def deduplicate_data(all_data):
    if not all_data: return []
    print(f"\n🧹 開始資料清洗 (原始總數: {len(all_data)} 則)...")
    
    unique_url_data = []
    seen_urls = set()
    for item in all_data:
        if item['link'] not in seen_urls:
            seen_urls.add(item['link'])
            unique_url_data.append(item)
    
    final_data = []
    for item in unique_url_data:
        is_duplicate = False
        # 提高門檻到 0.85，減少誤刪
        for existing_item in final_data:
            if similarity(item['title'], existing_item['title']) > 0.85:
                is_duplicate = True
                break
        if not is_duplicate:
            final_data.append(item)
            
    print(f"✨ 清洗完成: 最終保留 {len(final_data)} 則")
    return final_data

# --- 3. AI 報告生成 (核心修正) ---
def generate_ai_report(cleaned_headlines):
    if not model_instance:
        return "AI 報告生成失敗：模型未就緒。"

    news_list_text = ""
    for i, item in enumerate(cleaned_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    print(f"   [AI] 正在處理文本長度: {len(news_list_text)} 字元")

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
    - FORMAT: Use Markdown with bold headers.
    """

    try:
        # 關鍵修正：關閉內容安全過濾 (Safety Settings)
        # 賽馬內容常被 AI 誤認為非法賭博而封鎖，這裡強行開啟
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model_instance.generate_content(
            prompt, 
            generation_config={"max_output_tokens": 4000, "temperature": 0.7},
            safety_settings=safety_settings
        )
        
        if response.text:
            return response.text.strip()
        else:
            return "AI 回傳內容為空，可能被內容過濾器阻擋。"
            
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

# --- 4. 執行流程 ---
def run_all():
    raw_collected_data = []
    # 確保這 11 個名稱與 scrapers 資料夾檔案一致
    SITES = [
        'racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 
        'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 
        'the_straight', 'anz_bloodstock', 'ttr_ausnz'
    ]
    
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
            print(f"    ❌ {site} 錯誤: {e}")

    # 1. 清洗數據
    cleaned_data = deduplicate_data(raw_collected_data)

    if cleaned_data:
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # 2. 儲存 CSV
        df = pd.DataFrame(cleaned_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: data/raw_news_{date_str}.csv")

        # 3. 生成 AI 報告
        print(f"\n🤖 啟動 AI 總編輯模式 (三語輸出)...")
        ai_report_content = generate_ai_report(cleaned_data)
        
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        
        print(f"✨ AI 戰報已生成: {md_filename}")
        # 在終端機印出前 100 字確認有內容
        print(f"--- 內容預覽 ---\n{ai_report_content[:100]}...")
    else:
        print("\n❌ 今日無數據，不生成報告。")

if __name__ == "__main__":
    run_all()
