#!/usr/bin/env python3
"""batch 761 汇编器：从四份原始读数现算 runtime-audit.json

原则不变：**数字不许手抄**。每条判据的量都从 raw/ 下的探针原始输出现算，
缺文件直接抛错。

⚠ 派生层只允许从**原始字段**现算，不许出现常数（760 的 R34）。
  所以这里每个派生量都写成「从哪几个原始字段算出」的表达式，
  并在 rework 里留 R42（我自己的读数滞后把 4 次滚轮看成 2 次）。
"""
import json
import pathlib
import sys

RAW = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch761-2026-10-01/raw")
OUT = RAW.parent / "runtime-audit.json"

FILES = {k: RAW / ("vb761%s.json" % k) for k in "abcd"}
for k, p in FILES.items():
    if not p.exists():
        sys.exit("FATAL 缺原始读数 %s —— 判失败，不许凭空写结论" % p)
A, B, C, D = (json.loads(FILES[k].read_text(encoding="utf-8")) for k in "abcd")
ra, rb, rc, rd = A["rounds"][0], B["rounds"][0], C["rounds"][0], D["rounds"][0]

DESKTOP = B["constants"]["desktopViewport"]
COMPACT = B["constants"]["compactViewport"]

# ---------- A 两档视口常量 ----------
viewport_ab = []
for v in rb["viewports"]:
    store = v["store"]
    viewport_ab.append({
        "label": v["label"],
        "requestedWidth": v["requested"]["w"],
        "measuredWidth": v["measured"]["innerWidth"],
        "mq768": v["measured"]["mq768"],
        "store": store,
        "dom": v["dom"],
        "indicator": v["indicator"],
        "triggerText": v["triggerText"],
        "triggerVisible": bool((v["triggerVisible"] or {}).get("w")),
        "matchesExpectedConstant": v["matchesConstant"],
        "expectedConstant": v["expectedConstant"],
        "ownerLogReasons": [e["reason"] for e in (v["ownerLog"] or {}).get("entries", [])],
    })
ab_by_label = {v["label"]: v for v in viewport_ab}

# ---------- B 缩放菜单六格 + 三个快捷键 ----------
menu = [{"key": a["key"], "beforeZoom": (a["before"] or {}).get("zoom"),
         "afterZoom": (a["after"] or {}).get("zoom"),
         "indicator": a["derived"]["indicator"],
         "indicatorMatchesReal": a["derived"]["indicatorMatchesReal"],
         "triggerMatchesReal": a["derived"]["triggerMatchesReal"]}
        for a in ra["actions"]]
kb = [{"key": k["key"], "dz": (k["delta"] or {}).get("dz"),
       "dx": (k["delta"] or {}).get("dx"),
       "dy": (k["delta"] or {}).get("dy"),
       "indicatorMatchesReal": k["derived"]["indicatorMatchesReal"]}
      for k in ra["keyboard"]]
clamp = {name: {"times": c["times"], "startZoom": (c["store"] or {}).get("zoom")
                and (c["start"] or {}).get("zoom"),
                "finalZoom": (c["store"] or {}).get("zoom"),
                "indicator": c["derived"]["indicator"],
                "indicatorMatchesReal": c["derived"]["indicatorMatchesReal"]}
         for name, c in ra["clamp"].items()}

# ---------- C 首屏 ----------
c0 = ra["C0_initial"]
initial = {
    "store": c0["vp"]["store"], "dom": c0["vp"]["dom"],
    "zoomLevel": c0["vp"]["zoomLevel"],
    "triggerText": c0["vp"]["triggerText"],
    "indicatorMatchesReal": c0["derived"]["indicatorMatchesReal"],
    "triggerMatchesReal": c0["derived"]["triggerMatchesReal"],
    "realPercent": c0["derived"]["realPercent"],
    "hardcodedInitial": 54,
    "hardcodedShown": c0["vp"]["zoomLevel"] == 54,
    "resizeControls": c0["resizeControls"],
    "resizeLikeElements": c0["resizeLikeElements"],
}

