#!/usr/bin/env python3
"""
更新 puxiao 个人主页里 "Open source" 区块的数据。

它会自动完成下面这些事（全部基于 GitHub API 的真实数据）：

  1. 抓取指定用户**全部已合并（merged）的 PR**（不限仓库，全局查询）。
  2. 按仓库分组：仓库按「该仓库最新一条 PR 的日期」倒序；仓库内部按日期倒序。
  3. 重写 index.html 里的 `const REPOS = [...]` 数组。
  4. 同步更新三处数字：
       - `.counts` 里的 PR 总数、仓库总数、年份区间（如 2020–2026）
       - 自我介绍 p3 里的「92 个 PR」/「92 pull requests」
       - 开源贡献 contribP 里的「34 个开源仓库」/「34 open source repositories」
  5. （默认）更新 Tutorials 列表里各仓库的 star 数。

用法：
    python tools/update_opensource.py              # 更新 index.html
    python tools/update_opensource.py --dry-run    # 只看会改什么，不写文件
    python tools/update_opensource.py --no-stars   # 跳过 star 数更新
    python tools/update_opensource.py --user puxiao --file index.html

说明：
    - 只用标准库，无需 pip 安装任何东西。
    - 未登录的 GitHub Search API 限制为 10 次/分钟；想更稳可设置环境变量
      GITHUB_TOKEN（或传 --token），限额会提高到 30 次/分钟。
    - 写文件前会先把旧文件备份到 tools/backup/。
    - 保留原文件的 CRLF 行尾与 UTF-8 无 BOM 编码。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

SEARCH_URL = "https://api.github.com/search/issues"
REPO_URL = "https://api.github.com/repos/{full_name}"
PER_PAGE = 100
UA = "puxiao-homepage-updater/1.0"


# --------------------------------------------------------------------------
# GitHub API
# --------------------------------------------------------------------------

def api_get(url: str, token: str | None) -> dict:
    """带重试的 GET JSON。"""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code in (403, 429) and "rate limit" in body.lower():
                raise SystemExit(
                    "GitHub API 触发限流。\n"
                    "  未登录时 Search API 只有 10 次/分钟，稍微等一会儿再跑，\n"
                    "  或设置环境变量 GITHUB_TOKEN 提高限额。\n"
                    f"  接口返回：{body}"
                ) from e
            last_err = SystemExit(f"GitHub API 返回 HTTP {e.code}：{body}")
        except Exception as e:  # 网络抖动
            last_err = e
        if attempt < 2:
            time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"请求失败：{url}\n{last_err}")


def _fetch_once(query: str, token: str | None) -> tuple[list[dict], int]:
    """翻页抓一轮，返回 (items, total_count)。"""
    items: list[dict] = []
    total = 0
    page = 1
    while True:
        params = urllib.parse.urlencode(
            {"q": query, "sort": "created", "order": "desc",
             "per_page": PER_PAGE, "page": page},
            quote_via=urllib.parse.quote,      # 空格编成 %20，避免 + 的歧义
        )
        data = api_get(f"{SEARCH_URL}?{params}", token)
        total = data.get("total_count") or 0
        batch = data.get("items") or []
        items.extend(batch)
        if len(batch) < PER_PAGE or len(items) >= total:
            break
        page += 1
        time.sleep(0.8)
    return items, total


def fetch_merged_prs(user: str, token: str | None, attempts: int = 4) -> tuple[list[dict], int]:
    """
    取回该用户全部已合并的 PR。

    ⚠️ GitHub 的搜索接口**偶发返回不完整的结果**（同一条查询前后两次可能拿到
    92 条和 44 条）。所以这里会拿 total_count 做校验并重试，直到两者一致；
    多次仍不一致就交给调用方决定是否中止——绝不能用残缺数据去覆盖页面。
    """
    query = f"author:{user} type:pr is:merged"
    best: list[dict] = []
    best_total = 0
    for attempt in range(attempts):
        items, total = _fetch_once(query, token)
        if total and len(items) >= total:
            return items, total
        if len(items) > len(best):
            best, best_total = items, total
        print(f"   … GitHub 本次只返回 {len(items)}/{total} 条，{2 * (attempt + 1)}s 后重试")
        time.sleep(2.0 * (attempt + 1))
    return best, best_total


def fetch_stars(full_name: str, token: str | None, cache: dict) -> int | None:
    if full_name in cache:
        return cache[full_name]
    try:
        data = api_get(REPO_URL.format(full_name=full_name), token)
        cache[full_name] = data.get("stargazers_count")
    except SystemExit:
        cache[full_name] = None
    return cache[full_name]


# --------------------------------------------------------------------------
# 数据整形
# --------------------------------------------------------------------------

def build_groups(items: list[dict]) -> list[dict]:
    """把 PR 列表整理成 [{r: "owner/repo", prs: [{n, d, t}]}]，已排好序。"""
    buckets: dict[str, list[dict]] = {}
    for it in items:
        repo = it.get("repository_url", "")
        parts = repo.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        full_name = f"{parts[-2]}/{parts[-1]}"

        # 合并时间优先取 pull_request.merged_at，退回 closed_at
        pr = it.get("pull_request") or {}
        stamp = pr.get("merged_at") or it.get("closed_at") or it.get("created_at") or ""
        date = stamp[:10] if stamp else ""
        if not date:
            continue

        buckets.setdefault(full_name, []).append({
            "n": it["number"],
            "d": date,
            "t": (it.get("title") or "").strip(),
        })

    groups = []
    for full_name, prs in buckets.items():
        # 同一天按 PR 号倒序，保证结果稳定
        prs.sort(key=lambda p: (p["d"], p["n"]), reverse=True)
        groups.append({"r": full_name, "prs": prs})
    # 仓库按「最新一条 PR 的日期」倒序
    groups.sort(key=lambda g: (g["prs"][0]["d"], g["prs"][0]["n"]), reverse=True)
    return groups


def count_prs(groups: list[dict]) -> int:
    return sum(len(g["prs"]) for g in groups)


def year_range(groups: list[dict]) -> str:
    years = [int(p["d"][:4]) for g in groups for p in g["prs"] if p["d"][:4].isdigit()]
    if not years:
        return ""
    lo, hi = min(years), max(years)
    return f"{lo}–{hi}" if lo != hi else str(lo)


# --------------------------------------------------------------------------
# 生成 / 解析 REPOS 代码块
# --------------------------------------------------------------------------

REPOS_RE = re.compile(r"const REPOS = \[.*?\r?\n\];", re.S)


def render_repos_block(groups: list[dict], eol: str) -> str:
    lines = ["const REPOS = ["]
    for g in groups:
        lines.append(f'  {{ r: {json.dumps(g["r"])}, prs: [')
        last = len(g["prs"]) - 1
        for i, pr in enumerate(g["prs"]):
            title = json.dumps(pr["t"], ensure_ascii=True)
            comma = "" if i == last else ","
            lines.append(f'      {{ n: {pr["n"]}, d: {json.dumps(pr["d"])}, t: {title} }}{comma}')
        lines.append("  ] },")
    lines.append("];")
    return eol.join(lines)


def parse_repos_block(text: str) -> list[dict]:
    """把文件里现有的 REPOS 数组解析回来，用于对比「本次改了什么」。"""
    m = REPOS_RE.search(text)
    if not m:
        return []
    groups = []
    for gm in re.finditer(r'\{ r: "([^"]+)", prs: \[(.*?)\] \}', m.group(0), re.S):
        prs = [
            {"n": int(n), "d": d}
            for n, d in re.findall(r'\{ n: (\d+), d: "([\d-]+)"', gm.group(2))
        ]
        if prs:
            groups.append({"r": gm.group(1), "prs": prs})
    return groups


# --------------------------------------------------------------------------
# 各类数字的替换
# --------------------------------------------------------------------------

COUNT_RE = r'(<div class="count-num">)([^<]*)(</div>\s*<div class="count-label" data-i18n="{key}">)'


def sub_count(text: str, key: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(COUNT_RE.format(key=key))
    m = pattern.search(text)
    if not m or m.group(2) == value:
        return text, False
    return pattern.sub(lambda mm: mm.group(1) + value + mm.group(3), text, count=1), True


I18N_NUM_TARGETS = [
    (r'(<strong>)(\d+)(\s*pull requests</strong>)', "自我介绍 p3（英文）", "prs"),
    (r'(<strong>)(\d+)(\s*个 PR</strong>)', "自我介绍 p3（中文）", "prs"),
    (r'(<strong>)(\d+)(\s*open source repositories</strong>)', "开源贡献 contribP（英文）", "repos"),
    (r'(<strong>)(\d+)(\s*个开源仓库</strong>)', "开源贡献 contribP（中文）", "repos"),
]


def sub_i18n_number(text: str, pattern: str, value: int) -> tuple[str, bool]:
    rx = re.compile(pattern)
    m = rx.search(text)
    if not m or m.group(2) == str(value):
        return text, False
    return rx.sub(lambda mm: mm.group(1) + str(value) + mm.group(3), text, count=1), True


STARS_LI_RE = re.compile(
    r'(<a href="https://github\.com/(?P<repo>[^"/]+/[^"/]+)"[^>]*>[^<]*</a>\s*'
    r'<span class="stars">★\s*)(?P<num>[^<]+)(?P<tail></span>)'
)
# 写入前用来自检：每个 <span class="stars"> 里必须只有一个数字
STARS_VALUE_RE = re.compile(r'<span class="stars">★\s*([^<]+)</span>')


def fmt_stars(n: int) -> str:
    if n >= 10_000:
        return f"{round(n / 1000)}k"
    if n >= 1_000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="更新 puxiao 主页 Open source 区块（PR 列表 / 统计数字 / star 数）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--file", default="index.html", help="要更新的 HTML 文件（默认 index.html）")
    ap.add_argument("--user", default="puxiao", help="GitHub 用户名（默认 puxiao）")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token（默认读 GITHUB_TOKEN）")
    ap.add_argument("--no-stars", action="store_true", help="不更新 Tutorials 里的 star 数")
    ap.add_argument("--dry-run", action="store_true", help="只显示将要做的改动，不写入文件")
    ap.add_argument("--force", action="store_true", help="即使 GitHub 返回的数据不完整也照样写入（危险）")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"找不到文件：{path}")

    raw = path.read_text(encoding="utf-8", newline="")   # 保留 CRLF
    eol = "\r\n" if "\r\n" in raw else "\n"
    eol_name = "CRLF" if eol == "\r\n" else "LF"

    print(f"→ 读取 {path}（{len(raw)} 字符，行尾 {eol_name}）")
    print(f"→ 抓取 GitHub 上 @{args.user} 全部已合并 PR …")
    items, total = fetch_merged_prs(args.user, args.token)
    if total and len(items) < total:
        msg = (f"GitHub 只返回了 {len(items)}/{total} 条，数据不完整。\n"
               "  搜索接口偶发这样，稍等一会儿重跑通常就好。\n"
               "  为避免把页面数据写坏，已中止。确要用这份数据可加 --force。")
        if not args.force:
            raise SystemExit("！" + msg)
        print("！" + msg)
    groups = build_groups(items)
    total_prs = count_prs(groups)
    total_repos = len(groups)
    years = year_range(groups)
    print(f"   得到 {total_prs} 个已合并 PR，分布在 {total_repos} 个仓库，时间跨度 {years}")

    old_groups = parse_repos_block(raw)
    old_prs = {f'{g["r"]}#{p["n"]}' for g in old_groups for p in g["prs"]}
    new_prs = {f'{g["r"]}#{p["n"]}' for g in groups for p in g["prs"]}
    added, removed = sorted(new_prs - old_prs), sorted(old_prs - new_prs)
    old_repos = {g["r"] for g in old_groups}
    new_repos = {g["r"] for g in groups}

    new = raw
    changed: list[str] = []

    # 1) REPOS 数组
    block = render_repos_block(groups, eol)
    if REPOS_RE.search(new):
        before = REPOS_RE.search(new).group(0)
        if before != block:
            new = REPOS_RE.sub(lambda _m: block, new, count=1)
            changed.append(f"REPOS 数组（{total_repos} 个仓库 / {total_prs} 个 PR）")
    else:
        raise SystemExit("在文件里找不到 `const REPOS = [...]`，无法定位插入点。")

    # 2) 统计数字
    for key, value, label in (
        ("countPR", str(total_prs), f"PR 总数 → {total_prs}"),
        ("countRepos", str(total_repos), f"仓库总数 → {total_repos}"),
        ("countSince", years, f"年份区间 → {years}"),
    ):
        new, ok = sub_count(new, key, value)
        if ok:
            changed.append(label)

    # 3) i18n 文案里的数字
    for pat, label, kind in I18N_NUM_TARGETS:
        value = total_prs if kind == "prs" else total_repos
        new, ok = sub_i18n_number(new, pat, value)
        if ok:
            changed.append(f"{label} 文案数字 → {value}")

    # 4) star 数
    star_changes: list[str] = []
    if not args.no_stars:
        seen: dict[str, int | None] = {}
        def repl(m: re.Match) -> str:
            full = m.group("repo")
            stars = fetch_stars(full, args.token, seen)
            if stars is None:
                return m.group(0)
            pretty = fmt_stars(stars)
            if pretty != m.group("num").strip():
                star_changes.append(f"{full}: {m.group('num').strip()} → {pretty}")
            # 注意 group(1) + 新值 + tail，不能写成 group(3)：命名组 repo 也占了一个序号
            return m.group(1) + pretty + m.group("tail")
        new = STARS_LI_RE.sub(repl, new)
        # 自检：替换后每个 star 块里必须只有一个数字，防止再次出现 "1.3k1.3k" 这类拼接
        for raw_val in STARS_VALUE_RE.findall(new):
            token = raw_val.strip()
            if not re.fullmatch(r"\d+(\.\d+)?k?", token):
                raise SystemExit(f"！star 值自检失败，得到异常内容：{token!r}\n  已中止，文件未被写入。")
        if star_changes:
            changed.extend(star_changes)

    # ---- 报告 ----
    print()
    if added:
        print(f"新增 PR（{len(added)}）：")
        for k in added:
            print(f"  + {k}")
    if removed:
        print(f"已消失的 PR（{len(removed)}）：")
        for k in removed:
            print(f"  - {k}")
        if len(removed) > 3:
            print("  ⚠ 一次少了这么多条很不寻常（通常是 GitHub 搜索接口返还不完整）。")
            print("    建议先跑一次 --dry-run 复核，必要时稍后重跑。")
    for r in sorted(new_repos - old_repos):
        print(f"新增仓库：{r}")
    for r in sorted(old_repos - new_repos):
        print(f"不再出现的仓库：{r}")
    if not (added or removed):
        print("PR 列表没有增删。")

    print()
    if not changed:
        print("✓ 文件已是最新，无需改动。")
        return 0
    print("将要更新的内容：")
    for c in changed:
        print(f"  · {c}")

    if args.dry_run:
        print("\n（--dry-run：未写入文件）")
        return 0

    # ---- 写入前的完整性自检：宁可不动，也不能写坏 ----
    problems: list[str] = []
    for marker in ('const REPOS = [', '</html>', 'data-i18n="countPR"', 'data-i18n="motto"'):
        if marker not in new:
            problems.append(f"缺少标志内容：{marker}")
    if new.count('<span class="stars">') != raw.count('<span class="stars">'):
        problems.append('<span class="stars"> 的数量发生了变化')
    if not REPOS_RE.search(new):
        problems.append('REPOS 数组结构异常')
    if problems:
        raise SystemExit("！完整性自检未通过，已中止（文件未被修改）：\n  - " + "\n  - ".join(problems))

    backup_dir = path.parent / "tools" / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"{path.stem}-{stamp}{path.suffix}"
    shutil.copy2(path, backup)

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new, encoding="utf-8", newline="")
    tmp.replace(path)

    print(f"\n✓ 已更新 {path}")
    print(f"  旧版本备份：{backup}")
    print("  刷新页面即可看到效果。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
