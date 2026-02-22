import pandas as pd
from datetime import datetime
import os
import importlib
import google.generativeai as genai
import time
from difflib import SequenceMatcher
import re

# --- 1. AI 核心設定 ---
API_KEY = os.getenv("GEMINI_API_KEY")

def init_ai():
    if not API_KEY:
        print("❌ 錯誤：找不到 GEMINI_API_KEY")
        return None
    try:
        genai.configure(api_key=API_KEY)
        # 直接使用模型名稱，避開 models/ 前綴以相容 v1beta
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"❌ AI 初始化失敗: {e}")
        return None

model = init_ai()

# --- 2. 智慧翻譯功能 (只翻譯中日文，節省 70% Token) ---
def is_need_translation(text):
    """檢查是否包含中日文字元"""
    # 匹配中文字元 (\u4e00-\u9fff) 或 日文假名 (\u3040-\u30ff)
    if re.search(r'[\u4e00-\u9fff\u3040-\u30ff]', text):
        return True
    return False

def translate_titles_smartly(all_data):
    if not model or not all_data:
        return all_data
    
    # 1. 篩選出需要翻譯的項目 (記錄索引)
    to_translate_indices = []
    titles_to_send = []
    
    for idx, item in enumerate(all_data):
        if is_need_translation(item['title']):
            to_translate_indices.append(idx)
            titles_to_send.append(item['title'])
    
    if not titles_to_send:
        print("✅ 所有標題均為英文，跳過翻譯步驟。")
        return all_data

    print(f"🌐 發現 {len(titles_to_send)} 則中/日文標題，準備翻譯 (其餘 {len(all_data)-len(titles_to_send)} 則跳過)...")
    
    # 2. 分段翻譯 (每 50 則一組)
    chunk_size = 50
    for i in range(0, len(titles_to_send), chunk_size):
        chunk_titles = titles_to_send[i : i + chunk_size]
        chunk_indices = to_translate_indices[i : i + chunk_size]
        
        prompt = (
            "Translate these Japanese or Chinese horse racing headlines into English. "
            "Return ONLY the translations, one per line, strictly maintaining the order:\n\n" 
            + "\n".join(chunk_titles)
        )
        
        try:
            response = model.generate_content(prompt)
            translated_lines = response.text.strip().split('\n')
            
            # 將翻譯結果塞回原始數據
            for j, orig_idx in enumerate(chunk_indices):
                if j < len(translated_lines):
                    en_text = translated_lines[j].strip()
                    # 避免 AI 廢話或重複
                    if en_text and len(en_text) > 5:
                        all_data[orig_idx]['title'] = f"{all_data[orig_idx]['title']} ({en_text})"
            
            print(f"   ✅ 已完成第 {i+1} 至 {min(i + chunk_size, len(titles_to_send))} 則翻譯")
            time.sleep(3) # 避開頻率限制
        except Exception as e:
            print(f"   ⚠️ 此段翻譯失敗: {str(e)[:50]}")
            
    return all_data

# --- 3. 戰略分析報告 (英文) ---
def generate_strategic_report(all_headlines):
    if not model: return "AI Model Not Ready."

    # 格式化清單供 AI 分析 (最多分析 200 則精華)
    news_text = ""
    for i, item in enumerate(all_headlines[:200]):
        news_text += f"ID: {i+1} | Source: {item['source']} | Title: {item['title']}\n"

    prompt = f"""
    # Role
    You are a Strategic Industry Analyst for global horse racing. 
    Review these headlines and provide a brief in ENGLISH for senior editors.

    # Raw Data
    {news_text}

    # Task
    1. **TOP 5 STRATEGIC KEYWORDS**: List 5 most important themes and briefly explain why they are trending.
    2. **OUTLIER RADAR**: Identify 2-3 niche/unusual stories with potential global impact.

    Format with professional Markdown.
    """

    try:
        safety = [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
        response = model.generate_content(prompt, safety_settings=safety)
        return response.text.strip()
    except Exception as e:
        return f"Report failed: {str(e)}"

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

# --- 5. 總執行流程 ---
def run_all():
    all_data = []
    SITES = ['racing_post', 'scmp_racing', 'singtao_racing', 'punters_au', 'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news', 'the_straight', 'anz_bloodstock', 'ttr_ausnz', 'smh_racing', 'drf_news', 'racenet_news', 'daily_telegraph', 'equidia_racing']
    
    for site in SITES:
        try:
            print(f"\n>>> 執行: {site}")
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            if data:
                for item in data: item['source'] = site
                all_data.extend(data)
                print(f"    ✅ 抓到 {len(data)} 則")
        except Exception as e:
            print(f"    ❌ {site} 錯誤: {e}")

    if all_data:
        # A. 數據去重
        all_data = deduplicate_data(all_data)
        
        # B. 智慧翻譯 (只翻譯非英文標題)
        all_data = translate_titles_smartly(all_data)

        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('data', exist_ok=True)

        # C. 儲存原始 CSV
        df = pd.DataFrame(all_data)
        df.to_csv(f"data/raw_news_{date_str}.csv", index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV 已存至: data/raw_news_{date_str}.csv")

        # D. 生成報告
        print(f"\n🤖 生成戰略報告...")
        report = generate_strategic_report(all_data)
        with open(f"data/strategic_report_{date_str}.md", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✨ 戰略報告完成: strategic_report_{date_str}.md")
    else:
        print("\n❌ 今日無新聞。")

if __name__ == "__main__":
    run_all()
