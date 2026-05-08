"""
inspect_racing_com_nextdata.py
==============================
專門分析 racing.com 的 __NEXT_DATA__ JSON 結構，
找到「新聞列表」實際存放的路徑。

執行方式：GitHub Actions workflow_dispatch
"""

import json
import os
import re

import requests

OUTPUT_DIR = "diagnose_output"
URL = "https://www.racing.com/news/latest-news"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def walk_keys(obj, prefix="", depth=0, max_depth=6, results=None):
    """遞迴列出 JSON 結構的所有 keys，並標出像是新聞列表的節點。"""
    if results is None:
        results = []
    if depth > max_depth:
        return results

    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(val, (dict, list)):
                size = len(val)
                type_str = "dict" if isinstance(val, dict) else f"list[{size}]"
                results.append({"path": path, "type": type_str, "depth": depth})
                walk_keys(val, path, depth + 1, max_depth, results)
            else:
                # primitives — 記下值的長度
                vstr = str(val)[:60]
                results.append({"path": path, "type": type(val).__name__, "value": vstr, "depth": depth})
    elif isinstance(obj, list) and obj:
        # 只看 list 第一個元素的結構 (假設 list 內元素同型)
        first = obj[0]
        if isinstance(first, (dict, list)):
            walk_keys(first, prefix + "[0]", depth + 1, max_depth, results)
    return results


def find_news_arrays(obj, prefix="", found=None, depth=0):
    """找看起來像新聞列表的 array (元素帶 title/headline/url 等欄位)。"""
    if found is None:
        found = []
    if depth > 8:
        return found

    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(val, list) and len(val) >= 3:
                # 看 list 元素是不是 dict 且有新聞相關欄位
                if all(isinstance(x, dict) for x in val[:5]):
                    sample_keys = set()
                    for x in val[:5]:
                        sample_keys.update(x.keys())
                    news_field_indicators = {
                        "title", "headline", "name", "url", "slug", "publishedAt",
                        "publishDate", "date", "summary", "description", "id"
                    }
                    overlap = sample_keys & news_field_indicators
                    if len(overlap) >= 2:
                        found.append({
                            "path": path,
                            "length": len(val),
                            "sample_keys": list(sample_keys)[:15],
                            "overlap_with_news_fields": list(overlap),
                            "first_item_sample": {k: str(v)[:80] for k, v in list(val[0].items())[:8]},
                        })
            if isinstance(val, (dict, list)):
                find_news_arrays(val, path, found, depth + 1)
    elif isinstance(obj, list):
        for i, x in enumerate(obj[:3]):  # 只看前 3 個避免爆炸
            find_news_arrays(x, f"{prefix}[{i}]", found, depth + 1)
    return found


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Fetching {URL}...")
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    print(f"Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Cannot fetch")
        return

    # Extract __NEXT_DATA__
    m = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.+?)</script>',
        resp.text, re.DOTALL,
    )
    if not m:
        print("❌ __NEXT_DATA__ not found")
        return

    json_str = m.group(1)
    print(f"__NEXT_DATA__ length: {len(json_str)} chars")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse failed: {e}")
        return

    # 存完整 JSON
    full_path = os.path.join(OUTPUT_DIR, "racing_com_nextdata_full.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Full JSON saved: {full_path}")

    # 找新聞 array
    print("\n🔍 Searching for news-like arrays...")
    found = find_news_arrays(data)

    summary_lines = ["# racing.com __NEXT_DATA__ Analysis\n"]
    summary_lines.append(f"- Full JSON: `{full_path}`\n")
    summary_lines.append(f"- Total length: {len(json_str)} chars\n")

    if found:
        print(f"\n✨ Found {len(found)} candidate news arrays:")
        summary_lines.append(f"## Found {len(found)} candidate news arrays\n")
        for i, f_info in enumerate(found):
            print(f"\n   [{i+1}] {f_info['path']}")
            print(f"       length: {f_info['length']}")
            print(f"       overlapping news fields: {f_info['overlap_with_news_fields']}")
            print(f"       sample keys: {f_info['sample_keys']}")
            print(f"       first item: {f_info['first_item_sample']}")

            summary_lines.append(f"### Candidate {i+1}: `{f_info['path']}`\n")
            summary_lines.append(f"- Array length: {f_info['length']}")
            summary_lines.append(f"- News-field overlap: {f_info['overlap_with_news_fields']}")
            summary_lines.append(f"- Sample keys in items: {f_info['sample_keys']}")
            summary_lines.append(f"- First item sample:")
            for k, v in f_info["first_item_sample"].items():
                summary_lines.append(f"  - `{k}`: `{v}`")
            summary_lines.append("")
    else:
        print("\n⚠️ No news-like arrays found")
        summary_lines.append("## ⚠️ No news-like arrays found\n")
        summary_lines.append("Top-level keys walk:")
        all_keys = walk_keys(data, max_depth=4)
        for k in all_keys[:80]:
            indent = "  " * k["depth"]
            line = f"{indent}- `{k['path']}` ({k['type']})"
            if "value" in k:
                line += f" = {k['value']}"
            summary_lines.append(line)

    summary_path = os.path.join(OUTPUT_DIR, "racing_com_nextdata_analysis.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"\n✓ Analysis: {summary_path}")


if __name__ == "__main__":
    main()