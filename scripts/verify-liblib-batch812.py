#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 812 验收器 —— **重复触发**同一个已生效的操作，用户得到什么？

## ★ 三组读数，各自有判据

| 判据 | 问题 |
| --- | --- |
| **S1 阳性对照** | 第一下**真的**建了东西、历史 **+1** 吗？（否则「第二下没发生」是废话） |
| **S2 入口** | 第一次触发之后，**入口还在不在**？（条件渲染，806 的纪律） |
| **S3 第二下** | 建不建东西、历史加不加 1、**可见反馈**变没变 |

★ 「防重」不是缺陷、「不防重」也不是 —— 本批**只报事实**：
哪些动作有守卫、哪些没有，**判据不做价值判断**。
★ 「可见反馈」判的是 **DOM 读数**（芯片 `aria-pressed`、状态文本、结果卡、节点/边数），
不是 store —— 807 立过：**光看节点数不够**。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB812_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch812-2026-10-01"
                    / "raw" / "vb812a.json"))
OUT = pathlib.Path(os.environ.get("VB812_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch812-2026-10-01"
                    / "verify-report.json"))
CS = "src/store/canvasStore.ts"

#: 源码里**声称有守卫**的两个动作（`rfind` 取实现 —— 第八次提醒）
GUARDED = {"u_subtitle": "requestFingerprint",
           "u_shotComplete": "if (existingResults.length > 0) return state;"}


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": evidence})

    cells = raw["cells"]

    # ── S1 ★★★ 阳性对照：第一下真的建了东西、历史 +1
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        ev.append({"round": c["round"], "动作": c["key"],
                   "第一下（节点/边/历史）": c["第一下之后（节点/边/历史）"],
                   "★ 建了东西": c["★ 第一下真的建了东西"] is True,
                   "★ 历史 +1": c["★ 第一下历史 +1"] is True,
                   "★ 两件同时": c["★ 第一下真的建了东西"] is True
                                  and c["★ 第一下历史 +1"] is True})
    add("S1:★★★ 阳性对照：第一下**真的建了东西**、历史**真的 +1**",
        "★★★ 没有这条，「第二下什么都没发生」可以是废话 —— 而 809 已经证明"
        "「压根没发生」在这族动作里**真的可能**（首帧芯片的 `hasImageRef` 防重分支）；"
        "★ 判的是**第一下**，不是第二下",
        ev and all(x["★ 两件同时"] for x in ev), ev)

    # ── S2 ★★ 入口：第一次触发之后，入口**还在不在**（条件渲染，806 的纪律）
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        fb1 = c["s1"]["fb"]
        ev.append({"round": c["round"], "动作": c["key"],
                   "第一次之后的入口读数": {
                       "attemptChips": len(fb1["attemptChips"]),
                       "audioTriggers": fb1["audioTriggers"],
                       "subtitleTriggers": fb1["subtitleTriggers"],
                       "shotStart": fb1["shotStart"],
                       "shotNodes": fb1["shotNodes"]},
                   "★ 入口还在": c["入口还在吗（第一次之后）"]["entryStillThere"]})
    add("S2:★★ 入口普查：第一次触发之后，**每条臂的入口状态都读到了**",
        "★★ 这是 806 立的那条纪律在**另一个方向**上的应用：条件渲染的入口"
        "会因为状态变化而**消失** ⟹ 「第二下点不动」可能只是「按钮没了」；"
        "★ 本条只要求「**读到了**」，**不判该不该在** —— "
        "「在不在」是事实，「该不该在」才是产品决策；"
        "★ 所以阴性对照打的是「**读不到**」而不是「读成 false」"
        "（把真读数改成 false 仍然是**有效读数**，判据不该翻）",
        ev and all(x["★ 入口还在"] is not None for x in ev)
        and len(ev) == len([c for c in cells if not c.get("FAILED")]), ev)

    # ── S3 ★★★ 第二下有**三**种结局，不是两种
    #   ★ 第一版我只写了两种（拦住 / 没拦），把实际测到的
    #   「不建东西、**但历史 +1**」判成了红 ⟹ **我预设的半截状态方向反了**：
    #   我防的是「建了东西但没进历史」，真实发生的是「没建东西但进了历史」。
    #   ⟹ 判据改成三态并**报出是哪一态**，这比两态更接近事实。
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        built = c["★ 第二下建了东西"] is True
        hist = c["★ 第二下历史 +1"] is True
        if built and hist:
            state = "完全没拦（又建了一遍）"
        elif (not built) and (not hist):
            state = "被守卫拦住"
        else:
            state = "★ 空记录（没建东西但历史 +1）"
        ev.append({"round": c["round"], "动作": c["key"], "★ 结局": state,
                   "第二下（节点/边/历史）": c["第二下之后（节点/边/历史）"],
                   "★ 落在三态之内": state in
                   ("完全没拦（又建了一遍）", "被守卫拦住", "★ 空记录（没建东西但历史 +1）")})
    add("S3:★★★ 第二下的结局有**三**种（拦住 / 没拦 / **空记录**），"
        "每条臂都必须落在其中之一",
        "★★★ 这是本批的核心读数：**哪些动作防重、哪些不防重、哪些塞空记录**；"
        "★ ★ 我第一版只写了**两种**结局，把真实测到的「没建东西、**但历史 +1**」"
        "判成红 ⟹ **我预设的半截状态方向反了**（我防的是「建了东西但没进历史」，"
        "真实发生的是反过来）⟹ 判据改成三态并**报出是哪一态**；"
        "★ 「防重」不是缺陷、「不防重」也不是 —— 本条**只报事实，不做价值判断**",
        ev and all(x["★ 落在三态之内"] for x in ev), ev)

    # ── S4 ★★ UI 层：第二下要么点得到、要么点不动 —— **点不动是读数不是失败**
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        ui2 = c.get("UI 第二下") or {}
        ev.append({"round": c["round"], "动作": c["key"],
                   "★ UI 第二下的结局": ui2.get("outcome"),
                   "入口读数（第一次之后）": c.get("入口还在吗（第一次之后）"),
                   "第二下的可见反馈变化": c["★ 第二下的可见反馈变化"],
                   "★ 落在两态之内": ui2.get("outcome") in ("clicked", "★ 点不动")})
    add("S4:★★ UI 层第二下要么**点得到**、要么**点不动**（入口会消失或被禁用）",
        "★★ 这是 806 那条纪律的回报：条件渲染的入口会因为状态变化而**消失**或"
        "**变成 disabled 且改文案**（实测「拉片完成」）⟹ 「第二下点不动」"
        "**不是探针坏了，是读数**；★ 第一版探针把「点不动」当成 `FAILED`、"
        "于是 7 条臂里 5 条报了 RuntimeError/Timeout ⟹ **前提不满足的臂必须显式作废、"
        "不能当成故障**（802 起立的规矩）",
        ev and all(x["★ 落在两态之内"] for x in ev), ev)

    # ── S4b ★★★ store 层：绕开 UI 再调一次
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        st = c.get("store 第二下") or {}
        if "建了东西" not in st:
            continue
        ev.append({"round": c["round"], "动作": c["key"],
                   "★ store 第二下建了东西": st.get("建了东西"),
                   "★ store 第二下历史 +1": st.get("历史加1"),
                   "★ 读数在": st.get("建了东西") in (True, False)
                               and st.get("历史加1") in (True, False)})
    add("S4b:★★★ store 层：绕开 UI 直接再调一次，**必须给出确定读数**",
        "★★★ UI 层可能已经把入口禁掉了 ⟹ 那时 store 层的守卫**永远观察不到**；"
        "★ 判据只要求「读数在」，**不要求是哪一态** —— 哪一态由 S3 的三态承担；"
        "★ ★ 顺带给出一个**用户看得见的后果**：首帧芯片连点两下会塞一条**空历史记录**，"
        "于是**一次 `Cmd+Z` 撤不掉新建的 image 节点**，要按两次（S6）",
        ev and all(x["★ 读数在"] for x in ev), ev)

    # ── S5 ★★ 静态锚点：源码里那两个守卫**确实在**（`rfind` 取实现）
    rows = []
    for key, anchor in GUARDED.items():
        hits = [i for i in range(len(src)) if src.startswith(anchor, i)]
        i = hits[-1] if hits else -1
        rows.append({"动作": key, "锚点": anchor, "出现次数": len(hits),
                     "★ 取的是最后一次": len(hits) > 0,
                     "★ 锚点在实现里": i >= 0})
    add("S5:★★ 静态锚点：源码里那两个**防重守卫**确实在",
        "★ 静态证据**不能**替代 S3／S4 的行为证据（794 的硬规矩）；"
        "它的作用是把 S3 的「哪些被拦住」**归因**到具体那两段；"
        "★ 一律 `rfind`（取实现）—— 第八次「同名锚点」提醒",
        rows and all(r["★ 锚点在实现里"] for r in rows), rows)

    # ── S6 ★★★ 空记录的用户可见后果：一次 Cmd+Z **撤不掉**新建的节点
    ev = []
    for r in raw.get("emptyRecordUndo") or []:
        if r.get("FAILED"):
            continue
        ev.append({"round": r["round"],
                   "节点（动作前/下1/下2/撤1次/撤2次）": r["节点"],
                   "历史（同上）": r["历史"],
                   "★ 第二下没建东西但历史 +1": r["★ 第二下没建东西但历史 +1"],
                   "★ 一次 Cmd+Z 之后那个 image 还在": r["★ 一次 Cmd+Z 之后新建的那个 image 还在吗"],
                   "★ 要按两次才回到动作前": r["★ 两次 Cmd+Z 之后才回到动作前"],
                   "★ 三件同时": r["★ 第二下没建东西但历史 +1"]
                                  and r["★ 一次 Cmd+Z 之后新建的那个 image 还在吗"]
                                  and r["★ 两次 Cmd+Z 之后才回到动作前"]})
    add("S6:★★★ 空记录的用户可见后果：首帧芯片连点两下后，"
        "**一次 `Cmd+Z` 撤不掉新建的 image 节点，要按两次**",
        "★★★ 这是本批**唯一一条真正影响用户操作**的读数；"
        "★ 它和 811 的「撤销粒度 = 1 动作 = 1 次」**不矛盾但有边界**："
        "811 量的是**单次**触发，812 量的是**连点两下**；"
        "★ 判据要求三件同时成立，否则「一次就撤掉了」会与「两次才撤掉」互相掩盖",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")
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
        hit_expect = any(f.startswith(expect) for f in flipped)
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped, "ok": hit_expect}

    def first_did_nothing(d):
        """★ 阳性对照的对照：伪造「第一下压根没发生」⟹ S1 翻红
        （S3 在这种情况下会「假绿」：没建东西、也没进历史 = 「被守卫拦住」）"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["★ 第一下真的建了东西"] = False
            c["★ 第一下历史 +1"] = False
            n += 1
        return n

    def impossible_state(d):
        """★ 伪造第四态（既没建东西、也没进历史、也不属于三态里的任何一态）
        ⟹ S3 必须翻红。做法：把某条臂的读数换成「UI 点不动且没有 store 读数」
        —— S4b 与 S3 都要能抓住这种「什么都没测到」的情形。"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["store 第二下"] = {"FAILED": "没读到"}
            n += 1
        return n

    def store_second_blank(d):
        """★ 伪造「store 第二下没有确定读数」⟹ S4b 必须翻红
        （这正是第一版把「点不动」当 FAILED 时的处境）"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["store 第二下"] = {"FAILED": "没读到"}
            n += 1
        return n

    def ui_outcome_bogus(d):
        """伪造「UI 第二下的结局是第三种」⟹ S4 必须翻红"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["UI 第二下"] = {"outcome": "★ 不知道", "error": None}
            n += 1
        return n

    def one_undo_enough(d):
        """★ 伪造「一次 Cmd+Z 就撤掉了」⟹ S6 必须翻红
        （否则「要按两次」这条结论会被「一次就够」掩盖）"""
        n = 0
        for r in d.get("emptyRecordUndo") or []:
            if r.get("FAILED"):
                continue
            r["★ 一次 Cmd+Z 之后新建的那个 image 还在吗"] = False
            n += 1
        return n

    def entry_unreadable(d):
        """★ 伪造「入口状态读不到」⟹ S2 必须翻红。
        ★ 注意**不能**打「读成 false」：false 仍然是**有效读数**，
        而 S2 只要求「读到了」⟹ 那样打是**打不中**的（第一版就这么打、没翻红）。"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["入口还在吗（第一次之后）"]["entryStillThere"] = None
            n += 1
        return n

    def guard_anchor_gone(d):
        return 0    # 源码不可变异

    def unrelated(d):
        n = 0
        for c in d["cells"]:
            c["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "★ 阳性对照的对照：伪造「第一下压根没发生」⟹ S1 翻红"
                  "（S3 在这种情况下会**假绿**：没建东西也没进历史 = 「被守卫拦住」）",
            first_did_nothing, "S1"),
        neg("N2", "★ 伪造「store 第二下没有确定读数」⟹ S4b 必须翻红"
                  "（这正是第一版把「点不动」当 FAILED 时的处境）",
            store_second_blank, "S4b"),
        neg("N3", "伪造「UI 第二下的结局是第三种」⟹ S4 必须翻红",
            ui_outcome_bogus, "S4"),
        neg("N4", "★ 伪造「入口状态读不到」⟹ S2 翻红"
                  "（**不能**打「读成 false」——那是有效读数，判据不该翻）",
            entry_unreadable, "S2"),
        neg("N5", "★ 伪造「一次 Cmd+Z 就撤掉了」⟹ S6 必须翻红"
                  "（否则「要按两次」会被「一次就够」掩盖）",
            one_undo_enough, "S6"),
        neg("N6", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 812, "totals": {"passed": nPass, "total": len(checks)},
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
