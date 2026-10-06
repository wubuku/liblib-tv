#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch 311：生成 / 重测 `scripts/gate-registry.json`。

**为什么必须生成而不是手写**：本批要立的那道闸治的正是「一份关于闸的手抄实测值」，
而登记本身若是手打的，它就是同一种病的第一例。

**本脚本是那张矩阵的重测工具**，取值两处，全部现场：
  · 条数：本轮逐闸落盘的 `<闸>.<ref>.out`
  · 指纹：当前 `scripts/verify-*.py` 的 sha256

## 三条从实测里长出来的硬规矩

**① 红态句与绿态句必须逐闸各登记一条，而它们的前缀逐字相同。**
实测 8 道闸里有 4 道的句首在两个形态下完全一样：

    绿：`标签漂移核对：27 项跨文件分歧全部与登记一致`   ← 27 是「核了多少项」
    红：`标签漂移核对：2 项需要处理`                     ← 2 是「有几处不一致」

`截图取证文案核对：82 个…`（绿）vs `…：2 处需处理`（红）、
`截图布局漂移核对：67 张截图…`（绿）vs `…：12 处问题`（红）、
`不可达声明核对：32 条断言仍成立`（绿）vs `…：4 处不一致`（红）——
**四条都在基线上是绿的**。
所以「扫全文取第一个数」会把一个全绿的基线读成 27/82/67/32 条问题。
**这就是纪律 332⑧② 记的那个坑的完整形状**：当时记的是「会挑到别处的数」，
实际是「会挑到句首相同的另一个含义的数」。

**② 取值必须锚定 rc，不能扫全文。** rc=0 只可能落在绿态句上，rc≠0 只可能落在红态句上。

**③ `rc≠0` 而数出 `0`、或 `rc=0` 而数出非 0，当场抛错**（纪律 155 / 297⑧）。
认不出合计句也抛错——**不许把 0 当结果报出去**。
"""

import hashlib
import io
import json
import os
import re

MAN = "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/beeftv-canvas"
SD = os.path.join(MAN, "scripts")
WORK = "/tmp/b311work"
OUT = os.path.join(SD, "gate-registry.json")

BASELINE = "bcc3b05"
UPSTREAM = "origin/main"

#: 每道闸的**红态句**与**绿态句**，各自带一个捕获组。
#: 红态组 = 需要处理的条数；绿态组 = 已核对的项数（**语义不同**，
#: 而绿态那一条**永远不进登记的条数**——绿就是 0 条）。
SENTENCES = {
    "verify-error-copy.py": (
        r"错误分类文案核对：(\d+) 处不一致",
        r"错误分类文案核对通过：",
    ),
    "verify-label-drift.py": (
        r"标签漂移核对：(\d+) 项需要处理",
        r"标签漂移核对：(\d+) 项跨文件分歧全部与登记一致",
    ),
    "verify-line-counts.py": (
        r"上游行数核对：(\d+)/\d+ 条声明与上游不符",
        r"上游行数核对通过：",
    ),
    "verify-quota-tables.py": (
        r"账号配额核对：(\d+) 处声明与上游不符",
        r"账号配额核对通过：",
    ),
    "verify-quote-punct.py": (
        r"标点漂移核对：(\d+) 处",
        r"标点漂移核对通过：",
    ),
    "verify-screenshots-literals.py": (
        r"截图取证文案核对：(\d+) 处需处理",
        r"截图取证文案核对：(\d+) 个保守形态片段全部在上游存在",
    ),
    "verify-shot-drift.py": (
        r"截图布局漂移核对：(\d+) 处问题",
        r"截图布局漂移核对通过：",
    ),
    "verify-unreachable.py": (
        r"不可达声明核对：(\d+) 处不一致",
        r"不可达声明核对：(\d+) 条断言仍成立",
    ),
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def read_out(gate, ref):
    p = os.path.join(WORK, "%s.%s.out" % (gate, ref.replace("/", "_")))
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rc_of(gate, ref):
    with io.open(os.path.join(WORK, "matrix.json"), encoding="utf-8") as fh:
        for r in json.load(fh):
            if r["gate"] == gate and r["ref"] == ref:
                return r["rc"]
    raise KeyError((gate, ref))


def upstream_items(gate):
    """按 rc 锚定形态取条数。**不扫全文。**"""
    rc = rc_of(gate, UPSTREAM)
    out = read_out(gate, UPSTREAM)
    red_re, green_re = SENTENCES[gate]

    if rc == 0:
        if not re.search(green_re, out):
            raise ValueError("%s：rc=0 却认不出绿态句 %r" % (gate, green_re))
        return 0, "绿态"

    m = re.search(red_re, out)
    if not m:
        raise ValueError("%s：rc=%s 却认不出红态句 %r" % (gate, rc, red_re))
    n = int(m.group(1))
    if n == 0:
        raise ValueError("%s：rc=%s 而数出 0 —— 探针故障，不是结果" % (gate, rc))
    return n, "红态"


def main():
    gates = sorted(SENTENCES)
    entries, problems = [], []

    for g in gates:
        try:
            n, form = upstream_items(g)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        base_rc = rc_of(g, BASELINE)
        if base_rc != 0:
            problems.append("%s：基线 rc=%s —— 矩阵前提已不成立" % (g, base_rc))
        red_re, green_re = SENTENCES[g]
        entries.append({
            "gate": g,
            "upstream_items": n,
            "measured_form": form,
            "red_sentence": red_re,
            "green_sentence": green_re,
            "gate_sha256": sha256_of(os.path.join(SD, g)),
        })

    if problems:
        print("**生成中止**，以下问题必须先解决：")
        for p in problems:
            print("  ✗ " + p)
        raise SystemExit(1)

    total = sum(e["upstream_items"] for e in entries)
    reg = {
        "_唯一真值": "纪律 332 那张「升版要过的门」矩阵的机器可读登记。"
                     "AUDIT-RULES.md 纪律 332② 是 Batch 297 的历史实测（8 道 / 32 条），"
                     "**不改**（证据处留痕）；当前值以本文件为准，订正见纪律 346。",
        "_为什么要指纹": "这张表登记的是**闸的行为**（某 ref 上报几条），而闸本身会被改。"
                         "**改闸不会自动作废这张表**——实测 Batch 304 改了 verify-quote-punct.py，"
                         "它那一行随即从 2 条变成 0 条，表上却一直写着 2，"
                         "过期了 7 个批次而没有任何东西会报。",
        "_重测方法": "python3 scripts/remeasure-gate-registry.py（需先逐闸落盘两个 ref 的输出）",
        "measured_at": "Batch 311",
        "baseline_ref": BASELINE,
        "upstream_ref": UPSTREAM,
        "gates": entries,
        "total": total,
    }
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(reg, ensure_ascii=False, indent=2) + "\n")

    print("已写出 %s（%d 字节）" % (OUT, os.path.getsize(OUT)))
    print("登记 %d 道闸，合计 %d 条" % (len(entries), total))
    for e in entries:
        print("  %-36s %2d 条（%s）  %s"
              % (e["gate"], e["upstream_items"], e["measured_form"],
                 e["gate_sha256"][:16]))


if __name__ == "__main__":
    main()