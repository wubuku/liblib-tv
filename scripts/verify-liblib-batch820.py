#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 820 验收器 —— ★ 撤销撤不掉，那**手动删**清得掉吗？

## 起点（819 自开的最重一条）

819 的「不声称」里明写：「**没测有没有别的自救路径**（手动拖走／逐个删）……
★ **但那是从 816／817 的读数推的、不是本批量的**」。

⟹ 本批就去量那条推论 —— ★ **它有可能把 819 的结论推翻**。

## ★ 两条臂，各测各的，但**都发生在同一个 T3 状态**上

| 臂 | 测什么 | 对应的检查 |
| --- | --- | --- |
| `A_delete_loop` | Delete 循环能不能清空 | S1–S5 |
| `B_duplicate` | 「创建副本」把副本放哪 | S1、S6 |

★ 探针第一版把「创建副本」放在 Delete 循环**之后** ⟹ 循环已把 10 份**全清掉**
⟹ `有活着的份可复制: false` ⟹ **那条臂前提不满足、作废**（807 纪律）
⟹ 修法是**拆臂**，不是「就这样算作废」。

## ★ 判据一律从 raw 的**原始字段**重算

原始存活份数、原始逐次 `节点数`／`历史`、原始 DOM `z-index` 与
`getBoundingClientRect` —— **不信**探针换算过的「选中的第几份」判据。
"""
import copy
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB820_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch820-2026-10-01"
                    / "raw" / "vb820a.json"))
OUT = pathlib.Path(os.environ.get("VB820_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch820-2026-10-01"
                    / "verify-report.json"))
STORE = "src/store/canvasStore.ts"

ARM_LOOP = "A_delete_loop"
ARM_DUP = "B_duplicate"

F_LOOP = "Delete 循环"
F_BASE = "起点"
F_STUCK = "★ 撤完之后还剩几份"
F_STUCK_N = "★ 撤完之后节点数"
F_STUCK_P = "★ 撤完之后历史"
F_END_R = "★ 循环之后还剩几份"
F_END_N = "★ 循环之后节点数"
F_END_P = "★ 循环之后历史"
F_CLEAR = "★ 清空了所有产物"
F_DUP = "★ 创建副本"


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    good = [x for x in raw["cells"] if not x.get("FAILED")]

    def pick(key):
        return [x for x in good if x.get("key") == key]

    # ── S1 ★★ 前提：两条臂都走到同一个 T3 状态
    ev = []
    for x in good:
        ev.append({"臂": x.get("key"), "还剩几份": x.get(F_STUCK),
                   "节点数": x.get(F_STUCK_N), "历史": x.get(F_STUCK_P),
                   "起点": x.get(F_BASE),
                   "★ 前提成立": (x.get(F_STUCK) or 0) > 0
                   and x.get(F_STUCK_P) == 0})
    add("S1:★★ **前提**：两条臂都走到**同一个 T3 状态**"
        "（还剩着撤不掉的东西 ＋ `历史` 为空）",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。"
        "★ 本批与 819／818 必须是**同一个状态**，否则两条路径的结局"
        "就没有可比性 ⟹ ★ **「对照」的前提是「对照的是同一件事」**。"
        "★ 两条臂**各自独立**地先走到 T3（60 次点击 → 撤到底），再各做各的事",
        bool(ev) and all(x["★ 前提成立"] for x in ev)
        and {x["臂"] for x in ev} == {ARM_LOOP, ARM_DUP},
        {"逐条": ev, "★ 两条臂都在": sorted({x["臂"] for x in ev})})

    loop_arm = pick(ARM_LOOP)

    # ── S2 ★★★ Delete 循环：每轮删掉 1 份、无一轮中断、逐次递减到 0
    ev = []
    for x in loop_arm:
        loop = x.get(F_LOOP) or []
        # ★ **终止轮**（点不动 ⟹ 已经没东西可点了）与**中断轮**（点得中
        #   却没删掉）是**两件不同的事**。第一版把它们混在一起算「中断」
        #   ⟹ 基线直接判红（终止轮里 `★ 删掉的份数` 是 None）。
        #   ★ 而分开口径之后判据**更严**了：它要求循环是
        #   **因为清空了才自然终止**的，**不是**被我按够次数硬截断的。
        term = [s.get("第几次") for s in loop if s.get("★ 点不动")]
        work = [s for s in loop if not s.get("★ 点不动")]
        dels = [s.get("★ 删掉的份数") for s in work]
        brok = [s.get("第几次") for s in work if s.get("★ 中断")]
        alive = [s.get("★ 还剩几份") for s in work]
        picked = [s.get("★ 选中的第几份") for s in work]
        ev.append({"总轮数": len(loop), "★ 终止轮（第几轮点不动）": term,
                   "干活轮数": len(work),
                   "逐次删掉的份数": dels,
                   "★ 中断发生在第几轮": brok,
                   "逐次选中的第几份": picked,
                   "逐次还剩几份": alive,
                   "★ 每轮都恰好删掉 1 份": bool(dels)
                   and all(d == 1 for d in dels),
                   "★ 干活轮里一轮都没中断": brok == [],
                   "★ 有终止轮（清空后才终止）": bool(term),
                   "★ 还剩份数逐次递减到 0": bool(alive) and alive[-1] == 0
                   and all(a > b for a, b in zip(alive, alive[1:])),
                   "★ 读数成立": bool(dels) and all(d == 1 for d in dels)
                   and brok == [] and bool(term) and bool(alive)
                   and alive[-1] == 0
                   and all(a > b for a, b in zip(alive, alive[1:]))})
    add("S2:★★★ Delete 循环：**每轮恰好删掉 1 份**、**一轮都没中断**、"
        "存活份数**逐次递减到 0**",
        "★★★ 这正是 816 那条读数的**可测推论**：「点中心只选中最上面那一份」"
        "⟹ 删掉它之后**下一份自动顶上来** ⟹ 循环 N 次就能清掉 N 份。"
        "★ **终止轮**与**中断轮**要分开（第一版混为一谈 ⟹ 基线假红）："
        "终止轮 = **点不动**（已经没东西可点 ⟹ 清空完成）；"
        "中断轮 = **点得中却没删掉**（真的失败）。"
        "★ 判据因此**更严**：要求循环是**因为清空了才自然终止**的，"
        "**不是**被探针按够次数硬截断的（`max_loop` 用满也算终止 ⟹ 判红）；"
        "★ 「干活轮里一轮都没中断」不能省：某一轮 Delete 失效，"
        "循环就会停在那儿，**清空**那条读数也就不成立；"
        "★ 「每轮恰好删掉 1 份」排除「某一轮一次删掉好几份」这种"
        "**读数相同、机制不同**的情形",
        bool(ev) and all(x["★ 读数成立"] for x in ev) and bool(ev),
        {"逐条": ev, "★ 总轮数 / 终止轮": [(e["总轮数"], e["★ 终止轮（第几轮点不动）"])
                            for e in ev],
         "★ 起点还剩几份": [x.get(F_STUCK) for x in loop_arm]})

    # ── S3 ★★★ 清空了所有产物
    ev = []
    for x in loop_arm:
        ev.append({"循环之后还剩几份": x.get(F_END_R),
                   "循环之后节点数": x.get(F_END_N),
                   "★ 读数成立": x.get(F_END_R) == 0
                   and x.get(F_CLEAR) is True})
    add("S3:★★★ ★★ Delete 循环**把所有产物都清掉了**（剩 0 份）",
        "★★ 这是本批**最重的一条**：819 说「**没有别的自救路径**」，"
        "本批把其中最可能的一条**实测出来**。"
        "★ 判据直接读**原始存活份数**（`★ 循环之后还剩几份`），"
        "**不信**探针算好的「清空了」标志位。"
        "★ 只在 `A_delete_loop` 臂上判 —— `B_duplicate` 臂**根本没跑循环**，"
        "它的「还剩几份」是 T3 的原值 ⟹ 混在一起判必然假红",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 节点数回到起点值": [e["循环之后节点数"] for e in ev],
         "★ 起点节点数": [(x.get(F_BASE) or {}).get("节点数")
                       for x in loop_arm]})

    # ── S4 ★★ 节点数回到起点（历史**故意不判**）
    ev = []
    for x in loop_arm:
        base = x.get(F_BASE) or {}
        ev.append({"起点": base, "循环之后": [x.get(F_END_N), x.get(F_END_P)],
                   "★ 节点数回到起点": x.get(F_END_N) == base.get("节点数"),
                   "★ 历史回到起点": x.get(F_END_P) == base.get("历史"),
                   "★ 读数成立": x.get(F_END_N) == base.get("节点数")})
    add("S4:★★ 循环之后**节点数回到起点**",
        "★★ ★ **历史**这一项**故意不判**：删除**也是一次操作**、也会压历史栈 "
        "⟹ 循环清完之后 `past` 回到 0 **才**是意外。"
        "★ 把「历史回到起点」写进判据，等于要求「删了 10 次却没留下 10 条记录」"
        "—— 那是一条**错误的**判据，不是更严的判据。"
        "★ 历史读数**如实报告**在 evidence 里（看它到底是多少）。",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 历史读数（看它到底停在多少）": [e["循环之后"][1] for e in ev],
         "★ 起点历史": [(x.get(F_BASE) or {}).get("历史") for x in loop_arm]})

    # ── S5 ★★★ ★ 两条路径的结局**不同**
    ev = []
    for x in loop_arm:
        stuck = x.get(F_STUCK) or 0
        ev.append({"撤销撤完之后还剩几份": stuck,
                   "撤销之后历史": x.get(F_STUCK_P),
                   "Delete 清完还剩几份": x.get(F_END_R),
                   "★ 撤销撤不掉": stuck > 0 and x.get(F_STUCK_P) == 0,
                   "★ 手动删清得掉": x.get(F_END_R) == 0,
                   "★ 两条路径结局不同": stuck > 0 and x.get(F_END_R) == 0})
    add("S5:★★★ ★★ **两条路径的结局不同**：`Cmd+Z` **撤不掉**、"
        "`Delete` **清得掉**",
        "★★ 这是本批的**核心对照**，也是对 819 的**修正**。"
        "★ 819 的读数「撤不掉」**依然成立**（同一状态、同一份数据），"
        "★ 但「**没有别的自救路径**」那句话是**从 816／817 推的**、"
        "本批把它**实测推翻了**：用户有一条可行的自救路径，"
        "只是要**按 N 次**（N ＝ 撤不掉的份数）。"
        "★ 所以准确的说法是：「**撤销这条路断了，但清得掉**」——"
        "★ 不是「清不掉」。",
        bool(ev) and all(x["★ 两条路径结局不同"] for x in ev),
        {"逐条": ev})

    # ── S6 ★★ 「创建副本」把副本挪开（B_duplicate 臂）
    m = re.search(r"position:\s*\{\s*x:\s*node\.position\.x\s*\+\s*(\d+)\s*,"
                  r"\s*y:\s*node\.position\.y\s*\+\s*(\d+)\s*\}", src)
    ev = []
    for x in pick(ARM_DUP):
        d = x.get(F_DUP) or {}
        moved = d.get("★ 副本有没有挪开")
        ev.append({"有活着的份可复制": d.get("有活着的份可复制"),
                   "★ 前提不满足": d.get("★ 前提不满足"),
                   "建出了几个": d.get("建出了几个"),
                   "原节点矩形": d.get("原节点矩形"),
                   "新节点矩形": d.get("新节点矩形"),
                   "★ 副本有没有挪开": moved,
                   "★ 副本与原节点的屏幕位移":
                       d.get("★ 副本与原节点的屏幕位移"),
                   "★ 读数成立": d.get("★ 前提不满足") is False
                   and d.get("建出了几个") == 1 and bool(moved)})
    add("S6:★★ 「创建副本」会把副本**挪开**——所以「同一坐标」是 "
        "`addDerivedNode` **独有的**行为",
        "★★ `duplicateGraphSelection`（副本实现）对每个副本做 "
        "`position: {x: 原文 x + 偏移, y: 原文 y + 偏移}` ⟹ "
        "★ **副本会被挪开**，不像 `addDerivedNode` 那样**压在同一个坐标**"
        "（815／816 的读数）。"
        "★ 这条**不是**自救路径（副本只增不减），但它把 815／816 的问题"
        "**归因到具体那一个 store 动作**、而不是「这套画布都这样」。"
        "★ 判据里的偏移**从源码正则读出**、**不写死**。",
        bool(ev) and all(x["★ 读数成立"] for x in ev) and bool(m),
        {"逐条": ev,
         "★ 源码里的偏移": m.group(0) if m else None,
         "★ 偏移量": [int(g) for g in m.groups()] if m else None})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / STORE).read_text(encoding="utf-8")
    checks = run_checks(raw, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def arms(d):
        return [x for x in d["cells"] if not x.get("FAILED")]

    def loop_arms(d):
        return [x for x in arms(d) if x.get("key") == ARM_LOOP]

    def dup_arms(d):
        return [x for x in arms(d) if x.get("key") == ARM_DUP]

    def hist_not_empty(d):
        n = 0
        for x in arms(d):
            x[F_STUCK_P] = 5
            n += 1
        return n

    def nothing_stuck(d):
        n = 0
        for x in arms(d):
            x[F_STUCK] = 0
            n += 1
        return n

    def one_loop_broke(d):
        n = 0
        for x in loop_arms(d):
            loop = x.get(F_LOOP) or []
            if len(loop) < 3:
                continue
            loop[1]["★ 中断"] = True          # 点得中却没删掉
            n += 1
        return n

    def no_terminal_round(d):
        """★ 伪造「循环是按满次数被硬截断的、没有自然终止轮」⟹ S2 必须翻红
        （这条守住「更严的口径」：清空了才终止，不是按够了才停）"""
        n = 0
        for x in loop_arms(d):
            loop = x.get(F_LOOP) or []
            for s in loop:
                s["★ 点不动"] = False
            n += 1
        return n

    def loop_deletes_zero(d):
        n = 0
        for x in loop_arms(d):
            loop = x.get(F_LOOP) or []
            if not loop:
                continue
            loop[0]["★ 删掉的份数"] = 0
            n += 1
        return n

    def one_left(d):
        """★★ 伪造「循环之后还剩 1 份」（清不掉）⟹ S3 与 S5 翻红
        （本批核心阴性对照：把最关键的结论直接否掉）"""
        n = 0
        for x in loop_arms(d):
            x[F_END_R] = 1
            x[F_CLEAR] = False
            n += 1
        return n

    def node_count_off(d):
        n = 0
        for x in loop_arms(d):
            x[F_END_N] = (x.get(F_END_N) or 0) + 1
            n += 1
        return n

    def same_outcome(d):
        """★ 伪造「Delete 也撤不掉（两条路径结局相同）」⟹ S5 翻红"""
        n = 0
        for x in loop_arms(d):
            x[F_END_R] = x.get(F_STUCK)
            n += 1
        return n

    def dup_not_moved(d):
        n = 0
        for x in dup_arms(d):
            x[F_DUP]["★ 副本有没有挪开"] = []
            n += 1
        return n

    def dup_premise_gone(d):
        """★ 伪造「B 臂的前提不满足」（没有可复制的份）⟹ S6 必须翻红
        —— ★ 这就是**第一版探针真实遇到的那个问题**，
        把当时的 raw 形态做成阴性对照，保证 S6 不会悄悄退化"""
        n = 0
        for x in dup_arms(d):
            x[F_DUP]["有活着的份可复制"] = False
            x[F_DUP]["★ 前提不满足"] = True
            x[F_DUP]["建出了几个"] = 0
            x[F_DUP]["★ 副本有没有挪开"] = []
            n += 1
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「撤完之后历史不为空」⟹ S1 翻红（前提坏掉）",
            hist_not_empty, "S1"),
        neg("N2", "伪造「撤完之后一份都没剩」⟹ S1 翻红（前提坏掉）",
            nothing_stuck, "S1"),
        neg("N3", "★ 伪造「循环某一轮中断」⟹ S2 翻红", one_loop_broke, "S2"),
        neg("N4", "★ 伪造「某一轮一份都没删掉」⟹ S2 翻红",
            loop_deletes_zero, "S2"),
        neg("N5", "★★ 伪造「循环之后还剩 1 份」（清不掉）⟹ S3 与 S5 翻红"
                  "（本批核心阴性对照：把最关键的结论直接否掉）", one_left, "S3"),
        neg("N6", "伪造「节点数没回到起点」⟹ S4 翻红", node_count_off, "S4"),
        neg("N7", "★ 伪造「Delete 也撤不掉（两条路径结局相同）」⟹ S5 翻红",
            same_outcome, "S5"),
        neg("N8", "伪造「副本没挪开」⟹ S6 翻红", dup_not_moved, "S6"),
        neg("N9", "★★ 伪造「B 臂前提不满足」⟹ S6 必须翻红"
                  "（这就是第一版探针真实遇到的问题）",
            dup_premise_gone, "S6"),
        neg("N10", "★★ 伪造「没有终止轮（按满次数被硬截断）」⟹ S2 翻红"
                   "（守住「更严的口径」）", no_terminal_round, "S2"),
        neg("N11", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 820,
              "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"]
              + " ｜ 翻红：" + str([f[:4] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())