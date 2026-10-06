#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 811 验收器 —— 7 个派生动作的**撤销**，与 `createAudioSplit` 的**跳画布语义**

## ★ 甲：撤销

判据是**节点 id 集合** + **边数**与动作前**完全相同**。
★ 判「id 集合」而不是「节点数」：数量相同但换了内容是另一种坏。
★ 判「**一次**就回到」而不是「按到回到为止」：后者会把
  「第一次按掉的是上一次别的操作」也判成通过。

## ★ 乙：跳画布

- **对照组**（不切画布）：音视频分离必须落到**源画布**，+2 节点 / +2 边 / 历史 +1，
  选区指向**新建的无声视频节点**。
- **切画布臂**（600ms 延迟内切走）：两张画布的**节点、边、历史三项全不变**。
  ★ 而源码 `VideoNode.tsx:175-198` 的 unmount cleanup 会 `cancel()` 挂起的操作
  ⟹ 这是**已声明的行为**（batch 449，contract §5.7），不是缺陷。
  本批要钉住的是**它到底是不是真的被取消了**，而不是「我以为它会怎样」。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB811_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch811-2026-10-01"
                    / "raw" / "vb811a.json"))
OUT = pathlib.Path(os.environ.get("VB811_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch811-2026-10-01"
                    / "verify-report.json"))
VN = "src/components/nodes/VideoNode.tsx"
OP = "src/lib/libtvOperationHandoff.ts"

UNDO_KEYS = ["u_firstFrame", "u_firstLast", "u_breakdown", "u_continuation",
             "u_subtitle", "u_audio", "u_shotComplete"]


