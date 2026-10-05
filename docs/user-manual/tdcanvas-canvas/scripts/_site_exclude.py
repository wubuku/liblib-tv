#!/usr/bin/env python3
"""**哪些 .md 页面会被发布** —— 唯一事实源是 `.vitepress/config.mjs` 的 `srcExclude`。

## 为什么要有这个模块（M240）

**本仓库曾有三道门禁各自手抄一份「内部资料」名单，三份互不一致，
而其中一份抄错了方向 —— 把正在发布的页面当成了内部资料。**

- `check-emphasis.py` 的 `INTERNAL` 写了 6 个文件，比 `srcExclude` 多一个 `README.md`。
  ★ **而 `README.md` 在 `config.mjs` 里被重命名成 `index.md` 当站点首页。**
  它还被按 `p.name` 匹配，于是 `10-tasks/README.md` 一起被跳过——
  **两道门禁因此跳过了整个首页与任务索引**，
  而它们恰恰是 M90 立这道门禁要抓的「源文件没事、产物坏了」的最要紧位置。
- `check-tables.py` 的 `INTERNAL_PAGES` 只有 4 个，**漏了 `PUBLISH.md`**，
  尽管它上面的注释白纸黑字写着「由 config.mjs 的 srcExclude 排除」。
  后果不是漏报而是**贴错标签**：`PUBLISH.md` 的表格缺陷被当成读者可见缺陷，
  **M239 正是因为这条报错文案，才差点在账本里写下「会从发布页上消失」这句假断言。**
- `check-ledger-sync.py` 的 `INTERNAL` 漏了 `TEST_MEDIA_ASSETS.md`（潜伏型）。

## 本模块的取舍

**「不扫哪些文件」这种名单，永远要从事实推导，而不是另抄一份。**
所以这里只提供读取与匹配，**不在任何地方硬编码文件名**。

★ **读不到 `srcExclude` 时返回 `None`，由调用方判失败**——
**既不退回硬编码名单（那正是病根），也不默默扫全库（M90 第一版 382 条假阳性）。**
**「不知道扫什么」和「扫了没问题」在输出里必须长得不一样**（F42）。

## 匹配语义

`srcExclude` 的条目形如 `**/AUDIT.md`：**`**/` 前缀是「任意深度」的意思**。
★ **必须按「相对路径」而不是「文件名」匹配**——
按文件名匹配会让 `README.md` 一条同时命中根目录与 `10-tasks/` 两份 README，
**而它们的发布状态未必相同**（本仓库两份都发布，但这不是可以靠猜的）。
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["read_src_exclude", "is_excluded", "split_published"]

_CONFIG_REL = Path(".vitepress") / "config.mjs"


def read_src_exclude(root: Path) -> set[str] | None:
    """读出 `srcExclude` 的原始条目集合。读不到返回 `None`（**不是空集**）。"""
    config = root / _CONFIG_REL
    if not config.is_file():
        return None
    block = re.search(
        r"srcExclude:\s*\[(.*?)\]",
        config.read_text(encoding="utf-8"),
        re.S,
    )
    if not block:
        return None
    return set(re.findall(r"['\"]([^'\"]+)['\"]", block.group(1)))


def is_excluded(rel: str, patterns: set[str]) -> bool:
    """`rel` 是相对 root 的 posix 路径。"""
    for pattern in patterns:
        tail = pattern.lstrip("*").lstrip("/")
        if "/" in tail:
            if rel == tail or rel.endswith("/" + tail):
                return True
        elif Path(rel).name == tail:
            return True
    return False


def split_published(
    paths: list[Path], root: Path, patterns: set[str]
) -> tuple[list[Path], list[Path]]:
    """返回 `(发布的, 被 srcExclude 排除的)`，两者都保持输入顺序。"""
    published, excluded = [], []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        (excluded if is_excluded(rel, patterns) else published).append(path)
    return published, excluded
