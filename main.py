import pandas as pd
from datetime import datetime
import os
import importlib
import time

# 這裡列出你所有的爬蟲模組
SCRAPER_SITES = [
    'racing_post',
    'scmp_racing',
    'on_cc_racing',
    'punters_au'
]

def run_all():
    all_data = []
    
    for site in SCRAPER_SITES:
        try:
            print(f"\n>>> 任務開始: {site}")
            # 動態載入 scrapers/ 資料夾下的模組
            module = importlib.import_module(f"scrapers.{site}")
            data = module.scrape()
            
            if data and isinstance(data, list):
                for item in data:
                    item['source'] = site
                all_data.extend(data)
                print(f"    ✅ {site} 成功抓取 {len(data)} 則")
            else:
                print(f"    ⚠️ {site} 抓取結果為空")
                
        except Exception as e:
            print(f"    ❌ {site} 執行模組出錯: {e}")

    # 彙整存檔
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs('data', exist_ok=True)
        # 檔名包含日期
        filename = f"data/racing_news_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✨ 全部完成！總計抓取 {len(all_data)} 則新聞")
        print(f"儲存路徑: {filename}")
    else:
        print("\n💀 失敗：所有網站都沒有抓到任何資料。")

if __name__ == "__main__":
    run_all()
