#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 815 验收器 —— ImageNode 七个动作的**累积行为**（防不防重完全未知）

## ★ 为什么每个动作都要单独测

`ImageNode` 的七个 UI 动作共用同一个 store 动作 `addDerivedNode`
（`ImageNode.tsx:141` 旋转、`:161` 全景、`:185` 派生五连），
但各自的 `offset`／`dimensions`／`data` **都不同**
⟹ **抽样会让「某个动作有守卫」被平均掉** ⟹ 必须 7/7 全测。

## ★ 全部判据都**从 raw 的原始字段重算**，不信探针算好的标志位

探针会把 `★ 第一下建了东西`、`★ 三份的 x 全同`、`★ 每个 kind 只有一种文本`
这类结论**预先算好**写进 raw。本验收器**一律重算**——
理由是 801–815 反复踩到的坑：**阴性对照必须打在性质真正读取的字段上**；
如果判据读的是探针算好的标志位，那么阴性对照就只能去改那个标志位，
打不中真正的原始读数 ⟹ 那样的阴性对照是**装饰**。

## ★ 判据

- **S1 ★★**：第一下**真的**建了东西（阳性对照），且按钮**存在、不 disabled**。
- **S2 ★★★**：每个动作的结局落在 {完全没拦 / 被守卫拦住 / 空记录 / 点不动} 之内
  —— 四态，因为「按钮找不到」也是一种结局（807 起立的「点不动是读数」）。
- **S3 ★★★**：**防重动作清单**被**显式列出来**（清单本身是交付物）。
- **S4 ★★**：静态锚点 —— 三个 `addDerivedNode` 调用点 + 五个标签 + iconOnly。
- **S5 ★★★**（本批新增）：三份产物的**绝对几何逐像素相同**（叠在一起）。
- **S6 ★★★**（本批新增）：同 kind 的多份产物**可见文本逐字相同**。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB815_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch815-2026-10-01"
                    / "raw" / "vb815a.json"))
OUT = pathlib.Path(os.environ.get("VB815_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch815-2026-10-01"
                    / "verify-report.json"))
IN = "src/components/nodes/ImageNode.tsx"
TB = "src/components/ImageToolbar.tsx"

LABELS = ["旋转", "全景", "多角度", "打光", "九宫格", "高清", "宫格切分"]
DERIVED5 = ["多角度", "打光", "九宫格", "高清", "宫格切分"]

#: 判据在读**哪些 raw 原始字段** —— 阴性对照必须打在这些字段上
#: （这是本文件最重要的一段：字段名写死，判据和对照就不会各说各话）
F_BTN = "工具栏按钮"      # S1
F_MARKS = "marks"        # S1 / S2 / S5 / S6
F_UI = "UI 结局"          # S2 / S3
F_IDS = "建出来的 id"     # S5 / S6
F_GEOM = "绝对几何"        # S5
F_VIS = "可见文本"         # S6
F_VIA = "命中路径"         # S1


def _has_btn(btns, label):
    """★ 三条匹配路径：可见文字 / `aria-label` / `title`
    —— `ImageToolbar.tsx:171` 是 `!iconOnly && <span>`，
    四个 `iconOnly: true` 的动作（`:91/100/108/116`）**没有可见文字** ⟹
    第一版只按 `label`（= textContent）匹配，「旋转」永远 not-found ⟹ **假红**。"""
    return any(b.get("label") == label or b.get("aria") == label
               or b.get("title") == label for b in btns)


