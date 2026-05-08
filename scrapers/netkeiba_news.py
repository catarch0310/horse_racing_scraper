"""
scrapers/netkeiba_news.py
netkeiba (Japan) - via Google News
"""
from scrapers._google_news_helper import scrape_via_google_news


def scrape():
    blacklist = ["検索結果", "コラム検索", "のニュース", "のコラム", "一覧"]
    return scrape_via_google_news(
        site_query="site:news.netkeiba.com",
        extra_query="inurl:news_view",
        hl="ja",
        gl="JP",
        ceid="JP:ja",
        max_age_hours=36,
        min_title_len=12,
        title_blacklist=blacklist,
        debug_label="Netkeiba",
    )
