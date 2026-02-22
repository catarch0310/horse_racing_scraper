import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher

# --- 1. AI 核心設定 ---
API_KEY = os.getenv("GEMINI_API_KEY")

def init_model():
    if not API_KEY:
        print("❌ 錯誤：找不到 GEMINI_API_KEY")
        return None
    try:
        genai.configure(api_key=API_KEY)
        # 修正：直接使用最基本的字串，避開 v1beta 404 問題
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"❌ 模型初始化異常: {e}")
        return None

model = init_model()

# --- 2. 標題翻譯 (分段處理 350 則) ---
def translate_all_titles(all_data):
    if not model or not all_data:
        return all_data
    
    print(f"🌐 正在翻譯 {len(all_data)} 則標題 (分段模式)...")
    
    # 將資料切成 50 則一組，避免 AI 斷頭
    chunk_size = 50
    for i in range(0, len(all_data), chunk_size):
        chunk = all_data[i:i + chunk_size]
        raw_titles = [item['title'] for item in chunk]
        
        prompt = "Translate these horse racing headlines to English. One per line, NO numbering. If already English, keep original:\n\n" + "\n".join(raw_titles)
        
        try:
            response = model.generate_content(prompt)
            translated_lines = response.text.strip().split('\n')
            
            # 對齊並寫入
            for j, item in enumerate(chunk):
                if j < len(translated_lines):
                    en_title = translated_lines[j].strip()
                    if item['title'].lower() != en_title.lower():
                        item['title'] = f"{item['title']} ({en_title})"
            
            print(f"   ✅ 已完成第 {i} 到 {i+len(chunk)} 則翻譯")
            time.sleep(2) # 避開 15 RPM 限制
        except Exception as e:
            print(f"   ⚠️ 此段翻譯跳過: {e}")
            
    return all_data

# --- 3. 戰略報告 (針對資深編輯) ---
def generate_strategic_report(all_headlines):
    if not model: return "AI Model Not Ready."

    # 抽取前 200 則做分析即可（避免文本過長導致超時）
    news_text = ""
    for i, item in enumerate(all_headlines[:200]):
        news_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    prompt = f"""
    # Role
    You are a Strategic Industry Analyst for global horse racing media.
    Review the following headlines and produce a brief in ENGLISH for senior editors.

    # Data
    {news_text}

    # Task
    1. **TOP 5 STRATEGIC KEYWORDS/THEMES**: Identify the 5 most significant recurring themes across these global headlines. Explain the industry context for each.
    2. **OUTLIER RADAR (2-3 items)**: Find the most "unusual" or "niche" stories that differ from mainstream trends but merit deeper investigation.

    Output in Markdown. Be concise and authoritative.
    """

    try:
        # 強制關閉安全過濾
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model.generate_content(prompt, safety_settings=safety)
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

# --- 5. 主程式 ---
def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 'the_straight', 'anz_bloodstock', 'ttr_ausnz', 'smh_racing', 'drf_news', 'racenet_news', 'daily_telegraph', 'equidia_racing']
    
    for site in SITES:
        try:
            print(f">>> Task: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
        except Exception as e:
            print(f"❌ {site} 錯誤: {e}")

    if all_data:
        # A. 清洗
        all_data = deduplicate_data(all_data)
        
        # B. 分段翻譯 (確保 350 則不中斷)
        all_data = translate_all_titles(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # C. 存 CSV
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"💾 CSV 已存檔")

        # D. 存報告 (MD)
        print(f"🤖 生成戰略報告...")
        report = generate_strategic_report(all_data)
        with open(f"data/strategic_report_{date_str}.md", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✨ 報告已存檔")
    else:
        print("❌ 無數據")

if __name__ == "__main__":
    run_all()
