#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 809 验收器 —— 802 遗留的 7 个高风险动作：**宿主组挪 Δ，新节点必须挪 Δ**

## ★ 本验收器自己的两条纪律（都是踩过才写下来的）

1. **第六次踩「同名锚点」**：S7 找 `ungroupSelectedNodes` 时 `src.find` 抓到的是
   `CanvasState` 的**接口声明**而不是实现 ⟹ 一律 `rfind` / 取最后一次出现，
   并把「同名出现次数」记进证据。
2. **判据里每个除法都要先看分母**（808 的 N3 崩过一次）：本文件没有除法，
   但所有比值都先判分母非零再算。

## ★ 判据为什么不含任何常量

判据是**两个位置之间的差**：

    新节点B.pos − 新节点A.pos  ==  源B.abs − 源A.abs

偏移是 80 还是 120 还是别的**一律不参与** ⟹ 这就是「不预设常量」那条纪律。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
import os
RAW = pathlib.Path(os.environ.get("VB809_RAW") or
      (ROOT / "docs/research/liblib-canvas-batch809-2026-10-01/raw/vb809a.json"))
OUT = pathlib.Path(os.environ.get("VB809_REPORT") or
      (ROOT / "docs/research/liblib-canvas-batch809-2026-10-01/verify-report.json"))
CS = "src/store/canvasStore.ts"

#: 量几何的那 7 个动作（`keepRef` 两条是防重分支的读数，不参与几何判据）
GEOM_ACTIONS = ["firstFrame", "firstLast", "breakdown", "continuation",
                "subtitle", "audio", "shotComplete"]
KEEPREF_ACTIONS = ["firstFrameKeepRef", "firstLastKeepRef"]

