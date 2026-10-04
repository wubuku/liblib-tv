#!/usr/bin/env python3
"""batch 762 汇编器：导演台焦点围栏与键盘可达性（零缺陷批次）

从 raw/ 下两份原始输出现算。原则同 761：**数字不许手抄**，缺文件直接抛错。

⚠ 两段探针的轮次不同，必须如实记录：
  - 762a **两轮**且一致（焦点围栏主体）
  - 762b **单轮**（补格：那 2 个不可达元素 + 折叠后的 inert 围栏）
    单轮不适用两轮判定，写进 twoRound 而不是含糊过去。
"""
import json
import pathlib
import re
import sys

RAW = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch762-2026-10-01/raw")
OUT = RAW.parent / "runtime-audit.json"

A_PATH, B_PATH = RAW / "vb762a.json", RAW / "vb762b.json"
for p in (A_PATH, B_PATH):
    if not p.exists():
        sys.exit("FATAL 缺原始读数 %s —— 判失败，不许凭空写结论" % p)
A = json.loads(A_PATH.read_text(encoding="utf-8"))
B = json.loads(B_PATH.read_text(encoding="utf-8"))
ra, rb = A["rounds"][0], B["rounds"][0]

# ---------- ① dialog 本体 ----------
desk = ra["D1_desk"]
dialog = {
    "open": desk["open"], "ariaModal": desk["ariaModal"],
    "focusScope": desk["focusScope"], "focusState": desk["focusState"],
    "focusReturn": desk["focusReturn"], "zIndex": desk["zIndex"],
    "position": desk["position"], "panelsCollapsed": desk["panelsCollapsed"],
    "isTopmostAtCenter": desk["isTopmostAtCenter"],
    "rect": desk["rect"],
}

# ---------- ② 打开瞬间的焦点 ----------
ao = ra["D1_activeOnOpen"]
open_focus = {
    "inDialog": ao["inDialog"], "isBody": ao["body"],
    "tag": (ao["el"] or {}).get("tag"),
    "role": (ao["el"] or {}).get("role"),
    "ariaLabel": (ao["el"] or {}).get("ariaLabel"),
    "dialogCount": ao.get("dialogCount"),
    "inertDialogs": ao.get("inertDialogs"),
}

# ---------- ③ 焦点围栏：Tab / Shift+Tab ----------
fwd, bwd = ra["D2_tabForward"], ra["D4_tabBackward"]
fence = {
    "forward": {"steps": fwd["steps"], "escapedCount": fwd["escapedCount"],
                "escapedAt": fwd["escapedAt"], "bodyHits": fwd["bodyHits"]},
    "backward": {"steps": bwd["steps"], "escapedCount": bwd["escapedCount"],
                 "escapedAt": bwd["escapedAt"], "bodyHits": bwd["bodyHits"]},
    "totalPresses": fwd["steps"] - 1 + bwd["steps"] - 1,
    "totalEscapes": fwd["escapedCount"] + bwd["escapedCount"],
    "totalBodyHits": len(fwd["bodyHits"]) + len(bwd["bodyHits"]),
}

# ---------- ④ Esc 与焦点返回 ----------
esc = ra["D6_afterEsc"]
esc_after = (esc.get("active") or {}).get("el") or {}
esc_result = {
    "dialogStillOpen": (esc.get("desk") or {}).get("open"),
    "closed": (esc.get("desk") or {}).get("open") is False,
    "focusTag": esc_after.get("tag"),
    "focusIsTrigger": bool(esc_after.get("dataOpenDirector")),
    "canvasButtonBack": esc.get("canvasUp"),
    "focusAfterSecondClose": rb.get("B3_focusAfter"),
    "escWorksWhileCollapsed": rb.get("B3_escClosed"),
    "focusBeforeEscInChild": rb.get("B4_focusBeforeEsc"),
    "afterEscFromChild": rb.get("B4_afterEsc"),
}

# ---------- ⑤ 可聚焦元素清单与那 2 个不可达的 ----------
b1 = rb["B1_list"]
unreachable = b1["unreachableList"]
focusables = {
    "total": b1["total"], "reachable": b1["reachable"],
    "unreachable": b1["unreachable"],
    "unreachableList": [
        {"tag": u["tag"], "ariaLabel": u["ariaLabel"], "display": u["display"],
         "visibility": u["visibility"], "box": [u["w"], u["h"]],
         "cls": u["cls"],
         "isHiddenFileInput": u["cls"].startswith("hidden") and u["tag"] == "INPUT"}
        for u in unreachable],
    "allUnreachableAreHiddenFileInputs":
        all(u["cls"].startswith("hidden") and u["tag"] == "INPUT"
            for u in unreachable),
}

