#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ batch 867 探针：★ 核对「回归日志」与「落盘 JSON」**逐条一致**。

## ★ 为什么要有这一步

★ 回归那一跑同时留下两份东西：
  ⟹ ⟹ ① `raw/regression-189.log`（**逐条日志**）
  ⟹ ⟹ ② `raw/regression.json`（**落盘读数** ＋ 判定）

★ ★★ 这两份**必须**同口径 ⟹ ⟹ 否则「落盘 189 条」这句话**没有意义**
⟹ ⟹ （★ 落盘 189 条而日志只有 180 条 ⟹ ⟹ 说明**日志漏了 9 条**）
⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以要**逐条比对** ⟹ ⟹ 而不是只比数量。

## ★ ★★ 一个容易踩的坑：★ 日志行数 ≠ 条数

★ 某些门禁的 verdict 里**含换行** ⟹ ⟹ 日志里那一条会**占多行**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 日志**行数**比条数**多** ⟹ ⟹ ⟹ ⟹
⟹ ⟹ ⟹ ⟹ ⇒ ★ 因此「行数 == 条数」**不是**判据 ⟹ ⟹ 判据是
⟹ ⟹ ⟹ ⟹ ⇒ **能定位到条目的那些行**的条数 == 条数 ⟹ ⟹ 且**顺序**与 rc **逐条相同**。
⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 且**每一行**要么是条目行 ⟹ ⟹ 要么是上一条的**续行**
⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 不能有「孤儿续行」（★ 那样说明有条目**整个丢了**）。

## ★ 判据

1. 落盘条数 == 清单条数（**189**）⟹ ⟹ 且**清单**本身去重后条数相同
2. 日志里**能定位到条目**的行数 == 落盘条数
3. 日志里**每一条**的 (批次, 扩展名, rc) 与落盘**逐条**相同（★ 顺序也要相同）
4. 日志里**没有孤儿续行**（★ 每一行非条目行都必须紧跟在一个条目行之后）
5. 落盘的判定**自洽**：★ 红 ⟹ 全在 `KNOWN_RED` 里（★ 即「红全旧账、新红 0」）
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch867-2026-10-01"
LOG = BATCH / "raw/regression-189.log"
JSON_PATH = BATCH / "raw/regression.json"
REGRESS = BATCH / "probes/regress867.py"
OUT = BATCH / "raw/regression-consistency.json"

# ★ 条目行：★ 「批次  扩展名  rc=...」开头
ENTRY = re.compile(r"^\s*(?P<batch>\S+)\s+(?P<ext>py|mjs)\s+rc=(?P<rc>\S+)")


def strip_comments(text: str) -> str:
    """★ 与 `verify-liblib-batch867.py` 的 `parse_gates()` **同口径**：★ 先剥注释。"""
    text = re.sub(r'"""[\s\S]*?"""', " ", text)
    text = re.sub(r"#[^\n]*", " ", text)
    return text


