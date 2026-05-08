"""
scrapers/daily_telegraph.py
Daily Telegraph (Australia) - via Google News, 過濾賽馬內容
"""
from scrapers._google_news_helper import scrape_via_google_news


def scrape():
    # Daily Telegraph 全站新聞，需要過濾出賽馬相關
    racing_keywords = [
        "race", "horse", "jockey", "trainer", "bet", "stakes",
        "cup", "racing", "colt", "filly", "punters", "mile",
        "handicap", "gelding", "thoroughbred",
    ]
    return scrape_via_google_news(
        site_query="site:dailytelegraph.com.au",
        extra_query='"horse racing"',
        hl="en-AU",
        gl="AU",
        ceid="AU:en",
        max_age_hours=36,
        min_title_len=15,
        title_whitelist=racing_keywords,
        title_blacklist=["dailytelegraph"],
        debug_label="Daily Telegraph",
    )
