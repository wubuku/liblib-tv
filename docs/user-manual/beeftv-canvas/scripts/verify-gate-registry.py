#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十四道闸：**闸门行为登记的新鲜度**（Batch 311 新增）。

## 它守的是一个刚刚真实发生过、且没有任何东西会报的事

纪律 332 那张「升版要过的 8 道门」矩阵，是 Batch 297 逐道对跑两个 ref 量出来的，
写在 `AUDIT-RULES.md` 纪律 332② 里，**合计 32 条**。
它登记的是**闸的行为**——每道闸在 `origin/main` 上会报几条。
**而闸本身一直在被改。**

实测（Batch 311）：

  · Batch 304 改了 `verify-quote-punct.py`（测试文件不进语料），
    它那一行随即从 **2 条变成 0 条**；
  · 而登记上一直写着 2，**过期了 7 个批次**，期间每一道闸都绿；
  · 复现实验：把 Batch 304 之前那版闸放进镜像树、其余一字不动，
    在 `origin/main` 上原样复现那 2 条 —— **唯一变量就是闸文件**。

**「改闸」和「改关于闸的登记」是两件事，而没有任何机制要求它们一起发生。**

## 与 `SELFTEST_COSTS` 的 `measured_at` 是同一个病（Batch 307 已治过一处）

那里是「反验耗时只能由人手推动更新」，这里是「闸的输出条数只能由人重测更新」。
两处都是**手抄的实测值**，两处都只在有人重测之后才变。
Batch 307 的方向四h 给前者配了用例；本闸给后者配。

## 能力上限（如实写在这张闸的首页）

**本闸不重跑那 8 道闸**，所以它**核不了登记里的条数对不对**——
它只核「产出这些条数的东西有没有变」。这与 `measured_at` 那个方向的上限相同：
**判据能发现「输入变了」，不能发现「当初就抄错了」。**

## 判据逐条

方向一 · **指纹**：登记每行带的 `gate_sha256` 必须等于该闸文件当前的 sha256。
不等 = 这一行登记的实测值已作废（产出它的那道闸在测量之后被改过）。
方向二 · **悬空**：登记指名的闸文件必须真实存在。
方向三 · **合计自洽**：各行 `upstream_items` 之和必须等于 `total`。
方向四 · **形态齐全**：每行必须同时登记**红态句与绿态句**。
方向五 · **正文对账**：`AUDIT-RULES.md` 里那条「闸门登记现状」必须存在且唯一，
且它写的道数 / 红态数 / 条数 / `measured_at` 必须与本登记逐个相符。
方向六 · **自检**：登记读不到、字段缺失、判别式失效 → rc=2「未能核对」。
方向七 · **生成器指纹**（Batch 312 新增）：登记自己必须带**产出它的那个脚本**
的 sha256。**上一批只给「产出那些条数的 8 道闸」打了指纹，却没给「产出那些条的脚本」打**
——**而后者才是链子的最后一环**：改了它，「重测」就换了做法，
而闸会照旧说「每行的产出闸都没变过」。

## 方向五为什么要存在

