"""
diagnose_broken_scrapers.py
============================
診斷 3 個 NO DATA scraper 對應網站的現行 HTML 結構。

設計：
- 抓網站 raw HTML、寫到 ./diagnose_output/
- stdout 印出統計資訊，同時寫一份 summary.md
- 在 GitHub Actions 上跑時，由 workflow 自動 commit diagnose_output/ 回 repo
"""

import os
import re
from collections import Counter

import requests
from bs4 import BeautifulSoup

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

OUTPUT_DIR = "diagnose_output"


def diagnose(name: str, url: str) -> dict:
    print(f"\n{'='*70}")
    print(f"🔬 {name}")
    print(f"   URL: {url}")
    print(f"{'='*70}")

    summary = {"name": name, "url": url}

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            timeout=20,
        )
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        summary["error"] = str(e)
        return summary

    print(f"   Status: {resp.status_code}")
    print(f"   Final URL: {resp.url}")
    print(f"   HTML length: {len(resp.text)} chars")
    summary["status"] = resp.status_code
    summary["final_url"] = resp.url
    summary["html_length"] = len(resp.text)

    # 寫 raw HTML
    out_path = os.path.join(OUTPUT_DIR, f"{name}_sample.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"   ✓ Saved: {out_path}")

    if resp.status_code != 200:
        print(f"   ⚠️ Non-200 — likely blocked. Raw response saved for inspection.")
        summary["likely_blocked"] = True
        if "cloudflare" in resp.text.lower() or "challenge-platform" in resp.text:
            print(f"   🛡️  Cloudflare challenge detected")
            summary["cloudflare"] = True
        return summary

    soup = BeautifulSoup(resp.text, "html.parser")

    all_links = soup.find_all("a", href=True)
    print(f"\n   📊 Total <a> tags with href: {len(all_links)}")
    summary["total_a_tags"] = len(all_links)

    news_links = [a for a in all_links if "/news/" in a["href"]]
    print(f"   📊 Links with '/news/' in href: {len(news_links)}")
    summary["news_links_count"] = len(news_links)

    class_counter = Counter()
    for a in all_links:
        for cls in a.get("class", []):
            class_counter[cls] += 1

    print(f"\n   📊 Top 10 most common <a> class names:")
    top_classes = class_counter.most_common(10)
    for cls, count in top_classes:
        print(f"      [{count}x] {cls}")
    summary["top_classes"] = [{"class": c, "count": n} for c, n in top_classes]

    print(f"\n   📋 First 5 news link samples:")
    samples = []
    for i, a in enumerate(news_links[:5]):
        href = a["href"]
        text = a.get_text(strip=True)[:80]
        cls = " ".join(a.get("class", [])) or "(no class)"
        print(f"      [{i+1}] href={href[:80]}")
        print(f"          text=\"{text}\"")
        print(f"          class={cls}")
        samples.append({"href": href, "text": text, "class": cls})
    summary["news_link_samples"] = samples

    title_pattern = re.compile(r"(title|headline|news-item|article|story|post|card)", re.I)
    matching = [c for c in class_counter.keys() if title_pattern.search(c)]
    if matching:
        print(f"\n   📊 Classes matching title/headline/article/card patterns:")
        for cls in matching[:15]:
            print(f"      - {cls}")
        summary["title_like_classes"] = matching[:15]

    is_react = "__NEXT_DATA__" in resp.text or "_app-" in resp.text or 'data-reactroot' in resp.text
    is_cloudflare = "challenge-platform" in resp.text or "cf-ray" in str(resp.headers).lower()
    server = resp.headers.get("server", "")
    print(f"\n   📊 Framework / infra hints:")
    print(f"      React/Next.js: {is_react}")
    print(f"      Cloudflare: {is_cloudflare}")
    print(f"      Server header: {server or '(none)'}")

    summary["framework"] = {
        "react_next": is_react,
        "cloudflare": is_cloudflare,
        "server": server,
    }
    return summary


def write_summary_md(summaries: list[dict]):
    lines = ["# Diagnose Output: Broken Scrapers\n"]
    for s in summaries:
        lines.append(f"## {s['name']}\n")
        lines.append(f"- URL: {s['url']}")
        if "error" in s:
            lines.append(f"- ❌ Request failed: `{s['error']}`")
            lines.append("")
            continue
        lines.append(f"- Status: {s.get('status')}")
        lines.append(f"- Final URL: {s.get('final_url')}")
        lines.append(f"- HTML length: {s.get('html_length')} chars")
        if s.get("likely_blocked"):
            lines.append(f"- 🛡️ **Likely blocked** (non-200 response)")
            if s.get("cloudflare"):
                lines.append(f"- 🛡️ **Cloudflare challenge detected**")
        else:
            lines.append(f"- Total `<a>` tags: {s.get('total_a_tags')}")
            lines.append(f"- News links found: {s.get('news_links_count')}")
            fw = s.get("framework", {})
            lines.append(f"- React/Next: {fw.get('react_next')} | Cloudflare: {fw.get('cloudflare')} | Server: `{fw.get('server')}`")
            if s.get("top_classes"):
                lines.append("\n**Top class names on `<a>` tags:**")
                for c in s["top_classes"]:
                    lines.append(f"- `{c['class']}` ({c['count']}x)")
            if s.get("title_like_classes"):
                lines.append("\n**Title-like classes:**")
                for c in s["title_like_classes"]:
                    lines.append(f"- `{c}`")
            if s.get("news_link_samples"):
                lines.append("\n**Sample news links:**")
                for sample in s["news_link_samples"]:
                    lines.append(f"- href: `{sample['href']}`")
                    lines.append(f"  - text: \"{sample['text']}\"")
                    lines.append(f"  - class: `{sample['class']}`")
        lines.append("")

    out = os.path.join(OUTPUT_DIR, "summary.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n✓ Summary written: {out}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Diagnosing {len(TARGETS)} broken scraper sites...")
    print(f"Output directory: {OUTPUT_DIR}/\n")

    summaries = []
    for name, url in TARGETS.items():
        try:
            s = diagnose(name, url)
            summaries.append(s)
        except Exception as e:
            print(f"   💀 Unexpected: {e}")
            summaries.append({"name": name, "url": url, "error": str(e)})

    write_summary_md(summaries)
    print(f"\n{'='*70}")
    print("✅ Done. Check ./diagnose_output/")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