#: 每个动作在源码里**应该**调用的绝对坐标换算函数（不预设，只是钉住读法）
ABS_FN = "getAbsoluteNodePosition"


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": evidence})

    rounds = raw["rounds"]

    def cell(rd, key, pos):
        for c in rd["cells"]:
            if c.get("key") == key and c.get("pos") == pos:
                return c
        return None

    # ── S1 ★★ 阳性对照：**宿主组真的被挪了**（否则 S2 什么都没比）
    ev = []
    for rd in rounds:
        for key in GEOM_ACTIONS:
            a, b_ = cell(rd, key, "A"), cell(rd, key, "B")
            if not a or not b_ or a.get("FAILED") or b_.get("FAILED"):
                continue
            ds = (b_["src"]["abs"]["x"] - a["src"]["abs"]["x"],
                  b_["src"]["abs"]["y"] - a["src"]["abs"]["y"])
            dh = ((b_["host"]["pos"]["x"] - a["host"]["pos"]["x"]),
                  (b_["host"]["pos"]["y"] - a["host"]["pos"]["y"]))
            ev.append({"round": rd["round"], "动作": key,
                       "源 abs（A→B）": [a["src"]["abs"], b_["src"]["abs"]],
                       "宿主组 pos（A→B）": [a["host"]["pos"], b_["host"]["pos"]],
                       "源的位移": list(ds), "组的位移": list(dh),
                       "★ 组确实挪了": dh != (0, 0),
                       "★ 源跟着组一起挪": ds == dh,
                       "★ 源在组内（depth=1）": a["src"]["abs"]["depth"] == 1
                                                and b_["src"]["abs"]["depth"] == 1,
                       "★ 三件同时": dh != (0, 0) and ds == dh
                                      and a["src"]["abs"]["depth"] == 1
                                      and b_["src"]["abs"]["depth"] == 1})
    add("S1:★★ 阳性对照：宿主组真的被挪了、源是组内节点（depth=1）且跟着组一起动",
        "★★ 没有这条，S2 的「新节点也挪了 Δ」可能只是**两组 Δ 相同**（探针没挪成）"
        "或者源本来就是顶层节点（压根没测到「组内」这一档）⟹ "
        "★ 802 的缺陷条件正是「源在组里」，depth 必须钉死",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    # ── S2 ★★★ 主判据：新节点位移 == 源位移（**逐位**，不含任何常量）
    ev = []
    for rd in rounds:
        for key in GEOM_ACTIONS:
            a, b_ = cell(rd, key, "A"), cell(rd, key, "B")
            if not a or not b_ or a.get("FAILED") or b_.get("FAILED"):
                continue
            if not a["fresh"] or not b_["fresh"]:
                ev.append({"round": rd["round"], "动作": key,
                           "★ 两臂都建了节点": False,
                           "A 建了几个": len(a["fresh"]), "B 建了几个": len(b_["fresh"])})
                continue
            ds = (b_["src"]["abs"]["x"] - a["src"]["abs"]["x"],
                  b_["src"]["abs"]["y"] - a["src"]["abs"]["y"])
            rows = []
            ok_all = len(a["fresh"]) == len(b_["fresh"])
            for i, (fa, fb) in enumerate(zip(a["fresh"], b_["fresh"])):
                d = (fb["pos"]["x"] - fa["pos"]["x"], fb["pos"]["y"] - fa["pos"]["y"])
                rows.append({"序": i + 1, "类型": fa["type"],
                             "A 位置": list(fa["pos"].values()),
                             "B 位置": list(fb["pos"].values()),
                             "新节点位移": list(d), "源位移": list(ds),
                             "★ 逐位相等": d == ds})
                ok_all = ok_all and d == ds
            ev.append({"round": rd["round"], "动作": key,
                       "★ 两臂都建了节点": True,
                       "A 建了几个": len(a["fresh"]), "B 建了几个": len(b_["fresh"]),
                       "源位移": list(ds), "逐个新节点": rows,
                       "★ 全部逐位相等": ok_all})
    covered = {x["动作"] for x in ev if x.get("★ 两臂都建了节点")}
    add("S2:★★★ 主判据：宿主组挪 Δ，7 个动作新建的节点**每一个**都跟着挪 Δ（逐位）",
        "★★★ 这是 802 留下的那条判据的推广版，**完全不含偏移常量** ⟹ "
        "偏移是 80/120/320 都无所谓；★ 而它正是 `createImageHdPreset` 当年"
        "栽掉的那种读法（拿 `source.position` 当绝对坐标 ⟹ 新节点纹丝不动）；"
        "★ 判据要求 **7 个动作全覆盖**，少一个就不能说「7 个都验过了」",
        ev and covered == set(GEOM_ACTIONS)
        and all(x.get("★ 全部逐位相等") for x in ev), ev)

    # ── S3 ★★ 新节点是**顶层**的（不继承宿主组）
    ev = []
    for rd in rounds:
        for key in GEOM_ACTIONS:
            c = cell(rd, key, "A")
            if not c or c.get("FAILED") or not c["fresh"]:
                continue
            tops = [f["parentId"] is None for f in c["fresh"]]
            ev.append({"round": rd["round"], "动作": key,
                       "新建了几个": len(c["fresh"]),
                       "parentId": [f["parentId"] for f in c["fresh"]],
                       "★ 全是顶层": all(tops),
                       "★ 且都不是组": all(f["type"] != "storyboard-group"
                                          for f in c["fresh"])})
    add("S3:★★ 新建的节点全是**顶层**（不挂进宿主组）",
        "★★ 这是「派生节点不进组」这条设计的实测读数；★ 它也解释了 S4 —— "
        "既然不在组里，组框的 fit 就管不到它",
        ev and all(x["★ 全是顶层"] and x["★ 且都不是组"] for x in ev), ev)

    # ── S4 ★★★ 新节点**不与宿主组框重叠**（用户看得见的读数）
    ev = []
    for rd in rounds:
        for key in GEOM_ACTIONS:
          for pk in ("A", "B"):
            c = cell(rd, key, pk)
            if not c or c.get("FAILED") or not c["fresh"] or not c.get("host"):
                continue
            hx, hy = c["host"]["abs"]["x"], c["host"]["abs"]["y"]
            hw, hh = c["host"]["w"] or 0, c["host"]["h"] or 0
            rows = []
            for f in c["fresh"]:
                fx, fy, fw, fh = f["pos"]["x"], f["pos"]["y"], f["w"] or 0, f["h"] or 0
                ov = not (fx + fw <= hx or fx >= hx + hw
                          or fy + fh <= hy or fy >= hy + hh)
                gap = (hx - (fx + fw)) if fx + fw <= hx else (
                    fx - (hx + hw) if fx >= hx + hw else None)
                rows.append({"类型": f["type"], "新节点框": [fx, fy, fw, fh],
                             "组框": [hx, hy, hw, hh], "★ 与组框重叠": ov,
                             "水平间隙": gap})
            ev.append({"round": rd["round"], "动作": key, "位置": pk,
                       "逐个": rows,
                       "★ 全都不重叠": all(not r["★ 与组框重叠"] for r in rows),
                       "★ 都在组的同一侧": len({
                           "左" if r["水平间隙"] is not None
                           and r["新节点框"][0] + r["新节点框"][2] <= r["组框"][0]
                           else ("右" if r["水平间隙"] is not None else "叠着")
                           for r in rows}) == 1})
    add("S4:★★★ 新建的节点**不压在宿主组上**，且都在组的**同一侧**",
        "★★★ 「叠在组上」是用户一眼能看见的坏读数，而 S2 的等式**抓不到它**"
        "（节点照样可以跟着挪 Δ，只是同时压着组）⟹ 这条是 S2 的必要补充；"
        "★ 间隙由 raw 独立重算，**不写死任何偏移常量**",
        ev and all(x["★ 全都不重叠"] and x["★ 都在组的同一侧"] for x in ev), ev)

    # ── S5 ★★★ DOM 交叉验证：**store 里的位置就是屏幕上看到的位置**
    #   ★★ 判据形式：同臂内 (DOM位移 ÷ 由 DOM 反推的 zoom) 必须等于 store 位移。
    #   —— 不跨臂比，因为 fitView 在每臂缩放得不一样（shotComplete 那条臂实测
    #      zoom 0.526 vs 0.327），跨臂比会得出假结论。
    #   ★★ 这条判据**抓得住一类夹具假象**：第一版我给 shot-breakdown 节点
    #      **注入** `parentId`，store 侧对、DOM 侧源节点纹丝不动 ⟹ 比值对不上
    #      ⟹ 是它逼我改用 UI 造组的。
    ev = []
    for rd in rounds:
        for key in GEOM_ACTIONS:
            for pk in ("A", "B"):
                c = cell(rd, key, pk)
                if not c or c.get("FAILED") or not c["fresh"] or not c.get("dom"):
                    continue
                keys = list(c["dom"])          # [源, 新1, 新2, …]，与 fresh 同序
                dom_src = c["dom"][keys[0]]
                # ★ 第二次踩 808 的坑：阴性对照 N7 把 DOM 全抹成 null 之后，
                #   这里直接 `dom_src["w"]` 会**把整个验收器打崩** ⟹
                #   崩掉意味着「阴性对照测不出东西」，读数不动会被误当成没崩。
                #   守卫：源自己都没渲染 ⟹ 这一臂判「对不上」，不崩。
                if not dom_src:
                    ev.append({"round": rd["round"], "动作": key, "位置": pk,
                               "逐个": [], "★ 全部对上": False,
                               "★ 源节点在 DOM 里都没渲染": True})
                    continue
                rows = []
                # ★ 先看分母（808 的 N3 崩过一次），再算比值
                zw = (c["src"]["w"] or 0)
                zoom = (dom_src["w"] / zw) if zw else 0
                for i, f in enumerate(c["fresh"]):
                    d = c["dom"].get(keys[i + 1])
                    if d is None or not zoom:
                        rows.append({"序": i + 1, "★ 渲染出来了": False})
                        continue
                    dx = (d["x"] - dom_src["x"]) / zoom
                    dy = (d["y"] - dom_src["y"]) / zoom
                    sx = f["pos"]["x"] - c["src"]["abs"]["x"]
                    sy = f["pos"]["y"] - c["src"]["abs"]["y"]
                    rows.append({"序": i + 1, "类型": f["type"],
                                 "★ 渲染出来了": True,
                                 "由 DOM 反推的 zoom": round(zoom, 6),
                                 "DOM 位移÷zoom": [round(dx, 3), round(dy, 3)],
                                 "store 位移": [sx, sy],
                                 "★ 两者相等（亚像素容差 0.05）":
                                     abs(dx - sx) <= 0.05 and abs(dy - sy) <= 0.05})
                ev.append({"round": rd["round"], "动作": key, "位置": pk,
                           "逐个": rows,
                           "★ 全部对上": all(
                               r.get("★ 两者相等（亚像素容差 0.05）")
                               for r in rows)})
    add("S5:★★★ DOM 交叉验证：(DOM 位移 ÷ 由 DOM 反推的 zoom) **等于** store 位移",
        "★★★ 「store 里建了」**不等于**「用户看得见」；★ 这条不跨臂比，"
        "因为 fitView 每臂缩放不同（实测 0.526 vs 0.327），跨臂比会得出假结论；"
        "★ 容差 0.05px：实测 DOM 读数只差 0.01px（亚像素渲染舍入），"
        "**不写死成逐位相等**——那会把真实通过判成失败",
        ev and all(x["★ 全部对上"] for x in ev), ev)

    # ── S6 ★★★ 防重分支：已有 image→video 入边时，两个首帧芯片**一个节点都不建**
    ev = []
    for rd in rounds:
        for key in KEEPREF_ACTIONS:
            for pk in ("A", "B"):
                c = cell(rd, key, pk)
                if not c or c.get("FAILED"):
                    continue
                before_att = c["src"].get("attempt")
                after_att = (c.get("srcAfter") or {}).get("attempt")
                pressed = {x["label"]: x["pressed"] for x in (c.get("chipsAfter") or [])}
                ev.append({"round": rd["round"], "动作": key, "位置": pk,
                           "建了几个节点": len(c["fresh"]),
                           "★ 一个都没建": len(c["fresh"]) == 0,
                           "源节点数 Δ": c["afterCount"] - c["beforeCount"],
                           "attempt（之前）": before_att,
                           "attempt（之后）": after_att,
                           "★ attempt 标签变了": before_att != after_att,
                           "芯片 aria-pressed": pressed,
                           "★ 至少一个芯片被按下": any(
                               v == "true" for v in pressed.values()),
                           "★ 三件同时": len(c["fresh"]) == 0
                                          and before_att != after_att
                                          and any(v == "true"
                                                  for v in pressed.values())})
    add("S6:★★★ 防重分支：视频已有 image→video 入边时，两个首帧芯片"
        "**一个节点都不建**，但**芯片的选中态和 attempt 标签都变了**",
        "★★★ 这是本批**顺带测出来的一条分支**，第一版探针把它读成了「功能坏了」；"
        "★ 结论要分两半说：**画布上什么都没变**（不是静默，因为芯片按下了、"
        "标签也写了）⟹ 用户点了「首帧生成视频」却看不到首帧图，"
        "**只有芯片高亮这一个反馈**；★ 判据分三件正是为了不把"
        "「没建节点」直接写成「完全没反应」",
        ev and all(x["★ 三件同时"] for x in ev) and len(ev) == 2 * len(KEEPREF_ACTIONS)
        * len(rounds), ev)

    # ── S7 ★★ 静态锚点：7 个动作的**实现**里都调了绝对坐标换算
    #   ★★ 第六次踩同名锚点：`src.find("ungroupSelectedNodes: (")` 抓到的是
    #   `CanvasState` 的接口声明（`:385`），实现在 `:3568`。
    #   本条数的是「每个动作的实现段里有没有 ABS_FN」，用「取实现段 = 往后找
    #   `position:` 的那次出现」这种不依赖同名声明的切法。
    anchors = {
        "createFirstFrameReference": "素材 - 首帧参考",
        "createFirstLastFrameReference": "素材 - 尾帧参考",
        "addDerivedNode": "const offset = options?.offset",
        "createVideoContinuation": "continuation: VideoContinuationMetadata",
        "createSubtitleErase": "video-continuation",   # 只用来定位段落起点
        "createAudioSplit": "audioLabelByMode",
        "completeShotBreakdown": "SHOT_BREAKDOWN_RESULT_DEFINITIONS",
    }
    rows = []
    for name, anchor in anchors.items():
        hits = [i for i in range(len(src)) if src.startswith(anchor, i)]
        # ★ 取**最后一次**出现：声明在文件前部、实现靠后
        i = hits[-1] if hits else -1
        seg = src[max(0, i - 1500):i + 1500] if i >= 0 else ""
        rows.append({"动作": name, "锚点出现次数": len(hits),
                     "★ 取的是最后一次": len(hits) > 0,
                     "实现段里有没有 %s" % ABS_FN: ABS_FN in seg})
    add("S7:★★ 静态锚点：7 个动作的实现段里都调了 `%s`（绝对坐标换算）"
        % ABS_FN,
        "★★ 静态证据**不能**替代 S2 的行为证据（794 的硬规矩）；"
        "它的作用是**解释** S2 为什么成立，并钉住「读源码时的取法」；"
        "★ 一律取锚点的**最后一次**出现（= 实现），同名出现次数一并记进证据",
        rows and all(r["★ 取的是最后一次"] and
                     r["实现段里有没有 %s" % ABS_FN] for r in rows), rows)

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
        # ★ `expect` 传的是**短前缀**（"S2"），`flipped` 存的是**完整 id**
        #   ⟹ 用 `in` 会拿字符串和列表比、永远 False。第六次「读数对但判定错」。
        hit_expect = any(f.startswith(expect) for f in flipped)
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped, "ok": hit_expect}

    def groups_not_moved(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("pos") == "B" and c.get("host"):
                    c["host"]["pos"] = copy.deepcopy(
                        next(x for x in rd["cells"]
                             if x.get("key") == c["key"] and x.get("pos") == "A"
                             )["host"]["pos"])
                    c["src"]["abs"] = copy.deepcopy(
                        next(x for x in rd["cells"]
                             if x.get("key") == c["key"] and x.get("pos") == "A"
                             )["src"]["abs"])
                    n += 1
        return n

    def relative_coord_bug(d):
        """★ 阴性对照要打在**性质真正读取的字段**上（801–808 各踩过一次）：
        把 B 臂的新节点位置改成**没跟着源走**（模拟 802 当年用相对坐标）。"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("pos") != "B" or c.get("FAILED") or not c.get("fresh"):
                    continue
                a = next(x for x in rd["cells"]
                         if x.get("key") == c["key"] and x.get("pos") == "A")
                for f, fa in zip(c["fresh"], a["fresh"]):
                    f["pos"] = {"x": fa["pos"]["x"], "y": fa["pos"]["y"]}
                    n += 1
        return n

    def source_depth_top(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("host") and c["src"]["abs"]["depth"] == 1:
                    c["src"]["abs"]["depth"] = 0
                    n += 1
        return n

    def new_nodes_overlap_group(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                h = c.get("host")
                if not h or c.get("FAILED") or not c.get("fresh"):
                    continue
                for f in c["fresh"]:
                    f["pos"] = {"x": h["abs"]["x"] + 10, "y": h["abs"]["y"] + 10}
                    n += 1
        return n

    def keepref_created_something(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("key") in KEEPREF_ACTIONS and not c.get("FAILED"):
                    c["fresh"] = [{"type": "image", "pos": {"x": 0, "y": 0},
                                   "abs": {"x": 0, "y": 0, "depth": 0},
                                   "w": 100, "h": 100, "gen": None,
                                   "cont": 0, "parentId": None}]
                    c["afterCount"] = c["beforeCount"] + 1
                    n += 1
        return n

    def keepref_no_feedback(d):
        """反向对照：防重分支**确实是有反馈的**（芯片按下 + attempt 标签变）⟹
        只把 attempt 改回原值，S6 应当翻红。"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("key") in KEEPREF_ACTIONS and c.get("srcAfter"):
                    c["srcAfter"]["attempt"] = c["src"].get("attempt")
                    n += 1
        return n

    def dom_not_rendered(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("dom"):
                    for k in list(c["dom"]):
                        c["dom"][k] = None
                        n += 1
        return n

    def unrelated(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                c["secs"] = 999
                n += 1
        return n

    negs = [
        neg("N1", "★ 阴性对照打在**性质真正读取的字段**上：把 B 臂的新节点"
                  "位置改回与 A 臂一样（= 当年 802 那种「用相对坐标、新节点纹丝不动」）",
            relative_coord_bug, "S2"),
        neg("N2", "★ 阳性对照的对照：把宿主组**没挪成**（B 臂的组与源都改回 A 臂）"
                  "⟹ S1 必须翻红，否则「组没挪」也能让 S2 成立",
            groups_not_moved, "S1"),
        neg("N3", "把源的 depth 改成 0（假装源不是组内节点）⟹ S1 必须翻红，"
                  "钉死「测的确实是组内这一档」",
            source_depth_top, "S1"),
        neg("N4", "★ 把新节点挪到**组框里面**⟹ S2 的等式**照样成立**（它只管"
                  "「跟着挪 Δ」），但 S4 必须翻红 ⟹ 这正是 S4 存在的理由",
            new_nodes_overlap_group, "S4"),
        neg("N5", "防重分支改成「也建了节点」⟹ S6 必须翻红",
            keepref_created_something, "S6"),
        neg("N6", "把 attempt 标签改回原值（伪造「连标签都没变」）⟹ S6 必须翻红，"
                  "钉死「不是完全没反馈」这半句",
            keepref_no_feedback, "S6"),
        neg("N7", "把 DOM 读数全抹成 null（store 里有、DOM 里没有）⟹ S5 必须翻红",
            dom_not_rendered, "S5"),
        neg("N8", "反向对照：只动 `secs` 这个与任何判据无关的字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 809, "totals": {"passed": nPass, "total": len(checks)},
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
              str([f[:12] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())
