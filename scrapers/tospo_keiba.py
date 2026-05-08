"""
scrapers/tospo_keiba.py
東京スポーツ 競馬 (Japan) - via Google News
"""
from scrapers._google_news_helper import scrape_via_google_news


def scrape():
    return scrape_via_google_news(
        site_query="site:tospo-keiba.jp",
        extra_query="inurl:breaking_news",
        hl="ja",
        gl="JP",
        ceid="JP:ja",
        max_age_hours=36,
        min_title_len=6,  # 日文標題短
        debug_label="Tospo Keiba",
    )
