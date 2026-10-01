#!/usr/bin/env python3
"""产物渲染体检：扫构建后的 HTML，找**源码层完全看不出来**的渲染病理。

**为什么需要这道检查**：M84 与 M90 已经两次证明同一件事——

- M84：表格单元格里的行内代码含未转义竖线 → 该行被撑成多格 → **多出的格连同
  内容一起被渲染器丢弃**。七道源码层门禁全部报 ok。
- M90：`**` 紧邻标点使 CommonMark 的 flanking 不成立 → 产物里留下**字面量 `**`**，
  加粗彻底失效。七道门禁仍然全部报 ok。

两次都是"源文件没问题、产物坏了"。`check-render.py` 是**唯一一道从产物侧看问题
的门禁**，它跑在 `build-site.sh` 的产物校验步骤（与 `check-dist-links.py` 同期）。

**扫描范围严格限定在 `<main>…</main>`**：VitePress 的主题自带大量空 span（图标
占位）与内联脚本，不限定范围就是 254 条纯噪声——M90 第一版就栽在这里。

**六类病理**：

1. **表格列数不一致**——`thead` 的列数与各 `tbody` 行的实际列数不符。
   **这是内容被丢弃的直接症状**（M84 那类），优先级最高。
2. **裸露的管道文本**——本该渲染成表格的内容，在正文里留下了 `| a | b |` 原文。
3. **`<img>` 异常**——`src` 为空、指向不存在的资源，或 `alt` 为空。
4. **页内锚点悬空**——`href="#x"` 在本页找不到对应 `id`（**页内**；跨页锚点是
   `check-anchors.py` 的地盘，两者不重叠）。
5. **空内容标签**——`<code></code>`、`<strong></strong>` 这类**正文里**的空元素。
6. **行内代码段被提前截断**——内容以 `\` 结尾（M92）。CommonMark 在代码段内部
   不处理反斜杠转义，作者想用 `\`` 显示反引号时会把代码段截断，**源码层判据抓不到**
   （反引号总数仍是偶数），只有产物里看得见。

**本脚本的每一条判据都做过阳性对照**（M91 做的）：故意在最小产物里注入对应病理，
确认能被抓到，再拿它去扫真实产物。**没做过阳性对照的扫描器，其"0 命中"不能当
"没问题"的证据**——只能当"我还没测它会不会响"。

用法: python3 check-render.py <手册根>          # 自动读 <根>/.vitepress/dist
      python3 check-render.py <dist 目录>        # 直接给产物目录
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAIN_RE = re.compile(r"<main\b[^>]*>(?P<body>.*?)</main>", re.S)
TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table>", re.S)
ROW_RE = re.compile(r"<tr\b[^>]*>.*?</tr>", re.S)
CELL_RE = re.compile(r"<t[hd]\b[^>]*>.*?</t[hd]>", re.S)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
EMPTY_RE = re.compile(r"<(code|strong|em|b|i)\b[^>]*>\s*</\1>", re.I)
HREF_ID_RE = re.compile(r'href="#(?P<id>[^"]+)"')
ID_RE = re.compile(r'id="(?P<id>[^"]+)"')
TAG_RE = re.compile(r"<[^>]+>")
# 裸露管道文本：段落/列表项里，出现「| … | … |」这种表格骨架
PIPE_ROW_RE = re.compile(r"\|\s*[^|\n]{1,40}\s*\|\s*[^|\n]{1,40}\s*\|")


def content_region(html: str) -> str:
    m = MAIN_RE.search(html)
    return m.group("body") if m else ""


def check_tables(region: str, rel: str, out: list[str]) -> None:
    for ti, tbl in enumerate(TABLE_RE.finditer(region), 1):
        widths = [len(CELL_RE.findall(r)) for r in ROW_RE.findall(tbl.group(0))]
        if len(widths) < 2:
            continue
        head_w = widths[0]
        bad = [(i + 1, w) for i, w in enumerate(widths) if w != head_w]
        if bad:
            detail = "、".join(f"第{i}行{w}列" for i, w in bad[:5])
            out.append(
                f"{rel}: 第{ti}张表表头 {head_w} 列，但 {detail} —— "
                f"多出来的格子连同内容已被渲染器丢弃"
            )


def check_pipe_leak(region: str, rel: str, out: list[str]) -> None:
    for m in re.finditer(r"<(p|li|blockquote)\b[^>]*>(?P<body>.*?)</\1>", region, re.S):
        text = TAG_RE.sub("", m.group("body")).strip()
        if PIPE_ROW_RE.search(text):
            out.append(f"{rel}: 正文里出现裸露的表格管道文本：{text[:60]}")


def check_images(region: str, rel: str, assets: set[str], out: list[str]) -> None:
    for m in IMG_RE.finditer(region):
        tag = m.group(0)
        src = re.search(r'src="([^"]*)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        if not src or not src.group(1).strip():
            out.append(f"{rel}: <img> 的 src 为空：{tag[:60]}")
        elif src.group(1).startswith("/") and src.group(1) not in assets:
            out.append(f"{rel}: <img> 指向不存在的资源：{src.group(1)[:60]}")
        if not alt or not alt.group(1).strip():
            shown = src.group(1)[:50] if src else tag[:50]
            out.append(f"{rel}: <img> 的 alt 为空：{shown}")


def check_anchor(region: str, rel: str, out: list[str]) -> None:
    ids = {m.group("id") for m in ID_RE.finditer(region)}
    for m in HREF_ID_RE.finditer(region):
        if m.group("id") not in ids:
            out.append(f"{rel}: 页内锚点 #{m.group('id')} 在本页找不到对应 id")


def check_empty(region: str, rel: str, out: list[str]) -> None:
    for m in EMPTY_RE.finditer(region):
        out.append(f"{rel}: 正文里出现空标签 {m.group(0)[:40]}")


def check_early_closed_code(region: str, rel: str, out: list[str]) -> None:
    """行内代码段被**提前截断**：`<code>` 的内容以反斜杠结尾。

    **M92 实测**：CommonMark 规定**行内代码段内部不处理反斜杠转义**，所以写
    `` `title={a \\| \\`x\\`}` `` 想在代码里显示反引号时，里面那个 `\\`` 会被当成
    **收尾标记**，代码段就地截断，后半截漏成正文：

        源：  源码是 `title={a \\| \\`x\\`}` 这种嵌套反引号
        产物：源码是 <code>title={a \\| \\</code>x`}` 这种嵌套反引号

    **为什么只能在产物侧判**：`check-tables.py` 的行内代码判据数的是**反引号总数
    的奇偶**，而这里的反引号总数是 4（偶数）——**判据形态上就抓不到**。M92 实测
    注入后 `check-tables.py` 报 ok，产物却是坏的。
    产物里的可靠特征是唯一的：代码段内容**以 `\\` 结尾**，这在正常写法里不会出现。
    """
    for m in re.finditer(r"<code(?![^>]*v-pre)[^>]*>(?P<body>.*?)</code>", region, re.S):
        body = TAG_RE.sub("", m.group("body"))
        if body.rstrip().endswith("\\"):
            out.append(
                f"{rel}: 行内代码段被提前截断（内容以反斜杠结尾）——CommonMark 在代码段"
                f"内部不处理反斜杠转义，里面的反引号会当收尾标记：{body.strip()[:40]}"
            )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    arg = Path(sys.argv[1]).resolve()
    dist = arg if arg.name == "dist" else arg / ".vitepress" / "dist"
    if not dist.is_dir():
        print(f"  [渲染] 找不到产物目录 {dist}")
        print("  [渲染] 提示：产物体检必须跑在 vitepress build 之后")
        return 2

    pages = sorted(dist.rglob("*.html"))
    if not pages:
        print("  [渲染] 产物里没有 .html")
        return 2
    assets = {f"/{p.relative_to(dist).as_posix()}" for p in dist.rglob("*") if p.is_file()}

    problems: list[str] = []
    skipped: list[str] = []
    for page in pages:
        rel = page.relative_to(dist).as_posix()
        region = content_region(page.read_text(encoding="utf-8", errors="ignore"))
        if not region:
            # 404 是 VitePress 自己生成的壳页，没有 <main>；它由框架保证，不归本门禁管
            skipped.append(rel)
            continue
        check_tables(region, rel, problems)
        check_pipe_leak(region, rel, problems)
        check_images(region, rel, assets, problems)
        check_anchor(region, rel, problems)
        check_empty(region, rel, problems)
        check_early_closed_code(region, rel, problems)

    for problem in problems:
        print(f"  [渲染] {problem}")
    if problems:
        print(f"产物渲染体检失败：{len(problems)} 项")
        return 1
    note = f"，跳过 {len(skipped)} 个无正文区的壳页（{', '.join(skipped)}）" if skipped else ""
    print(f"  [ ok ] 产物渲染体检：{len(pages) - len(skipped)} 页的六类渲染病理均未命中{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
