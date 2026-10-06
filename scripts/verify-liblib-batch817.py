#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 817 验收器 —— 叠到**五份**之后：还点得中底下四份吗？连续撤得干净吗？

## 起点（815／816 各自留下的洞）

- 815「不声称」：★ **只测了连点三次**。
- 816「不声称」三处：
  ① ★ **第四份、第五份叠上去之后是否仍只有最上面那份可点，未测**
     （按 `z-index` 机理应当仍是，但 ★ **没量就不说**）；
  ② ★ **连按 `Cmd+Z` 能不能把多份全撤掉，未测**（811／814 只量过**单次**）；
  ③ ★ **右键菜单路径没测**（807／808 两批留的同一条遗留）。

## ★ 为什么一定要连按、而且要**逐次**记

单次撤销成立（811／814）**不蕴含**连按成立：`undo()` 中途可能撞上
`MAX_HISTORY` 截断、或某一步 `currentCanvas` 对不上而**静默 return**。
⟹ 必须**逐次**记录**原始**节点数与历史长度，**不能**只看最后一步。

## ★ 右键是**独立于左键**的另一条入口

`page.tsx:1656` 的 `onNodeContextMenu` 会 `selectNode(node.id)` **再**打开
`CanvasContextMenu`（菜单里有 `data-canvas-context-item="删除"`）⟹ 得单独量。

## ★ 判据一律从 raw 的**原始字段**重算

原始 `selectedNodeIds`（`选区原文`）、原始存活 id、原始总节点数、原始历史长度、
原始 `z-index` 与 `getBoundingClientRect` —— **不信**探针换算过的
「选中的第几份」「还活着的份数」判据（815／816 的教训）。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB817_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch817-2026-10-01"
                    / "raw" / "vb817a.json"))
OUT = pathlib.Path(os.environ.get("VB817_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch817-2026-10-01"
                    / "verify-report.json"))
MENU_SRC = "src/components/CanvasContextMenu.tsx"

LABELS = ["旋转", "全景", "多角度", "打光", "九宫格", "高清", "宫格切分"]

#: 判据在读**哪些 raw 原始字段** —— 阴性对照必须打在这些字段上
F_IDS = "建出来的 id"
F_ZO = "Z 序"
F_BASE = "★ 起点节点数/历史"
F_END_N = "★ 撤完之后总节点数"
F_END_P = "★ 撤完之后历史"
F_UNDO = "★ 连续撤销逐次"
F_SEL = "选区原文"
F_MENU = "★ 右键菜单"
F_DEL_PRE_N = "★ 路径三·右键删除前节点数"
F_DEL_POST_N = "★ 路径三·删掉的份数"
P1 = "★ 路径一·点中心"
P2 = "★ 路径二·右键中心"


def picked(cell, key, ids):
    """★ 重算：这条路径的选区里，落进叠在一起的那几份的有哪几份（1-based）"""
    sel = set((cell.get(key) or {}).get(F_SEL) or [])
    return [i + 1 for i, v in enumerate(ids) if v in sel]


