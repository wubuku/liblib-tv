#!/usr/bin/env python3
"""校验手册内部 Markdown 链接的锚点是否真实存在。

复刻 VitePress（@mdit-vue/shared slugify）的规则：标题转小写，
非字母数字字符一律折成 `-`，连续 `-` 折叠为一个，首尾 `-` 去掉。
再逐条比对 `xxx.md#anchor` 形式的内部链接。

退出码 0 表示全部有效，1 表示存在坏锚点。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SKIP_DIRS = {"node_modules", ".vitepress", "dist", ".git"}


def slugify(text: str) -> str:
    text = text.strip().lower()
    out = []
    for char in text:
        out.append(char if char.isalnum() else "-")
    collapsed = re.sub(r"-+", "-", "".join(out))
    return collapsed.strip("-")


def collect_ids(markdown: Path) -> set[str]:
    ids: set[str] = set()
    for line in markdown.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if match:
            ids.add(slugify(match.group(2)))
    return ids


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    pages = [
        path
        for path in sorted(root.rglob("*.md"))
        if not SKIP_DIRS & set(path.parts)
    ]
    ids_by_page = {path.resolve(): collect_ids(path) for path in pages}

    checked = 0
    problems: list[str] = []
    for page in pages:
        for target in LINK_RE.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            if "#" not in target:
                continue
            raw_path, _, anchor = target.partition("#")
            destination = (
                (page.parent / unquote(raw_path)).resolve() if raw_path else page.resolve()
            )
            checked += 1
            if not destination.exists():
                problems.append(f"{page.relative_to(root)}: 目标文件不存在 -> {target}")
                continue
            if not raw_path:
                continue  # 同页锚点，由 VitePress 保证
            if anchor and anchor not in ids_by_page.get(destination, set()):
                problems.append(
                    f"{page.relative_to(root)}: 锚点不存在 -> {target}"
                )

    for problem in problems:
        print(f"  [锚点] {problem}")
    if problems:
        print(f"锚点校验失败：{len(problems)}/{checked} 个内部锚点链接无效")
        return 1
    print(f"  [ ok ] 锚点校验：{checked} 个内部锚点链接全部有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
