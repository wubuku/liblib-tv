#!/usr/bin/env python3
"""**「哪些文件是内部资料」不许有第二份** —— 唯一事实源是 `config.mjs` 的 `srcExclude`。

## 这道门禁为什么存在（M240）

M240 在两小时里翻出**三道门禁各自手抄了一份「内部资料」名单，三份互不一致**，
而其中一份把**正在发布的页面**当成了内部资料：

| 脚本 | 原名单 | 与 `srcExclude` 的差 | 后果 |
|---|---|---|---|
| `check-emphasis.py` | 6 个，多了 `README.md` | ★ **把站点首页当内部资料** | **整道门禁跳过首页与任务索引**：注入一个必定违规的跨度，**构建 exit=0、产物首页留着字面量 `**`** |
| `check-tables.py` | 4 个，少了 `PUBLISH.md` | 贴错标签 | 内部页被当发布页报错，**M239 照着报错文案写下了假断言** |
| `check-ledger-sync.py` | 4 个，少了 `TEST_MEDIA_ASSETS.md` | 冗余兜底过滤器漏一项 | 无行为差异（内部文件都匹配不上 `BODY_PREFIXES`），但它仍是一份会悄悄过期的副本 |

★ **三份都不是「抄错了值」，而是「根本不该抄」**：
**排除名单是一种会过期的状态**（今天不发布，不代表明天不发布），
**把它抄成字面量，就等于把一个事实 froze 成三份需要人工同步的副本。**

## 三条判据

1. **不许有第二份**：任何 `scripts/*.py` 里，形如 `[A-Z_]*INTERNAL[A-Z_]* = {...}` 或 `(...)`
   的字面量名单，其内容必须与 `srcExclude` 命中的文件集合**完全相等**。
2. **三道该推导的必须真的在推导**：`check-emphasis.py` / `check-tables.py` /
   `check-ledger-sync.py` 必须都 import `_site_exclude`。
   （判据 1 只看名单，**看不出有人把推导悄悄改回字面量又恰好没起冲突**。）
3. **唯一事实源自己不许硬编码**：`_site_exclude.py` 里除文档字符串外，
   **不许出现任何 `.md` 文件名**。★ **判据 3 是前两条的封口**——
   **否则「单一事实源」自己内部又长出一份名单，前面全白做。**
   扫描走 `ast` 而不是正则，**因此注释与文档字符串天然不算**
   （M194：扫源码前必须先剥注释，否则正文里举例的文件名会造成假阳性）。

★ **读不到 `srcExclude` 时直接判失败**——一道不知道事实源的守卫不是守卫。
**既不退回旧名单，也不默默当成空集**（F42：「没查」与「查了没问题」必须长得不一样）。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _site_exclude import is_excluded, read_src_exclude  # noqa: E402

SKIP_DIRS = {"node_modules", ".vitepress", "dist", ".git", "screenshots"}
SCRIPTS = "_site_exclude.py"
# ★ **判据 2 点名的三道门禁**（都曾各自抄过一份名单）
MUST_DERIVE = ("check-emphasis.py", "check-tables.py", "check-ledger-sync.py")

# 形如 `INTERNAL` / `INTERNAL_PAGES` / `SKIP_INTERNAL_MD` 的**变量名**。
# ★★ **这里必须只匹配名字本身**：第一版写成了 `^([A-Z_]*INTERNAL[A-Z_]*)\s*=\s*[\{\(]`，
# 而调用处传进来的就是光秃秃的名字，**于是它一次都匹配不上**——
# **判据 1 从落地起就是死的，而它的报读一直印着「手抄名单 0 处」。**
# ★ **这正是本门禁自己撞上的那类假阴性**：注入「手抄一份少文件的名单」进去，
# **门禁照样 exit=0**——**假阴性比漏报更危险，因为它输出的是「通过」。**
# （M240 抓 `check-emphasis.py` 用的就是这个手法。）
INTERNAL_ASSIGN = re.compile(r"^[A-Z_]*INTERNAL[A-Z_]*$")


def script_files(root: Path) -> list[Path]:
    return sorted(
        p for p in (root / "scripts").glob("*.py")
        if not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )


def literal_md_names(path: Path) -> dict[str, set[str]]:
    """用 `ast` 找模块级赋值里形如 `[A-Z_]*INTERNAL[A-Z_]*` 的字面量集合。

    ★ **只取「模块级」**：函数内部同名局部变量不是名单（check-tables 就有
    `internal` 这个形参，M184 曾专门记过「形参同名局部变量会把传进来的字典遮掉」）。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, set[str]] = {}
    for node in tree.body:                      # 只遍历模块级语句
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if not isinstance(value, (ast.Set, ast.Tuple, ast.List)):
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if not INTERNAL_ASSIGN.match(name):
                continue
            names = {
                elt.value for elt in value.elts
                if isinstance(elt, ast.Constant)
                and isinstance(elt.value, str) and elt.value.endswith(".md")
            }
            if names:                            # 空的（如 `INTERNAL = None`）不算名单
                found[name] = names
    return found


