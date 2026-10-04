"""batch 761 验收器：画布缩放与视口（两档视口常量 / 缩放菜单 / 滚轮 / 节点尺寸 / 断点）

三层结构（与 753–760 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
  2. **产物层** —— 判据条数、四段探针两轮一致性、证据链、返工条目、不声称清单
  3. **原始读数交叉核对** —— 从 `docs/research/.../raw/` 下四份原始输出
     **按正确键名重算**全部派生量，与产物逐项对账。缺失时**判失败而不是通过**。

⚠ 与 760 的两处结构性教训直接相关，这里都做了：
  - 派生量必须能由**被派生的原始字段**现算得出（R34）
  - 同一事实存两份时，**两份都要守住**（R33 / 760 的 R38）

⚠ 本批原始读数**随产物提交**在 `raw/` 下，不再只放 /tmp
  （/tmp 于 2026-10-04 23:44 被清空，760 的读数就是这么丢的 —— 见 R43）。

判据 **16 条**（探针 a/b/c/d 各跑满两轮；a 的 clamp 格按 zoom/指示器判一致，
x/y 因 zoomTo 锚点漂移不参与判定，理由写在 twoRound.excludedReason）。
"""
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch761-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def static_side():
    page = src("src/app/page.tsx")
    ui = src("src/store/uiStore.ts")
    bt = src("src/components/BottomToolbar.tsx")

    all_src = []
    for p in sorted((ROOT / "src").rglob("*.ts*")):
        try:
            all_src.append(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    joined = "\n".join(all_src)

    return {
        # ① 滚轮：两个开关同时开 + panActivationKeyCode 被置 null
        "panOnScroll": "\n            panOnScroll\n" in page,
        "zoomOnScroll": "            zoomOnScroll\n" in page,
        "panOnScrollSpeed": "panOnScrollSpeed={1}" in page,
        "panActivationKeyNull": "panActivationKeyCode={null}" in page,
        "minMaxZoom": "minZoom={0.1}" in page and "maxZoom={8}" in page,
        "zoomByClamp": "Math.min(8, Math.max(0.1, viewport.zoom + delta))" in page,
        "zoomByDelta": "const zoomBy = useCallback((delta: number) => {" in page,
        "fitViewPadding": 'fitView({ padding: 0.12, duration: 260 })' in page,
        "metaZoomKeys": ('event.key === "+" || event.key === "="' in page
                         and 'event.key === "-"' in page
                         and "fitView();" in page),
        # ② 两档视口常量
        "desktopConst": "const desktopViewport = { x: -583.8, y: 260.8, "
                        "zoom: 0.526 };" in page,
        "compactConst": "const compactViewport = { x: 17, y: 128, "
                        "zoom: 0.28 };" in page,
        "desktopUses": page.count("desktopViewport"),
        "compactUses": page.count("compactViewport"),
        "mq768Uses": page.count('(max-width: 768px)'),
        "innerWidth768": "window.innerWidth <= 768" in page,
        "ownerLogHook": "window.__libtv_viewport_owner_log = []" in page,
        "breakpointDelegated": "breakpoint-flip-delegated" in page,
        # ③ 缩放菜单
        "zoomTriggerHook": 'data-viewport-menu-trigger="zoom"' in bt,
        "zoomTriggerCount": joined.count('data-viewport-menu-trigger="zoom"'),
        "zoomMenuHiddenClass": "relative sm:max-[850px]:hidden" in bt,
        "zoomActions": [a for a in ("in", "out", "fit")
                        if 'data-zoom-action="%s"' % a in bt],
        "zoomPresetDynamic": "data-zoom-action={option.value}" in bt,
        "zoomPresetValues": [v for v in ('value: "50"', 'value: "100"',
                                         'value: "800"') if v in bt],
        "zoomPresetZooms": [z for z in ("{ zoom: 0.5,", "{ zoom: 1,",
                                        "{ zoom: 8,") if z in bt],
        "zoomCurrentHook": "data-zoom-current" in bt,
        "hardcodedZoomLevel": "zoomLevel: 54," in ui,
        # ④ 节点尺寸
        "nodeResizerAnywhere": "NodeResizer" in joined,
        "nodesResizableProp": "nodesResizable" in joined,
        "resizeNodeOnlyFrameos": (
            "resizeNode" in joined
            and "resizeNode" in src("src/store/frameosStore.ts")
            and "resizeNode" not in src("src/store/canvasStore.ts")),
    }


def raw_side():
    """从 raw/ 下四份原始输出现算。缺文件 → 抛错（判失败而非通过）。"""
    data = {}
    for k in "abcd":
        p = RAWDIR / ("vb761%s.json" % k)
        if not p.exists():
            raise FileNotFoundError(str(p))
        data[k] = json.loads(p.read_text(encoding="utf-8"))
    A, B, C, D = (data[k]["rounds"][0] for k in "abcd")

    cl1 = [{"zoom": c["store"]["zoom"], "ind": c["derived"]["indicator"]}
           for c in A["clamp"].values()]
    cl2 = [{"zoom": c["store"]["zoom"], "ind": c["derived"]["indicator"]}
           for c in data["a"]["rounds"][1]["clamp"].values()]

    bursts = []
    for key in ("burstSlow", "burstFast", "burstDown"):
        b = C.get(key) or {}
        if "FAILED" in b:
            continue
        bursts.append({"key": key, "n": b["n"], "storeDz": b["storeDz"],
                       "domDz": b["domDz"], "storeDy": b["storeDy"],
                       "domDy": b["domDy"], "acceptedDelta": b["acceptedDelta"]})

    tl = D.get("timeline") or {}
    gaps = D.get("gapSeries") or []
    reprojLog = (B.get("reproject") or {}).get("ownerLog") or {}

    return {
        "rawFlags": {k: data[k]["consistent"] for k in "abcd"},
        "rawDiffKeys": {k: sorted(data[k]["roundDiff"]) for k in "abcd"},
        "clampZoomIndicatorIdentical": cl1 == cl2,
        "constants": data["b"]["constants"],
        # 两档视口（自己按常量重算「是否逐位相等」，不信产物的 matchesConstant）
        "viewportMatch": {
            v["label"]: {
                "measuredWidth": v["measured"]["innerWidth"],
                "mq768": v["measured"]["mq768"],
                "store": v["store"],
                "expected": v["expectedConstant"],
                "allFieldsEqual": all(
                    abs(v["store"][f] - v["expectedConstant"][f]) <= 0.001
                    for f in ("x", "y", "zoom")) if v["store"] else False,
                "triggerVisible": bool((v["triggerVisible"] or {}).get("w")),
            } for v in B["viewports"]},
        "menu": [{"key": a["key"], "afterZoom": a["after"]["zoom"],
                  "ind": a["derived"]["indicator"],
                  "indOk": a["derived"]["indicatorMatchesReal"]}
                 for a in A["actions"]],
        "keyboard": [{"key": k["key"], "dz": k["delta"]["dz"],
                      "indOk": k["derived"]["indicatorMatchesReal"]}
                     for k in A["keyboard"]],
        "clamp": {n: {"finalZoom": c["store"]["zoom"],
                      "ind": c["derived"]["indicator"]}
                  for n, c in A["clamp"].items()},
        "initial": {"zoomLevel": A["C0_initial"]["vp"]["zoomLevel"],
                    "storeZoom": A["C0_initial"]["vp"]["store"]["zoom"],
                    "triggerText": A["C0_initial"]["vp"]["triggerText"],
                    "indOk": A["C0_initial"]["derived"]["indicatorMatchesReal"],
                    "trigOk": A["C0_initial"]["derived"]["triggerMatchesReal"]},
        "wheel": {"bursts": bursts,
                  "eventsTotal": sum(b["n"] for b in bursts),
                  "allDzZero": all(abs(b["storeDz"]) < 1e-9
                                   and abs(b["domDz"]) < 1e-9
                                   for b in bursts),
                  "dzSet": sorted({b["storeDz"] for b in bursts}),
                  "perEventDy": {b["key"]: round(b["domDy"] / b["n"], 2)
                                 for b in bursts}},
        "wheelStale": {"a": [(s.get("delta") or {}).get("dy")
                             for s in A["wheel"]["steps"] if s.get("delta")],
                       "b": B["wheelPane"].get("dyValues"),
                       "cTotal": C["burstSlow"]["domDy"],
                       "cEvents": C["burstSlow"]["n"]},
        "wheelNode": {"nopan": (B["wheelNode"].get("point") or {}).get("nopan"),
                      "unchanged": B["wheelNode"].get("before")
                      == B["wheelNode"].get("after")},
        "divergence": {
            "marks": sorted(tl.keys()),
            "gaps": gaps,
            "gapStable": len({json.dumps(g, sort_keys=True)
                              for g in gaps}) == 1,
            "logLenFrozen": len({(v or {}).get("logLen")
                                 for v in tl.values()}) == 1,
            "converged": D.get("converged"),
            "yGap": gaps[-1]["y"] if gaps else None,
            "secondGapY": ((D.get("secondBurst") or {})
                           .get("gap") or {}).get("y"),
            "secondStoreDy": (D.get("secondBurst") or {}).get("storeDy"),
            "secondDomDy": (D.get("secondBurst") or {}).get("domDy"),
        },
        "triggerByWidth": {t["width"]: t["visible"]
                           for t in C.get("triggerByWidth", [])},
        "resize": {"controls": (A.get("resize") or {}).get("resizeControls"),
                   "likeElements": (A.get("resize") or {})
                   .get("resizeLikeElements"),
                   "cells": {c["where"]: {
                       "cls": (c.get("hit") or {}).get("cls"),
                       "domWChanged": c.get("domWidthChanged"),
                       "domHChanged": c.get("domHeightChanged"),
                       "storeWChanged": c.get("storeWidthChanged"),
                       "storeHChanged": c.get("storeHeightChanged"),
                       "positionChanged": c.get("positionChanged")}
                       for c in (A.get("resize") or {}).get("cells", [])
                       if "FAILED" not in c}},
        "reproject": {
            "delta": (B.get("reproject") or {}).get("delta"),
            "reasons": [e["reason"] for e in reprojLog.get("entries", [])],
            "delegated": any(e["reason"] == "breakpoint-flip-delegated"
                             for e in reprojLog.get("entries", [])),
            "delegatedStatus": next(
                (e["status"] for e in reprojLog.get("entries", [])
                 if e["reason"] == "breakpoint-flip-delegated"), None),
        },
    }


def run_checks(a, st, rw):
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    try:
        _body(a, st, rw, ck)
    except Exception as e:          # 检查器自身崩掉 ⟹ 记成失败，不许伪装成通过
        ck("检查器自身未因结构破坏而崩溃", False, repr(e))
    return checks


def _body(a, st, rw, ck):
    J = {j["no"]: j for j in a["judgments"]}
    a1 = a["judgments"]
    f = a["findings"]

    # ================= 静态层 =================
    ck("静态：panOnScroll 与 zoomOnScroll 同时开，且 panActivationKeyCode 被置 null",
       st["panOnScroll"] and st["zoomOnScroll"] and st["panActivationKeyNull"])
    ck("静态：panOnScrollSpeed={1}，minZoom=0.1 / maxZoom=8",
       st["panOnScrollSpeed"] and st["minMaxZoom"])
    ck("静态：zoomBy 自己把 zoom 夹在 [0.1, 8]",
       st["zoomByDelta"] and st["zoomByClamp"])
    ck("静态：fitView 用 padding 0.12；⌘+/⌘-/⌘0 三键都接上了",
       st["fitViewPadding"] and st["metaZoomKeys"])
    ck("静态：两档视口常量原文都在，且各被引用多次（不是死常量）",
       st["desktopConst"] and st["compactConst"]
       and st["desktopUses"] >= 3 and st["compactUses"] >= 3,
       [st["desktopUses"], st["compactUses"]])
    ck("静态：断点判据就是 (max-width: 768px)，且 viewport 里也有一份 innerWidth<=768",
       st["mq768Uses"] >= 2 and st["innerWidth768"], st["mq768Uses"])
    ck("静态：owner_log 钩子与 breakpoint-flip-delegated 都在源码里",
       st["ownerLogHook"] and st["breakpointDelegated"])
    ck("静态：data-viewport-menu-trigger 全 src/ 只出现一次（缩放菜单唯一入口）",
       st["zoomTriggerCount"] == 1, st["zoomTriggerCount"])
    ck("静态：缩放按钮容器 class 就是 relative sm:max-[850px]:hidden",
       st["zoomMenuHiddenClass"])
    ck("静态：缩放菜单动作钩子齐全 —— 三个字面量（in/out/fit）+ 三档动态预设"
       "（option.value = 50/100/800，zoom 0.5/1/8）+ data-zoom-current",
       len(st["zoomActions"]) == 3 and st["zoomPresetDynamic"]
       and len(st["zoomPresetValues"]) == 3
       and len(st["zoomPresetZooms"]) == 3 and st["zoomCurrentHook"],
       [st["zoomActions"], st["zoomPresetValues"], st["zoomPresetZooms"]])
    ck("静态：uiStore 里那个硬编码的 zoomLevel: 54 确实存在",
       st["hardcodedZoomLevel"])
    ck("静态：LibTV 侧无 NodeResizer / nodesResizable，resizeNode 只在 FrameOS",
       (not st["nodeResizerAnywhere"]) and (not st["nodesResizableProp"])
       and st["resizeNodeOnlyFrameos"],
       [st["nodeResizerAnywhere"], st["nodesResizableProp"],
        st["resizeNodeOnlyFrameos"]])

    # ================= 产物层 =================
    ck("产物：判据 16 条且编号连续 1..16",
       len(a1) == 16 and a["judgeCount"] == 16 and sorted(J) == list(range(1, 17)),
       sorted(J))
    ck("产物：写明四段探针，并如实记录 a 的 clamp 格两轮有差",
       set(a["twoRound"]["inconsistentCells"]) == {"a"}
       and a["twoRound"]["inconsistentCells"]["a"] == ["clamp"]
       and "zoomTo" in a["twoRound"]["excludedReason"],
       a["twoRound"]["inconsistentCells"])
    ck("产物：排除 clamp 的 x/y 之后其余判定为一致",
       a["twoRound"]["consistentAfterExcludingClampXY"] is True)
    ck("产物：返工 9 条，含 R42（读数滞后）、R43（/tmp 被清空）、"
       "R46（阴性对照复发）与 R47（撞上别人的 pre-commit 正则）",
       len(a["rework"]) == 9
       and any(r["id"] == "R42" for r in a["rework"])
       and any(r["id"] == "R43" for r in a["rework"])
       and any("480" in r["lesson"] for r in a["rework"])
       and any("不可复现" in r["lesson"] for r in a["rework"])
       and any(r["id"] == "R46" for r in a["rework"])
       and any("第三次" in r["lesson"] for r in a["rework"])
       and any(r["id"] == "R47" for r in a["rework"])
       and any("--no-verify" in r["lesson"] for r in a["rework"]))
    ck("产物：不声称 ≥ 9 条且含「没有与源站对照」",
       len(a["notClaimed"]) >= 9
       and any("源站" in s for s in a["notClaimed"]))
    ck("产物：原始读数登记为随产物提交的 raw/ 路径（不再只写 /tmp）",
       all(p.startswith("raw/") for p in a["rawProbeFiles"]
           if p.endswith(".json")))

    # ================= 原始读数交叉核对 =================
    vm = rw["viewportMatch"]
    ck("原始：三档视口逐位相等由重算确认（不信产物的 matchesConstant）",
       all(v["allFieldsEqual"] for v in vm.values()), vm)
    ck("原始：700 档 mq768 为 true、1440/800 为 false（断点按 768 生效）",
       vm["compact"]["mq768"] is True and vm["desktop"]["mq768"] is False
       and vm["midband"]["mq768"] is False,
       {k: v["mq768"] for k, v in vm.items()})
    ck("原始：两档常量与源码字面量一致",
       vm["desktop"]["expected"] == rw["constants"]["desktopViewport"]
       and vm["compact"]["expected"] == rw["constants"]["compactViewport"])
    ck("原始：产物判据 1/2/3 的证据与重算一致",
       J[1]["evidence"]["store"] == vm["desktop"]["store"]
       and J[2]["evidence"]["store"] == vm["compact"]["store"]
       and J[3]["evidence"]["mq768"] == vm["midband"]["mq768"])
    ck("原始：clamp 的 zoom 与指示器两轮完全相同（排除 x/y 的依据成立）",
       rw["clampZoomIndicatorIdentical"] is True)

    ck("原始：菜单六格的 afterZoom 与重算一致且指示器全对",
       [(m["key"], m["afterZoom"], m["indicatorMatchesReal"])
        for m in f["zoomMenu"]["menu"]]
       == [(m["key"], m["afterZoom"], m["indOk"]) for m in rw["menu"]]
       and all(m["indOk"] for m in rw["menu"]))
    ck("原始：菜单六格的 key 集合与源码钩子完全对应",
       {m["key"] for m in rw["menu"]}
       == {"in", "out", "fit", "50", "100", "800"})
    ck("原始：⌘+ 是 +0.1、⌘- 是 −0.1、⌘0 改变 zoom，三格指示器都对",
       [(k["key"], k["dz"], k["indicatorMatchesReal"])
        for k in f["zoomMenu"]["keyboard"]]
       == [(k["key"], k["dz"], k["indOk"]) for k in rw["keyboard"]]
       and rw["keyboard"][0]["dz"] == 0.1
       and rw["keyboard"][1]["dz"] == -0.1
       and rw["keyboard"][2]["dz"] != 0)
    ck("原始：clamp 下限恰好 0.1、上限恰好 8（= minZoom/maxZoom）",
       rw["clamp"]["min"]["finalZoom"] == 0.1
       and rw["clamp"]["max"]["finalZoom"] == 8
       and f["zoomMenu"]["clamp"]["min"]["finalZoom"] == 0.1
       and f["zoomMenu"]["clamp"]["max"]["finalZoom"] == 8)

    ini = rw["initial"]
    ck("原始：首屏 zoomLevel 不是硬编码的 54，且三处一致",
       ini["zoomLevel"] != 54 and ini["indOk"] and ini["trigOk"]
       and ini["triggerText"] == "%d%%" % ini["zoomLevel"]
       and ini["zoomLevel"] == round(ini["storeZoom"] * 100),
       ini)
    ck("原始：产物判据 4 的「硬编码未露脸」与重算一致",
       J[4]["evidence"]["hardcodedShown"] is False
       and J[4]["evidence"]["zoomLevel"] == ini["zoomLevel"])

    wh = rw["wheel"]
    ck("原始：滚轮事件数与 Δzoom 取值（应为 13 次、全 0）",
       wh["eventsTotal"] == 13 and wh["allDzZero"] and wh["dzSet"] == [0.0], wh)
    ck("原始：产物判据 8 的 dzValues 与重算一致（按取值集合口径）",
       sorted(set(J[8]["evidence"]["dzValues"])) == wh["dzSet"]
       and len(J[8]["evidence"]["dzValues"]) == len(wh["bursts"])
       and J[8]["evidence"]["eventsTotal"] == wh["eventsTotal"],
       [J[8]["evidence"]["dzValues"], wh["dzSet"]])
    ck("原始：每格位移恒为 ±120（panOnScrollSpeed=1）",
       sorted({abs(v) for v in wh["perEventDy"].values()}) == [120.0],
       wh["perEventDy"])
    ck("原始：★ 761a/761b 的假形状是 [0,240,0,-240]，761c 真值 4 次共 480",
       rw["wheelStale"]["a"] == [0.0, 240.0, 0.0, -240.0]
       and rw["wheelStale"]["b"] == [0.0, 240.0, 0.0, -240.0]
       and rw["wheelStale"]["cEvents"] == 4
       and rw["wheelStale"]["cTotal"] == 480,
       rw["wheelStale"])
    ck("原始：产物把这段假形状原样留在产物里（没有偷偷抹掉）",
       f["wheel"]["stalePattern"]["probeA_dySeries"] == [0.0, 240.0, 0.0, -240.0]
       and f["wheel"]["stalePattern"]["probeC_burstSlow_totalDy"] == 480)
    ck("原始：滚轮落在节点上命中 nopan，且 viewport 前后完全相同",
       rw["wheelNode"]["nopan"] is True and rw["wheelNode"]["unchanged"] is True,
       rw["wheelNode"])
    ck("原始：产物判据 9 的证据与重算一致",
       J[9]["evidence"]["viewportUnchanged"] is True
       and J[9]["evidence"]["nodeNopan"] == rw["wheelNode"]["nopan"])

    dv = rw["divergence"]
    ck("原始：store 与 DOM 的视口差在五个时点上恒定（不收敛）",
       len(dv["gaps"]) == 5 and dv["gapStable"] and dv["converged"] is False
       and abs(dv["yGap"] - 119.8) < 0.05, dv)
    ck("原始：五个时点的 owner_log 条数冻结（不会再有提交）",
       dv["logLenFrozen"] is True)
    ck("原始：下一次视口变化后差距被抹平（第二轮 3 次上滚后 |gap| < 1）",
       dv["secondStoreDy"] == 240 and dv["secondDomDy"] == 360
       and abs(dv["secondGapY"]) < 1, dv)
    ck("原始：产物判据 10/11 的差距与重算一致",
       J[10]["evidence"]["yGap"] == dv["yGap"]
       and J[10]["evidence"]["converged"] == dv["converged"]
       and J[11]["evidence"]["gapAfter"]["y"] == dv["secondGapY"])

    tb = rw["triggerByWidth"]
    ck("原始：缩放按钮只在 700/800 隐藏，560/900/1440 可见",
       {w: v for w, v in tb.items()
        if v is False} == {700: False, 800: False}
       and tb[560] is True and tb[900] is True and tb[1440] is True, tb)
    ck("原始：产物判据 12 的隐藏宽度集合与重算一致",
       J[12]["evidence"]["hiddenWidths"] == f["zoomTriggerByWidth"]["hiddenWidths"]
       == sorted([w for w, v in tb.items() if v is False]))

    rz = rw["resize"]
    ck("原始：DOM 里没有任何 resize 控件或含 resize 的 class",
       rz["controls"] == 0 and rz["likeElements"] == 0, rz)
    ck("原始：三处起点分别是 rightEdge / bottomEdge / corner",
       set(rz["cells"]) == {"rightEdge", "bottomEdge", "corner"})
    ck("原始：★ 右边缘命中的是带 nodrag 的 source handle",
       "react-flow__handle-right" in (rz["cells"]["rightEdge"]["cls"] or "")
       and "nodrag" in (rz["cells"]["rightEdge"]["cls"] or ""),
       rz["cells"]["rightEdge"]["cls"])
    ck("原始：右边缘拖拽四项全为 false（完全无反应）",
       all(rz["cells"]["rightEdge"][k] is False
           for k in ("domWChanged", "domHChanged", "storeWChanged",
                     "positionChanged")))
    ck("原始：★ 下边缘与右下角是「移动了节点」而不是缩放",
       rz["cells"]["bottomEdge"]["positionChanged"] is True
       and rz["cells"]["corner"]["positionChanged"] is True
       and all(rz["cells"][w][k] is False
               for w in ("bottomEdge", "corner")
               for k in ("domWChanged", "domHChanged", "storeWChanged")))
    rp = rw["reproject"]
    ck("原始：改宽 1440→700 视口 Δ 全 0",
       rp["delta"] == {"dx": 0.0, "dy": 0.0, "dz": 0.0}, rp["delta"])
    ck("原始：★ owner_log 里确实有 breakpoint-flip-delegated 且 status=skipped",
       rp["delegated"] is True and rp["delegatedStatus"] == "skipped")
    ck("原始：产物判据 16 把它判为「设计而非缺陷」且与重算一致",
       "设计" in J[16]["text"] and "不是缺陷" in J[16]["text"]
       and J[16]["evidence"]["breakpointFlipDelegated"] == rp["delegated"]
       and J[16]["evidence"]["breakpointFlipStatus"] == rp["delegatedStatus"])

    # ---------- 产物是否忠实抄了原始读数（R33 / R38 第三次复发，必须逐项对账）----------
    # 上面那些检查验的是「原始读数自洽」；这一段验的是「产物 == 重算」。
    # 只做前者时，把产物里的读数改掉能一路蒙混过关。

    prod_vm = {v["label"]: v for v in f["viewportAB"]}
    bad_vm = [lb for lb, v in vm.items()
              if lb in prod_vm and (
                  prod_vm[lb]["store"] != v["store"]
                  or prod_vm[lb]["mq768"] != v["mq768"]
                  or prod_vm[lb]["measuredWidth"] != v["measuredWidth"]
                  or prod_vm[lb]["triggerVisible"] != v["triggerVisible"]
                  or all((prod_vm[lb]["matchesExpectedConstant"] or {})
                         .values()) != v["allFieldsEqual"])]
    ck("原始：产物 viewportAB 三档的 store/mq768/宽度/按钮可见/命中标志"
       "逐项与重算一致", not bad_vm, bad_vm)

    ck("原始：产物判据 1/2/3 的 store 与 mq768 与重算一致",
       J[1]["evidence"]["store"] == vm["desktop"]["store"]
       and J[1]["evidence"]["mq768"] == vm["desktop"]["mq768"]
       and J[2]["evidence"]["store"] == vm["compact"]["store"]
       and J[2]["evidence"]["mq768"] == vm["compact"]["mq768"]
       and J[3]["evidence"]["store"] == vm["midband"]["store"])

    ck("原始：产物首屏的 zoomLevel / triggerText / 一致标志与重算一致",
       J[4]["evidence"]["zoomLevel"] == ini["zoomLevel"]
       and J[4]["evidence"]["triggerText"] == ini["triggerText"]
       and J[4]["evidence"]["indicatorMatchesReal"] == ini["indOk"]
       and J[4]["evidence"]["triggerMatchesReal"] == ini["trigOk"]
       and J[4]["evidence"]["realPercent"] == ini["zoomLevel"])

    bad_burst = [b["key"] for b in f["wheel"]["bursts"]
                 if b.get("n") != wh["bursts"][[x["key"] for x in wh["bursts"]]
                                                .index(b["key"])]["n"]
                 or b.get("domDyPerEvent") != wh["perEventDy"][b["key"]]]
    ck("原始：产物每格位移 domDyPerEvent 与重算一致（不能改成 240 之类）",
       not bad_burst, bad_burst)
    ck("原始：产物 wheel.eventsTotal / dzValues 与重算一致",
       f["wheel"]["eventsTotal"] == wh["eventsTotal"]
       and sorted(set(f["wheel"]["dzValues"])) == wh["dzSet"])

    ck("原始：产物判据 9 的 nopan / viewportUnchanged 与重算一致",
       J[9]["evidence"]["nodeNopan"] == rw["wheelNode"]["nopan"]
       and J[9]["evidence"]["viewportUnchanged"] == rw["wheelNode"]["unchanged"])

    ck("原始：产物判据 10 的差距/收敛/logLenFrozen 与重算一致",
       J[10]["evidence"]["gaps"] == dv["gaps"]
       and J[10]["evidence"]["yGap"] == dv["yGap"]
       and J[10]["evidence"]["converged"] == dv["converged"]
       and J[10]["evidence"]["logLenFrozen"] == dv["logLenFrozen"])

    prod_trig = {t["width"]: t["visible"]
                 for t in f["zoomTriggerByWidth"]["rows"]}
    ck("原始：产物 triggerByWidth 每一行的 visible 与重算一致",
       prod_trig == tb, prod_trig)

    prod_rz = {c["where"]: c for c in f["nodeResize"]["cells"]}
    bad_rz = [w for w, c in rz["cells"].items()
              if w not in prod_rz or
              prod_rz[w]["domWidthChanged"] != c["domWChanged"] or
              prod_rz[w]["domHeightChanged"] != c["domHChanged"] or
              prod_rz[w]["storeWidthChanged"] != c["storeWChanged"] or
              prod_rz[w]["storeHeightChanged"] != c["storeHChanged"] or
              prod_rz[w]["positionChanged"] != c["positionChanged"]]
    ck("原始：产物三格 resize 的五项布尔与重算逐格一致", not bad_rz, bad_rz)
    KEYMAP = {"domWidthChanged": "domWChanged", "domHeightChanged": "domHChanged",
              "storeWidthChanged": "storeWChanged",
              "storeHeightChanged": "storeHChanged",
              "positionChanged": "positionChanged"}
    ck("原始：★ 判据 14/15 的证据与 findings 里的同一批格子逐项同源",
       J[14]["evidence"]["where"] == "rightEdge"
       and J[15]["evidence"]["cells"]
       == [c for c in f["nodeResize"]["cells"] if c["where"] != "rightEdge"]
       and all(J[14]["evidence"][pk] == prod_rz["rightEdge"][pk]
               for pk in KEYMAP)
       and J[15]["evidence"]["anyResizeHappened"]
       == f["nodeResize"]["anyResizeHappened"],
       J[14]["evidence"]["where"])

    ck("原始：产物 resize 计数与重算一致",
       f["nodeResize"]["resizeControls"] == rz["controls"]
       and f["nodeResize"]["resizeLikeElements"] == rz["likeElements"]
       and J[13]["evidence"]["resizeControls"] == rz["controls"]
       and J[13]["evidence"]["resizeLikeElements"] == rz["likeElements"])

    _rp = rw["reproject"]
    ck("原始：产物 reproject 的 delta / delegated / status 与重算一致",
       f["reprojectOnResize"]["delta"] == _rp["delta"]
       and f["reprojectOnResize"]["breakpointFlipDelegated"] == _rp["delegated"]
       and f["reprojectOnResize"]["breakpointFlipStatus"]
       == _rp["delegatedStatus"]
       and f["reprojectOnResize"]["logReasons"] == _rp["reasons"])

    ck("原始：产物 clamp 的 finalZoom / indicator 与重算一致",
       all(f["zoomMenu"]["clamp"][n]["finalZoom"] == rw["clamp"][n]["finalZoom"]
           and f["zoomMenu"]["clamp"][n]["indicator"] == rw["clamp"][n]["ind"]
           for n in rw["clamp"]))

    ck("结构：派生布尔必须能由原始字段现算得出（滚轮 allDzZero）",
       J[8]["evidence"]["allDzZero"] is True
       and all(abs(b["storeDz"]) < 1e-9 and abs(b["domDz"]) < 1e-9
               for b in wh["bursts"]))


def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        bad = copy.deepcopy(a)
        mutate(bad)
        failed = [c["label"] for c in run_checks(bad, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # ---- 产物里的读数被改（只改产物、不改 /tmp 与 raw/）----
    inj("伪造 desktop 档「未命中常量」", lambda x:
        x["findings"]["viewportAB"][0].__setitem__(
            "matchesExpectedConstant", {"x": False, "y": True, "zoom": False}))
    inj("伪造 compact 档 mq768 为 false", lambda x:
        x["judgments"][1]["evidence"].__setitem__("mq768", False))
    inj("伪造 midband 档 store 被换掉", lambda x:
        x["judgments"][2]["evidence"].__setitem__(
            "store", {"x": 0, "y": 0, "zoom": 1}))
    inj("伪造 desktop 档按钮可见性", lambda x:
        x["findings"]["viewportAB"][0].__setitem__("triggerVisible", False))
    inj("伪造首屏 zoomLevel 就是硬编码的 54", lambda x:
        x["judgments"][3]["evidence"].__setitem__("zoomLevel", 54))
    inj("伪造首屏 zoomLevel 与 store 不一致", lambda x:
        x["judgments"][3]["evidence"].__setitem__(
            "indicatorMatchesReal", False))
    inj("伪造首屏 triggerText", lambda x:
        x["judgments"][3]["evidence"].__setitem__("triggerText", "54%"))
    inj("伪造菜单某一格指示器不一致", lambda x:
        x["findings"]["zoomMenu"]["menu"][0].__setitem__(
            "indicatorMatchesReal", False))
    inj("伪造 clamp 下限不是 0.1", lambda x:
        x["findings"]["zoomMenu"]["clamp"]["min"].__setitem__(
            "finalZoom", 0.2))
    inj("伪造每格位移不是 120", lambda x:
        x["findings"]["wheel"]["bursts"][0].__setitem__(
            "domDyPerEvent", 240.0))
    inj("伪造滚轮事件数", lambda x:
        x["findings"]["wheel"].__setitem__("eventsTotal", 4))
    inj("★ 抹掉 761a/761b 的假形状（只留好看的真值）", lambda x:
        x["findings"]["wheel"]["stalePattern"].__setitem__(
            "probeA_dySeries", [120.0, 120.0, 120.0, 120.0]))
    inj("伪造滚轮在节点上有响应", lambda x:
        x["judgments"][8]["evidence"].__setitem__(
            "viewportUnchanged", False))
    inj("伪造节点处 nopan 为 false", lambda x:
        x["judgments"][8]["evidence"].__setitem__("nodeNopan", False))
    inj("伪造 store 与 DOM 差距已收敛", lambda x:
        x["judgments"][9]["evidence"].__setitem__("converged", True))
    inj("伪造差距只有 1px", lambda x:
        x["judgments"][9]["evidence"].__setitem__("yGap", 1.0))
    inj("伪造 logLen 没有冻结", lambda x:
        x["judgments"][9]["evidence"].__setitem__("logLenFrozen", False))
    inj("伪造差距时间线被抹平", lambda x:
        x["judgments"][9]["evidence"].__setitem__("gaps", [{"x": 0.2,
                                                            "y": 0.0,
                                                            "zoom": 0.0}]))
    inj("伪造下一轮没被抹平", lambda x:
        x["judgments"][10]["evidence"]["gapAfter"].__setitem__("y", 119.8))
    inj("伪造 560 宽度下缩放按钮也隐藏", lambda x:
        x["findings"]["zoomTriggerByWidth"]["rows"][0].__setitem__(
            "visible", False))
    inj("伪造隐藏宽度集合", lambda x:
        x["judgments"][11]["evidence"].__setitem__("hiddenWidths", [700]))
    inj("伪造 resize 控件存在", lambda x:
        x["judgments"][12]["evidence"].__setitem__("resizeControls", 1))
    inj("伪造 resize 控件数为 1（findings 那份）", lambda x:
        x["findings"]["nodeResize"].__setitem__("resizeControls", 1))
    inj("★ 伪造判据 14（右边缘无反应）改成宽度变了", lambda x:
        x["judgments"][13]["evidence"].__setitem__(
            "domWidthChanged", True))
    inj("伪造右下角拖拽是缩放（宽变了）", lambda x:
        x["findings"]["nodeResize"]["cells"][2].__setitem__(
            "domWidthChanged", True))
    inj("伪造下边缘拖拽没有移动节点", lambda x:
        x["findings"]["nodeResize"]["cells"][1].__setitem__(
            "positionChanged", False))
    inj("★ 把「改宽不重投影」从设计改判成缺陷", lambda x:
        x["judgments"][15].__setitem__("text", "缺陷：改宽不重投影"))
    inj("伪造 breakpoint-flip-delegated 是 committed", lambda x:
        x["findings"]["reprojectOnResize"].__setitem__(
            "breakpointFlipStatus", "committed"))
    inj("伪造 reproject 的 delta 不为 0", lambda x:
        x["findings"]["reprojectOnResize"].__setitem__(
            "delta", {"dx": 0.0, "dy": 1.0, "dz": 0.0}))
    inj("清空不声称清单", lambda x: x.__setitem__("notClaimed", []))
    inj("删掉判据 8", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["no"] != 8]))
    inj("伪造两轮判定为全一致（抹掉 clamp 的例外）", lambda x:
        x["twoRound"].__setitem__("inconsistentCells", {}))
    inj("伪造 clamp 排除依据被写掉", lambda x:
        x["twoRound"].__setitem__("excludedReason", "无"))
    inj("篡改返工条目：删掉 R42", lambda x:
        x.__setitem__("rework", [r for r in x["rework"] if r["id"] != "R42"]))
    inj("篡改 rawProbeFiles 退回只放 /tmp", lambda x:
        x.__setitem__("rawProbeFiles", ["/tmp/vb761a.json"]))
    return cases


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        rw = raw_side()
        rawErr = None
    except Exception as e:
        rw, rawErr = {}, str(e)

    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用（raw/ 下四份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 761, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:200]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 761 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
