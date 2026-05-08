"""
Scraper Extractability Test
============================
測試 16 個 scrapers 的內文可抓性，產出分級報告。

設計：
- 重用現有 scrapers/ 模組拿到 URL 列表
- 對每個 source 取前 3 則，用 trafilatura 抓內文
- 量化字數、quote 數、抓取成功率，自動分級
- 在 GitHub Actions 上執行，IP 環境跟 production 一致
"""

import importlib
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

import requests

try:
    import trafilatura
except ImportError:
    print("❌ 缺少 trafilatura，請執行：pip install trafilatura")
    sys.exit(1)


SITES = [
    'racing_post', 'scmp_racing', 'singtao_racing', 'punters_au',
    'racing_com', 'tospo_keiba', 'netkeiba_news', 'bloodhorse_news',
    'the_straight', 'anz_bloodstock', 'ttr_ausnz', 'smh_racing',
    'drf_news', 'racenet_news', 'daily_telegraph', 'equidia_racing'
]

SAMPLES_PER_SITE = 3
REQUEST_TIMEOUT = 20
SLEEP_BETWEEN_REQUESTS = 1.5

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

QUOTE_PATTERNS = [
    re.compile(r'"([^"]{10,300})"'),
    re.compile(r'[\u201c]([^\u201d]{10,300})[\u201d]'),
    re.compile(r'\u300c([^\u300d]{5,300})\u300d'),
    re.compile(r'\u300e([^\u300f]{5,300})\u300f'),
]


def count_quotes(text):
    if not text:
        return 0, []
    found = []
    for p in QUOTE_PATTERNS:
        found.extend(p.findall(text))
    unique = list(dict.fromkeys(found))
    return len(unique), unique[:3]


def fetch_with_trafilatura(url):
    try:
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        text = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if not text:
            return None, "trafilatura returned empty"
        return text, None
    except requests.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:80]}"


def test_one_url(url):
    start = time.time()
    text, err = fetch_with_trafilatura(url)
    elapsed = round(time.time() - start, 2)
    if not text:
        return {
            "url": url, "success": False, "error": err,
            "char_count": 0, "quote_count": 0,
            "sample_quotes": [], "preview": "", "elapsed": elapsed,
        }
    qc, samples = count_quotes(text)
    return {
        "url": url, "success": True, "error": None,
        "char_count": len(text), "quote_count": qc,
        "sample_quotes": samples,
        "preview": text[:250].replace("\n", " "),
        "elapsed": elapsed,
    }


def test_one_scraper(site):
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {site}")
    print(f"{'='*60}")

    result = {
        "site": site, "scraper_works": False,
        "items_found": 0, "samples": [], "error": None,
    }

    try:
        module = importlib.import_module(f"scrapers.{site}")
        items = module.scrape()
        result["scraper_works"] = True
        result["items_found"] = len(items) if items else 0
        print(f"   ✅ Scraper 回傳 {result['items_found']} 則")
    except Exception as e:
        result["error"] = f"Scraper failed: {type(e).__name__}: {str(e)[:120]}"
        print(f"   ❌ {result['error']}")
        return result

    if not items:
        print("   ⚠️ Scraper 回傳空列表")
        return result

    for i, item in enumerate(items[:SAMPLES_PER_SITE]):
        url = item.get('link') or item.get('url')
        title = item.get('title', '(no title)')
        if not url:
            print(f"   [{i+1}] ⚠️ 沒有 link 欄位，跳過")
            continue
        print(f"   [{i+1}] {title[:65]}")
        sample = test_one_url(url)
        sample["title"] = title
        result["samples"].append(sample)
        if sample["success"]:
            print(f"       ✅ {sample['char_count']} chars, {sample['quote_count']} quotes ({sample['elapsed']}s)")
        else:
            print(f"       ❌ {sample['error']} ({sample['elapsed']}s)")
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    return result


def classify_tier(r):
    if not r["scraper_works"]:
        return "BROKEN"
    if not r["samples"]:
        return "NO_DATA"
    successes = [s for s in r["samples"] if s["success"]]
    if not successes:
        return "TIER_C"
    avg_chars = sum(s["char_count"] for s in successes) / len(successes)
    avg_quotes = sum(s["quote_count"] for s in successes) / len(successes)
    rate = len(successes) / len(r["samples"])
    if rate >= 0.66 and avg_chars >= 1500 and avg_quotes >= 1:
        return "TIER_A"
    if rate >= 0.5 and avg_chars >= 500:
        return "TIER_B"
    return "TIER_C"


