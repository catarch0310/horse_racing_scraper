import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- 1. AI 設定與自動偵測 (完全保留你的穩定邏輯) ---
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

# --- 2. 標題翻譯 (增加休息時間以解決 429 問題) ---
def translate_titles_to_en(all_data):
    if not model_instance or not all_data: return all_data
    print(f"🌐 正在分段翻譯 {len(all_data)} 則標題...")
    
    # 增加 chunk_size 到 100 可以減少請求次數，降低 429 風險
    chunk_size = 100 
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
            
            if len(translated_lines) == len(chunk):
                for j in range(len(chunk)):
                    orig = chunk[j]['title']
                    en = translated_lines[j].strip()
                    if orig.lower() != en.lower():
                        all_data[i + j]['title'] = f"{orig} ({en})"
                print(f"   ✅ 已完成第 {i+1} 至 {min(i + chunk_size, len(all_data))} 則")
            else:
                print(f"   ⚠️ 第 {i+1} 區段行數不符，跳過翻譯")
            
            # 關鍵修改：延長休息時間至 6 秒，確保不觸發 RPM 限制
            time.sleep(6) 
        except Exception as e:
            print(f"   ⚠️ 第 {i+1} 區段翻譯出錯: {e}")
            time.sleep(10) # 報錯後休息久一點
            continue
    return all_data

# --- 3. 戰略分析報告 (加入自動重試機制) ---
def generate_strategic_brief(all_headlines):
    if not model_instance: return "AI Model Not Ready."

    news_list_text = ""
    for i, item in enumerate(all_headlines):
        news_list_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    prompt = f"""
    # Role
    You are a Strategic Industry Analyst for global horse racing. 
    Review the following news headlines collected from global sources (UK, HK, AU, JP, US, FR).

    # Raw Data Input
    {news_list_text}

    # Task (Output in ENGLISH only)
    Perform a cross-check analysis and output the following:

    ## 1. TOP 5 STRATEGIC KEYWORDS
    Identify the 5 most frequent or significant keywords/themes currently trending across global media. 
    For each keyword, briefly explain the industry context.

    ## 2. OUTLIER RADAR (2-3 Items)
    Identify 2-3 specific headlines that are "unusual," "niche," or "out-of-the-ordinary." 
    Explain why a senior editor should look deeper into these.

    # Style
    Authoritative, analytical, and concise. Use professional Markdown headers.
    """

    # 關鍵修改：報告生成加入自動重試 (針對 429 錯誤)
    for attempt in range(3):
        try:
            print(f"    🤖 嘗試生成分析報告 (第 {attempt+1} 次)...")
            safety = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            response = model_instance.generate_content(
                prompt, 
                generation_config={"temperature": 0.2},
                safety_settings=safety
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                wait_time = 25 # 如果被擋，強制休息 25 秒
                print(f"    ⚠️ 觸發頻率限制，強制休息 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                return f"Strategic brief generation failed: {str(e)}"
    
    return "Strategic brief generation failed after multiple retries due to rate limits."

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
        all_data = deduplicate_data(all_data)
        all_data = translate_titles_to_en(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: data/raw_news_{date_str}.csv")

        # 報告生成前的最終冷卻
        print(f"\n⌛ 正在為 AI 分析進行最後冷卻 (10秒)...")
        time.sleep(10)

        print(f"\n🤖 啟動 AI 戰略分析模式...")
        strategic_brief = generate_strategic_brief(all_data)
        
        md_filename = f"data/strategic_report_{date_str}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(strategic_brief)
        print(f"✨ 戰略報告已生成: {md_filename}")
    else:
        print("\n❌ 今日無數據。")

if __name__ == "__main__":
    run_all()
