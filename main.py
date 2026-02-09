import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time

# --- AI 設定與自動偵測 ---
API_KEY = os.getenv("GEMINI_API_KEY")

def get_best_model():
    """ 自動偵測可用的模型名稱，解決 404 v1beta 錯誤 """
    if not API_KEY:
        return None
    
    genai.configure(api_key=API_KEY)
    
    # 這裡列出幾個可能的模型名稱格式
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
            # 測試性的小請求，確認模型是否真的存在且可用
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            print(f"✅ 成功啟用模型: {name}")
            return model
        except Exception:
            continue
    
    # 如果候選名單都失敗，嘗試從系統清單中抓第一個可用的
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
    """將所有標題投給 AI 進行分類、排序與綜合摘要"""
    if not model_instance:
        return "AI 報告生成失敗：模型初始化失敗，請檢查 API Key 或模型權限。"

    # 整理標題清單
    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    prompt = f"""
    你是一位專業的全球賽馬新聞總編輯。以下是今天從英國、香港、澳洲、日本及美國收集到的最新賽馬新聞標題清單：
    
    {news_list_text}
    
    請根據以上內容，為我撰寫一份「全球賽馬情報摘要」，要求如下：
    
    1. **今日頭條 (Top 5 Priority)**：從清單中挑選出全球最重要的 5 則新聞，並分別用一句話解釋其重要性。
    2. **分類整理**：將剩餘新聞按「香港馬圈動態」、「國際大賽情報」、「名家分析與貼士」、「育馬與拍賣市場」等類別進行歸納摘要。
    3. **全球趨勢短評**：用約 100 字分析今日全球賽馬界的整體氛圍或值得關注的趨勢。
    4. **要求**：請全部使用「繁體中文」，風格專業且精煉。
    
    輸出格式請直接使用 Markdown 語法。
    """

    try:
        response = model_instance.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI 報告內容生成出錯: {str(e)}"

def run_all():
    all_data = []
    # 確保模組名稱正確
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'netkeiba_news', 'bloodhorse_news']
    
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
        print(f"\n🤖 啟動 AI 總編輯模式...")
        ai_report_content = generate_ai_report(all_data)
        
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        
        print(f"✨ AI 戰報已生成: {md_filename}")
    else:
        print("\n❌ 今日無新聞數據，不生成報告。")

if __name__ == "__main__":
    run_all()
