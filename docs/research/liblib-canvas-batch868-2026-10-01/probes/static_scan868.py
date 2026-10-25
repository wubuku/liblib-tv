#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 静态扫描：★ 找「**可点元素既没有行为、也没标惰性**」的糊弄形状。

## ★ 靶子

★ 运行时普查（`census868.py`）能在**当前这一版**上发现「点了没反应」的控件
⟹ ⟹ 但它**测不到未来** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 需要一道**源码层**的判据 ⟹ ⟹
⟹ ⟹ ★ 让「新的糊弄」**进不来**。

★ 糊弄在源码层的形状就是：★ 一个 `<button>`（或 `<a>`）
  ⟹ ⟹ **既没有** `onClick`／`onPointerDown`／`href` 之类**行为**
  ⟹ ⟹ **也没有** `data-inert`／`disabled` 之类**惰性声明**。

## ★ ★★ 为什么不能用正则 `<button([^>]*)>`

★ ★★ `onClick={() => foo(1)}` 里**含有 `>`** ⟹ ⟹ `[^>]*` 会在 `=>` 处**截断**
⟹ ⟹ ⟹ ⟹ ⇒ 后面的 `onClick` 被**漏看** ⟹ ⟹ ⟹ ⟹ ⇒ 报出一堆**假阳性**。
★ ⇒ 所以这里**手写一个扫描器**：★ 逐字符走 ⟹ ⟹ 跟踪
★ ① 引号（`"` / `'`）② 花括号深度 ③ 注释 ⟹ ⟹ ⟹ ⟹ 找到一个标签的**完整属性表**。

## ★ 范围

★ 只扫 **LibTV 复刻自己的**组件 ⟹ ⟹ 排除 `jimeng/` 与 `frameos/`
（★ 那两块是**别人的并发编辑区** ⟹ ⟹ 不碰）。

## ★ 输出
  raw/static-scan-868.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"
SRC = ROOT / "src"

# ★ 排除**别人的并发编辑区**
SKIP_DIRS = ("/jimeng/", "/frameos/")

# ★ 「有行为」的判据：★ 出现这些属性名 ⟹ ⟹ 它**接了事**
BEHAVIOR_KEYS = ("onClick", "onPointerDown", "onMouseDown", "onMouseUp",
                 "onDoubleClick", "onChange", "onInput", "onKeyDown", "onSubmit")
# ★ 「已标惰性」的判据
INERT_KEYS = ("data-inert", "disabled", "aria-disabled")


def mask_comments(text: str) -> str:
    """★ 把**注释**替换成等长空格（★ 保留换行 ⟹ ⟹ 偏移量不变）。

    ★ ★★ 为什么必须做这一步（★ 本脚本自己踩了**两个**坑）：
    ① 注释里出现 `<button>` 字样 ⟹ ⟹ 会被当成**真的标签** ⟹ ⟹ **假阳性**
       （★ 例：`TopNavBar.tsx` 的注释里就写着「用 `<a>`（Link）而不是 `<button>`」）
    ② 注释里出现 `>` ⟹ ⟹ 标签的属性表会被**提前截断** ⟹ ⟹ 后面的
       `data-inert`／`onClick` 被**漏看** ⟹ ⟹ **假阳性**
       （★ 例：`TopNavBar.tsx` 的「积分余额」按钮 ⟹ ⟹ 它的 `data-inert`
       正好写在**注释之后** ⟹ ⟹ 被截断 ⟹ ⟹ 误报成「没标惰性」）

    ★ ⇒ 所以：**先剥注释，再扫标签**（★ 与 batch 867 的 `parse_gates()` 同一纪律）。
    """
    out = list(text)
    i, n = 0, len(text)
    # ★ 模板字符串里的 `${}` 内部是**代码** ⟹ ⟹ 用栈跟踪
    tmpl_stack: list[int] = []
    while i < n:
        ch = text[i]
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        if ch in "\"'":
            q = ch
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if ch == "`":
            # ★ 模板字符串：★ 逐字符走 ⟹ ⟹ 遇到 `${` 就**回到代码模式**
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == "`":
                    i += 1
                    break
                if text[i] == "$" and i + 1 < n and text[i + 1] == "{":
                    # ★ 递归处理 `${}` 内的代码 ⟹ ⟹ 用一个哨兵标记
                    depth = 1
                    i += 2
                    start = i
                    while i < n and depth:
                        if text[i] == "{":
                            depth += 1
                        elif text[i] == "}":
                            depth -= 1
                            if depth == 0:
                                break
                        i += 1
                    inner = text[start:i]
                    masked = mask_comments(inner)
                    for k, c in enumerate(masked):
                        out[start + k] = c
                    i += 1
                    continue
                i += 1
            continue
        i += 1
    return "".join(out)


