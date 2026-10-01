#!/usr/bin/env python3
"""强断言必须有证据：正文里出现「逐字 / 完全一致 / 一一对应」这类话，
所在小节内必须同时出现证据标记。

**为什么需要这道检查（M44/M45 起因）**：`shortcuts-help.md` 曾把一个小节
标题写成「键位速查（与弹窗逐字一致）」，实测下来并不成立——表格混进了 3 条
弹窗里没有的条目，还把「剪切板」写成「剪贴板」。更刺眼的是**手册自己的截图
就证伪了它自己的表格**。这类错误靠人眼复核很容易放过：写的时候手里有截图，
但没人回头把文字和截图逐条对一遍。

所以把纪律固化成门禁：**凡是正文出现强断言，同一小节里必须写清楚它凭什么
这么说**（实测 / 复核 / 对拍 / 源码 / 抓取 / 逐条 / 回归）。

判据落在「小节」而不是「同一行」：表格单元格里的「完全相同」往往靠邻近正文
交代证据（见 20-reference 的配置双入口一节），按行判定会误报。

只扫**对外发布页**，不扫 PROGRESS / AUDIT / SOURCE_OBSERVATIONS /
TEST_MEDIA_ASSETS——那些是内部账本，本来就大量使用这类分析性措辞。

退出码 0 表示全部强断言都带证据，1 表示存在裸断言。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 正文页（相对手册根）
BODY_PAGES = [
    "README.md",
    "00-quickstart.md",
    "20-reference.md",
    "30-concepts.md",
    "90-troubleshooting.md",
]
BODY_GLOBS = ["10-tasks/*.md"]

# 强断言标记：说「完全/一致/精确」这类话，就是一个可被证伪的承诺
CLAIM_MARKERS = [
    "逐字", "完全一致", "完全相同", "完全等同", "一一对应",
    "一字不差", "一模一样", "精确匹配", "零差异", "全部有效",
]
# 证据标记：说明这句话凭什么这么说
EVIDENCE_MARKERS = ["实测", "复核", "对拍", "源码", "抓取", "逐条", "回归", "脚本"]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

# 小节最大行数：防止一个巨大的小节里藏了裸断言却蹭到别处的证据
MAX_SECTION_LINES = 80


def load_pages(root: Path) -> list[Path]:
    pages: list[Path] = []
    for name in BODY_PAGES:
        path = root / name
        if path.is_file():
            pages.append(path)
    for pattern in BODY_GLOBS:
        pages.extend(sorted(root.glob(pattern)))
    return pages


def split_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    """按标题切成小节，返回 [(标题或 '<页首>', 该小节的行)]。"""
    sections: list[tuple[str, list[str]]] = []
    current_title = "<页首>"
    current: list[str] = []
    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            if current:
                sections.append((current_title, current))
            current_title = match.group(2).strip()
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append((current_title, current))
    return sections


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems: list[str] = []
    checked = 0

    for page in load_pages(root):
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(root)
        for title, lines in split_sections(text.splitlines()):
            if len(lines) > MAX_SECTION_LINES:
                problems.append(
                    f"{rel}: 小节「{title}」有 {len(lines)} 行（超过 {MAX_SECTION_LINES}），"
                    f"证据判定不可靠，请拆小"
                )
                continue
            body = "\n".join(lines)
            claims = [m for m in CLAIM_MARKERS if m in body]
            if not claims:
                continue
            checked += 1
            evidence = [m for m in EVIDENCE_MARKERS if m in body]
            if not evidence:
                problems.append(
                    f"{rel}: 小节「{title}」出现强断言 {claims}，"
                    f"但整节没有任何证据标记（{'/'.join(EVIDENCE_MARKERS)}）"
                )

    for problem in problems:
        print(f"  [断言] {problem}")
    if problems:
        print(f"强断言校验失败：{len(problems)} 处裸断言")
        return 1
    print(
        f"  [ ok ] 强断言校验：{checked} 个含强断言的小节都写明了证据来源"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