def run_checks(raw, src_in, src_tb):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    cells = raw["cells"]

    def c(rd, label):
        return next((x for x in cells if x.get("round") == rd
                     and x.get("label") == label), None)

    rounds = sorted({x["round"] for x in cells})
    good = [x for x in cells if not x.get("FAILED")]

    # ── S1 ★★ 阳性对照：按钮存在 + 不 disabled + 第一下真的建了东西
    ev = []
    for x in good:
        label = x.get("label")
        btns = x.get(F_BTN) or []
        marks = x.get(F_MARKS) or []
        # ★ 重算，不读探针的标志位
        first_made = marks[0].get("这次新建了几个") if marks else 0
        dis = [b for b in btns if _has_btn([b], label) and b.get("disabled")]
        vias = [v.get("★ 命中路径") for v in (x.get(F_VIA) or [])]
        ev.append({"round": x.get("round"), "动作": label,
                   "★ 按钮存在": _has_btn(btns, label),
                   "★ 按钮不是 disabled": not dis,
                   "第一下建了几个": first_made,
                   "★ 命中路径": vias,
                   "★ 三件同时": _has_btn(btns, label) and not dis
                                 and first_made >= 1})
    add("S1:★★ 阳性对照：七个动作的按钮**都存在、都可点**，且第一下**真的建了东西**",
        "★★ 「按钮存在」用**三条匹配路径**（可见文字／`aria-label`／`title`）—— "
        "raw 里逐条记了**命中路径**：`ImageToolbar.tsx:91/100/108/116` 有四个 "
        "`iconOnly: true` 的动作**没有** `<span>` 文字（`:171`），"
        "第一版 raw 只记 `label` ⟹「旋转」永远 not-found ⟹ **假红**（已修）；"
        "★ 没有这条，「点了没反应」分不清是**守卫拦的**还是**按钮没找到**；"
        "★ 三件（存在／不 disabled／建了东西）必须**同时**成立——"
        "第一版只聚合后两件，于是 N2 打不中",
        bool(ev) and all(x["★ 三件同时"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS)
        # ★ iconOnly 的动作**只可能**靠 aria/title 命中：证明确有三路径
        and any(v not in (None, "文字")
                for x in ev for v in x["★ 命中路径"]),
        {"逐条": ev, "★ 七个动作一个不落":
            {x["动作"] for x in ev} == set(LABELS),
         "★ 至少一条靠非「文字」路径命中": any(
             v not in (None, "文字") for x in ev for v in x["★ 命中路径"]),
         "命中路径分布": {v: sum(
             1 for x in ev for p in x["★ 命中路径"] if p == v)
             for v in ("文字", "aria", "title")},
         "非文字路径的动作": sorted({x["动作"] for x in ev
                                     if any(p not in (None, "文字")
                                            for p in x["★ 命中路径"])})})

    # ── S2 ★★★ 结局落在四态之内
    ev = []
    for x in good:
        marks = x.get(F_MARKS) or []
        total = len(x.get(F_IDS) or [])
        pasts = [m.get("历史") or [0, 0] for m in marks]
        if x.get(F_UI):
            state = "★ 点不动"
        elif marks and total >= len(marks) >= 2:
            state = "完全没拦（每次都建）"
        elif total == 0 and pasts and pasts[-1][1] > 1:
            state = "★ 空记录（没建东西但历史 +1）"
        else:
            state = "被守卫拦住"
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "★ 结局": state, "一共建了几份": total,
                   "逐次": [[m.get("第几次"), m.get("节点"),
                             m.get("这次新建了几个")] for m in marks],
                   "★ 落在四态之内": state in
                   ("完全没拦（每次都建）", "被守卫拦住",
                    "★ 空记录（没建东西但历史 +1）", "★ 点不动")})
    add("S2:★★★ 每个动作的结局落在四态之内"
        "（完全没拦 / 被守卫拦住 / 空记录 / **点不动**）",
        "★★★ 第四态「点不动」是 **807 起立的规矩**：前提不满足的臂**显式作废、"
        "不得据此下结论**；★ 判四态而不是三态，是因为 814 的三态里没有"
        "「按钮根本找不到」这一种；★ 七个动作**逐一测**（各自 `offset`／"
        "`dimensions` 都不同），**抽样会让某个动作的守卫被平均掉**",
        bool(ev) and all(x["★ 落在四态之内"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 结局分布": {s: sorted({x["动作"] for x in ev if x["★ 结局"] == s})
                        for s in sorted({x["★ 结局"] for x in ev})},
         "★ 两个时刻都跑了": rounds})

    # ── S3 ★★★ 防重动作清单被显式列出来
    dupes, guarded, dead = [], [], []
    r0 = min(rounds)
    for label in LABELS:
        x = c(r0, label)
        if not x or x.get("FAILED"):
            continue
        if x.get(F_UI):
            dead.append(label)
        elif len(x.get(F_IDS) or []) >= 2:
            dupes.append(label)
        else:
            guarded.append(label)
    add("S3:★★★ **防重动作清单**被显式列出来（清单本身是交付物）",
        "★★★ 813/814 把「哪些不防重」当成交付物，本批继续沿用；"
        "★ 清单**只从第一轮出**（否则同一个动作会被列两遍）；"
        "★ 判据要求：**清单非空**、且**七个动作一个不落地被分到三类里**——"
        "★ 注意「三类互斥」是**结构性**的（三个清单由 `if/elif/else` 生成）、"
        "**不是**从证据里读出来的 ⟹ 我第一版把它当成可证伪的判据、"
        "配了个打不中的阴性对照，**那是我的错**：那一条对任何输入都恒真。",
        bool(dupes) and sorted(dupes + guarded + dead) == sorted(LABELS),
        {"完全没拦": sorted(dupes), "被守卫拦住": sorted(guarded),
         "点不动": sorted(dead),
         "★ 七个动作一个不落": sorted(dupes + guarded + dead) == sorted(LABELS),
         "★ 清单非空": bool(dupes)})

    # ── S4 ★★ 静态锚点
    hits = [i for i in range(len(src_in)) if src_in.startswith("addDerivedNode(", i)]
    i_map = src_in.find("const derivedImageActions")
    seg = src_in[i_map:i_map + 900] if i_map >= 0 else ""
    rot = any('"旋转"' in src_in[max(0, h - 200):h + 60] for h in hits)
    pano = any('"720°全景图"' in src_in[max(0, h - 300):h + 260] for h in hits)
    add("S4:★★ 静态锚点：七个动作的调用点**确实共用** `addDerivedNode`",
        "★ 静态证据**不能**替代 S2／S3 的行为证据（794 的硬规矩）；"
        "它的作用是把 S3 的清单**归因**到具体那几行、而不是「它们碰巧都建了东西」；"
        "★ 一律**取最后一次**出现（实现；同名声明在文件前部）—— 第十一次提醒；"
        "★ 全景那处是**多行**调用（`addDerivedNode(` 后换行才写 `filename`），"
        "`\"720°全景图\"` 落在调用点**之后**约 60 字符处 ⟹ 第一版窗口取窄了、"
        "判成红 ⟹ **又是我自己造的假红**；"
        "★ `!iconOnly && <span>` ⟹ iconOnly 的动作**没有可见文字**，"
        "这是 S1 必须走三条匹配路径的**根据**",
        len(hits) >= 3 and all(('"%s"' % d) in seg for d in DERIVED5)
        and rot and pano and "!iconOnly &&" in src_tb,
        {"addDerivedNode 调用点数": len(hits),
         "★ 派生五连的五个标签都在表里": all(('"%s"' % d) in seg
                                    for d in DERIVED5),
         "★ 旋转的调用点附近有「旋转」": rot,
         "★ 全景的调用点附近有「720°全景图」": pano,
         "iconOnly 动作数": src_tb.count("iconOnly: true"),
         "★ 有 `!iconOnly &&` 这个条件": "!iconOnly &&" in src_tb})

    # ── S5 ★★★ 本批新增：三份产物的**绝对几何逐像素相同**（叠在一起）
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        geom = x.get(F_GEOM) or {}
        gs = [geom.get(i) for i in ids]
        xs = [g["x"] for g in gs if g]
        ys = [g["y"] for g in gs if g]
        wh = [(g["w"], g["h"]) for g in gs if g]
        same_x = bool(xs) and len(set(xs)) == 1
        same_y = bool(ys) and len(set(ys)) == 1
        same_wh = bool(wh) and len(set(wh)) == 1
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "建了几份": len(ids), "x 序列": xs, "y 序列": ys,
                   "宽高": sorted(set(wh)),
                   "★ 全部 x 相同": same_x, "★ 全部 y 相同": same_y,
                   "★ 全部宽高相同": same_wh,
                   "★ 三份逐像素重叠": len(ids) >= 3 and same_x
                                    and same_y and same_wh})
    add("S5:★★★ 本批新增读数：连点三次建出来的**三份完全重叠**"
        "（x／y／宽高**逐像素相同**）",
        "★★★ 这是 814 没有的读数：814 只比了**文本**，没比**位置**。"
        "★ 判据用 **DOM `getBoundingClientRect`**（用户看得见的几何），"
        "**不读 store 的 `position`** ——809/810 的规矩；"
        "★ 机理可归因：`canvasStore.ts:1784-1792` 的位置是"
        "「**源节点**绝对位置 + 源宽 + offset」，而三次的 `sourceId` **都是源节点** "
        "⟹ 三次必然算出**同一个坐标**；"
        "★ 真实后果：用户在画布上**只看到一份**（三份压在一起），"
        "但 store 里有三份、撤销栈里有三条 ⟹ 「点三次」的反馈和「点一次」**完全一样**",
        bool(ev) and all(x["★ 三份逐像素重叠"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev, "★ 七个动作一个不落":
            {x["动作"] for x in ev} == set(LABELS),
         "★ 两轮都跑": len({x["round"] for x in ev}) == len(rounds)})

    # ── S6 ★★★ 本批新增：同 kind 的多份产物**可见文本逐字相同**
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        vis = x.get(F_VIS) or {}
        # ★ 排除**选中态**：最后一次产物正被选中，编辑面板展开，
        #   `textContent` 会把面板文字一起吃进去（814 踩过，探针注释里也记着）
        picked = [(i, vis.get(i) or {}) for i in ids
                  if (vis.get(i) or {}).get("text")
                  and not (vis.get(i) or {}).get("selected")]
        groups = {}
        for i, v in picked:
            groups.setdefault(v.get("type"), []).append(v["text"])
        one = bool(groups) and all(len(set(v)) == 1 for v in groups.values())
        multi = any(len(v) >= 2 for v in groups.values())
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "可比份数": len(picked), "按 kind 分组": {
                       k: sorted(set(v)) for k, v in groups.items()},
                   "★ 每个 kind 只有一种文本": one,
                   "★ 至少一个 kind 出现两次以上": multi,
                   "★ 读数成立": one and multi})
    add("S6:★★★ 本批新增读数：同一 kind 的多份产物**可见文本逐字相同**",
        "★★★ 把 814 在 VideoNode 上的结论**搬到 ImageNode 七个动作**；"
        "★ 必须**排除选中态**（814 的坑：最后一份正被选中、编辑面板展开、"
        "`textContent` 会把面板文字吃进去 ⟹ 那是**选中态**的差异、"
        "不是节点身份的差异）；"
        "★ 判据用 **DOM 可见读数**，不读 store；"
        "★ 与 S5 合起来才构成完整后果：**文本一样 + 位置一样** ⟹ "
        "用户在画布上**没有任何办法**把它们分开",
        bool(ev) and all(x["★ 读数成立"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 每个动作都有「同一 kind 两种文本」的样本": all(
             x["★ 至少一个 kind 出现两次以上"] for x in ev),
         "样本文本": {x["动作"]: sorted(
             {t for vs in x["按 kind 分组"].values() for t in vs})
             for x in ev if x["round"] == r0}})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src_in = (ROOT / IN).read_text(encoding="utf-8")
    src_tb = (ROOT / TB).read_text(encoding="utf-8")
    checks = run_checks(raw, src_in, src_tb)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src_in, src_tb)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def first_did_nothing(d):
        """伪造「第一下压根没建东西」⟹ S1 必须翻红"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            for m in x.get(F_MARKS) or []:
                if m.get("第几次") == 1:
                    m["这次新建了几个"] = 0
                    n += 1
        return n

    def button_disabled(d):
        """★ 伪造「按钮 disabled」⟹ S1 必须翻红
        （只清空按钮列表太粗：S1 的「存在」和「不 disabled」是两件事，
        分开打才知道判据到底读的是哪一件）"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            for b in x.get(F_BTN) or []:
                if _has_btn([b], x.get("label")):
                    b["disabled"] = True
                    n += 1
        return n

    def button_missing(d):
        """伪造「按钮根本不存在」⟹ S1 必须翻红"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            x[F_BTN] = []
            n += 1
        return n

    def all_guarded(d):
        """伪造「每个动作都被守卫拦住（一份都建不出）」⟹ S3 必须翻红"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            x[F_IDS] = []
            n += 1
        return n

    def drop_a_label(d):
        """伪造「某个动作从三类清单里整个消失」⟹ S3 必须翻红
        （第一版打的是「两类重叠」—— 那是结构性的、对任何输入都恒真，打不中）"""
        n = len(d["cells"])
        d["cells"] = [x for x in d["cells"] if x.get("label") != "全景"]
        return n

    def fan_out(d):
        """★ 伪造「三份产物排开、不再重叠」⟹ S5 必须翻红"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            ids = x.get(F_IDS) or []
            for k, i in enumerate(ids):
                g = (x.get(F_GEOM) or {}).get(i)
                if g:
                    g["x"] = g["x"] + 200 * k
                    n += 1
        return n

    def texts_differ(d):
        """★ 伪造「同一 kind 的两份文本不同」⟹ S6 必须翻红"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            ids, vis = x.get(F_IDS) or [], x.get(F_VIS) or {}
            picked = [i for i in ids
                      if (vis.get(i) or {}).get("text")
                      and not (vis.get(i) or {}).get("selected")]
            for k, i in enumerate(picked):
                v = vis.get(i) or {}
                v["text"] = v["text"] + "　第%d份" % (k + 1)
                vis[i] = v
                n += 1
        return n

    def mangle_selected_text(d):
        """★ 反向对照：只把**选中**那一份的文本改成完全不同的内容 ⟹ 期望**不翻**
        （S6 明确排除选中态 ⟹ 选中态带进来的编辑面板文字**不该**影响判据；
        如果它翻了，说明判据其实在读选中态 —— 814 正是栽在这里）"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            vis = x.get(F_VIS) or {}
            for i in (x.get(F_IDS) or []):
                v = vis.get(i) or {}
                if v.get("text") and v.get("selected"):
                    v["text"] = "★这一份被选中了所以文本完全不一样" + "x" * 200
                    vis[i] = v
                    n += 1
        return n

    def no_comparable_sample(d):
        """★ 伪造「没有任何可比样本」（每一份都被选中）⟹ S6 **必须**翻红
        —— 这是我第一版误标成「反向对照」的那一条：它翻红是**对的**，
        「同一 kind 的多份文本相同」这个主张在**零样本**时本来就无法成立 ⟹
        判据理应可证伪。★ 教训：「我以为它不该翻」要先问
        **「这条判据在这种输入下应不应该成立」**，而不是先问「它翻没翻」"""
        n = 0
        for x in d["cells"]:
            if x.get("FAILED"):
                continue
            for i in (x.get(F_IDS) or []):
                v = (x.get(F_VIS) or {}).get(i) or {}
                if v.get("text"):
                    v["selected"] = True
                    n += 1
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「第一下压根没建东西」⟹ S1 翻红",
            first_did_nothing, "S1"),
        neg("N2", "伪造「按钮 disabled」⟹ S1 翻红"
                  "（分开打才知道判据读的是「存在」还是「不 disabled」）",
            button_disabled, "S1"),
        neg("N3", "伪造「按钮根本不存在」⟹ S1 翻红"
                  "（否则「点了没反应」分不清是守卫拦的还是按钮没找到）",
            button_missing, "S1"),
        neg("N4", "伪造「每个动作都被守卫拦住」⟹ S3 翻红"
                  "（否则「清单非空」这条判据恒真）",
            all_guarded, "S3"),
        neg("N5", "伪造「某个动作从三类清单里整个消失」⟹ S3 翻红"
                  "（第一版打的是「两类重叠」，那是结构性的、打不中）",
            drop_a_label, "S3"),
        neg("N6", "★ 伪造「三份产物排开、不再重叠」⟹ S5 翻红",
            fan_out, "S5"),
        neg("N7", "★ 伪造「同一 kind 的两份文本不同」⟹ S6 翻红",
            texts_differ, "S6"),
        neg("N8", "★ 伪造「没有任何可比样本」（每份都被选中）⟹ S6 **必须**翻红",
            no_comparable_sample, "S6"),
        neg("N9", "★ 反向对照：只把**选中**那一份的文本改成完全不同的内容 ⟹ "
                  "期望**不翻**（证明 S6 真的在排除选中态，814 的坑没踩）",
            mangle_selected_text, "__NO_FLIP__"),
        neg("N10", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 815,
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