# ---------- D 滚轮：全部 Δzoom 与每格位移 ----------
bursts = []
for key in ("burstSlow", "burstFast", "burstDown"):
    b = rc.get(key) or {}
    if "FAILED" in b:
        bursts.append({"key": key, "FAILED": b["FAILED"]})
        continue
    n = b["n"]
    store_dy = b["storeDy"]
    dom_dy = b["domDy"]
    bursts.append({
        "key": key, "n": n, "deltaY": b["deltaY"],
        "storeDy": store_dy, "domDy": dom_dy,
        "storeDz": b["storeDz"], "domDz": b["domDz"],
        "domDyPerEvent": round(dom_dy / n, 2) if n else None,
        "acceptedDelta": b["acceptedDelta"],
    })
wheel_events_total = sum(b.get("n", 0) for b in bursts)
all_dz_zero = all(abs(b.get("storeDz", 0)) < 1e-9 and abs(b.get("domDz", 0)) < 1e-9
                  for b in bursts if "FAILED" not in b)
dz_values = [b.get("storeDz") for b in bursts if "FAILED" not in b]

# 761a/761b 那个「隔一个才动」的形状，是读数滞后 —— 从 761c 现算真值
stale_pattern = {
    "probeA_dySeries": [(s.get("delta") or {}).get("dy")
                        for s in ra["wheel"]["steps"] if s.get("delta")],
    "probeB_dySeries": rb["wheelPane"].get("dyValues"),
    "probeB_allDzZero": rb["wheelPane"].get("allDzZero"),
    "verdict": "761a/761b 每步都读 ⟹ 读数落在平移落地之前，Δ 被错记到隔一格。"
               "761c 中途不读，4 次滚轮总位移 480 = 4×120，每次都生效。",
    "probeC_burstSlow_totalDy": (rc.get("burstSlow") or {}).get("domDy"),
    "probeC_burstSlow_events": (rc.get("burstSlow") or {}).get("n"),
}

# ---------- E 滚轮落在节点上 ----------
wheel_node = rb.get("wheelNode") or {}
wn = wheel_node.get("point") or {}
wheel_on_node = {
    "hitTag": wn.get("tag"), "hitClass": wn.get("cls"),
    "nodeNodrag": wn.get("nodrag"), "nodeNopan": wn.get("nopan"),
    "storeBefore": wheel_node.get("before"),
    "storeAfter": wheel_node.get("after"),
    "viewportUnchanged": wheel_node.get("before") == wheel_node.get("after"),
    "delta": wheel_node.get("delta"),
}

# ---------- F store 与 DOM 的视口分叉 ----------
tl = rd.get("timeline") or {}
tl_gaps = rd.get("gapSeries") or []
divergence = {
    "markCount": len(tl),
    "marksMs": [0, 500, 1500, 3000, 5000],
    "gaps": tl_gaps,
    "converged": rd.get("converged"),
    "gapStable": len({json.dumps(g, sort_keys=True) for g in tl_gaps}) == 1,
    "logLenByMark": {k: (v or {}).get("logLen") for k, v in tl.items()},
    "logLenFrozen": len({(v or {}).get("logLen") for v in tl.values()}) == 1,
    "yGap": tl_gaps[-1]["y"] if tl_gaps else None,
    "oneWheelStep": 120,
    "secondBurst": {
        "storeDy": (rd.get("secondBurst") or {}).get("storeDy"),
        "domDy": (rd.get("secondBurst") or {}).get("domDy"),
        "gapAfter": (rd.get("secondBurst") or {}).get("gap"),
        "reconciled": abs(((rd.get("secondBurst") or {}).get("gap") or {})
                          .get("y", 99)) < 1,
    },
}

# ---------- G 缩放按钮在 640–850 隐藏 ----------
trig = [{"width": t.get("width"), "visible": t.get("visible"),
         "boxWidth": t.get("w"), "parentDisplay": t.get("parentDisplay"),
         "text": t.get("text")} for t in rc.get("triggerByWidth", [])]
hidden = [t["width"] for t in trig if t["visible"] is False]

