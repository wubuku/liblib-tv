#!/usr/bin/env python3
"""页面覆盖闭合校验（第二十二道门禁，M162 新增）。

**背景（M162 是一次真实的穿透，不是假想故障）**：

M161 查实「自己写的核查工具漏扫了账本里 45 处引用」之后，本批回头查了同一类问题：
**手册里的每一页，是否至少被一道内容类门禁扫到**。

先做了覆盖矩阵，**21 页正文全部被三道声明式门禁扫到、没有孤儿**——
按惯例这该记成阴性结论就收工。但 M153 已经吃过一次教训：
**覆盖不全的实验会给出「没问题」的错觉**。于是做了阳性对照，
造一个顶层页面 `40-test-coverage.md`，里面放三样东西：

1. 一句**已订正的说法**（R25 的「Dock 认不出 9 个」）→ `check-retractions.py` 该拦
2. 一个**不存在的源码引用** `nonexistent-file.ts:99999` → `check-source-refs.py` 该拦
3. 一个**坏锚点** `#no-such-anchor` → `check-anchors.py` 该拦

结果：**21 道门禁全跑，构建 exit=0 全绿**，只在末尾留了一句
`warn 以下页面未收录进 config.mjs 侧边栏`。**三样东西一件都没被拦下。**

**根因不是某个门禁写得不好，是三道声明式门禁都用「显式枚举顶层页面」**：

    BODY_PAGES = ["README.md", "00-quickstart.md", ...]   # 加了新页不会自动进 list
    BODY_GLOBS = ["10-tasks/*.md"]                          # 只有这个目录是 glob

`10-tasks/` 下新增页面会被 glob 接住，**根目录新增页面不会**——
而根目录正是 `README` / `快速上手` / `参考` / `概念` / `排障` 这五页所在的地方。

**为什么不用「改成 glob 顶层 `*.md`」这个更省事的修法**：
`AUDIT.md` / `PROGRESS.md` 是**订正史载体**，里面按设计就引用着大量已订正的说法
（全库 22 处，M153 划的边界）；`PUBLISH.md` / `TEST_MEDIA_ASSETS.md` 是维护文档。
把它们扫进 `check-retractions.py` 会立刻爆出成片的假阳性，**而那正是 M62/M93/M105
反复制造过的噪声**。所以本门禁采用**「枚举 + 有理由的排除」**：
既不放过漏网页，也不假装那四份文件该被扫。

**本门禁只做一件事**：断言「每一个顶层 `.md` 要么被至少一道声明式门禁扫到，
要么出现在 `KNOWN_EXCLUDED` 里并写明理由」。**它不检查页面内容**——
内容归各门禁管，它只管**别有页谁都不管**。

**它的边界（必须如实说清）**：
* 只看**根目录**的 `.md`。`10-tasks/` 下由三道门禁共用的 `10-tasks/*.md` glob 接住，
  已实测覆盖（新增 `10-tasks/xxx.md` 会被三道同时扫到）。
* 只认「显式枚举 + `BODY_GLOBS`」这一类门禁的覆盖面。走目录遍历的门禁
  （`check-anchors` / `check-emphasis` / `check-tables` / `check-encoding`）**不计入**——
  它们查的是结构与排版一致性，**查不出「这句话是不是已订正的错说法」**。
  这一点是本门禁存在的全部理由：把结构类门禁算作覆盖，会让漏网页显示为「已被覆盖」。

用法：

    python3 scripts/check-page-coverage.py .
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 三道「声明式」门禁：它们的覆盖面写在源码常量里，本门禁直接从源码读，
# 与 check-probe-contracts.py 同一套做法——**文档/清单不能与源码悄悄漂移**。
# 第三项是「附加的声明式页清单」：M153 起 `check-retractions.py` 把账本也纳入了扫描。
# ★ M162 第一版漏了它，于是门禁把 `SOURCE_OBSERVATIONS.md` 误报成「部分未覆盖」——
#   **覆盖面算错会给出一个反向的错误信号**，比不算更坏。
DECLARATIVE_GATES = {
    "check-claims.py": (("BODY_PAGES",), ("BODY_GLOBS",), "EXCLUDED"),
    "check-retractions.py": (("BODY_PAGES", "LEDGER_PAGES"), ("BODY_GLOBS",), "EXCLUDED"),
    "check-source-refs.py": (("BODY_PAGES",), ("BODY_GLOBS",), "EXCLUDED"),
}

# 被有意排除的顶层页面。**每条都必须写理由**——没有理由的排除等于漏网。
KNOWN_EXCLUDED: dict[str, str] = {
    "AUDIT.md": "订正史载体：按设计就要原样记下「当时写的是什么」，全库 22 处引用已订正说法；纳入 check-retractions 会爆出成片假阳性（M153 划的边界）",
    "PROGRESS.md": "同上，批次流水账，性质与 AUDIT.md 一致",
    "PUBLISH.md": "维护文档（发布流程），不是读者读到的正文",
    "TEST_MEDIA_ASSETS.md": "测试用素材说明，不是读者读到的正文",
}

PAGE_RE = re.compile(r"^([A-Za-z0-9_.\-]+\.md)$")


def read_string_list(path: Path, name: str) -> set[str]:
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"{name}\s*(?::[^=]+)?=\s*\[(.*?)\]", text, re.S)
    if not m:
        raise SystemExit(
            f"[页面覆盖] 读不出 {name}：{path}\n"
            "  若该常量已改名或删除，请同步修改本门禁，不要让它静默失效。"
        )
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def read_optional_list(path: Path, name: str) -> set[str]:
    """读一个可能不存在的列表常量（该门禁可能没有这一项）。"""
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"{name}\s*(?::[^=]+)?=\s*\[(.*?)\]", text, re.S)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def read_set(path: Path, name: str) -> set[str]:
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"{name}\s*(?::[^=]+)?=\s*\{{(.*?)\}}", text, re.S)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.exists():
        print(f"[页面覆盖] 手册目录不存在：{root}")
        return 1

    # —— 汇总三道门禁声明的覆盖面 ——
    covered: set[str] = set()
    per_gate: dict[str, set[str]] = {}
    for fname, (p_names, g_names, e_name) in DECLARATIVE_GATES.items():
        script = HERE / fname
        if not script.exists():
            print(f"[页面覆盖] 声明式门禁不存在：{fname}")
            return 1
        pages: set[str] = set()
        for p_name in p_names:
            pages |= read_optional_list(script, p_name)
        globs: set[str] = set()
        for g_name in g_names:
            globs |= read_optional_list(script, g_name)
        excl = read_set(script, e_name)
        hit: set[str] = set()
        for page in root.glob("*.md"):
            rel = page.name
            if rel in excl:
                continue
            if rel in pages:
                hit.add(rel)
                continue
            for g in globs:
                if g.startswith("10-tasks/") and rel in KNOWN_EXCLUDED:
                    continue
                if "/" not in g and rel in pages:
                    hit.add(rel)
        # 目录型 glob（10-tasks/*.md）对根目录文件不适用，这里只记显式页
        per_gate[fname] = hit | {p for p in pages if "/" not in p}
        covered |= per_gate[fname]

    # —— 根目录实际存在的页面 ——
    actual = {p.name for p in root.glob("*.md")}

    problems: list[str] = []

    # 1) 根目录里有、谁都不扫的页
    orphans = sorted(
        f for f in actual
        if f not in covered and f not in KNOWN_EXCLUDED
    )
    for f in orphans:
        problems.append(
            f"[漏网] 顶层页面 {f} 不被任何声明式门禁扫描。\n"
            "  **三道门禁的顶层页面是显式枚举的**（BODY_PAGES），只有 `10-tasks/*.md` 是 glob——\n"
            "  所以在根目录新增页面会静默逃过全部内容类检查。\n"
            "  修法二选一：① 把该页加进三道门禁的 BODY_PAGES（若它确实是正文）；\n"
            "  ② 若它本就不该被扫，写进本脚本的 KNOWN_EXCLUDED 并**补上理由**。"
        )

    # 2) KNOWN_EXCLUDED 里写了、但文件已经不在了
    for f in sorted(set(KNOWN_EXCLUDED) - actual):
        problems.append(
            f"[过期] KNOWN_EXCLUDED 登记的 {f} 已不存在。"
            "删掉这条登记，或把文件加回来——**留着会让排除表逐渐失真**。"
        )

    # 3) KNOWN_EXCLUDED 里的条目没写理由
    for f, why in sorted(KNOWN_EXCLUDED.items()):
        if len(why.strip()) < 12:
            problems.append(
                f"[豁免过宽] KNOWN_EXCLUDED 里 {f} 的理由过短（{why!r}）。\n"
                "  **排除必须写清为什么它不该被扫**，否则和漏网没有区别。"
            )

    print(
        f"[页面覆盖] 根目录 {len(actual)} 个 md；"
        f"三道声明式门禁声明覆盖 {len(covered & actual)} 个；"
        f"有理由排除 {len(set(KNOWN_EXCLUDED) & actual)} 个"
    )
    for fname, hit in sorted(per_gate.items()):
        print(f"  · {fname}：{len(hit & actual)} 页")

    # ★ 可见但不阻断：**部分覆盖**（被至少一道扫到、但没被全部扫到）不是本门禁的失败条件，
    #   因为现存的分化是有理由的（账本不进 `check-claims` 等）。
    #   但**不打印出来就等于不存在**——M161 漏扫 45 处引用，根子就在「没人知道覆盖面差在哪」。
    gaps = sorted(f for f in actual if f in covered and f not in KNOWN_EXCLUDED
                  and any(f not in hit for hit in per_gate.values()))
    if gaps:
        print("  [提醒] 以下页面被**部分**门禁扫到（不是漏网，仅供知情）：")
        for f in gaps:
            missing = sorted(n for n, hit in per_gate.items() if f not in hit)
            print(f"    · {f} —— 未被 {', '.join(missing)} 扫到")

    if problems:
        print("[FAIL] 页面覆盖校验未通过：")
        for p in problems:
            print("  " + p)
        print()
        print("  提示：这不是「某页内容有问题」，而是「有页谁都不看」——")
        print("        前者由各内容门禁负责，后者只有本门禁能发现。")
        return 1

    print("[ ok ] 页面覆盖：根目录每个 md 要么被声明式门禁扫到、要么有理由排除")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
