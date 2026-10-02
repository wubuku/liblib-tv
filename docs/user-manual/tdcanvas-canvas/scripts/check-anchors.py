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

**第二次假通过（M140，同族复发）**：`collect_ids` 逐行匹配标题、**不识别代码围栏**，
把 bash 代码块里的 `# 注释` 当成真标题收进 id 集合。手册现存 4 处这样的"假标题"
（README.md 两处、PUBLISH.md 两处）。实测阳性对照：按本脚本算法算出的
`#启动一个静态服务器-浏览器打开-http-localhost-4173` 写进链接后，本脚本报
「58 个内部锚点链接全部有效」exit=0 **放行**，而产物里那行是 `<span>` 着色代码、
**没有这个 id**——链接点不动。

**两次都是同一个教训：门禁的假通过比门禁的报错更难发现。** 报错会逼你去查，
假通过让你把一个坏链接当成已验证的结论写进手册。**所以每改一次判据，
必须先问「它现在会不会假通过」，并用阳性对照实测，而不是只看退出码。**

**另一条判据边界（M140 实测）**：源码层与产物层的锚点口径不一致，
**源码层假通过时只有产物侧 `check-render.py` 能兜住**；但 `PUBLISH.md` 恰被
`srcExclude` 排除，它那两处假标题**永远到不了产物侧，两层都漏**——这就是
为什么根因必须在源码层修，不能指望下游兜。

退出码 0 表示全部有效，1 表示存在坏锚点。
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
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
    fenced = False
    for line in markdown.read_text(encoding="utf-8").splitlines():
        # M140：**代码围栏必须识别**。此前这里逐行匹配标题、不看是不是在 ``` 里，
        # 于是 bash 代码块里的 `# 注释` 被当成真标题收进 id 集合——而产物里那行是
        # `<span>` 着色代码、**根本没有 id**。实测：按本脚本算法算出的 slug 写进
        # 链接后，本脚本报「58 个内部锚点链接全部有效」exit=0 放行，**假通过**。
        # 与 M41（漏 NFKD）是同族复发：门禁的假通过比门禁的报错更难发现。
        # 缩进代码块（4 空格 / 制表符）同理不产生标题。
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or line.startswith(("    ", "\t")):
            continue
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
        # 行内代码里的 `[x](#y)` 是**文档在讲语法**，不是真链接——必须跳过。
        # M91 补同页锚点检查时立刻撞上这个：AUDIT.md 里把 `` `[文字](#标题)` ``
        # 当示例写出来，被新判据当成一条坏锚点报了出来。判据没错，**输入没净化**。
        text = INLINE_CODE_RE.sub(
            lambda m: " " * len(m.group(0)), page.read_text(encoding="utf-8")
        )
        for target in LINK_RE.findall(text):
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
            # 同页锚点（M91 订正）：此前在这里直接 `continue`，注释写"由 VitePress
            # 保证"——**那个假设是假的**。同页锚点的 id 同样来自 slugify，标题里的
            # 标点（`：` `，` `"`）会被折成 `-`，手写链接少写连字符就点不动。
            # 实测：全站仅 3 条同页锚点，**2 条是坏的**（generate-images 的
            # `#生图之外音频与…`、undo-persistence 的 `#清空画布撤销救得回来…`），
            # 而本门禁当时报的是"44 个内部锚点链接全部有效"——一条都没查。
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