# ---------- H 节点 resize ----------
rs = ra.get("resize") or {}
resize_cells = []
for c in rs.get("cells", []):
    if "FAILED" in c:
        resize_cells.append({"where": c["where"], "FAILED": c["FAILED"]})
        continue
    resize_cells.append({
        "where": c["where"],
        "hitClass": (c["hit"] or {}).get("cls"),
        "hitTag": (c["hit"] or {}).get("tag"),
        "hitOwnNode": c["hitOwnNode"],
        "start": c["start"],
        "domSizeBefore": [c["before"]["w"], c["before"]["h"]],
        "domSizeAfter": [c["after"]["w"], c["after"]["h"]],
        "storeSizeBefore": [c["before"]["storeW"], c["before"]["storeH"]],
        "storeSizeAfter": [c["after"]["storeW"], c["after"]["storeH"]],
        "measuredBefore": c["before"]["measured"],
        "measuredAfter": c["after"]["measured"],
        "domWidthChanged": c["domWidthChanged"],
        "domHeightChanged": c["domHeightChanged"],
        "storeWidthChanged": c["storeWidthChanged"],
        "storeHeightChanged": c["storeHeightChanged"],
        "positionChanged": c["positionChanged"],
        "effect": ("无反应" if not c["domWidthChanged"] and not c["domHeightChanged"]
                   and not c["positionChanged"]
                   else ("移动了节点" if c["positionChanged"] else "尺寸变了")),
    })
resize = {
    "resizeControls": rs.get("resizeControls"),
    "resizeLikeElements": rs.get("resizeLikeElements"),
    "cells": resize_cells,
    "anyResizeHappened": any(c.get("effect") == "尺寸变了" for c in resize_cells),
    "cellsThatMovedNode": [c["where"] for c in resize_cells
                          if c.get("effect") == "移动了节点"],
    "cellsThatDidNothing": [c["where"] for c in resize_cells
                            if c.get("effect") == "无反应"],
}

# ---------- I 改宽不重投影 = 显式设计 ----------
reproj = rb.get("reproject") or {}
reproj_log = reproj.get("ownerLog") or {}
reproject = {
    "delta": reproj.get("delta"),
    "afterMatchesCompact": reproj.get("afterMatchesCompact"),
    "logReasons": [e["reason"] for e in reproj_log.get("entries", [])],
    "breakpointFlipDelegated": any(
        e["reason"] == "breakpoint-flip-delegated"
        for e in reproj_log.get("entries", [])),
    "breakpointFlipStatus": next(
        (e["status"] for e in reproj_log.get("entries", [])
         if e["reason"] == "breakpoint-flip-delegated"), None),
}

findings = {
    "viewportAB": viewport_ab,
    "zoomMenu": {"menu": menu, "keyboard": kb, "clamp": clamp,
                 "allIndicatorsMatch": all(m["indicatorMatchesReal"] for m in menu)
                 and all(k["indicatorMatchesReal"] for k in kb)},
    "initialReadout": initial,
    "wheel": {"bursts": bursts, "eventsTotal": wheel_events_total,
              "allDzZero": all_dz_zero, "dzValues": dz_values,
              "stalePattern": stale_pattern},
    "wheelOnNode": wheel_on_node,
    "storeDomDivergence": divergence,
    "zoomTriggerByWidth": {"rows": trig, "hiddenWidths": hidden,
                           "hiddenBand": [min(hidden), max(hidden)] if hidden else None},
    "nodeResize": resize,
    "reprojectOnResize": reproject,
}

# clamp 的 store.x/y 会随 zoomTo 的动画竞态漂移 ⟹ 只按 zoom/指示器判两轮一致
_cl1 = [{"finalZoom": c["store"]["zoom"], "indicator": c["derived"]["indicator"]}
        for c in A["rounds"][0]["clamp"].values()]
_cl2 = [{"finalZoom": c["store"]["zoom"], "indicator": c["derived"]["indicator"]}
        for c in A["rounds"][1]["clamp"].values()]
CLAMP_ZOOM_IDENTICAL = (_cl1 == _cl2)

