"""
diagnose_round2.py
==================
第二輪診斷：
- punters_au, racenet_news: 用 cloudscraper 嘗試繞反爬
- racing_com: 從 HTML 中抽 __NEXT_DATA__ / window.__INITIAL_STATE__ 之類的 JSON blob

執行方式：GitHub Actions workflow_dispatch
"""

import json
import os
import re

import requests

OUTPUT_DIR = "diagnose_output"

# 試多種 user agent 和 header 組合
HEADER_VARIANTS = [
    # 1. 標準 Chrome desktop
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    },
    # 2. Mobile Safari
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    },
]

CLOUDSCRAPER_TARGETS = {
    "punters_au":   "https://www.punters.com.au/news/latest-news/",
    "racenet_news": "https://www.racenet.com.au/news",
}


def try_cloudscraper(name: str, url: str) -> dict:
    """嘗試 cloudscraper 繞反爬。"""
    print(f"\n{'='*70}")
    print(f"🛡️  cloudscraper attempt: {name}")
    print(f"   URL: {url}")
    print(f"{'='*70}")

    result = {"name": name, "url": url, "method": "cloudscraper"}

    try:
        import cloudscraper
    except ImportError:
        result["error"] = "cloudscraper not installed"
        print(f"   ❌ cloudscraper not installed")
        return result

    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "mobile": False},
        )
        resp = scraper.get(url, timeout=30)
        result["status"] = resp.status_code
        result["html_length"] = len(resp.text)
        print(f"   Status: {resp.status_code}")
        print(f"   HTML length: {len(resp.text)} chars")

        if resp.status_code == 200 and len(resp.text) > 5000:
            out_path = os.path.join(OUTPUT_DIR, f"{name}_cloudscraper.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"   ✅ Saved: {out_path}")
            result["success"] = True

            # 簡單統計：找 a 標籤的 href 中包含 /news/
            news_link_count = len(re.findall(r'href="[^"]*?/news/[^"]+', resp.text))
            result["news_links_in_raw"] = news_link_count
            print(f"   Found ~{news_link_count} '/news/' refs in raw HTML")
        else:
            result["success"] = False
            print(f"   ❌ Still blocked or empty")

    except Exception as e:
        result["error"] = str(e)
        print(f"   ❌ Exception: {e}")

    return result


def try_header_variants(name: str, url: str) -> dict:
    """嘗試多種 header 組合 (純 requests)。"""
    print(f"\n{'='*70}")
    print(f"🔧 header variants: {name}")
    print(f"{'='*70}")

    result = {"name": name, "url": url, "attempts": []}

    for i, headers in enumerate(HEADER_VARIANTS):
        ua_short = headers["User-Agent"].split(")")[0][:50]
        print(f"   [{i+1}] UA: {ua_short}...")
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            attempt = {"variant": i + 1, "status": resp.status_code, "length": len(resp.text)}
            result["attempts"].append(attempt)
            print(f"       → Status {resp.status_code}, {len(resp.text)} chars")
            if resp.status_code == 200 and len(resp.text) > 5000:
                out_path = os.path.join(OUTPUT_DIR, f"{name}_variant{i+1}.html")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                print(f"       ✅ Saved: {out_path}")
                attempt["success"] = True
        except Exception as e:
            print(f"       ❌ {e}")
            result["attempts"].append({"variant": i + 1, "error": str(e)})

    return result


def analyze_racing_com() -> dict:
    """racing.com 是 React SPA — 抽 JSON blob。"""
    name = "racing_com"
    url = "https://www.racing.com/news/latest-news"
    print(f"\n{'='*70}")
    print(f"⚛️  React SPA analysis: {name}")
    print(f"   URL: {url}")
    print(f"{'='*70}")

    result = {"name": name, "url": url}

    try:
        resp = requests.get(url, headers=HEADER_VARIANTS[0], timeout=20)
    except Exception as e:
        result["error"] = str(e)
        return result

    html = resp.text
    result["status"] = resp.status_code
    result["html_length"] = len(html)
    print(f"   Status: {resp.status_code}")
    print(f"   HTML length: {len(html)} chars")

    # 找各種常見 React/Next.js JSON blob pattern
    patterns = {
        "__NEXT_DATA__":     r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.+?)</script>',
        "__INITIAL_STATE__": r'window\.__INITIAL_STATE__\s*=\s*({.+?});\s*</script>',
        "__APOLLO_STATE__":  r'window\.__APOLLO_STATE__\s*=\s*({.+?});\s*</script>',
        "self.__next_f":     r'self\.__next_f\.push\(\[1,\s*"(.+?)"\]\)',
        "<script type=application/ld+json>": r'<script type="application/ld\+json">(.+?)</script>',
    }

    found = {}
    for name_p, pattern in patterns.items():
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"   ✓ Found pattern: {name_p} ({len(matches)} match{'es' if len(matches) != 1 else ''})")
            found[name_p] = len(matches)

            # 存第一個 match 給人工檢查
            sample = matches[0][:5000]  # 限長度
            out_path = os.path.join(OUTPUT_DIR, f"racing_com_{name_p.strip('_').replace('.', '_')}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# Pattern: {name_p}\n# Sample (first 5000 chars):\n\n{sample}")
            print(f"     Sample saved: {out_path}")

            # 嘗試 JSON parse 看內容結構
            if name_p in ("__NEXT_DATA__", "__INITIAL_STATE__", "__APOLLO_STATE__"):
                try:
                    parsed = json.loads(matches[0])
                    keys = list(parsed.keys())[:20] if isinstance(parsed, dict) else []
                    print(f"     Top-level keys: {keys}")
                    found[name_p + "_keys"] = keys
                except json.JSONDecodeError as e:
                    print(f"     ⚠️ JSON parse failed: {e}")
        else:
            pass  # 不印 not found，太雜

    if not found:
        print(f"   ⚠️ No common React/Next data patterns found")

    # 也找 API endpoints (XHR fetch URLs)
    api_endpoints = re.findall(r'["\'](?:/api/[^"\']+|https?://[^"\']*api[^"\']*)["\']', html)
    api_endpoints = list(set(api_endpoints))[:20]
    if api_endpoints:
        print(f"\n   📡 Possible API endpoints found in HTML:")
        for ep in api_endpoints:
            print(f"      - {ep}")
        result["api_endpoints"] = api_endpoints

    result["json_patterns_found"] = found
    return result