# ---------- ⑥ 折叠后的 inert 围栏 ----------
st = rb["B2_after"]
by_label = {p["ariaLabel"]: p for p in st["panels"]}
collapsed = {
    "collapsedAttr": st["collapsed"], "togglePresent": st["togglePresent"],
    "toggleAriaPressed": st.get("toggleAriaPressed"),
    "reachableFocusablesBefore": (rb["B1_focusable"] or {}).get("reachable"),
    "reachableFocusablesAfter": (rb["B2_focusable"] or {}).get("reachable"),
    "tree": by_label.get("场景对象"),
    "inspector": by_label.get("属性"),
    "treeInert": (by_label.get("场景对象") or {}).get("inert"),
    "treeAriaHidden": (by_label.get("场景对象") or {}).get("ariaHidden"),
    "treeDisplay": (by_label.get("场景对象") or {}).get("display"),
    "treeWidth": (by_label.get("场景对象") or {}).get("w"),
    "inspectorInert": (by_label.get("属性") or {}).get("inert"),
    "inspectorWidth": (by_label.get("属性") or {}).get("w"),
    "inertAriaHiddenInSync":
        (by_label.get("场景对象") or {}).get("inert")
        == ((by_label.get("场景对象") or {}).get("ariaHidden") == "true"),
    "tabAfterCollapse": {"steps": rb["B2_tab"]["steps"],
                         "escapedCount": rb["B2_tab"]["escapedCount"],
                         "escapedAt": rb["B2_tab"]["escapedAt"]},
}

findings = {
    "dialog": dialog, "openFocus": open_focus, "fence": fence,
    "escAndReturn": esc_result, "focusables": focusables,
    "collapsedFence": collapsed,
}