def non_docstring_md_literals(path: Path) -> set[str]:
    """除文档字符串外，源码里出现的 `.md` 字面量（判据 3 用）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    return {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and node.value.endswith(".md") and id(node) not in docstrings
    }


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    patterns = read_src_exclude(root)
    if patterns is None:
        print("  [内部名单] 读不到 .vitepress/config.mjs 里的 srcExclude —— "
              "**判据不知道事实源**，不敢判。请先修 config.mjs。")
        return 1
    truth = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*.md")
        if not SKIP_DIRS.intersection(p.relative_to(root).parts)
        and is_excluded(p.relative_to(root).as_posix(), patterns)
    }
    truth_names = {Path(rel).name for rel in truth}
    if not truth:
        print("  [内部名单] srcExclude 一个文件都没命中 —— "
              "**事实源本身是空的**，所有判据都会自动失效。请先修 config.mjs。")
        return 1

    problems: list[str] = []
    scripts = script_files(root)
    hardcoded = 0
    for path in scripts:
        for name, names in literal_md_names(path).items():
            hardcoded += 1
            rel = path.relative_to(root).as_posix()
            if names == truth_names:
                continue
            extra, missing = sorted(names - truth_names), sorted(truth_names - names)
            problems.append(
                f"{rel}: `{name}` 是手抄的内部名单，与 srcExclude 不一致："
                f"多出 {extra or '无'}、缺少 {missing or '无'}。"
                f"**排除名单会过期，不许另抄**——改成从 `_site_exclude.read_src_exclude()` 推导"
            )

    for name in MUST_DERIVE:
        path = root / "scripts" / name
        if not path.is_file():
            problems.append(f"scripts/{name} 不存在，判据 2 无从核对")
        elif "_site_exclude" not in path.read_text(encoding="utf-8"):
            problems.append(
                f"scripts/{name} 没有 import `_site_exclude` —— "
                f"**它曾各自抄过一份内部名单**（M240），请确认它现在是从 config.mjs 推导的"
            )

    source = root / "scripts" / SCRIPTS
    if not source.is_file():
        problems.append(f"scripts/{SCRIPTS} 不存在，判据 3 无从核对")
    else:
        leaked = sorted(non_docstring_md_literals(source))
        if leaked:
            problems.append(
                f"scripts/{SCRIPTS} 里出现了硬编码的 .md 文件名 {leaked} —— "
                f"**「唯一事实源」自己又长出一份名单，前面两条判据就都白做了**"
            )

    for problem in problems:
        print(f"  [内部名单] {problem}")
    if problems:
        print(f"内部名单校验失败：{len(problems)} 项")
        return 1
    print(
        f"  [ ok ] 内部名单校验：事实源 srcExclude 命中 {len(truth)} 个内部页"
        f"（{'、'.join(sorted(truth_names))}）；"
        f"扫了 {len(scripts)} 个脚本、手抄名单 {hardcoded} 处、"
        f"{len(MUST_DERIVE)} 道该推导的门禁均在推导、唯一事实源内无硬编码文件名"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
