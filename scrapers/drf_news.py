"""
scrapers/drf_news.py
Daily Racing Form (US) - via Google News
"""
from scrapers._google_news_helper import scrape_via_google_news


def scrape():
    return scrape_via_google_news(
        site_query="site:drf.com",
        hl="en-US",
        gl="US",
        ceid="US:en",
        max_age_hours=36,
        min_title_len=10,
        debug_label="DRF",
    )