def run_checks(raw, src_vn, src_op):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": evidence})

    undos = raw["undo"]
    crosses = raw["cross"]

    def u(rd, key):
        return next((c for c in undos if c.get("round") == rd
                     and c.get("key") == key), None)

    def x(rd, key):
        return next((c for c in crosses if c.get("round") == rd
                     and c.get("key") == key), None)

    # ── S1 ★★ 阳性对照：每个动作**真的**建了东西、历史**真的**多了一条
    ev = []
    for c in undos:
        if c.get("FAILED"):
            continue
        n_new = len(set(c["after"]["nodeIds"]) - set(c["before"]["nodeIds"]))
        ev.append({"round": c["round"], "动作": c["key"],
                   "节点": [len(c["before"]["nodeIds"]), len(c["after"]["nodeIds"])],
                   "边": [c["before"]["edges"], c["after"]["edges"]],
                   "历史长度": [c["before"]["past"], c["after"]["past"]],
                   "新建了几个": n_new,
                   "★ 建了东西": c["★ 动作真的建了东西"] is True and n_new > 0,
                   "★ 历史 +1": c["★ 历史真的多了一条"] is True,
                   "★ 两件同时": c["★ 动作真的建了东西"] is True and n_new > 0
                                  and c["★ 历史真的多了一条"] is True})
    add("S1:★★ 阳性对照：7 个动作每个都**真的建了东西**、历史**真的 +1**",
        "★★ 没有这条，「一次 Cmd+Z 就还原了」可能只是「压根什么都没发生、"
        "按 Cmd+Z 也没东西可按」⟹ ★ 809 记的「防重分支」让这件事**真的可能发生**"
        "（`createSubtitleErase` 指纹去重、`completeShotBreakdown` 已有结果就 return）",
        ev and all(x["★ 两件同时"] for x in ev)
        and {x["动作"] for x in ev} == set(UNDO_KEYS), ev)

    # ── S2 ★★★ 主判据甲：一次 Cmd+Z 就**完全还原**（id 集合 + 边数逐位相同）
    ev = []
    for c in undos:
        if c.get("FAILED"):
            continue
        b, f = c["before"], c["final"]
        ev.append({"round": c["round"], "动作": c["key"],
                   "★ 动作后 id 集合": c["after"]["nodeIds"],
                   "★ 按 1 次之后 id 集合": c["final"]["nodeIds"],
                   "★ 动作前 id 集合": b["nodeIds"],
                   "边（动作前→按后）": [b["edges"], f["edges"]],
                   "历史（动作前→按后）": [b["past"], f["past"]],
                   "★ 按了几次": c["★ 按了几次才回到动作前"],
                   "★ 一次就回到": c["★ 按了几次才回到动作前"] == 1,
                   "★ id 集合逐位相同": f["nodeIds"] == b["nodeIds"],
                   "★ 边数相同": f["edges"] == b["edges"],
                   "★ 三件同时": c["★ 按了几次才回到动作前"] == 1
                                  and f["nodeIds"] == b["nodeIds"]
                                  and f["edges"] == b["edges"]})
    add("S2:★★★ 主判据甲：**一次** `Cmd+Z` 就让节点 id 集合与边数**逐位回到动作前**",
        "★★★ 809 验的是几何、没验撤销；★ 判「id 集合」而不是「节点数」——"
        "数量相同但换了内容是另一种坏；★ 判「一次」而不是「按到回到为止」——"
        "后者会把「第一次按掉的是上一次别的操作」也判成通过；"
        "★ 809 的防重分支让「压根没发生、按 Cmd+Z 也没东西可按」**真的可能**，"
        "所以 S1 的阳性对照不可省",
        ev and all(x["★ 三件同时"] for x in ev)
        and {x["动作"] for x in ev} == set(UNDO_KEYS), ev)

    # ── S3 ★★★ 对照组（不切画布）：音视频分离落到**源画布**、选区指向新节点
    ev = []
    for c in crosses:
        if c.get("FAILED") or c.get("key") != "crossStay":
            continue
        owner, after = c["源画布"], c["after"]
        b0, a0 = c["before"][owner], after[owner]
        others = [k for k in after if k != owner]
        ev.append({"round": c["round"], "源画布": owner,
                   "切过去的画布": c["切过去的画布"],
                   "★ 对照组没真的切": c["切过去的画布"] == owner,
                   "源画布 节点（之前→之后）": [b0["n"], a0["n"]],
                   "源画布 边（之前→之后）": [b0["e"], a0["e"]],
                   "源画布 历史（之前→之后）": [b0["past"], a0["past"]],
                   "★ 落在源画布": a0["n"] == b0["n"] + 2
                                   and a0["e"] == b0["e"] + 2
                                   and a0["past"] == b0["past"] + 1,
                   "★ 别的画布没被动": all(after[k] == c["before"][k] for k in others),
                   "★ 当前画布的选区指向新建的无声视频": bool(c.get("selAfter"))
                       and all(str(s).startswith("silent-video-") for s in c["selAfter"]),
                   "★ 三件同时": a0["n"] == b0["n"] + 2
                                  and a0["e"] == b0["e"] + 2
                                  and a0["past"] == b0["past"] + 1
                                  and all(after[k] == c["before"][k] for k in others)
                                  and bool(c.get("selAfter"))
                                  and all(str(s).startswith("silent-video-")
                                          for s in c["selAfter"])})
    add("S3:★★★ 对照组（不切画布）：音视频分离**落在源画布**（+2 节点 / +2 边 / 历史 +1）、"
        "别的画布没被动、选区指向**新建的无声视频节点**",
        "★★★ 这是 S4 的对照：没有它，「切画布臂什么都没发生」可能只是"
        "「音视频分离压根不工作」；★ `createAudioSplit` 的选区更新被 "
        "`canvas.id === activeCanvasId` 守着（`canvasStore.ts:2177`），"
        "对照组正是「守卫生效」的那一档",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    # ── S4 ★★★ 切画布臂：两张画布的**节点、边、历史三项全不变**
    ev = []
    for c in crosses:
        if c.get("FAILED") or c.get("key") != "crossSwitch":
            continue
        unchanged = all(c["after"][k] == c["before"][k] for k in c["before"])
        ev.append({"round": c["round"], "源画布": c["源画布"],
                   "切过去的画布": c["切过去的画布"],
                   "★ 对照组确实切了": c["切过去的画布"] != c["源画布"],
                   "active 确实是切过去那张": c["activeAfter"] == c["切过去的画布"],
                   "before": c["before"], "after": c["after"],
                   "★ 两张画布三项全不变": unchanged})
    add("S4:★★★ 切画布臂：延迟内切走画布，**两张画布的节点、边、历史三项全都不变**",
        "★★★ 源码侧对应物：`VideoNode.tsx:175-198` 的 unmount cleanup 对 "
        "`audioSplitOpRef` 调 `cancel()`，`acceptLibTVOperation` 于是 "
        "`clearTimeout` ⟹ **整个操作被取消、压根没提交**；"
        "★ 而 `VideoNode.tsx:177-179` 的注释明写这是 **batch 449 的已声明处置**"
        "（contract §5.7）⟹ **本条不是缺陷，是行为**；"
        "★ 本批要钉住的是「它到底是不是真的被取消了」，而不是「我以为它会怎样」",
        ev and all(x["★ 两张画布三项全不变"] and x["★ 对照组确实切了"]
                   and x["active 确实是切过去那张"] for x in ev), ev)

    # ── S5 ★★ 用户看得见的读数：切过去之后是**一张空画布、选区空的**
    ev = []
    for c in crosses:
        if c.get("FAILED") or c.get("key") != "crossSwitch":
            continue
        ev.append({"round": c["round"], "切过去的画布": c["切过去的画布"],
                   "当前画布选区": c.get("selAfter"),
                   "DOM 里的节点数": len((c.get("dom") or {}).get("DOM 节点") or []),
                   "DOM 画布下拉读数": (c.get("dom") or {}).get("画布下拉"),
                   "★ 选区是空的": c.get("selAfter") == [],
                   "★ DOM 里也是空的":
                       len((c.get("dom") or {}).get("DOM 节点") or []) == 0,
                   "★ 切走之后没有任何提示": len((c.get("dom") or {}).get("DOM 节点")
                                                or []) == 0
                   and c.get("selAfter") == []})
    add("S5:★★ 用户看得见的读数：切过去之后是**一张空画布、选区空的、零提示**",
        "★★ S4 说「什么都没发生」，S5 说「**用户看见的**也是什么都没发生」；"
        "★ 判据优先用 **DOM** 读数（能读 DOM 就不只读 store）；"
        "★ 「取消要不要给用户一句话」是**产品决策**、且要源站依据 ⟹ 本批只报读数、"
        "不发明提示文案",
        ev and all(x["★ 切走之后没有任何提示"] for x in ev), ev)

    # ── S6 ★★ 切过去之后按 Cmd+Z **不会误伤**（那张画布根本没有历史）
    ev = []
    for c in crosses:
        if c.get("FAILED") or c.get("key") != "crossSwitch":
            continue
        same = c["在当前画布按 Cmd+Z 之后"] == c["after"]
        ev.append({"round": c["round"], "按之前": c["after"],
                   "★ 按 Cmd+Z 之后": c["在当前画布按 Cmd+Z 之后"],
                   "★ 两张画布都没变": same})
    add("S6:★★ 切过去之后按 `Cmd+Z` **不会误伤**任何一张画布",
        "★★ `undo()` 作用在 `activeCanvasId` 的历史上（`canvasStore.ts:3923`）"
        "而那张画布**根本没有历史**（`past=0`）⟹ 按了是 no-op；"
        "★ 这条把「跨会话/跨画布撤销」（796 遗留）的一个具体子情形钉成了**读数**："
        "**空历史时按 Cmd+Z 是安全的 no-op**，不会回退到别的画布上",
        ev and all(x["★ 两张画布都没变"] for x in ev), ev)

    # ── S7 ★★ 静态锚点：取消逻辑确实在源码里
    #   ★ 第七次提醒：一律 `rfind` / 取实现（同名声明在前部）
    hits_vn = [i for i in range(len(src_vn)) if src_vn.startswith("audioSplitOpRef.current", i)]
    i_vn = hits_vn[0] if hits_vn else -1
    seg_vn = src_vn[max(0, i_vn - 900):i_vn + 300] if i_vn >= 0 else ""
    i_cancel = src_op.rfind("cancel: () => {")
    seg_op = src_op[i_cancel:i_cancel + 420] if i_cancel >= 0 else ""
    add("S7:★★ 静态锚点：「unmount 就 cancel 挂起的操作」这条链在源码里",
        "★ 静态证据**不能**替代 S4 的行为证据（794 的硬规矩），"
        "它的作用是把 S4 的结论**归因**到具体那两行而不是「反正就是没发生」；"
        "★ 一律取实现（`cancel` 的实现用 `rfind`）",
        i_vn >= 0 and "handle?.cancel();" in seg_vn
        and "audioSplitOpRef.current" in seg_vn
        and i_cancel >= 0 and "clearTimeout(timer)" in seg_op,
        {"audioSplitOpRef 出现次数": len(hits_vn),
         "★ 取的是第一次（cleanup 里的那个）": len(hits_vn) > 0,
         "cleanup 段里有 handle?.cancel()": "handle?.cancel();" in seg_vn,
         "cancel 实现里有 clearTimeout": "clearTimeout(timer)" in seg_op})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src_vn = (ROOT / VN).read_text(encoding="utf-8")
    src_op = (ROOT / OP).read_text(encoding="utf-8")
    checks = run_checks(raw, src_vn, src_op)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src_vn, src_op)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        hit_expect = any(f.startswith(expect) for f in flipped)
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped, "ok": hit_expect}

    def nothing_happened(d):
        """★ 阳性对照：伪造「动作压根没建东西」⟹ S1 必须翻红。
        （S2 在这种情况下会「假绿」——按 Cmd+Z 也没东西可按，自然回到动作前）"""
        n = 0
        for c in d["undo"]:
            if c.get("FAILED"):
                continue
            c["after"] = copy.deepcopy(c["before"])
            n += 1
        return n

    def needs_two_presses(d):
        """伪造「要按两次才回到」⟹ S2 必须翻红（795 撤销粒度那条）"""
        n = 0
        for c in d["undo"]:
            if c.get("FAILED"):
                continue
            c["undoPresses"] = [{"第几次": 1, "节点 id 集合": ["junk"],
                                "边数": 999}] + c["undoPresses"]
            c["★ 按了几次才回到动作前"] = 2
            n += 1
        return n

    def undo_leftover_node(d):
        """伪造「撤销后少不了一个节点」⟹ S2 必须翻红"""
        n = 0
        for c in d["undo"]:
            if c.get("FAILED"):
                continue
            c["final"] = copy.deepcopy(c["final"])
            c["final"]["nodeIds"] = c["final"]["nodeIds"][:-1] + ["leftover-zzz"]
            n += 1
        return n

    def cross_did_commit(d):
        """★ 伪造「切画布臂其实提交了」⟹ S4 必须翻红"""
        n = 0
        for c in d["cross"]:
            if c.get("FAILED") or c.get("key") != "crossSwitch":
                continue
            c["after"] = copy.deepcopy(c["after"])
            c["after"][c["源画布"]]["n"] += 2
            c["after"][c["源画布"]]["e"] += 2
            c["after"][c["源画布"]]["past"] += 1
            n += 1
        return n

    def cross_didnt_switch(d):
        """伪造「切画布臂其实没切」⟹ S4 必须翻红（否则「没变化」只是没切）"""
        n = 0
        for c in d["cross"]:
            if c.get("FAILED") or c.get("key") != "crossSwitch":
                continue
            c["切过去的画布"] = c["源画布"]
            c["activeAfter"] = c["源画布"]
            n += 1
        return n

    def cross_gave_feedback(d):
        """伪造「切走之后给了提示」（选区非空）⟹ S5 必须翻红"""
        n = 0
        for c in d["cross"]:
            if c.get("FAILED") or c.get("key") != "crossSwitch":
                continue
            c["selAfter"] = ["silent-video-fake"]
            n += 1
        return n

    def cross_undo_harmed(d):
        """伪造「切过去按 Cmd+Z 误伤了」⟹ S6 必须翻红"""
        n = 0
        for c in d["cross"]:
            if c.get("FAILED") or c.get("key") != "crossSwitch":
                continue
            c["在当前画布按 Cmd+Z 之后"] = copy.deepcopy(c["在当前画布按 Cmd+Z 之后"])
            c["在当前画布按 Cmd+Z 之后"][c["切过去的画布"]]["n"] = 99
            n += 1
        return n

    def unrelated(d):
        n = 0
        for c in d["undo"] + d["cross"]:
            c["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "★ 阳性对照：伪造「动作压根没建东西」⟹ S1 翻红"
                  "（S2 在这种情况下会**假绿**：没东西可按，自然回到动作前）",
            nothing_happened, "S1"),
        neg("N2", "伪造「要按两次才回到」⟹ S2 翻红（795 撤销粒度那条）",
            needs_two_presses, "S2"),
        neg("N3", "伪造「撤销后残留一个节点」⟹ S2 翻红（判 id 集合而不是只判数量）",
            undo_leftover_node, "S2"),
        neg("N4", "★ 伪造「切画布臂其实提交了」⟹ S4 翻红",
            cross_did_commit, "S4"),
        neg("N5", "★ 伪造「切画布臂其实没切」⟹ S4 翻红（否则「没变化」只是没切）",
            cross_didnt_switch, "S4"),
        neg("N6", "伪造「切走之后给了提示」（选区非空）⟹ S5 翻红",
            cross_gave_feedback, "S5"),
        neg("N7", "伪造「切过去按 Cmd+Z 误伤了」⟹ S6 翻红",
            cross_undo_harmed, "S6"),
        neg("N8", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 811, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"] + " ｜ 翻红：" +
              str([f[:10] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())
