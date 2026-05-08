"""
scrapers/racenet_news.py
Racenet (Australia) — uses cloudscraper to bypass WAF
"""
import re
from datetime import datetime, timedelta

import cloudscraper
from bs4 import BeautifulSoup


def parse_racenet_time(time_str: str) -> datetime:
    """Parse '2 hours ago', '30 mins ago', 'a day ago' etc."""
    now = datetime.now()
    s = time_str.lower().strip()
    try:
        m = re.search(r"\d+", s)
        n = int(m.group()) if m else 1
        if "min" in s:
            return now - timedelta(minutes=n)
        if "hour" in s:
            return now - timedelta(hours=n)
        if "day" in s:
            return now - timedelta(days=n)
    except Exception:
        pass
    return now


def scrape():
    news_url = "https://www.racenet.com.au/news"
    base_url = "https://www.racenet.com.au"

    print("--- Racenet (cloudscraper mode) ---")

    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "mobile": False},
        )
        res = scraper.get(news_url, timeout=30)
        if res.status_code != 200:
            print(f"    ❌ Status {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        extracted_data = []
        seen_links = set()
        threshold = datetime.now() - timedelta(hours=36)

        # 多策略 selector — 從原本的 news-item 開始試，再 fallback 到任何含 /news/ 的連結
        articles = soup.find_all("a", class_=re.compile(r"news-item", re.I))

        if not articles:
            # Fallback 1: 找標題類 class 的父連結
            title_nodes = soup.select(
                '[class*="news-item__title"], [class*="NewsItem"], [class*="article-card"]'
            )
            articles = [n.find_parent("a") for n in title_nodes if n.find_parent("a")]

        if not articles:
            # Fallback 2: 任何指向 /news/ 的連結 (寬鬆但有風險)
            articles = soup.find_all(
                "a", href=re.compile(r"/news/[a-z0-9\-]+/?$", re.I)
            )

        print(f"    Found {len(articles)} candidate links")

        for a in articles:
            link = a.get("href", "")
            if not link:
                continue
            full_link = base_url + link if link.startswith("/") else link
            if full_link in seen_links:
                continue

            # Title
            title_node = a.select_one(
                '[class*="news-item__title"], [class*="title"], h2, h3, h4'
            )
            title = title_node.get_text(strip=True) if title_node else a.get_text(strip=True)

            # Time
            time_node = a.find(string=re.compile(r"ago|day", re.I))
            time_text = time_node.strip() if time_node else "0 hours ago"

            if len(title) > 10:
                pub_date = parse_racenet_time(time_text)
                if pub_date >= threshold:
                    seen_links.add(full_link)
                    extracted_data.append({
                        "title": title,
                        "link": full_link,
                        "time": pub_date.strftime("%Y-%m-%d %H:%M"),
                    })

        print(f"    ✅ Racenet: {len(extracted_data)} items")
        return extracted_data

    except Exception as e:
        print(f"    ❌ Racenet error: {e}")
        return []