def run_checks(raw, src_menu):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    cells = raw["cells"]
    good = [x for x in cells if not x.get("FAILED")]
    howmany = raw.get("howmany")

    # ── S1 ★★ 前提
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        zo = ((x.get(F_ZO) or {})) or {}
        rects = [(v["rect"]["x"], v["rect"]["y"], v["rect"]["w"],
                  v["rect"]["h"]) for v in zo.values() if v]
        ev.append({"动作": x.get("label"), "★ 叠了几份": len(ids),
                   "★ 坐标全同": bool(rects) and len(set(rects)) == 1,
                   "★ 前提成立": len(ids) == howmany
                   and bool(rects) and len(set(rects)) == 1})
    add("S1:★★ **前提**：真的叠到了 **%s 份**、且 %s 份**坐标全同**"
        % (howmany, howmany),
        "★★ 807 起立的规矩：**前提不满足的臂显式作废、不得据此下结论**。"
        "★ 815 只量到**三份**、816 沿用三份 ⟹ 本批把份数抬到 "
        "**%s**（探针参数 `HOWMANY`，从 raw 的 `howmany` 读出来，"
        "**不写死**）" % howmany,
        bool(ev) and all(x["★ 前提成立"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"howmany": howmany, "逐条": ev,
         "★ 七个动作一个不落": {x["动作"] for x in ev} == set(LABELS)})

    # ── S2 ★★★ 叠到五份之后，底下四份仍然一次都选不中
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        a, b = picked(x, P1, ids), picked(x, P2, ids)
        bottom = [i for i in set(a) | set(b) if i <= len(ids) - 1]
        ev.append({"动作": x.get("label"),
                   "★ 路径一·点中心选中的第几份": a,
                   "★ 路径二·右键中心选中的第几份": b,
                   "★ 两路都只选中最后一份": a == [len(ids)] and b == [len(ids)],
                   "★ 底下那几份被选中过": bottom,
                   "★ 底下那些从未被选中": bottom == []})
    add("S2:★★★ ★ 叠到 %s 份之后，**底下那 %s 份仍然一次都选不中**"
        % (howmany, int(howmany) - 1),
        "★★★ 816「不声称」① 的原话：「第四份、第五份叠上去之后是否仍只有"
        "最上面那份可点，**没量就不说**」。本批把它量掉。"
        "★ **左键与右键各算一条路径**（807 的纪律）：`onNodeContextMenu` "
        "在 `page.tsx:1656` 也会 `selectNode(node.id)`，它**不是**左键那条；"
        "★ 判据从**原始 `selectedNodeIds`** 重算「选中了第几份」",
        bool(ev) and all(x["★ 两路都只选中最后一份"]
                         and x["★ 底下那些从未被选中"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 七条动作读数完全一致": len({json.dumps(
             [e["★ 路径一·点中心选中的第几份"],
              e["★ 路径二·右键中心选中的第几份"]],
             ensure_ascii=True) for e in ev}) == 1,
         "★ 七个动作一个不落": {x["动作"] for x in ev} == set(LABELS)})

    # ── S3 ★★★ Z 序：只有最后一份在最上面
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        zo = (x.get(F_ZO) or {})
        top = [i + 1 for i, v in enumerate(ids)
               if (zo.get(v) or {}).get("zIndex") not in (None, "0")]
        last_dom = max((zo.get(v) or {}).get("dom序号", -1) for v in ids)
        ev.append({"动作": x.get("label"),
                   "★ zIndex 大于 0 的份号": top,
                   "★ zIndex 大于 0 的有几份": len(top),
                   "★ DOM 最靠后的是第几份":
                       [i + 1 for i, v in enumerate(ids)
                        if (zo.get(v) or {}).get("dom序号") == last_dom],
                   "★ 读数成立": top == [len(ids)]})
    add("S3:★★★ Z 序：`z-index` 大于 0 的**恰好一份**，且就是**最后建的那份**",
        "★★ 这解释了 816 的「为什么第 3 份永远在最上面」，并且**在 %s 份上依然成立**："
        "叠加顺序**不是**「后建的在上」，而是「**选中的那份**在最上」——"
        "`addDerivedNode` 末尾有 `selectedNodeIds: [nodeId]`，"
        "React Flow 给选中节点 `z-index: 1000`；"
        "★ 于是用户在 %s 份上**永远只看见最后点的那份**" % (howmany, howmany),
        bool(ev) and all(x["★ 读数成立"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         # ★ 样本 zIndex 取自**第一条 good 臂的 raw**，不是从 `ev` 里翻
         #   （`ev` 的每条只有「★ zIndex 大于 0 的份号」，没有整张表——
         #    第一版写成从 ev 里取，直接抛异常）
         "样本 zIndex": {k: v["zIndex"] for k, v in
                        ((good[0].get(F_ZO) or {})).items()},
         "★ 七条动作读数完全一致": len({json.dumps(
             e["★ zIndex 大于 0 的份号"], ensure_ascii=True)
             for e in ev}) == 1})

    # ── S4 ★★★ 连续撤销逐次递减，最后精确回到起点
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        steps = x.get(F_UNDO) or []
        base = x.get(F_BASE) or [None, None]
        ns = [s.get("总节点数") for s in steps]
        ps = [s.get("历史") for s in steps]
        desc = all(a > b for a, b in zip(ns, ns[1:]))
        ev.append({"动作": x.get("label"),
                   "★ 起点（节点数/历史）": base,
                   "逐次总节点数": ns, "逐次历史": ps,
                   "逐次还活着的份数": [s.get("还活着的份数") for s in steps],
                   "★ 步数": len(steps),
                   "★ 逐次严格递减": desc,
                   "★ 最后节点数回到起点": x.get(F_END_N) == base[0],
                   "★ 最后历史回到起点": x.get(F_END_P) == base[1],
                   "★ 三件同时": desc and x.get(F_END_N) == base[0]
                   and x.get(F_END_P) == base[1]})
    add("S4:★★★ ★ **连续撤销逐次递减**，最后**精确回到起点**"
        "（节点数 + 历史长度两件同时）",
        "★★★ 816「不声称」② 的原话：811／814 只量过**单次**撤销，"
        "**连按能不能把多份全撤掉未测**。"
        "★ **单次成立不蕴含连按成立** —— 中途可能撞上 `MAX_HISTORY` 截断、"
        "或某一步 `currentCanvas` 对不上而**静默 return** ⟹ "
        "必须**逐次**记**原始**节点数与历史长度，**不能**只看最后一步；"
        "★ 这是 815／816 那一串坏读数（叠在一起、底下选不中）之后的**好消息**："
        "**撤得干净** ⟹ 用户至少有一条能真正清干净的路径",
        bool(ev) and all(x["★ 三件同时"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 七条动作读数完全一致": len({json.dumps(
             [e["逐次总节点数"], e["逐次历史"], e["逐次还活着的份数"]],
             ensure_ascii=True) for e in ev}) == 1,
         "★ 起始历史长度": sorted({e["★ 起点（节点数/历史）"][1] for e in ev})})

    # ── S5 ★★★ 右键菜单渲染出来了，「删除」删掉的是最后一份
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        menu = x.get(F_MENU)
        items = (menu or {}).get("菜单项") or []
        ev.append({"动作": x.get("label"),
                   "★ 菜单渲染出来了": isinstance(menu, dict) and bool(items),
                   "★ 菜单项": items,
                   "★ 菜单项个数": len(items),
                   "★ 有「删除」项": "删除" in items,
                   "★ 菜单可见文本": (menu or {}).get("可见文本"),
                   "★ 右键删除前节点数": x.get(F_DEL_PRE_N),
                   "★ 右键删掉的份数": x.get(F_DEL_POST_N),
                   # ★ 「删除前节点数 == 起点 + 叠出来的份数」——
                   #   这一条是**前提的交叉验证**：不成立就说明中途有别的
                   #   操作动过画布，右键那条臂的读数就不作数。
                   #   ★ 第一版写成 `len((F_BASE)[:1])` —— 那是**列表长度 1**，
                   #   不是起点节点数 10 ⟹ 15 ≠ 6 ⟹ **基线直接判红**；
                   #   又一次「基线红 ⟹ 先怀疑判据」（808 起连续第十次）。
                   "★ 删除前 == 起点 + 叠出来的份数":
                       x.get(F_DEL_PRE_N) == len(ids)
                       + (x.get(F_BASE) or [0, 0])[0],
                   "★ 读数成立": isinstance(menu, dict) and "删除" in items
                   and x.get(F_DEL_POST_N) == 1
                   and x.get(F_DEL_PRE_N) == len(ids)
                   + (x.get(F_BASE) or [0, 0])[0]})
    add("S5:★★★ **右键菜单渲染出来了**，而菜单里的「删除」也只删掉**最后一份**",
        "★★★ 807／808 两批留的同一条遗留：「节点右键菜单是另一条入口，未测」。"
        "★ 菜单项是**DOM 可见读数**（808 的纪律：能读 DOM 就不只读 store）；"
        "★ 所以右键**既不是**「另一条能选中底下那几份的路」（S2 的读数），"
        "**也不是**「另一条能一次清干净的路」——它和左键一样只碰得到最上面那份",
        bool(ev) and all(x["★ 读数成立"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 七条动作的菜单项完全一致": len({json.dumps(
             e["★ 菜单项"], ensure_ascii=True) for e in ev}) == 1,
         "★ 菜单项": next((e["★ 菜单项"] for e in ev), None),
         "★ 菜单可见文本": next((e["★ 菜单可见文本"] for e in ev), None),
         "源码里有删除项": 'data-canvas-context-item="删除"' in src_menu})

    # ── S6 ★★ 每一次撤销之后选区都是空的
    ev = []
    for x in good:
        ids = set(x.get(F_IDS) or [])
        steps = x.get(F_UNDO) or []
        leftovers = [i + 1 for i, s in enumerate(steps)
                     for v in (s.get("选区") or []) if v in ids]
        nonempty = [i + 1 for i, s in enumerate(steps) if s.get("选区")]
        ev.append({"动作": x.get("label"),
                   "逐次选区": [s.get("选区") for s in steps],
                   "★ 第几步之后选区还留着这几份中的某份": leftovers,
                   "★ 第几步之后选区非空": nonempty,
                   "★ 读数成立": leftovers == []})
    add("S6:★★ 每一次撤销之后，**选区里都不再留着那 %s 份中的任何一份**" % howmany,
        "★★ `canvasStore.ts:3922` 的 `undo()` 在 `:3941` **清空选区**；"
        "811 记过「单次撤销之后选区被清空」，本批把它延伸到**连撤**。"
        "★ 判据只问「叠在一起的那几份还在不在选区里」——"
        "**不预设**选区必须完全为空（811 的读数只是「清空」，"
        "若将来改成保留某个选择，这条判据不该误报）",
        bool(ev) and all(x["★ 读数成立"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 七条动作读数完全一致": len({json.dumps(
             e["逐次选区"], ensure_ascii=True) for e in ev}) == 1})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src_menu = (ROOT / MENU_SRC).read_text(encoding="utf-8")
    checks = run_checks(raw, src_menu)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src_menu)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def every(d):
        return [x for x in d["cells"] if not x.get("FAILED")]

    def click_bottom(d):
        """伪造「点中心选中了第 1 份」⟹ S2 必须翻红"""
        n = 0
        for x in every(d):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x[P1] = dict(x[P1], **{F_SEL: [ids[0]]})
            n += 1
        return n

    def ctx_bottom(d):
        """伪造「右键中心选中了第 1 份」⟹ S2 必须翻红"""
        n = 0
        for x in every(d):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x[P2] = dict(x[P2], **{F_SEL: [ids[0]]})
            n += 1
        return n

    def two_on_top(d):
        """伪造「有两份在顶层」⟹ S3 必须翻红"""
        n = 0
        for x in every(d):
            ids = x.get(F_IDS) or []
            if len(ids) < 2:
                continue
            zo = x.get(F_ZO) or {}
            zo[ids[-2]] = dict(zo.get(ids[-2]) or {}, zIndex="1000")
            n += 1
        return n

    def undo_stuck(d):
        """★ 伪造「撤销到一半卡住」（某一步节点数不变）⟹ S4 必须翻红"""
        n = 0
        for x in every(d):
            steps = x.get(F_UNDO) or []
            if len(steps) < 3:
                continue
            steps[2]["总节点数"] = steps[1]["总节点数"]
            n += 1
        return n

    def undo_not_back(d):
        """伪造「撤完没回到起点」⟹ S4 必须翻红"""
        n = 0
        for x in every(d):
            base = x.get(F_BASE) or [None, None]
            x[F_END_N] = (base[0] or 0) + 1
            n += 1
        return n

    def history_not_back(d):
        """★ 伪造「节点数回到起点但历史没回去」⟹ S4 必须翻红
        （两件必须**同时**，否则「回到起点」就是一句空话）"""
        n = 0
        for x in every(d):
            steps = x.get(F_UNDO) or []
            if not steps:
                continue
            steps[-1]["历史"] = 999
            x[F_END_P] = 999
            n += 1
        return n

    def menu_gone(d):
        """伪造「右键菜单没渲染出来」⟹ S5 必须翻红"""
        n = 0
        for x in every(d):
            x[F_MENU] = None
            n += 1
        return n

    def menu_delete_all(d):
        """伪造「右键一次删掉全部 %s 份」⟹ S5 必须翻红""" % raw.get("howmany")
        n = 0
        for x in every(d):
            base = (x.get(F_BASE) or [0])[0]
            x[F_DEL_POST_N] = raw.get("howmany")
            x[F_DEL_PRE_N] = base + raw.get("howmany")
            n += 1
        return n

    def undo_keeps_selection(d):
        """伪造「撤销之后选区还留着叠在一起的那些份」⟹ S6 必须翻红"""
        n = 0
        for x in every(d):
            ids = x.get(F_IDS) or []
            steps = x.get(F_UNDO) or []
            if not ids or not steps:
                continue
            steps[-1]["选区"] = list(ids)
            n += 1
        return n

    def not_stacked(d):
        """伪造「坐标不全同」（前提坏掉）⟹ S1 必须翻红"""
        n = 0
        for x in every(d):
            zo = x.get(F_ZO) or {}
            for v in zo.values():
                if v:
                    v["rect"]["x"] += 41
                    n += 1
                    break
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「点中心选中了第 1 份」⟹ S2 翻红", click_bottom, "S2"),
        neg("N2", "伪造「右键中心选中了第 1 份」⟹ S2 翻红", ctx_bottom, "S2"),
        neg("N3", "伪造「有两份同时在顶层」⟹ S3 翻红", two_on_top, "S3"),
        neg("N4", "★ 伪造「撤销到一半卡住」⟹ S4 翻红", undo_stuck, "S4"),
        neg("N5", "伪造「撤完没回到起点」⟹ S4 翻红", undo_not_back, "S4"),
        neg("N6", "★ 伪造「节点数回到起点但历史没回去」⟹ S4 翻红"
                  "（两件必须**同时**）", history_not_back, "S4"),
        neg("N7", "伪造「右键菜单没渲染」⟹ S5 翻红", menu_gone, "S5"),
        neg("N8", "★ 伪造「右键一次删掉全部 %s 份」⟹ S5 翻红"
             % raw.get("howmany"), menu_delete_all, "S5"),
        neg("N9", "伪造「撤销之后选区还留着叠在一起的那些份」⟹ S6 翻红",
            undo_keeps_selection, "S6"),
        neg("N10", "★ 伪造「坐标不全同」（前提坏掉）⟹ S1 翻红",
            not_stacked, "S1"),
        neg("N11", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 817,
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