纪律 332② 的 **8 道 / 32 条必须原样留着**——它是 Batch 297 的历史实测，
证据处留痕。而留着它就意味着**订正必须挨着它**，否则读的人只会看到那个已经过期的数。
方向五把「订正还在不在、还对不对」变成构建期可判的事实。
"""

import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(ROOT, "scripts")
REGISTRY = os.path.join(SD, "gate-registry.json")
RULES = os.path.join(ROOT, "AUDIT-RULES.md")

#: 纪律 346 订正块里那行的标记。**要求全文件恰好出现一次**——
#: 0 次 = 订正不见了（于是只剩那个过期的 8/32 在被人读），>1 次 = 有歧义。
MARKER = "闸门登记现状"

fails = []
notes = []


def fail(msg):
    fails.append(msg)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def load_registry():
    """读登记。**读不到就 rc=2，不许当成通过**（纪律 101）。"""
    if not os.path.isfile(REGISTRY):
        return None, "登记文件不存在：%s" % REGISTRY
    try:
        with io.open(REGISTRY, encoding="utf-8") as fh:
            return json.load(fh), None
    except (ValueError, UnicodeDecodeError) as exc:
        return None, "登记不是可解析的 JSON：%s" % exc


def check_rows(reg):
    """方向一 / 二 / 三 / 四。返回核过的行数。"""
    rows = reg.get("gates")
    if not isinstance(rows, list) or not rows:
        fail("  ✗ 登记里没有 `gates` 列表，或它是空的——**没有登记就没有可作废的东西**")
        return 0

    seen, total = set(), 0
    for i, row in enumerate(rows):
        name = row.get("gate")
        if not name:
            fail("  ✗ 第 %d 行没有 `gate` 字段" % (i + 1))
            continue
        if name in seen:
            fail("  ✗ `%s` 登记了两次——同一道闸两次登记，两份都可能过期" % name)
            continue
        seen.add(name)

        # 方向二 · 悬空
        path = os.path.join(SD, name)
        if not os.path.isfile(path):
            fail("  ✗ 登记指名 `%s`，而 scripts/ 下没有这个文件——"
                 "**闸被改名或删除了，登记没跟上**" % name)
            continue

        # 方向一 · 指纹
        want = row.get("gate_sha256")
        if not want:
            fail("  ✗ `%s` 没登记 `gate_sha256`——**没有指纹的登记无法判断自己过期了没有**"
                 % name)
            continue
        got = sha256_of(path)
        if got != want:
            fail("  ✗ `%s` 的登记已作废：产出这行实测值的闸在测量之后被改过"
                 "（登记 %s…，现场 %s…）。**处置是重测并更新登记，"
                 "不是把指纹改回去**——改回去等于让过期值继续冒充实测值"
                 % (name, want[:16], got[:16]))

        # 方向四 · 形态齐全
        for key in ("red_sentence", "green_sentence"):
            if not row.get(key):
                fail("  ✗ `%s` 没登记 `%s`——**只登记一半形态，"
                     "下一次重测就会在另一种形态上数错**（红态句与绿态句句首逐字相同，"
                     "而数字含义相反）" % (name, key))

        # 条数本身
        n = row.get("upstream_items")
        if not isinstance(n, int) or n < 0:
            fail("  ✗ `%s` 的 `upstream_items` 不是非负整数：%r" % (name, n))
            continue
        total += n

    # 方向三 · 合计自洽
    want_total = reg.get("total")
    if want_total != total:
        fail("  ✗ 合计不自洽：各行相加 %d，登记写着 %r" % (total, want_total))
    return len(seen)


def check_prose(reg):
    """方向五 · 正文对账。"""
    if not os.path.isfile(RULES):
        fail("  ✗ 找不到 AUDIT-RULES.md")
        return
    with io.open(RULES, encoding="utf-8") as fh:
        text = fh.read()

    hits = [m for m in re.finditer(re.escape(MARKER), text)]
    if len(hits) == 0:
        fail("  ✗ AUDIT-RULES.md 里找不到「%s」那一行——**订正不见了，"
             "于是只剩纪律 332② 那个已经过期的 8 道 / 32 条在被人读**" % MARKER)
        return
    if len(hits) > 1:
        fail("  ✗ AUDIT-RULES.md 里「%s」出现 %d 次，判据不知道该对哪一行"
             % (MARKER, len(hits)))
        return

    line = text[hits[0].start():]
    line = line[:line.find("\n")]

    rows = reg.get("gates") or []
    gates = len(rows)
    red = sum(1 for r in rows if r.get("measured_form") == "红态")
    total = reg.get("total")
    at = reg.get("measured_at")

    for label, want in (("道数", gates), ("红态数", red),
                        ("条数", total), ("measured_at", at)):
        if want is None:
            continue
        if str(want) not in line:
            fail("  ✗ 「%s」那一行里没有 %s=%s（原文：%s）——**正文与登记分家了**"
                 % (MARKER, label, want, line.strip()[:90]))
    if at and at not in line:
        notes.append("  订正行里没有写 measured_at（%s）" % at)


def check_generator(reg):
    """方向七 · 生成器指纹。

    **为什么它是独立的一向而不是并进方向一**：方向一钉的是「产出条数的闸」，
    这一向钉的是「产出登记的脚本」。**两者是链子上相邻的两环**，
    而**漏掉任何一环，整条链就有一处不被看守的接缝**——
    漏掉这一环的后果具体是：改了重测脚本，「重测」换了做法，
    而闸 44 照旧报「每行的产出闸都没变过」。
    """
    gen = reg.get("generator")
    if not isinstance(gen, dict) or not gen.get("script") or not gen.get("sha256"):
        fail("  ✗ 登记里没有 `generator`（产出它自己的那个脚本）——"
             "**指纹链在最后一环是断的**")
        return
    name = gen["script"]
    path = os.path.join(SD, name)
    if not os.path.isfile(path):
        fail("  ✗ 登记指名的生成器 `%s` 不存在——**登记说的「怎么重测」已经无处可执行**"
             % name)
        return
    got = sha256_of(path)
    if got != gen["sha256"]:
        fail("  ✗ 生成器 `%s` 已改而登记没跟上（登记 %s…，现场 %s…）——"
             "**处置是重跑一次重测脚本**，不是把指纹改回去"
             % (name, gen["sha256"][:16], got[:16]))


def main():
    reg, err = load_registry()
    if err:
        print("[未能核对] %s" % err)
        print("闸门行为登记新鲜度核对：未能核对")
        return 2

    n = check_rows(reg)
    check_generator(reg)
    check_prose(reg)

    measured = "%s／基线 %s" % (reg.get("measured_at"), reg.get("baseline_ref"))
    print("闸门行为登记：%d 道闸、%d 条（%s）" % (n, reg.get("total", -1), measured))
    for note in notes:
        print(note)

    if fails:
        for f in fails:
            print(f)
        print("闸门行为登记新鲜度核对：%d 处需处理" % len(fails))
        return 1
    print("闸门行为登记新鲜度核对通过：每行的产出闸都没变过，合计自洽，正文订正与登记相符")
    return 0


if __name__ == "__main__":
    sys.exit(main())