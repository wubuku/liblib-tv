#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 共用工具：★ **门禁的失败提取** ＋ **门禁的运行**。

## ★ ★★ 为什么要有这个文件（★ 本批踩到的坑）

★ `new_gates868.py` 原本用「**最后一行含 `/` 且以「通过」结尾**」来提取 verdict
⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是 `9/10 判据通过`（★ **有 1 项失败**）被提取成 `通过`
⟹ ⟹ ⟹ ⟹ ⇒ ★ 读数表里出现「rc=1 但 verdict=通过」的**矛盾行**
⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 这正是本仓反复出现的那个形状：
⟹ ⟹ ⟹ ⟹ ⇒ 「**跑通了 ≠ 看到了**」⟹ ⟹ ⟹ ⟹ ⇒ 「**『通过』两个字不等于通过**」。

★ 所以本文件把 verdict **彻底换掉**：
  - 判据层：抽取 **`FAILED:` / `FAIL … ｜` / `[FAIL]` / `AssertionError`** ⟹ ⟹ 真实的红条；
  - 兜底层：**最后一行非空输出**（★ 保留原文，不做摘要）⟹ ⟹ 崩了也能看见崩在哪；
  - ★ **绝不再用「通过」两个字当结论** ⟹ ⟹ 判据自己必须**能失败**。

## ★ ★★ 提取器的判据强度（★ 门禁自身的门禁）

★ 提取器如果**看不见**某类失败 ⟹ ⟹ 那类失败就会**静默变成绿**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以提取器有**自测**：`self_test()` ⟹ ⟹ 喂它 5 种失败形状
⟹ ⟹ ⟹ ⟹ ⇒ 断言它**每一种都能看见** ⟹ ⟹ ⟹ ⟹ ⇒ 否则**不许用**。
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

# ★ 各类门禁的红条形状（★ 取自本仓真实门禁的输出）
EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$")


def extract_failures(text: str) -> list[str]:
    """★ 从门禁输出里抽出**真实**的红条（★ 不靠「通过」两个字）。"""
    out: list[str] = []
    lines = text.splitlines()
    for ln in lines:
        s = ln.strip()
        if s.startswith("FAILED:"):
            out.extend(x.strip() for x in s[len("FAILED:"):].strip().split(",")
                       if x.strip())
            continue
        m = re.match(r"^FAIL\s{2,}(.+?)\s*｜", s)
        if m:
            out.append(m.group(1).strip())
            continue
        m = re.match(r"^\[FAIL\]\s*(.+?)(?:\s*⟵.*)?$", s)
        if m:
            out.append(m.group(1).strip())
            continue
        if s.startswith("AssertionError"):
            out.append(s[:200])
            continue
    if "Traceback (most recent call last):" in text and not out:
        for ln in reversed(lines):
            m = EXC_RE.match(ln.strip())
            if m:
                out.append("CRASH: %s: %s" % (m.group(1), m.group(2)[:160]))
                break
    seen: set[str] = set()
    uniq: list[str] = []
    for f in out:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def last_meaningful(text: str) -> str:
    """★ 最后一行**非空**输出（★ 保留原文 ⟹ 不做摘要 ⟹ 崩了能看见崩在哪）。"""
    ls = [x.strip() for x in text.splitlines() if x.strip()]
    return ls[-1][:240] if ls else "(无输出)"


def run_gate(batch: str, ext: str, timeout: int = 1800,
             cwd: pathlib.Path = ROOT) -> dict:
    """★ 跑一道门禁 ⟹ ⟹ 返回 rc ＋ 真实红条 ＋ 完整输出。"""
    script = cwd / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=str(cwd))
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = "timeout", ""
    return {
        "batch": batch, "ext": ext, "rc": rc,
        "failures": extract_failures(out),
        "last": last_meaningful(out),
        "seconds": round(time.time() - t0, 1),
        "out": out,
    }


def self_test() -> bool:
    """★ 提取器**自己也要经得起检查**（★ 否则「看不见」就等于「绿」）。"""
    cases = [
        ("3/10 判据通过\n  FAILED: the-first-red\n",
         ["the-first-red"], "★ 分母式摘要不能骗人"),
        ("★ 7/7 判据通过\n  FAILED: a, b\n", ["a", "b"], "★ 逗号分隔"),
        ("FAIL  S3: xxx ｜ detail\n", ["S3: xxx"], "★ FAIL ｜ 形状"),
        ("[FAIL] S9: yyy ⟵ z\n", ["S9: yyy"], "★ [FAIL] 形状"),
        ("AssertionError: nope\n", ["AssertionError: nope"], "★ 断言形状"),
    ]
    for text, want, why in cases:
        got = extract_failures(text)
        if got != want:
            print("★ 提取器自测失败：%s ⟹ 期望 %s 实得 %s" % (why, want, got))
            return False
    # ★ 反向：★ **真的全绿**的输出 ⟹ ⟹ 必须抽不出任何红条
    green = "★ 12/12 判据通过\n★ 阴性对照 6/6\n"
    if extract_failures(green):
        print("★ 提取器自测失败：★ 全绿输出被抽出了红条")
        return False
    # ★ 反向：★ 「通过」两个字**不能**当成结论
    if "通过" in (extract_failures("★ 9/10 判据通过\n") or [""])[0]:
        print("★ 提取器自测失败：★ 把「通过」当成了结论")
        return False
    print("★ 提取器自测：%s 种失败形状全部可见 ＋ 全绿不误报 ＋ 「通过」不当结论"
          % len(cases))
    return True


if __name__ == "__main__":
    sys.exit(0 if self_test() else 1)