def scan_tags(text: str):
    """★ 逐字符扫描 ⟹ ⟹ 产出 (tag, attrs_text, start_offset)。"""
    out = []
    i = 0
    n = len(text)
    while i < n:
        j = text.find("<", i)
        if j < 0:
            break
        # ★ 跳过注释与闭合标签
        if text.startswith("<!--", j):
            k = text.find("-->", j)
            i = (k + 3) if k >= 0 else n
            continue
        m = text[j + 1:j + 2]
        if m == "/" or not (m.isalpha()):
            i = j + 1
            continue
        # ★ 读标签名
        k = j + 1
        while k < n and (text[k].isalnum() or text[k] in "-_:"):
            k += 1
        tag = text[j + 1:k]
        # ★ 走属性表：★ 跟踪引号 ＋ 花括号深度 ⟹ ⟹ 遇到**标签外的** `>` 才算结束
        p = k
        depth = 0
        quote = None
        while p < n:
            ch = text[p]
            if quote:
                if ch == "\\":
                    p += 2
                    continue
                if ch == quote:
                    quote = None
            else:
                if ch in "\"'":
                    quote = ch
                elif ch in "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                elif ch == ">" and depth == 0:
                    break
            p += 1
        attrs = text[k:p]
        out.append((tag, attrs, j))
        i = p + 1
    return out


def has_prop(attrs: str, name: str) -> bool:
    """★ 属性名是否**出现在属性表**里（★ 精确到属性名 ⟹ ⟹ 不会被 className 里的字样骗到）。"""
    import re
    return re.search(r'(^|[\s{])' + re.escape(name) + r'\s*[=\s/>]', attrs) is not None


def main() -> int:
    findings = []
    scanned = 0
    for p in sorted(SRC.rglob("*.tsx")):
        sp = "/" + str(p.relative_to(SRC))
        if any(k in sp for k in SKIP_DIRS):
            continue
        scanned += 1
        text = p.read_text(encoding="utf-8")
        # ★ ★★ 先剥注释 ⟹ ⟹ 再扫（★ 偏移量不变 ⟹ ⟹ 行号仍然对得上）
        masked = mask_comments(text)
        for tag, attrs, off in scan_tags(masked):
            if tag not in ("button", "a"):
                continue
            if tag == "a" and not has_prop(attrs, "href"):
                # ★ `<a>` 没有 href ⟹ ⟹ 它**不是**导航 ⟹ ⟹ 要么有行为、要么该标惰性
                pass
            elif tag == "a":
                continue
            has_behavior = any(has_prop(attrs, k) for k in BEHAVIOR_KEYS)
            if tag == "a":
                has_behavior = has_behavior or has_prop(attrs, "href")
            has_inert = any(has_prop(attrs, k) for k in INERT_KEYS)
            if has_behavior or has_inert:
                continue
            line = text[:off].count("\n") + 1
            findings.append({
                "file": str(p.relative_to(ROOT)),
                "line": line,
                "tag": tag,
                "attrs": " ".join(attrs.split())[:200],
            })
    out = {
        "扫描文件数": scanned,
        "范围": "src/**/*.tsx（排除 jimeng/ 与 frameos/）",
        "候选数": len(findings),
        "判据": "★ 可点元素 ⟹ ⟹ 既无 onClick/onPointerDown/onChange/href 等行为 ⟹ ⟹ "
                "又无 data-inert/disabled/aria-disabled 等惰性声明",
        "候选": findings,
    }
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "static-scan-868.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("扫描 %s 个文件 ⟹ ⟹ ★ 候选 %s 条" % (scanned, len(findings)))
    for f in findings:
        print("  %s:%d  <%s> %s" % (f["file"], f["line"], f["tag"], f["attrs"][:110]))
    print("读数已落盘：%s" % (RAW / "static-scan-868.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