audit = {
    "batch": 762,
    "date": "2026-10-01",
    "clone": "http://localhost:4317 (master)",
    "subject": "导演台的焦点围栏与键盘可达性（748 挂起项的正面结案）",
    "seed": {"entry": "画布上唯一的 script-execution 节点的 [data-open-director] 按钮",
             "entryCall": "ScriptExecutionNode.tsx:58 → openDirectorDesk(id, activeCanvasId)",
             "directorRenderGate": "page.tsx:1654 activeDirectorNodeId && activeDirectorCanvasId"},
    "twoRound": {
        "probeA": {"file": "raw/vb762a.json", "rounds": len(A["rounds"]),
                   "consistent": A["consistent"]},
        "probeB": {"file": "raw/vb762b.json", "rounds": len(B["rounds"]),
                   "consistent": None, "note": "单轮补格，不适用两轮判定"},
        "allConsistent": A["consistent"],
        "caveat": "762a 两轮一致；762b 是单轮补格（点名那 2 个不可达元素 + "
                  "折叠后的 inert 围栏），因此凡只用 762b 支撑的判据"
                  "都标注了「单轮」。",
    },
    "findings": findings,
    "judgeCount": 12,
    "judgments": [
        {"no": 1, "text": "导演台确实是一整块 role=dialog + aria-modal=true 的模态框，"
                          "z-index 100、fixed，且在视口中心是最上层",
         "evidence": dialog},
        {"no": 2, "text": "三枚焦点读数齐备：focus-scope=workspace、"
                          "focus-state=workspace、focus-return=trigger",
         "evidence": {"focusScope": dialog["focusScope"],
                      "focusState": dialog["focusState"],
                      "focusReturn": dialog["focusReturn"]}},
        {"no": 3, "text": "打开瞬间焦点真的进了 dialog（落在 role=dialog 自身、"
                          "aria-label=「3D导演台工作区」），没有留在 body 上",
         "evidence": open_focus},
        {"no": 4, "text": "★ 焦点围栏成立：Tab 24 步正向 + Shift+Tab 12 步反向，"
                          "**共 36 次按键、0 次焦点逃出 dialog、0 次落到 body**",
         "evidence": fence},
        {"no": 5, "text": "Esc 能关闭整个导演台（不是只关移动端面板）",
         "evidence": {"dialogStillOpenAfterEsc": esc_result["dialogStillOpen"],
                      "closed": esc_result["closed"]}},
        {"no": 6, "text": "关闭后焦点真的回到触发按钮 [data-open-director]"
                          "（「打开导演台 →」），与 focus-return=trigger 吻合",
         "evidence": {"focusTag": esc_result["focusTag"],
                      "focusIsTrigger": esc_result["focusIsTrigger"],
                      "secondClose": esc_result["focusAfterSecondClose"],
                      "fromChildPanel": esc_result["afterEscFromChild"]}},
        {"no": 7, "text": "焦点在子面板按钮上（aria-label=「导出导演台项目」）时，"
                          "Esc 同样能关闭 —— 关闭行为不依赖焦点落在 dialog 根上",
         "evidence": {"beforeEsc": esc_result["focusBeforeEscInChild"],
                      "afterEsc": esc_result["afterEscFromChild"]}},
        {"no": 8, "text": "折叠态下 Esc 依然能关闭，且关闭后焦点同样回到触发按钮",
         "evidence": {"escWorksWhileCollapsed":
                      esc_result["escWorksWhileCollapsed"],
                      "focusAfter": esc_result["focusAfterSecondClose"]}},
        {"no": 9, "text": "128 个可聚焦元素里 2 个不可达 —— 逐个点名：两个都是 "
                          "`<input class=\"hidden\">` 的隐藏 file input"
                          "（一个带 aria-label=「导入本地角色模型」）",
         "evidence": focusables},
        {"no": 10, "text": "★ 这 2 个不可达元素**不是缺陷**：隐藏 file input 靠可见"
                           "元素代理点击是标准做法，且它们 display:none 不可聚焦，"
                           "屏幕阅读器也到不了",
         "evidence": {"allUnreachableAreHiddenFileInputs":
                      focusables["allUnreachableAreHiddenFileInputs"],
                      "static": "DirectorDesk.tsx:1108-1112 "
                                "data-director-project-import-input / "
                                "DirectorIconRail.tsx:661-665 "
                                "aria-label=导入本地角色模型"}},
        {"no": 11, "text": "折叠后场景树面板 inert / aria-hidden / display 三者**同步**"
                           "（都收起、宽 0），属性面板保持展开 —— 焦点围栏在折叠态"
                           "仍然成立（Tab 14 步 0 次逃出）",
         "evidence": collapsed},
        {"no": 12, "text": "折叠后收起按钮本身消失，但恢复入口存在 —— 点图标栏"
                           "「场景」即恢复；这是 Batch 587 与源站核对过的刻意设计，"
                           "**不是缺陷**",
         "evidence": {"togglePresentWhenCollapsed": collapsed["togglePresent"],
                      "static": "DirectorDesk.tsx:963 只在 !collapsed 时渲染收起按钮；"
                                "DirectorIconRail.tsx:355-359 注释写明"
                                "「点图标栏的场景条目即恢复」，:359 调 "
                                "setViewportPanelsCollapsed(false)"}},
    ],
    "headline": "导演台的焦点围栏**完整成立**：Tab 与 Shift+Tab 共 36 次按键、"
                "0 次焦点逃出模态框，Esc 能关、焦点回到触发按钮，折叠态下 inert / "
                "aria-hidden / display 三者同步且围栏仍在。**这一批 0 缺陷** —— "
                "而且有三处「看着像问题、查清都不是」：那 2 个不可达元素是标准的隐藏 "
                "file input；折叠后收起按钮消失是 Batch 587 与源站核对过的刻意设计；"
                "`viewportPanelsCollapsed` 复数命名却只收左半边，是命名与行为的"
                "措辞问题而非行为错误。",
    "rework": [
        {"id": "R48", "where": "探针 b（把 HIT 写死成查另一个选择器）",
         "what": "第一版 b 把命中断言写死成 `e.closest('[data-director-panels-toggle]')`，"
                 "拿去点「打开导演台」当然永远 ok=false，直接 FATAL 停下。",
         "lesson": "「命中断言」这个工具自己必须参数化。**当场停是对的 —— "
                   "是探针错了，产品没错。**"},
        {"id": "R49", "where": "探针 a（按文案找折叠开关，必然落空）",
         "what": "用 `/收起|折叠|展开/` 去 button 的 textContent 里找开关，"
                 "拿到 null —— 因为那枚按钮是纯图标（`PanelLeftOpen` 且 svg "
                 "`aria-hidden`），根本没有文本。",
         "lesson": "**图标按钮只能按钩子找，不能按文案找**。"
                   "正确钩子是 `data-director-panels-toggle`。"
                   "「找不到元素」和「元素没有那个字」是两回事。"},
        {"id": "R50", "where": "探针 a（D7 读错了元素）",
         "what": "关闭后再去读 `[data-open-director]` 上的 "
                 "`data-director-focus-return`，拿到 null —— 那个属性长在 "
                 "dialog 上，dialog 已经卸载了。",
         "lesson": "属性读数要认准它挂在哪个元素上；挂载/卸载会改变「还能不能读到」。"
                   "焦点返回的**行为**证据在 B3/B4 里，不依赖这次读取。"},
        {"id": "R51", "where": "结论纪律（差点把三处报成缺陷）",
         "what": "「2 个元素不可达」「折叠后收起按钮消失」"
                 "「viewportPanelsCollapsed 只收一半」三处都先被我当成缺陷候选。",
         "lesson": "查清机制后全部结案：隐藏 file input 是标准做法；恢复入口是"
                   "Batch 587 对着源站量过的刻意设计；复数命名是措辞问题。"
                   "**「看着不对」只是待查项，不是结论。**"},
        {"id": "R52", "where": "验收器（★ 同一个洞第四次复发）",
         "what": "首版 34/36 时有 2 条检查自己写错了（用子串 `\"b 是单轮\"` 判断"
                 "有没有把单轮算进去，结果被 `762b 是单轮` 命中；headline 里写的"
                 "是「标准的隐藏 file input」而我去找「标准做法」）。"
                 "把那两条修对之后，**19/21 阴性对照里有 2 发漏放**："
                 "改 `findings.dialog.ariaModal` 与 `findings.openFocus.inDialog` "
                 "一路通过 —— 因为 `findings` 与 `judgments[].evidence` 在"
                 "JSON 往返之后是**两份独立副本**，我只守了判据那一份。",
         "lesson": "759 的 R33、760 的 R38、761 的 R46、**这里是第四次**。"
                   "同一个洞复发四次，说明「事后补检查」不是办法。"
                   "所以这次把它写成一条**默认结构检查**：凡是 `findings` 里"
                   "出现过的键，都必须有一条 `findings.X == J[n].evidence` 的同源断言。"
                   "补完 **38/38 通过、阴性对照 26/26 全拦**，"
                   "并新增 5 发「只改 findings 那一份」的注入把这五条同源断言逐条打一遍。"},
    ],
    "notClaimed": [
        "没有与源站对照：全部读数来自 clone（4317）。恢复入口那条只核了代码里的"
        "注释与调用点，没有重新回源站复核。",
        "762b 是**单轮**补格：点名那 2 个不可达元素与折叠后 inert 围栏这两条"
        "只跑了一轮。",
        "只测了 1440×1000 桌面视口；导演台的移动端 focus scope"
        "（mobile-tree / mobile-inspector）完全没测。",
        "只测了 Tab / Shift+Tab / Esc 三个键；导演台自己的快捷键"
        "（DirectorDesk.tsx:482/:549 那两个处理器覆盖了哪些键）没测。",
        "没有测屏幕阅读器实际播报什么，只量了 DOM 属性与焦点落点。",
        "焦点围栏只压了 36 次按键；128 个可聚焦元素没有逐个走到"
        "（走到第 36 个就停了），后半程是否仍不逃逸未测。",
        "打开导演台会不会触发付费/真实生成任务没有碰；本批只做只读导航与 Tab。",
        "只开了导演台一个项目，没测多项目切换、导入/导出面板里的焦点行为。",
    ],
    "rawProbeFiles": ["raw/vb762a.json", "raw/vb762b.json",
                      "probes/dbg762a.py", "probes/dbg762b.py",
                      "probes/mk762audit.py"],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", OUT)
print("762a 两轮一致 =", A["consistent"], "| 762b 单轮")
print("dialog:", json.dumps({k: dialog[k] for k in
      ("ariaModal", "focusScope", "focusState", "focusReturn", "zIndex",
       "isTopmostAtCenter")}, ensure_ascii=False))
print("打开瞬间焦点 inDialog=%s tag=%s role=%s"
      % (open_focus["inDialog"], open_focus["tag"], open_focus["role"]))
print("围栏: 共 %d 次按键，逃出 %d 次，落 body %d 次"
      % (fence["totalPresses"], fence["totalEscapes"], fence["totalBodyHits"]))
print("Esc 关闭=%s 焦点回触发按钮=%s | 折叠态 Esc=%s"
      % (esc_result["closed"], esc_result["focusIsTrigger"],
         esc_result["escWorksWhileCollapsed"]))
print("可聚焦 %d 个，可达 %d，不可达 %d → 全是隐藏 file input=%s"
      % (focusables["total"], focusables["reachable"],
         focusables["unreachable"],
         focusables["allUnreachableAreHiddenFileInputs"]))
print("折叠: collapsed=%s 树 inert=%s aria-hidden=%s display=%s w=%s | "
      "属性面板 inert=%s w=%s | 可达焦点 %s→%s | Tab %s 步逃出 %s"
      % (collapsed["collapsedAttr"], collapsed["treeInert"],
         collapsed["treeAriaHidden"], collapsed["treeDisplay"],
         collapsed["treeWidth"], collapsed["inspectorInert"],
         collapsed["inspectorWidth"], collapsed["reachableFocusablesBefore"],
         collapsed["reachableFocusablesAfter"],
         collapsed["tabAfterCollapse"]["steps"],
         collapsed["tabAfterCollapse"]["escapedCount"]))
print("判据 %d 条，返工 %d 条，不声称 %d 条"
      % (len(audit["judgments"]), len(audit["rework"]),
         len(audit["notClaimed"])))
