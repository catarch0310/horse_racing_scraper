"""
scrapers/_google_news_helper.py
================================
共用工具：透過 Google News RSS 抓某個 site 的近期文章，並解出真實 URL。

設計考量：
1. 不用 `when:Xh` 條件（命中率低），改在 Python 端用 pubDate 過濾
2. RSS link 是 Google redirect URL（trafilatura 抓不到內文），所以優先取 <source url> 屬性
3. <source url> 是 Google News RSS 標準欄位，幾乎所有 item 都有
4. 多語系支援（hl/gl/ceid 從外部傳入）
"""

import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)


def fetch_google_news_rss(
    site_query: str,
    extra_query: str = "",
    hl: str = "en-US",
    gl: str = "US",
    ceid: str = "US:en",
    timeout: int = 20,
) -> Optional[str]:
    """向 Google News RSS 發 request，回傳 raw XML 字串。失敗回傳 None。

    site_query 範例: "site:thestraight.com.au"
    extra_query 範例: '"horse racing"' 或空字串
    """
    full_query = site_query
    if extra_query:
        full_query += f" {extra_query}"
    encoded = urllib.parse.quote(full_query)

    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=timeout,
        )
        if resp.status_code != 200:
            print(f"    ⚠️ Google News RSS 回 {resp.status_code}")
            return None
        return resp.text
    except Exception as e:
        print(f"    ❌ Google News RSS 請求失敗: {e}")
        return None


def parse_rss_items(xml_text: str) -> list[dict]:
    """從 Google News RSS XML 解出所有 item，回傳 list of dict。

    每個 dict 包含: title, real_url, google_url, pub_date, source_name
    real_url 會優先用 <source url=""> 屬性 (真實網站 URL)，
    fallback 才用 <link> (Google redirect URL)。
    """
    if not xml_text:
        return []

    items_raw = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
    parsed = []

    for raw in items_raw:
        # title (處理 CDATA)
        t_match = re.search(
            r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
            raw, re.DOTALL,
        )
        # link (Google redirect URL)
        l_match = re.search(
            r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>",
            raw, re.DOTALL,
        )
        # pubDate
        d_match = re.search(
            r"<pubDate>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</pubDate>",
            raw, re.DOTALL,
        )
        # 關鍵: <source url="https://real.site/article">Site Name</source>
        # 這個 url 屬性才是真實網站 URL
        source_match = re.search(
            r'<source url="([^"]+)"[^>]*>(.*?)</source>',
            raw, re.DOTALL,
        )

        if not (t_match and l_match):
            continue

        raw_title = t_match.group(1).strip()
        # Google News 會在標題後面加 " - 來源名"，去掉
        title = re.split(r"\s+-\s+", raw_title)[0].strip()

        google_link = l_match.group(1).strip()
        pub_date = d_match.group(1).strip() if d_match else ""

        if source_match:
            real_url = source_match.group(1).strip()
            source_name = source_match.group(2).strip()
        else:
            # Fallback: 沒有 <source>，只能用 Google redirect URL
            real_url = google_link
            source_name = ""

        parsed.append({
            "title": title,
            "real_url": real_url,
            "google_url": google_link,
            "pub_date": pub_date,
            "source_name": source_name,
        })

    return parsed


def filter_by_age(
    items: list[dict],
    max_age_hours: int = 36,
) -> list[dict]:
    """過濾掉超過 max_age_hours 的 item。"""
    now_utc = datetime.now(timezone.utc)
    threshold = now_utc - timedelta(hours=max_age_hours)
    kept = []

    for item in items:
        try:
            d = pd.to_datetime(item["pub_date"])
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            if d >= threshold:
                item["parsed_date"] = d
                kept.append(item)
        except Exception:
            # 解析失敗的暫時保留 (寧可多抓也不要漏)
            item["parsed_date"] = None
            kept.append(item)

    return kept


def scrape_via_google_news(
    site_query: str,
    extra_query: str = "",
    hl: str = "en-US",
    gl: str = "US",
    ceid: str = "US:en",
    max_age_hours: int = 36,
    min_title_len: int = 10,
    title_blacklist: Optional[list[str]] = None,
    title_whitelist: Optional[list[str]] = None,
    debug_label: str = "",
) -> list[dict]:
    """High-level wrapper: 抓 → 解析 → 過濾。

    回傳 list of {"title", "link", "time"}，相容 main.py 既有格式。
    `link` 是真實網站 URL（優先 <source url>），讓 trafilatura 能抓內文。

    title_whitelist: 標題必須**包含至少一個**這些關鍵字（不分大小寫）才保留
    title_blacklist: 標題包含**任何一個**這些關鍵字就丟棄（不分大小寫）
    """
    print(f"--- Google News 代理: {debug_label or site_query} ---")

    xml = fetch_google_news_rss(site_query, extra_query, hl, gl, ceid)
    if not xml:
        return []

    raw_items = parse_rss_items(xml)
    print(f"    [Debug] RSS 原始項目: {len(raw_items)}")

    if not raw_items:
        return []

    fresh = filter_by_age(raw_items, max_age_hours)
    print(f"    [Debug] {max_age_hours}h 內: {len(fresh)}")

    extracted = []
    seen_links = set()

    for item in fresh:
        title = item["title"]
        if len(title) < min_title_len:
            continue

        title_lower = title.lower()

        if title_blacklist and any(b.lower() in title_lower for b in title_blacklist):
            continue
        if title_whitelist and not any(w.lower() in title_lower for w in title_whitelist):
            continue

        link = item["real_url"]
        if link in seen_links:
            continue
        seen_links.add(link)

        # 格式化時間
        time_str = ""
        if item.get("parsed_date") is not None:
            time_str = item["parsed_date"].strftime("%Y-%m-%d %H:%M")
        else:
            time_str = item["pub_date"]

        extracted.append({
            "title": title,
            "link": link,
            "time": time_str,
        })

    print(f"    ✅ 通過過濾: {len(extracted)} 則")
    return extracted
