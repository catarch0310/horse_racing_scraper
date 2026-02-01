import pandas as pd
from datetime import datetime
import os
import importlib

# 務必確保這三個名稱與 scrapers 資料夾下的檔案名一致 (底線)
SCRAPER_SITES = [
    'racing_post',
    'scmp_racing',
    'on_cc_racing',
]

def run_all():
    all_headlines = []
    
    for site in SCRAPER_SITES:
        try:
            print(f"\n========== 啟動 {site} 任務 ==========")
            module = importlib.import_module(f"scrapers.{site}")
            # 呼叫各模組的 scrape 函式
            data = module.scrape()
            
            if data and isinstance(data, list):
                for item in data:
                    item['source'] = site
                all_headlines.extend(data)
                print(f"✅ {site} 執行成功：抓到 {len(data)} 則")
            else:
                print(f"⚠️ {site} 回傳資料為空")
            
        except Exception as e:
            print(f"❌ {site} 模組發生錯誤: {e}")

    # 彙整存檔
    if all_headlines:
        df = pd.DataFrame(all_headlines)
        
        # 確保 data 目錄存在
        os.makedirs('data', exist_ok=True)
        
        # 存檔 (使用 utf-8-sig 確保 Excel 開啟中文不亂碼)
        filename = f"data/all_racing_news_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"\n✨ 全部完成！")
        print(f"共計抓取: {len(all_headlines)} 則新聞")
        print(f"儲存路徑: {filename}")
    else:
        print("\n💀 嚴重錯誤：所有爬蟲都沒有抓到任何資料！")

if __name__ == "__main__":
    run_all()
