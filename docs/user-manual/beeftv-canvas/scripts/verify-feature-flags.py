#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十三道闸：特性开关的默认值——手册说的「关掉会怎样」，读者到底站在哪一边？

**为什么要有这道闸（Batch 173 的由来）**：手册多处写「这一整块由 `xxxEnabled` 特性开关
控制，**开关关掉时会怎样**」，**却从不说默认是哪一边**。实测 7 个开关里 **6 个默认开**，
唯一默认关的只有 `frontendModels`。于是本地读者看到「需开启 `pluginCenterEnabled` 特性」
这类措辞时，**会以为有个开关等他去打开——而那个开关根本不存在**：
服务端只注册了 `GET /features`，写入方法 `UpdateFeatureAvailability` 在 handler/cmd 层
**零调用**（这一点由闸 7 的 `feature-availability-readonly` 断言守着）。

**这与 Batch 172 的策略常量是同一类错误**：一句条件句，读者不知道自己站在哪一边。
**纪律 113 的续集**：同一个量有多套取值时，手册必须把「你属于哪一套」写出来。

**本闸判什么**：`20-reference.md` 的「特性开关默认值」表里，每个开关的默认值都必须与
`backend/internal/platform/feature_availability.go` 的 `DefaultFeatureAvailability()` 相符。

**覆盖不到什么（如实说明）**：
  · 只核 `DefaultFeatureAvailability()` **这一个**来源；`readFeatureAvailability()`
    在配置已存在时会读数据库里的值——**那属于运维改过的部署**，与本手册的默认场景无关；
  · 解析不出某个字段时按「未能核对」报 rc=2，**不假装通过**（纪律 101）。

退出码：0 全部相符；1 有不符；2 未能核对（找不到源码 / 找不到表 / 任一行解析不出）。
"""
import os
import re
import subprocess
import sys
from baseline import resolve_ref, BaselineError, module_ref, baseline_guard
from baseline import SRC as _BEEFSRC
from baseline import announce_fallback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, "20-reference.md")
#: **Batch 197：不再单点读环境变量，改从 `baseline` 取统一解析后的路径**
#: （原先无任何校验，坏路径会被原样塞进 `git -C <path>`）。
SRC = _BEEFSRC
REF = module_ref()
FLAGS_FILE = "backend/internal/platform/feature_availability.go"


def _git_show(path):
    r = subprocess.run(["git", "-C", SRC, "show", f"{REF}:{path}"],
                       capture_output=True, text=True)
    return None if r.returncode != 0 else r.stdout


def parse_defaults(text):
    """从 DefaultFeatureAvailability() 的函数体里取 {字段名: True/False}。"""
    m = re.search(r"^func\s+DefaultFeatureAvailability\s*\(\)[^{]*\{", text, re.M)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    body = None
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                body = text[i:j + 1]
                break
    if body is None:
        return None
    out = {}
    for fm in re.finditer(r"\b([A-Za-z]\w*)\s*:\s*(true|false)\b", body):
        out[fm.group(1)] = fm.group(2) == "true"
    return out


def parse_table():
    if not os.path.isfile(MANUAL):
        raise ValueError(f"找不到 {MANUAL}")
    text = open(MANUAL, encoding="utf-8").read()
    m = re.search(r"###\s*特性开关默认值[^\n]*\n(.*?)(?=\n##\s|\n###\s)", text, re.S)
    if not m:
        raise ValueError("20-reference.md 里找不到「特性开关默认值」小节")
    rows = []
    for line in m.group(1).split("\n"):
        if not line.startswith("|") or re.match(r"\|\s*:?-", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("开关", ""):
            continue
        field = cells[1].strip("`")
        if cells[2] not in ("true", "false"):
            raise ValueError(f"开关 {field} 的默认值必须是 true/false，"
                             f"实得 [{cells[2]}]——表解析不了 = 整轮未能核对")
        rows.append((field, cells[2] == "true"))
    if not rows:
        raise ValueError("特性开关默认值表里没有数据行")
    return rows


@baseline_guard
def main():
    announce_fallback()
    try:
        rows = parse_table()
    except ValueError as exc:
        print(f"[skip] {exc}，特性开关默认值核对本轮未能进行")
        return 2
    if SRC is None:
        print(f"[skip] 未找到 BeefTV 源码 {SRC}，特性开关默认值核对本轮未能进行")
        return 2
    text = _git_show(FLAGS_FILE)
    if text is None:
        print(f"[skip] 读不到 {REF}:{FLAGS_FILE}，特性开关默认值核对本轮未能进行")
        return 2
    defaults = parse_defaults(text)
    if not defaults:
        print("[skip] 在 feature_availability.go 里找不到 DefaultFeatureAvailability()，"
              "本轮未能核对")
        return 2

    bad, void = [], []
    for field, want in rows:
        if field not in defaults:
            void.append(f"{field}：上游 DefaultFeatureAvailability() 里没有这个字段"
                        f"（可能已改名或删除）")
            continue
        got = defaults[field]
        if got != want:
            bad.append(f"{field}：手册写 {str(want).lower()}，上游 {str(got).lower()}")
    for v in void:
        print(f"[skip] {v}")
    if bad:
        print(f"特性开关默认值核对：{len(bad)} 条声明与上游不符")
        for b in bad:
            print("  " + b)
        print("→ 更新 20-reference.md 的开关表，并检查手册正文里"
              "「需开启 X 特性」这类措辞（**默认开着的话，这句话会让人去找一个不存在的开关**）")
        return 1
    if void:
        print(f"[skip] {len(void)}/{len(rows)} 行本轮未能核对，"
              f"其余 {len(rows) - len(void)} 条相符 —— **不是全部通过**")
        return 2
    off = [f for f, v in rows if not v]
    print(f"特性开关默认值核对通过：{len(rows)} 个开关的默认值与 {REF} 逐一相符"
          + (f"（其中默认关闭的只有 {', '.join(off)}）" if off else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
