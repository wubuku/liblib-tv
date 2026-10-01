#!/usr/bin/env python3
"""校验手册的结构闭环：任务页 ↔ 任务账本 ↔ 索引 ↔ 侧边栏。

**为什么需要这道检查（M42 实测）**：负向测试往 `10-tasks/` 里塞了一个
没登记的「孤儿页」，结果 `audit_manual.py` 退出码 0、`build-site.sh` 也只打了
一行 warn 就通过——**孤儿页可以完全不出现在账本和索引里就混进发布产物**。
同样地，从 `10-tasks/README.md` 索引里删掉一条已有任务页，也没有任何一道门禁会报错。

这两类问题都不会让构建失败，但会让手册的任务结构悄悄失真：
读者从首页/账本点不到某一页，或者某一页存在于站点却没有归属的任务。

本脚本做三组双向核对：
1. `10-tasks/*.md`（除 README）↔ `task-inventory.yml` 的 `manual_pages`
2. `task-inventory.yml` 的 `manual_pages` ↔ 磁盘上真实存在的页面
3. `10-tasks/*.md` ↔ `10-tasks/README.md` 索引 ↔ `.vitepress/config.mjs` 侧边栏

退出码 0 表示结构闭环，1 表示存在孤儿页/漏登记/漏索引/漏侧边栏/孤儿截图。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TASKS_DIR = "10-tasks"
INDEX = "10-tasks/README.md"
INVENTORY = "task-inventory.yml"
SIDEBAR = ".vitepress/config.mjs"
MANIFEST = "screenshots/manifest.yml"

PAGE_LINK_RE = re.compile(r"\]\((?:\./)?([A-Za-z0-9._-]+\.md)(?:#[^)]*)?\)")
INVENTORY_PAGE_RE = re.compile(r"^\s*-\s+(?:\./)?((?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.md)\s*$", re.M)
SIDEBAR_LINK_RE = re.compile(r"link:\s*['\"](/10-tasks/([A-Za-z0-9._-]+))['\"]")
MANIFEST_FILE_RE = re.compile(r"^\s*-\s*file:\s*(?P<v>\S+)\s*$", re.M)
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?P<path>[^)]+?\.png)\)")
SKIP_DIRS = {"node_modules", ".vitepress", "dist", ".git", "screenshots", "scripts"}


def check_orphan_screenshots(root: Path, problems: list[str]) -> tuple[int, int]:
    """孤儿截图：登记在 manifest 里，却没有任何页面引用它。

    **为什么需要（M89 实测）**：这一类和"孤儿页"是同一个错误家族，但当时只堵了
    页、没堵图。2026-10-01 在临时副本上注入一张孤儿图——文件放进 `screenshots/`、
    manifest 补一条**字段齐全、sha256 正确**的记录、账本 `screenshot_count` 也对齐——
    **七道门禁全部通过**，而这张图**没有任何页面引用**。

    后果不是"构建坏了"，而是三件更隐蔽的事：
    ① 账本写着「截图 4 张」，读者实际只看得到 3 张；
    ② manifest 给这张图记了 `verified_locator` 与 `visible_text`，看起来像是**核对过**，
       实际没有任何读者能走到它；
    ③ 站点体积被撑大，而产物链接校验只查"链出去的目标存不存在"，不查"有没有人链它"。

    **反方向已有门禁**：正文引用了但 manifest 没登记的情况，`audit_manual.py` 的
    `image missing from manifest` 会拦下（自检里有对应用例）。这里只补缺失的那一半。
    """
    manifest = root / MANIFEST
    if not manifest.is_file():
        problems.append(f"缺少 {MANIFEST}")
        return 0, 0

    registered = {
        Path(m.group("v")).name for m in MANIFEST_FILE_RE.finditer(manifest.read_text(encoding="utf-8"))
    }
    if not registered:
        problems.append(f"{MANIFEST} 里一条截图记录都没解析到")
        return 0, 0

    referenced: set[str] = set()
    for path in root.rglob("*.md"):
        if SKIP_DIRS.intersection(path.parts):
            continue
        for match in MD_IMAGE_RE.finditer(path.read_text(encoding="utf-8")):
            referenced.add(Path(match.group("path")).name)

    for name in sorted(registered - referenced):
        problems.append(
            f"{MANIFEST} 登记了 {name}，但没有任何页面引用它（孤儿截图："
            f"要么在某页补上引用，要么从 manifest 与账本里删掉）"
        )
    return len(registered), len(referenced)


def fail(problems: list[str]) -> int:
    for problem in problems:
        print(f"  [结构] {problem}")
    if problems:
        print(f"结构校验失败：{len(problems)} 项")
        return 1
    return 0


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    tasks_dir = root / TASKS_DIR
    problems: list[str] = []

    if not tasks_dir.is_dir():
        print(f"  [结构] 缺少目录 {TASKS_DIR}/")
        return 1

    pages = {
        path.name
        for path in tasks_dir.glob("*.md")
        if path.name != "README.md"
    }

    # ---- 1/2. 页面 ↔ 任务账本 ----
    inventory = root / INVENTORY
    declared: set[str] = set()
    if inventory.is_file():
        text = inventory.read_text(encoding="utf-8")
        for match in INVENTORY_PAGE_RE.findall(text):
            name = Path(match).name
            if name in pages:
                declared.add(name)
    else:
        problems.append(f"缺少 {INVENTORY}")

    for page in sorted(pages - declared):
        problems.append(
            f"{TASKS_DIR}/{page}: 任务页未登记到 {INVENTORY} 的 manual_pages（孤儿页）"
        )
    for page in sorted(declared - pages):
        problems.append(
            f"{INVENTORY} 登记了 {page}，但 {TASKS_DIR}/{page} 不存在"
        )

    # ---- 3a. 页面 ↔ 任务索引 ----
    index = root / INDEX
    if index.is_file():
        index_links = {
            name
            for name in PAGE_LINK_RE.findall(index.read_text(encoding="utf-8"))
        }
        for page in sorted(pages - index_links):
            problems.append(f"{INDEX} 索引缺少 {page}")
        for name in sorted(index_links - pages):
            problems.append(f"{INDEX} 索引指向不存在的 {TASKS_DIR}/{name}")
    else:
        problems.append(f"缺少 {INDEX}")

    # ---- 3b. 页面 ↔ 侧边栏 ----
    sidebar = root / SIDEBAR
    if sidebar.is_file():
        sidebar_links = {
            f"{name}.md"
            for _, name in SIDEBAR_LINK_RE.findall(
                sidebar.read_text(encoding="utf-8")
            )
        }
        for page in sorted(pages - sidebar_links):
            problems.append(f"{SIDEBAR} 侧边栏缺少 {page}")
    else:
        problems.append(f"缺少 {SIDEBAR}")

    shots, _ = check_orphan_screenshots(root, problems)

    if problems:
        return fail(problems)
    if shots:
        print(
            f"  [ ok ] 结构校验：{len(pages)} 个任务页全部登记在账本、索引与侧边栏中；"
            f"{shots} 张截图全部被正文引用（无孤儿截图）"
        )
    else:
        print(f"  [ ok ] 结构校验：{len(pages)} 个任务页全部登记在账本、索引与侧边栏中")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
