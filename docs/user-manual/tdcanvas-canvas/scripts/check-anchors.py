#!/usr/bin/env python3
"""校验手册内部 Markdown 链接的锚点是否真实存在。

逐字复刻 VitePress 内置的 slugify（见 vitepress/dist/node/chunk-*.js）：

    rControl   = /[\\u0000-\\u001f]/g
    rSpecial   = /[\\s~`!@#$%^&*()\\-_+=[]{}|\\\\;:"'“”‘’<>,.?/]+/g
    rCombining = /[\\u0300-\\u036F]/g
    slugify = NFKD -> 去组合符 -> 去控制符 -> rSpecial 折 `-` -> 折叠 `-`
               -> 去首尾 `-` -> 数字开头补 `_` -> 小写

**关键点是第一步 NFKD**：全角字符（`，：＋≠` 等）会先被分解成 ASCII 标点，
才会被 rSpecial 折成 `-`；而 `、。「」` 没有兼容分解，会原样留在 id 里。
早先的实现漏了 NFKD，且用 `isalnum()` 逐字判断，236 个标题里错判 29 个，
锚点门禁长期给假通过——M41 才把它暴露出来。

退出码 0 表示全部有效，1 表示存在坏锚点。
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SKIP_DIRS = {"node_modules", ".vitepress", "dist", ".git"}

R_CONTROL = re.compile("[\\u0000-\\u001f]")
R_SPECIAL = re.compile(
    "[\\s~`!@#$%^&*()\\-_+=\\[\\]{}|\\\\;:\"'“”‘’<>,.?/]+"
)
R_COMBINING = re.compile("[\\u0300-\\u036f]")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = R_COMBINING.sub("", text)
    text = R_CONTROL.sub("", text)
    text = R_SPECIAL.sub("-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    text = re.sub(r"^(\d)", r"_\1", text)
    return text.lower()
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
