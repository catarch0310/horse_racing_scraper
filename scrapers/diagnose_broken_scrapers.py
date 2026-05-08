"""
diagnose_broken_scrapers.py
============================
抓 3 個 NO DATA scraper 對應網站的 raw HTML 樣本，方便診斷現行結構。

執行方式 (本機或 GitHub Actions)：
    python3 diagnose_broken_scrapers.py

產出：3 個檔案 in /tmp:
    - punters_au_sample.html
    - racing_com_sample.html
    - racenet_news_sample.html

加上 stdout 印出每個網站的「候選 selectors」與「找到 N 個 a 標籤連結」統計。
"""

import re
import requests
from bs4 import BeautifulSoup
from collections import Counter

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

TARGETS = {
    "punters_au":   "https://www.punters.com.au/news/latest-news/",
    "racing_com":   "https://www.racing.com/news/latest-news",
    "racenet_news": "https://www.racenet.com.au/news",
}


def diagnose(name: str, url: str):
    print(f"\n{'='*70}")
    print(f"🔬 {name}")
    print(f"   URL: {url}")
    print(f"{'='*70}")

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            timeout=20,
        )
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return

    print(f"   Status: {resp.status_code}")
    print(f"   Final URL: {resp.url}")
    print(f"   HTML length: {len(resp.text)} chars")

    if resp.status_code != 200:
        # 仍寫檔，方便看是什麼錯誤頁
        with open(f"/tmp/{name}_sample.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"   ⚠️ Non-200, but raw response saved to /tmp/{name}_sample.html")
        return

    # 寫 raw HTML
    out_path = f"/tmp/{name}_sample.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"   ✓ Raw HTML saved: {out_path}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # 統計 1: 所有 a 標籤的 href pattern
    all_links = soup.find_all("a", href=True)
    print(f"\n   📊 Total <a> tags with href: {len(all_links)}")

    # 統計 2: 包含 /news/ 的連結
    news_links = [a for a in all_links if "/news/" in a["href"]]
    print(f"   📊 Links with '/news/' in href: {len(news_links)}")

    # 統計 3: class 名出現頻率 (找出可能的新聞區塊 class)
    class_counter = Counter()
    for a in all_links:
        for cls in a.get("class", []):
            class_counter[cls] += 1

    print(f"\n   📊 Top 10 most common <a> class names:")
    for cls, count in class_counter.most_common(10):
        print(f"      [{count}x] {cls}")

    # 統計 4: 看看前 5 個 news links 長什麼樣 (sample)
    print(f"\n   📋 First 5 news link samples:")
    for i, a in enumerate(news_links[:5]):
        href = a["href"]
        text = a.get_text(strip=True)[:60]
        cls = " ".join(a.get("class", [])) or "(no class)"
        print(f"      [{i+1}] href={href[:80]}")
        print(f"          text=\"{text}\"")
        print(f"          class={cls}")

    # 統計 5: 找帶有 "title" / "headline" / "news-item" 字眼的 class
    title_class_pattern = re.compile(r"(title|headline|news-item|article|story|post)", re.I)
    matching_classes = [c for c in class_counter.keys() if title_class_pattern.search(c)]
    if matching_classes:
        print(f"\n   📊 Classes matching title/headline/news-item/article patterns:")
        for cls in matching_classes[:15]:
            print(f"      - {cls}")

    # 統計 6: 是否疑似 React/Next.js (從 HTML 線索判斷)
    is_react = "__NEXT_DATA__" in resp.text or "_app-" in resp.text
    is_cloudflare = "challenge-platform" in resp.text or "cf-ray" in dict(resp.headers).get("server", "")
    print(f"\n   📊 Framework hints:")
    print(f"      React/Next.js: {is_react}")
    print(f"      Cloudflare: {is_cloudflare}")
    print(f"      Server header: {resp.headers.get('server', '(none)')}")


def main():
    print("Diagnosing 3 broken scraper sites...")
    for name, url in TARGETS.items():
        diagnose(name, url)
    print(f"\n{'='*70}")
    print("✅ Done. Three sample HTMLs saved to /tmp/")
    print("Please share stdout output + /tmp/*.html for further diagnosis.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