def generate_report(results):
    lines = []
    lines.append("# Scraper Extractability Report")
    lines.append(f"\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_")
    lines.append(f"_Environment: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else 'Local'}_\n")
    lines.append(f"Tested {len(results)} scrapers, up to {SAMPLES_PER_SITE} articles each.\n")

    tiers = {"TIER_A": [], "TIER_B": [], "TIER_C": [], "BROKEN": [], "NO_DATA": []}
    for r in results:
        tiers[classify_tier(r)].append(r)

    labels = {
        "TIER_A": "✅ Tier A — Full body + quotes (use trafilatura directly)",
        "TIER_B": "🟡 Tier B — Partial body / lede only (try-fail with fallback)",
        "TIER_C": "🔴 Tier C — Headlines only / blocked",
        "BROKEN": "💀 BROKEN — Scraper module failed",
        "NO_DATA": "⚠️ NO DATA — Scraper returned empty list",
    }

    lines.append("## Summary\n")
    lines.append("| Tier | Count | Sources |")
    lines.append("|---|---|---|")
    for k, label in labels.items():
        names = ", ".join(f"`{r['site']}`" for r in tiers[k])
        lines.append(f"| {label} | {len(tiers[k])} | {names or '_(none)_'} |")

    lines.append("\n---\n\n## Detailed Results\n")
    for k, label in labels.items():
        if not tiers[k]:
            continue
        lines.append(f"### {label}\n")
        for r in tiers[k]:
            lines.append(f"#### `{r['site']}`")
            if r["error"]:
                lines.append(f"- ❌ {r['error']}\n")
                continue
            lines.append(f"- Items found: {r['items_found']}")
            successes = [s for s in r["samples"] if s["success"]]
            lines.append(f"- Tested: {len(r['samples'])} | Success: {len(successes)}/{len(r['samples'])}")
            if successes:
                avg_c = int(sum(s["char_count"] for s in successes) / len(successes))
                avg_q = round(sum(s["quote_count"] for s in successes) / len(successes), 1)
                lines.append(f"- Avg body length: **{avg_c}** chars | Avg quotes: **{avg_q}**")

            for s in r["samples"]:
                status = "✅" if s["success"] else "❌"
                title = s.get("title", "")[:80]
                lines.append(f"\n{status} _{title}_")
                lines.append(f"  - URL: <{s['url']}>")
                if s["success"]:
                    lines.append(f"  - {s['char_count']} chars, {s['quote_count']} quotes")
                    if s["sample_quotes"]:
                        lines.append(f"  - **Sample quotes**:")
                        for q in s["sample_quotes"]:
                            qc = q.replace("\n", " ")[:140]
                            lines.append(f"    - `{qc}`")
                    if s["preview"]:
                        lines.append(f"  - Preview: _{s['preview'][:200]}…_")
                else:
                    lines.append(f"  - Error: `{s['error']}`")
            lines.append("")
        lines.append("")

    lines.append("---\n\n## Recommendations\n")
    if tiers["TIER_A"]:
        lines.append(f"- **Tier A ({len(tiers['TIER_A'])} sources)**: Stage 3 pipeline 直接用 trafilatura。")
    if tiers["TIER_B"]:
        lines.append(f"- **Tier B ({len(tiers['TIER_B'])} sources)**: Try-fail 模式；抓到 lede 用 lede，否則回退到標題。")
    if tiers["TIER_C"]:
        lines.append(f"- **Tier C ({len(tiers['TIER_C'])} sources)**: 只有標題可用。對高權威來源（如 Racing Post），保留標題中的引號 fragment 作為 partial quote。")
    if tiers["BROKEN"]:
        lines.append(f"- **BROKEN ({len(tiers['BROKEN'])} sources)**: Scraper 本身有問題，需先修復。")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print(f"Scraper Extractability Test")
    print(f"Testing {len(SITES)} sites, {SAMPLES_PER_SITE} articles each")
    print("=" * 60)

    all_results = []
    for site in SITES:
        try:
            all_results.append(test_one_scraper(site))
        except Exception as e:
            print(f"   💀 Unexpected error: {e}")
            all_results.append({
                "site": site, "scraper_works": False,
                "items_found": 0, "samples": [],
                "error": f"Unexpected: {type(e).__name__}: {str(e)[:120]}",
            })

    report = generate_report(all_results)
    out = "extractability_report.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"✨ 報告已產生: {out}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
