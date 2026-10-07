#!/usr/bin/env python3
"""页面里写的图片引用必须能解析到真实文件（第 31 道门禁，M308 新增）。

**它守的是什么**：★ **「图登记在清单里」与「页面引用的那个路径解析得到」是两件事，
而 M307 那批只有前一件有门禁。**

---

**M308 的由来（本批真实撞上的）**：★ **在根目录页面 `20-reference.md` 里我把图写成
`](../screenshots/xx.png)`，而根目录页面该写的是 `./screenshots/xx.png`。**
★ **结果：30 道门禁全过、自检 108/108 全过，★★ **只有 vitepress 打包时报
`Could not resolve "./../screenshots/xx.png"`，★★ **整轮构建 exit = 1。**

★ **★★ 为什么 30 道门禁一个都没报**：★★ **「正文引用的图片被删」那条判据在**共享的
★★ `audit_manual.py`** 里，★★ **而那是**手动**跑的技能脚本、不是构建门禁之一。**
★★★ **构建门禁里没有任何一道核对「页面里写的那个图片路径能不能解析到真实文件」。**

★ **★ 这与 F136 完全同族**：★★ **「清单登记了」与「引用真的能解析」是两件事，
★★ **而门禁只查了前一件。**

---

**判据（三条，窄到能全对）**：

对每个 md 页面（**含内部页**）里的每一条 `![alt](path)`：

1. **剥掉围栏代码块再扫**：★ **判据只认「读者真的会看到的那张图」**——
   ★ **★ 而一段演示 Markdown 语法的代码块里的 `![](…)` 不是图。★★
   ★ **★ M308 实测当前库里落在围栏里的引用是 0 条，★★ **所以这一步是为了将来，
   ★ **★ 不是为了现在这批数据。
2. **解析后的目标必须是一个真实存在的文件**；★ **★ 报不出「解析到了但不是文件」。
3. **★ 而且必须落在手册根目录之内**：★★ **这一条才是 M307 那次能被抓到的原因**——
   ★ **★ `20-reference.md` 里的 `../screenshots/x.png` 相对根目录解析出去是
   ★ **★ `docs/user-manual/screenshots/x.png`，★★ **那个目录不存在，
   ★ **★ 而判据 3 同时保证「即使那个目录碰巧存在、也仍然报」。★★

★ **★ 外部 URL（http/https/data/mailto）不参与判定，但会计数并打印**——
★★ **★ 理由：★ **「有多少条外链」是排查依据，★★ **★ 而静默跳过它
★★ **★ 就等于让外链变成一个没人管的盲区。**

---

**★ 内部页为什么也扫**：★ **M308 实测 5 个内部页的图片引用是 0 条**，
★★ **所以把扫描面扩大到它们**不增加任何误报**，★★ **却能在哪天有人往账本里
★★ **贴一张图时当场抓住。** ★ **★ 输出里分开报两个计数，★★ **不混在一起。**

用法：
    python3 scripts/check-image-refs.py .
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# 图片引用：![alt](path)。★ **path 不含空格**——★★
# ★ **含空格的写法在本库一条都没有（实测 152 条全是这种形态），★★
# ★ **所以不引入「带引号的 path」那一支，避免为了一个不存在的形态写正则**。
_IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
_FENCE = re.compile(r"```.*?```", re.S)
_EXTERNAL = re.compile(r"^(?:https?:|data:|mailto:)")


def _site_exclude():
    spec = importlib.util.spec_from_file_location("_site_exclude", _HERE / "_site_exclude.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scan(root: Path):
    se = _site_exclude()
    patterns = se.read_src_exclude(root)
    if patterns is None:
        raise SystemExit(
            "[FAIL] 读不到 .vitepress/config.mjs 的 srcExclude——"
            "分不清「发布页」与「内部页」，本门禁拒绝在口径不明时运行"
        )

    pages = [
        p for p in sorted(root.rglob("*.md"))
        if ".vitepress" not in p.parts and "node_modules" not in p.parts and "dist" not in p.parts
    ]
    published, excluded = se.split_published(pages, root, patterns)

    problems: list[str] = []
    stats = {"pub_refs": 0, "int_refs": 0, "external": 0}

    for group, key in ((published, "pub_refs"), (excluded, "int_refs")):
        for page in group:
            text = page.read_text(encoding="utf-8")
            # 判据 1：剥掉围栏
            body = _FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
            for m in _IMG.finditer(body):
                raw = m.group(1)
                line = body[: m.start()].count("\n") + 1
                stats[key] += 1
                if _EXTERNAL.match(raw):
                    stats["external"] += 1
                    continue
                # 判据 2 + 3：解析、判存在、判落在根目录内
                target = (page.parent / raw).resolve()
                rel = page.relative_to(root).as_posix()
                if not str(target).startswith(str(root) + "/") and target != root:
                    problems.append(
                        f"[{rel}:{line}] 引用解析到了手册根目录之外：{raw}\n"
                        f"        → 根目录下的页面要写 ./screenshots/…，10-tasks/ 下的才写 ../screenshots/…\n"
                        f"          解析结果是 {target}（手册根是 {root}）"
                    )
                elif not target.is_file():
                    problems.append(
                        f"[{rel}:{line}] 引用的图片不存在：{raw}\n"
                        f"        → 解析结果是 {target}，而它不是一个文件"
                    )

    return problems, stats, len(published), len(excluded)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems, stats, n_pub, n_int = scan(root)
    total = stats["pub_refs"] + stats["int_refs"]

    if problems:
        print(f"[fail] 图片引用校验未通过（{len(problems)} 项）：")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        f"[ ok ] 图片引用校验：{n_pub} 个发布页 + {n_int} 个内部页，"
        f"共 {total} 条图片引用（发布页 {stats['pub_refs']} / 内部页 {stats['int_refs']}）"
        f"全部解析到手册根目录内的真实文件"
        + (f"；另有 {stats['external']} 条外链不参与判定" if stats["external"] else "；无外链")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())