def main() -> int:
    checks: list[tuple[str, bool, object]] = []

    log_lines = LOG.read_text(encoding="utf-8").splitlines()
    json_doc = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    rows = json_doc["逐条读数"]
    verdict = json_doc["判定"]

    reg_text = strip_comments(REGRESS.read_text(encoding="utf-8"))
    m = re.search(r"^GATES\s*=\s*\[(.*?)^\]", reg_text, re.S | re.M)
    gates = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1)) if m else []

    # ── 1 落盘条数 == 清单条数 ⟹ ⟹ 且清单无重复 ──────────────────
    checks.append(("落盘条数 == 清单条数", len(rows) == len(gates),
                   {"落盘": len(rows), "清单": len(gates)}))
    checks.append(("清单无重复（按 批次+扩展名）",
                   len(gates) == len(set(gates)),
                   {"条目数": len(gates), "去重后": len(set(gates))}))

    # ── 2／3 日志条目行 == 落盘条数 ⟹ ⟹ 逐条 (批次, 扩展名, rc) 相同 ──
    entry_set: set[int] = set()
    entries: list[tuple[str, str, str]] = []
    entry_line_idx: list[int] = []
    for i, line in enumerate(log_lines):
        mm = ENTRY.match(line)
        if mm:
            entries.append((mm.group("batch"), mm.group("ext"), mm.group("rc")))
            entry_line_idx.append(i)
            entry_set.add(i)
    checks.append(("日志里能定位到条目的行数 == 落盘条数",
                   len(entries) == len(rows),
                   {"日志条目行": len(entries), "落盘": len(rows),
                    "日志总行数": len(log_lines),
                    "说明": "★ 日志行数 > 条数 是正常的（★ verdict 含换行）"}))
    mismatch = []
    for i, (row, ent) in enumerate(zip(rows, entries)):
        want = (str(row["batch"]), str(row["ext"]), str(row["rc"]))
        if want != ent:
            mismatch.append({"序号": i, "落盘": want, "日志": ent})
    checks.append(("日志与落盘逐条（批次, 扩展名, rc）相同",
                   not mismatch and len(entries) == len(rows),
                   {"不一致条数": len(mismatch), "样例": mismatch[:5]}))

    # ── 4a 条目**之间**没有孤儿续行（★ 末尾摘要块另算）──────────
    last_entry = max(entry_line_idx) if entry_line_idx else -1
    orphans = [i for i, line in enumerate(log_lines)
               if i not in entry_set and line.strip()
               and i < last_entry
               and (i == 0 or (i - 1) not in entry_set)]
    checks.append(("日志里条目之间没有孤儿续行（★ 否则有条目整个丢了）",
                   not orphans, {"孤儿行号": orphans[:10]}))

    # ── 4b ★★ 末尾摘要块必须与落盘 JSON **逐项一致** ──────────────
    #   ⟹ ⟹ ★ 第一版把末尾的摘要块**也算成孤儿** ⟹ ⟹ 判据**自己写错了**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ 修法：**不是**放宽判据 ⟹ ⟹ 而是把它改成**更强**的一条
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 摘要块里的数字必须与 JSON **一致** ⟹ ⟹ ⟹ ⟹
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 否则「日志说的」与「落盘的」会**各说各话**
    tail = "\n".join(log_lines[last_entry + 1:])
    m_total = re.search(r"^== 回归：(\d+) 条，红 (\d+) 条", tail, re.M)
    m_known = re.search(r"^== 其中旧账 (\d+) 条", tail, re.M)
    m_new = re.search(r"新红（相对基线）(\d+) 条", tail)
    m_attr = re.search(r"本批引入的红 (\d+) 条", tail)
    # ★ ★★ 「盯的 66 条里红的：[]」⟹ ⟹ 66 是 **WATCH 的总数**
    #   ⟹ ⟹ ★ **不是**「红的条数」⟹ ⟹ 「红的」是**后面那个名单的长度**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 第一版取了 66 当「红的条数」⟹ ⟹ 判据**自己写错了**
    m_watch = re.search(r"盯的 (\d+) 条里红的：\[(.*?)\]", tail, re.S)
    m_redlist = re.search(r"^== 回归：\d+ 条，红 \d+ 条 \[(.*?)\] ==", tail, re.M)
    log_redlist = ([x.strip().strip("'") for x in m_redlist.group(1).split(",")]
                   if m_redlist and m_redlist.group(1).strip() else [])
    summary = {
        "总条数": int(m_total.group(1)) if m_total else None,
        "红": int(m_total.group(2)) if m_total else None,
        "旧账": int(m_known.group(1)) if m_known else None,
        "新红": int(m_new.group(1)) if m_new else None,
        "本批引入": int(m_attr.group(1)) if m_attr else None,
        "WATCH总数": int(m_watch.group(1)) if m_watch else None,
        "WATCH里红的": (len([x for x in m_watch.group(2).split(",") if x.strip()])
                        if m_watch else None),
    }
    want_summary = {
        "总条数": len(rows),
        "红": len(verdict["红"]),
        "旧账": len(verdict["旧账"]),
        "新红": len(verdict["新红"]),
        "本批引入": len(verdict["本批引入"]),
        "WATCH里红的": len(verdict["WATCH里红的"]),
    }
    # ★ WATCH 的**总数**从回归脚本里读（★ 不手打）⟹ ⟹ 再与日志摘要块比对
    # ★ WATCH 是**列表**（★ 不是集合）⟹ ⟹ ★ 第一版按 `{...}` 找 ⟹ ⟹ 找不到 ⟹ ⟹ None
    m_watch_n = re.search(r"^WATCH\s*=\s*\[(.*?)^\]", reg_text, re.S | re.M)
    watch_n = (len(re.findall(r'"([^"]+)"', m_watch_n.group(1)))
               if m_watch_n else None)
    want_summary["WATCH总数"] = watch_n
    checks.append(("日志末尾摘要块的数字 == 落盘 JSON 的判定",
                   summary == want_summary,
                   {"日志摘要": summary, "落盘应有": want_summary}))
    checks.append(("日志末尾摘要块里的红名单 == 落盘 JSON 的红名单",
                   log_redlist == list(verdict["红"]),
                   {"日志": log_redlist[:5], "落盘": list(verdict["红"])[:5],
                    "条数": [len(log_redlist), len(verdict["红"])]}))

    # ── 5 判定自洽：★ 红全在 KNOWN_RED 里 ─────────────────────────
    red = set(verdict["红"])
    known_red = set(verdict["旧账"])
    checks.append(("红 ⟹ 全是旧账（新红 0）",
                   red == known_red and not verdict["新红"],
                   {"红": len(red), "旧账": len(known_red),
                    "新红": verdict["新红"], "本批引入": verdict["本批引入"],
                    "WATCH里红的": verdict["WATCH里红的"]}))
    checks.append(("本批引入 0 且 WATCH 里红的 0",
                   not verdict["本批引入"] and not verdict["WATCH里红的"],
                   {"本批引入": verdict["本批引入"],
                    "WATCH里红的": verdict["WATCH里红的"]}))

    failures = [c for c in checks if not c[1]]
    out = {
        "落盘条数": len(rows),
        "清单条数": len(gates),
        "日志总行数": len(log_lines),
        "日志条目行数": len(entries),
        "判定": verdict,
        "核对": [{"判据": c[0], "通过": c[1], "详情": c[2]} for c in checks],
        "失败": [c[0] for c in failures],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, ok, detail in checks:
        print("%s %s  %s" % ("✔" if ok else "★ FAILED", name, detail))
    print("\n%d 条核对，%d 失败" % (len(checks), len(failures)))
    print("读数已落盘：%s" % OUT)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
