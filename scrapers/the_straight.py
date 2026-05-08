"""
scrapers/the_straight.py
The Straight (Australia) - via Google News
"""
from scrapers._google_news_helper import scrape_via_google_news


def scrape():
    return scrape_via_google_news(
        site_query="site:thestraight.com.au",
        hl="en-AU",
        gl="AU",
        ceid="AU:en",
        max_age_hours=48,
        min_title_len=10,
        debug_label="The Straight",
    )
