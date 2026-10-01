#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取证基线（Batch 175 新增）——所有读上游源码的闸门共用**同一个**版本对象。

**这个文件为什么存在（Batch 175 的实测，不是假想问题）**：

手册正文声明「适用 v1.6.16」，正文是照 **v1.6.16** 写的。而在此之前，8 道读源码的
闸门各自把上游 ref 写死成 **`origin/main`**（浮动的）。两者会静悄悄地分家：

  · 上游从 v1.6.16 走到 v1.6.22（实测 27 个提交、223 个文件有差异），
  · 闸门却还在按新版本核对**照旧版本写的正文**，
  · 于是红灯亮起，而**红灯的含义被搞反了**。

实测抓到两处：`web/src/pages/canvas` 行数 17009→17122，以及「选择镜头模板」文案
在上游被删（`canvas-director-template-modal.tsx` 整个文件在 v1.6.22 已不存在）。
**这两条在 v1.6.16 上都是绿的**——手册没写错，是上游走了。

**为什么这个混淆很危险**：红灯只有一种修法（改手册正文），于是人会去改正文，
**把照 v1.6.16 写的内容改成 v1.6.22 的样子**——手册从此不再对应任何一个真实版本。
「上游走了」和「手册错了」这两件事的修法**正好相反**：
前者该做的是**重做一轮增量对账并升版**，后者才是改正文。

**本模块的约定**：

  · `BEEFTV_REF` 环境变量**优先**——反向验证需要指向合成 ref，这是 Batch 163
    之后所有 selftest 的既有做法，不能破坏。
  · 否则用**手册自己声明的版本**（`20-reference.md` 的「取证基线」小节）。
  · 读不到声明时**不猜**，抛 `BaselineError` 让调用方返回 rc=2「未能核对」——
    宁可报「无法核对」，也不静悄悄地退回浮动 `origin/main`（Batch 157 的教训：
    工具失败被当成零命中，是同一类错误的另一种形态）。

**基线声明写在手册里而不是代码里**，理由和闸 3 相同：被核对的文件必须是唯一真值。
基线改了只需改手册，不必碰 8 个脚本；而「基线声明与 README 的适用版本是否一致」
由闸 14 双向对账。

**`BEEFTV_MANUAL_ROOT` 为什么存在**（Batch 178 加）：
反向验证会把被测闸门**复制进临时目录**再运行，而闸门会 import 本模块。
本模块原先用 `dirname(dirname(__file__))` 推断手册根——**在临时目录里就指错了**，
于是 `resolve_ref()` 抛 `BaselineError: 读不到 20-reference.md`，
**反验的每一例都失败，而闸门本体的构建检查全绿**。
（同一批还有第二层：反验只复制了闸门脚本、没复制本模块，直接 ModuleNotFoundError。
**两层都静悄悄坏了三个批次**——因为「反验坏了」不会让构建变红，只有专门去跑它才看得见。）
**教训**：一个被多处 import 的模块，它的「定位自己所在仓」的假设**必须在被搬运时仍然成立**。
用环境变量显式传入是最省事、也最不容易被误删的做法。
"""

import os
import re
import subprocess

ROOT = os.environ.get("BEEFTV_MANUAL_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(ROOT, "20-reference.md")
SRC = os.environ.get("BEEFTV_SRC", "/Users/yangjiefeng/Documents/glanderness/BeefTV")

# 手册里「取证基线」小节声明的两个字段。改动这里 = 改手册的取证对象。
_FIELD_RE = re.compile(r"^-\s*\*\*(版本|提交)\*\*[：:]\s*`?([^`\s]+)`?\s*$")


class BaselineError(RuntimeError):
    """读不到基线声明、或声明的提交在上游不存在。调用方应返回 rc=2。"""


def declared_baseline():
    """从 `20-reference.md` 的「取证基线」小节读出 (版本, 提交)。

    **刻意锚在「小节标题 + 紧邻的两个字段」上**，而不是全文搜「v1.6.」：
    手册里到处都是版本号（每页的适用版本行、增量说明），全文搜必然抓到一堆，
    那就是 Batch 133「判据锚的是誊抄副本」的翻版。
    """
    try:
        with open(REFERENCE, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise BaselineError(f"读不到 {os.path.basename(REFERENCE)}：{exc}")

    start = text.find("### 取证基线")
    if start < 0:
        raise BaselineError(
            "20-reference.md 里找不到「### 取证基线」小节——手册没有声明它照哪个版本取证")
    end = text.find("\n### ", start + 1)
    section = text[start:] if end < 0 else text[start:end]

    version = commit = None
    for line in section.splitlines():
        m = _FIELD_RE.match(line.strip())
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "版本":
            version = val
        elif key == "提交":
            commit = val
    if not version or not commit:
        raise BaselineError(
            "「### 取证基线」小节里没有同时声明「版本」和「提交」两个字段")
    return version, commit


def resolve_ref():
    """闸门真正该读的上游 ref。

    优先级：`BEEFTV_REF`（反向验证用）> 手册声明的提交。
    读不到声明 → `BaselineError`，**绝不**静悄悄退回 `origin/main`。
    """
    override = os.environ.get("BEEFTV_REF")
    if override:
        return override
    _version, commit = declared_baseline()
    if not commit_exists(commit):
        raise BaselineError(
            f"手册声明的取证基线提交 {commit} 在 {SRC} 里不存在"
            "（上游可能已 gc 掉该对象，或提交号写错了）")
    return commit


def commit_exists(rev):
    r = subprocess.run(["git", "-C", SRC, "rev-parse", "--verify", "--quiet", rev + "^{commit}"],
                       capture_output=True, text=True)
    return r.returncode == 0


def describe():
    """给闸门输出用的一行说明：当前按哪个版本取证。"""
    version, commit = declared_baseline()
    return f"{version}（{commit}）"


def upstream_tip():
    """上游 origin/main 顶端，用于闸 14 报告「基线落后几个版本」。失败返回 None。"""
    r = subprocess.run(["git", "-C", SRC, "rev-parse", "--verify", "--quiet", "origin/main^{commit}"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None