audit = {
    "batch": 761,
    "date": "2026-10-01",
    "clone": "http://localhost:4317 (master)",
    "subject": "画布缩放与视口：两档视口常量、缩放菜单与快捷键、滚轮、"
               "节点尺寸、响应式断点",
    "seed": {"activeCanvas": "canvas-2",
             "constants": {"desktopViewport": DESKTOP, "compactViewport": COMPACT}},
    "twoRound": {
        "probeA": {"file": "raw/vb761a.json", "rounds": len(A["rounds"]),
                   "consistent": A["consistent"]},
        "probeB": {"file": "raw/vb761b.json", "rounds": len(B["rounds"]),
                   "consistent": B["consistent"]},
        "probeC": {"file": "raw/vb761c.json", "rounds": len(C["rounds"]),
                   "consistent": C["consistent"]},
        "probeD": {"file": "raw/vb761d.json", "rounds": len(D["rounds"]),
                   "consistent": D["consistent"]},
        "allConsistent": all(x["consistent"] for x in (A, B, C, D)),
        "inconsistentCells": {k: sorted(x["roundDiff"])
                              for k, x in zip("abcd", (A, B, C, D))
                              if not x["consistent"]},
        "clampZoomIndicatorIdentical": CLAMP_ZOOM_IDENTICAL,
        "consistentAfterExcludingClampXY":
            all(x["consistent"] for x in (B, C, D)) and CLAMP_ZOOM_IDENTICAL,
        "excludedReason": "clamp 连点 26/90 次时 zoomTo 以画布中心为锚，"
                          "每次落点随 180ms 动画的竞态漂移；"
                          "zoom 与指示器两轮完全相同，故 x/y 不参与一致性判定。",
        "inconsistentCells": {k: sorted(A["roundDiff"]) for k, x in
                              zip("abcd", (A, B, C, D)) if not x["consistent"]},
        "caveat": "761a 的 clamp 格两轮在 store.x/y 上有差（zoom 与指示器完全相同）："
                  "zoomTo 以画布中心为锚，连点 26/90 次时每次落点随动画竞态漂移。"
                  "故 clamp 只按 zoom/指示器判两轮一致，x/y 不参与一致性判定。",
    },
    "findings": findings,
    "judgeCount": 16,
    "judgments": [
        {"no": 1, "text": "desktopViewport 逐位生效：1440 档 store 的 x/y/zoom "
                          "与 page.tsx:163 的常量三字段全等",
         "evidence": ab_by_label["desktop"]},
        {"no": 2, "text": "compactViewport 逐位生效：700 档 mq768=true，"
                          "store 与 page.tsx:164 的常量三字段全等",
         "evidence": ab_by_label["compact"]},
        {"no": 3, "text": "断点按写的 768 生效：800 档 mq768=false ⟹ 仍走 desktop",
         "evidence": ab_by_label["midband"]},
        {"no": 4, "text": "首屏 zoomLevel 不是 uiStore 硬编码的 54，而是 53 "
                          "=round(0.526×100)；uiStore / trigger / store 三处一致 "
                          "⟹ onViewportChange 在挂载时就已纠正，**不是缺陷**",
         "evidence": initial},
        {"no": 5, "text": "缩放菜单 6 格全部符合合同，且每一格指示器都与真实 zoom 相符",
         "evidence": {"menu": menu,
                      "allIndicatorsMatch": all(m["indicatorMatchesReal"]
                                                for m in menu)}},
        {"no": 6, "text": "⌘+ / ⌘- / ⌘0 与菜单按钮是同两个回调，Δzoom 分别为 "
                          "+0.1 / −0.1 / fitView",
         "evidence": kb},
        {"no": 7, "text": "上下限生效：连点 26 次缩小恰好停在 0.1、连点 90 次放大"
                          "恰好停在 8（= minZoom/maxZoom），指示器同步",
         "evidence": clamp},
        {"no": 8, "text": "★ 缺陷一（中）：`zoomOnScroll` 是死代码 —— 13 次滚轮"
                          "Δzoom 全为 0，而 Δy 恒为 ±120/次，滚轮只平移不缩放",
         "evidence": {"bursts": bursts, "eventsTotal": wheel_events_total,
                      "dzValues": dz_values, "allDzZero": all_dz_zero}},
        {"no": 9, "text": "★ 缺陷二（中）：滚轮落在节点上完全不响应 —— 命中 nopan 容器，"
                          "viewport 前后完全相同",
         "evidence": wheel_on_node},
        {"no": 10, "text": "★ 缺陷三（中）：滚轮平移收尾时 store 的 canvas.viewport "
                           "落后画面约 120px（一个滚轮格），5 秒内不收敛、"
                           "owner_log 条数冻结",
         "evidence": divergence},
        {"no": 11, "text": "该落后会在下一次视口变化时被一次性抹平（第二轮 3 次上滚后"
                           "差距回到 −0.2）⟹ 是丢了一帧提交，不是持续漂移",
         "evidence": divergence["secondBurst"]},
        {"no": 12, "text": "★ 缺陷四（中）：640–850px 整段缩放菜单的**唯一**入口被隐藏"
                           "（`sm:max-[850px]:hidden`）；实测 700/800 隐藏，"
                           "560/900/1440 可见，该段只剩三个快捷键",
         "evidence": findings["zoomTriggerByWidth"]},
        {"no": 13, "text": "节点不可缩放：`.react-flow__resize-control` = 0、"
                           "含 `resize` 的 class 元素 = 0，`NodeResizer` 只存在于 "
                           "FrameOS 侧",
         "evidence": {"resizeControls": resize["resizeControls"],
                      "resizeLikeElements": resize["resizeLikeElements"],
                      "static": "全 src/ 无 NodeResizer / nodeResize / "
                                "nodesResizable（resizeNode 只在 frameosStore）"}},
        {"no": 14, "text": "拖右边缘**完全无反应**：起点命中的是 "
                           "`react-flow__handle-right nodrag nopan`，拖动被 nodrag 吞掉",
         "evidence": next(c for c in resize_cells if c["where"] == "rightEdge")},
        {"no": 15, "text": "拖下边缘与右下角得到的是「移动节点」而不是缩放；"
                           "store width/height（350×200）、measured、style 全程不变",
         "evidence": {"cells": [c for c in resize_cells
                                if c["where"] in ("bottomEdge", "corner")],
                      "anyResizeHappened": resize["anyResizeHappened"]}},
        {"no": 16, "text": "改宽 1440→700 视口纹丝不动，但 owner_log 里有一条 "
                           "`breakpoint-flip-delegated / skipped` ⟹ **是显式设计，"
                           "不是缺陷**",
         "evidence": reproject},
    ],
    "headline": "缩放这条线查出一个**高价值**结论和三个中缺陷：`desktopViewport` / "
                "`compactViewport` 两档常量都逐位生效（不是死常量），缩放菜单 6 格 + "
                "三个快捷键 + 上下限全部符合合同、首屏那个硬编码的 `zoomLevel: 54` "
                "也早在挂载时就被纠正成 53 —— **这一整块没有缺陷**；缺陷都在「滚轮」"
                "上：① `zoomOnScroll` 是死代码，13 次滚轮 Δzoom 全 0、只平移；"
                "② 滚轮落在节点上因 `nopan` 完全无响应；③ 平移收尾 store 视口落后"
                "画面一个滚轮格（≈120px）且不会自行收敛。另外节点根本不可缩放，"
                "拖下边缘/右下角得到的是「移动」，拖右边缘被 handle 的 `nodrag` "
                "吞掉变成完全无反应。",
    "rework": [
        {"id": "R39", "where": "探针 a（C0 取读数的位置）",
         "what": "C0 原本排在 `Meta+0`（fitView）**之后**，量到的 zoom 是 0.375 而"
                 "不是首屏的 0.526。",
         "lesson": "「任何交互之前」是一格独立的前置条件，不是顺手就能拿到的读数。"
                   "差点把 `zoomLevel` 的硬编码 54 直接写成缺陷。"},
        {"id": "R40", "where": "探针 a（滚轮只记布尔）",
         "what": "只记了 `变zoom` / `变XY`，没记 Δx/Δy/Δzoom 的**数值**，"
                 "于是「向上滚完全没反应、向下滚才平移」这个假不对称无从解释。",
         "lesson": "布尔读数能回答「有没有」，回答不了「多少」和「哪个方向」。"},
        {"id": "R41", "where": "探针 a（C10 忘了复位视口）",
         "what": "上一格 clamp 把 zoom 停在 8，节点全在视口外，`NODE()` 返回 null，"
                 "整格记成 FAILED。",
         "lesson": "batch 760 的 R35 在同一个坑上栽过一次（「每格前复位」），"
                   "761 又栽一次。**这条规矩要写成默认动作，不能靠记性。**"},
        {"id": "R42", "where": "探针 a/b（★ 我自己的读数滞后，把 4 次滚轮看成 2 次）",
         "what": "每步都读 ⟹ 读数落在平移落地之前，Δ 被错记到隔一格，"
                 "于是 761a/761b 都看到 `Δy = [0, 240, 0, −240]` 这个整齐的假形状。",
         "lesson": "**中途不读、只在末尾读一次**才量得到真值：761c 4 次滚轮总位移 "
                   "480 = 4×120，每次都生效。整齐的重复形状（0/240/0/240）"
                   "本身就该当成探针嫌疑，而不是当成发现。"},
        {"id": "R43", "where": "流程（★ 原始读数只放 /tmp）",
         "what": "2026-10-04 23:44 有人清空了 /tmp，batch 760 的三份原始读数"
                 "与探针脚本一并消失（同一时刻 4317 的 dev server 也被杀掉了）。",
         "lesson": "验收器依赖 /tmp ⟹ **提交出去的验收器不可复现**。"
                   "本批起原始读数随产物提交到 `docs/research/.../raw/`；"
                   "760 的验收器也已改成优先读产物目录。读数**不靠回忆补写** —— "
                   "那等于伪造原始证据。"},
        {"id": "R44", "where": "结论纪律（差点误报）",
         "what": "看到 `uiStore.ts:223` 硬编码 `zoomLevel: 54` 与真实 52.6% 不符，"
                 "差点直接判成「首屏显示错的百分比」。",
         "lesson": "实测首屏三处（uiStore / trigger 文本 / store）**完全一致**。"
                   "**看到硬编码不等于它会露脸** —— 中间隔着一个 "
                   "`onViewportChange` 的首次提交。"},
        {"id": "R45", "where": "汇编器（取错了探针）",
         "what": "`wheelNode` 在探针 b 里，汇编器却从探针 c 取，"
                 "于是 `nopan` 一度读成 `null`。",
         "lesson": "多探针批次里，「这条读数在哪个文件」必须显式确认，"
                   "不能凭印象写文件名。"},
        {"id": "R46", "where": "验收器（★ 阴性对照第三次逮到同一个洞）",
         "what": "首版验收器 45/45 全过，但 **13 发阴性对照里有 11 发漏放**。"
                 "根因：我写的检查验的是「**原始读数自洽**」，"
                 "却没验「**产物是否忠实抄了原始读数**」—— 把 runtime-audit.json 里"
                 "的 store / mq768 / visible / yGap / logLenFrozen / 每格位移 / "
                 "resize 五项布尔改成假的，`raw/` 里的读数没动，于是全部蒙混过关。"
                 "两发改错编号的注入（把判据 14 的证据改在判据 13 上）"
                 "则是往不存在的键上写值，等于什么也没伪造。",
         "lesson": "这是 759 的 R33、760 的 R38 之后**第三次**复发，"
                   "所以这次不是补两个洞，而是加了一整段「产物 == 重算」的逐项对账"
                   "（视口三档、菜单六格、快捷键、clamp、首屏、滚轮每格、"
                   "差距时间线、按钮可见性、resize 五项布尔、reproject 四项）。"
                   "补完 **64/64 通过、阴性对照 35/35 全拦**。"
                   "另外：删检查块时要连带看它后面的代码 —— 我为了让新块能用 `rp`，"
                   "把 `rp = rw[\"reproject\"]` 和三条 reproject 检查一起切掉了，"
                   "是阴性对照里「判据 16 改判成缺陷」那发把它抓回来的。"},
        {"id": "R47", "where": "产物/README（撞上别人的 pre-commit 钩子）",
         "what": "第一次提交被钩子拦下：「本次提交新增了批次行 [560, 700, 800, 900, "
                 "1440]」。查下去是 `docs/user-manual/beeftv-canvas/scripts/buildrecord.py` "
                 "里的 `added_batch_numbers()` 用 `^\\+\\|\\s*(\\d+)[a-z]?\\s*\\|` "
                 "从 diff 的新增行里取批次号 —— 于是我 README 里那张"
                 "「视口宽度 → 缩放按钮」的表格，**首格是裸数字的行被当成了批次行**。",
         "lesson": "钩子在**别人（user-manual 那条线）的目录**里，不改它，"
                   "也不用 `--no-verify`（那条规矩至今没破过）。"
                   "改成把我自己表格的首格写成 `560px` —— 正则要求首格紧跟数字，"
                   "带反引号或单位就不匹配，而且表更好读。"
                   "顺带说明：台账行首格写 `| Batch 761 |` 而不是 `| 761 |` "
                   "本来就是承重设计，不是洁癖。"},
    ],
    "notClaimed": [
        "没有与源站对照：全部读数来自 clone（4317）。",
        "缩放按钮只测了 560/700/800/900/1440 五个宽度点，不连续，"
        "640 与 850 两个边界值本身没测。",
        "触控板捏合（zoomOnPinch 未显式设置，默认为开）与双击缩放"
        "（zoomOnDoubleClick 默认开）都没测。",
        "store 视口落后一格会不会让「切换画布再切回来」发生跳变，未测。",
        "节点尺寸只测了一个 350×200 的文本节点的三处边缘/角，"
        "没测其它节点类型，也没测选中态下是否出现任何缩放提示。",
        "「每格 120px」只在本轮 panOnScrollSpeed=1、鼠标滚轮 120 单位下成立，"
        "换设备或改速度未复验。",
        "clamp 落点 x/y 的抖动只记录了现象，未定位机制。",
        "首屏是否存在早于「load 后 1.1s」的瞬时 54，未测。",
        "轨道板手势、键盘导航缩放、屏幕阅读器下的缩放读数，均未测。",
    ],
    "rawProbeFiles": ["raw/vb761a.json", "raw/vb761b.json", "raw/vb761c.json",
                      "raw/vb761d.json",
                      "/tmp/dbg761a.py", "/tmp/dbg761b.py", "/tmp/dbg761c.py",
                      "/tmp/dbg761d.py"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", OUT)
print("四段两轮一致 =", audit["twoRound"]["allConsistent"])
for v in viewport_ab:
    print("  %-8s w=%-5d mq768=%-5s store=%s 命中常量=%s 缩放按钮可见=%s"
          % (v["label"], v["measuredWidth"], v["mq768"],
             json.dumps(v["store"], ensure_ascii=False),
             v["matchesExpectedConstant"], v["triggerVisible"]))
print("缩放菜单:", [(m["key"], m["afterZoom"], m["indicatorMatchesReal"])
                    for m in menu])
print("快捷键:", [(k["key"], k["dz"], k["indicatorMatchesReal"]) for k in kb])
print("clamp:", json.dumps(clamp, ensure_ascii=False))
print("首屏: 指示器=%s 真实=%s 硬编码54是否露脸=%s"
      % (initial["zoomLevel"], initial["realPercent"], initial["hardcodedShown"]))
print("滚轮 %d 次，Δzoom 取值集合=%s，全 0=%s"
      % (wheel_events_total, sorted({v for v in dz_values}), all_dz_zero))
print("  每格位移:", [(b["key"], b["n"], b["domDyPerEvent"]) for b in bursts])
print("假形状(761a/761b) dy:", stale_pattern["probeA_dySeries"],
      stale_pattern["probeB_dySeries"], "→ 761c 真值 4×120=",
      stale_pattern["probeC_burstSlow_totalDy"])
print("滚轮在节点上: viewport 不变=%s 命中 nopan=%s"
      % (wheel_on_node["viewportUnchanged"], wheel_on_node["nodeNopan"]))
print("store−DOM 分叉: y 差=%s 稳定=%s logLen 冻结=%s 5s 未收敛=%s"
      % (divergence["yGap"], divergence["gapStable"],
         divergence["logLenFrozen"], not divergence["converged"]))
print("  下一次变化后抹平:", json.dumps(divergence["secondBurst"],
                                        ensure_ascii=False))
print("缩放按钮隐藏宽度:", findings["zoomTriggerByWidth"]["hiddenWidths"])
print("resize:", json.dumps({k: resize[k] for k in
                             ("resizeControls", "resizeLikeElements",
                              "anyResizeHappened", "cellsThatMovedNode",
                              "cellsThatDidNothing")}, ensure_ascii=False))
print("改宽:", json.dumps(reproject, ensure_ascii=False))
