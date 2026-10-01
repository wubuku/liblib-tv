#!/usr/bin/env python3
"""产物链接门禁：构建产物里每一条内部链接与资源引用都必须真实存在。

为什么要有这道门禁（M56）：`build-site.sh` 原本只检查「有没有残留的 `.md`
原始链接」。但 VitePress 会把**所有** markdown 链接都改写成 `.html`——包括那些
指向 `srcExclude` 排除掉的页面的。于是 `.md` 残留检查全部通过，站点里却躺着一
条死链：README 链向 `PUBLISH.md`，而 PUBLISH 被排除出站点，链接被改写成
`./PUBLISH.html`，那个文件根本不存在。读者点下去就是 404。

**「链接被正确改写」不等于「链接指向的东西存在」。** 前者查格式，后者查事实，
两者都要查。

只能在构建之后跑（需要 .vitepress/dist 已生成），故接在 build-site.sh 步骤 6。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

HREF_RE = re.compile(r'href="([^"]+)"')
SRC_RE = re.compile(r'src="([^"]+)"')
SKIP_PREFIX = ("http://", "https://", "mailto:", "tel:", "#", "data:", "javascript:", "//")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    dist = root / ".vitepress" / "dist"
    if not dist.is_dir():
        print(f"[FAIL] 找不到构建产物目录：{dist}")
        return 1

    pages = sorted(dist.rglob("*.html"))
    if not pages:
        print("[FAIL] 产物里没有任何 html 页面")
        return 1

    broken: list[str] = []
    checked = 0

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="ignore")
        for url in set(HREF_RE.findall(text)) | set(SRC_RE.findall(text)):
            if url.startswith(SKIP_PREFIX):
                continue
            path = unquote(urlparse(url).path)
            if not path:
                continue
            checked += 1
            target = (dist / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
            if not target.exists():
                rel = page.relative_to(dist)
                broken.append(f"{rel}  ->  {url}")

    print(f"[links] 扫描产物 {len(pages)} 页，校验内部链接与资源引用 {checked} 条")

    if broken:
        print("[FAIL] 产物中存在指向不存在目标的链接：")
        for item in sorted(set(broken)):
            print("  " + item)
        print()
        print("  常见成因：链接指向了被 srcExclude 排除出站点的页面（如 PUBLISH.md、")
        print("  AUDIT.md、PROGRESS.md）。改法二选一——把它写成纯文本路径而不是链接，")
        print("  或者确实需要读者看到，就把它从 srcExclude 里放出来。")
        return 1

    print(f"[ ok ] 产物链接校验：{checked} 条内部链接与资源引用全部指向真实存在的目标")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
