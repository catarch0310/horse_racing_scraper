import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time

# --- AI 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    # 使用 gemini-1.5-flash，處理速度快且上下文視窗大，適合處理整份清單
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def generate_ai_report(all_headlines):
    """將所有標題投給 AI 進行分類、排序與綜合摘要"""
    if not model or not all_headlines:
        return "AI 報告生成失敗：缺少數據或 API Key。"

    # 將所有新聞整理成帶有來源的清單
    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"{i+1}. [{item['source']}] {item['title']}\n"

    # 構造給 AI 的總編輯指令
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
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI 報告生成出錯: {e}"

def run_all():
    all_data = []
    # 執行所有已開發完成的媒體模組
    SITES = [
        'racing_post', 
        'scmp_racing', 
        'singtao_racing', 
        'punters_au', 
        'netkeiba_news', 
        'bloodhorse_news'
    ]
    
    # 1. 執行爬蟲抓取
    for site in SITES:
        try:
            print(f"\n>>> 正在抓取: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data:
                    item['source'] = site
                all_data.extend(data)
                print(f"    ✅ 成功抓取 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 出錯: {e}")

    if all_data:
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # --- 輸出文件 1：原始數據 Excel (CSV) ---
        df = pd.DataFrame(all_data)
        csv_filename = f"data/raw_news_{date_str}.csv"
        # 使用 utf-8-sig 確保 Excel 開啟中文不亂碼
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 原始數據已存至: {csv_filename}")

        # --- 輸出文件 2：AI 綜合報告 (Markdown) ---
        print(f"\n🤖 正在啟動 AI 總編輯模式，分析 {len(all_data)} 則情報...")
        ai_report_content = generate_ai_report(all_data)
        
        md_filename = f"data/racing_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ai_report_content)
        
        print(f"✨ AI 戰情日報已生成: {md_filename}")
        print("\n--- AI 摘要預覽 ---\n")
        print(ai_report_content[:300] + "...") 
    else:
        print("\n❌ 今日未抓取到任何資料。")

if __name__ == "__main__":
    run_all()