def write_summary(results: dict):
    lines = ["# Diagnose Round 2: Bypass Attempts\n"]

    for section, data in results.items():
        lines.append(f"## {section}\n")
        if isinstance(data, list):
            for d in data:
                _format_one(lines, d)
        else:
            _format_one(lines, data)
        lines.append("")

    out = os.path.join(OUTPUT_DIR, "summary_round2.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n✓ Summary written: {out}")


def _format_one(lines: list, d: dict):
    lines.append(f"### {d.get('name', 'unknown')}")
    if "method" in d:
        lines.append(f"- Method: {d['method']}")
    if "error" in d:
        lines.append(f"- ❌ Error: `{d['error']}`")
    if "status" in d:
        lines.append(f"- Status: {d['status']}")
    if "html_length" in d:
        lines.append(f"- HTML length: {d['html_length']}")
    if d.get("success"):
        lines.append(f"- ✅ **SUCCESS** — saved sample")
    if "news_links_in_raw" in d:
        lines.append(f"- News-link references in HTML: {d['news_links_in_raw']}")
    if "attempts" in d:
        lines.append(f"- Header variant attempts:")
        for a in d["attempts"]:
            if "error" in a:
                lines.append(f"  - Variant {a['variant']}: ❌ {a['error']}")
            else:
                tag = "✅" if a.get("success") else "—"
                lines.append(f"  - Variant {a['variant']}: {tag} status {a['status']}, {a['length']} chars")
    if "json_patterns_found" in d:
        if d["json_patterns_found"]:
            lines.append(f"- JSON patterns found:")
            for k, v in d["json_patterns_found"].items():
                lines.append(f"  - `{k}`: {v}")
        else:
            lines.append(f"- ⚠️ No JSON patterns found")
    if "api_endpoints" in d:
        lines.append(f"- Possible API endpoints:")
        for ep in d["api_endpoints"][:10]:
            lines.append(f"  - `{ep}`")
    lines.append("")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = {
        "Cloudscraper Attempts": [],
        "Header Variant Attempts": [],
        "racing.com SPA Analysis": None,
    }

    # Test 1: cloudscraper for blocked sites
    for name, url in CLOUDSCRAPER_TARGETS.items():
        results["Cloudscraper Attempts"].append(try_cloudscraper(name, url))

    # Test 2: 多種 header variants (給 cloudscraper 失敗的當 plan B)
    for name, url in CLOUDSCRAPER_TARGETS.items():
        results["Header Variant Attempts"].append(try_header_variants(name, url))

    # Test 3: racing.com SPA
    results["racing.com SPA Analysis"] = analyze_racing_com()

    write_summary(results)
    print(f"\n{'='*70}")
    print("✅ Round 2 done. Check ./diagnose_output/summary_round2.md")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
