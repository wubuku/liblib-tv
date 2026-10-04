"""batch 760 验收器：分组框拖动的方向性 + canvasTool 两态手势矩阵 + 底栏工具按钮状态

三层结构（与 753–759 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （page.tsx 的 effectivePan / panOnDrag / nodesDraggable / data-canvas-tool、
      LeftSidebar ToolButton 的 aria-pressed 与高亮绑定、MoveMenu 的两枚青色圆点、
      H/V 快捷键、data-canvas-tool 全仓零读取方）
  2. **产物层** —— 判据条数、三段探针两轮一致性、证据链、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb760{a,b,c}.json` 还在，**按正确键名**
     从原始输出重算全部派生量，与产物逐格对账。缺失时**判失败而不是通过**。

⚠ 第 3 层是本批的重点（R34）：760c 的派生层曾把 dict 的 `label` 读成
  `"aria-label"`、`ariaPressed` 读成 `"aria-pressed"`，三个派生布尔成了恒定常数，
  **而且两轮一致照样通过**。所以这里不信任产物里的派生值，一律从原始读数重算，
  再要求产物与重算结果逐格相等。

判据 **14 条**（760a/760b/760c 各跑满两轮且一致）。
"""
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch760-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWA = pathlib.Path("/tmp/vb760a.json")
RAWB = pathlib.Path("/tmp/vb760b.json")
RAWC = pathlib.Path("/tmp/vb760c.json")


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def static_side():
    page = src("src/app/page.tsx")
    ui = src("src/store/uiStore.ts")
    ls = src("src/components/LeftSidebar.tsx")

    all_src = []
    for p in sorted((ROOT / "src").rglob("*.ts*")):
        try:
            all_src.append(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    joined = "\n".join(all_src)

    return {
        "effectivePan": 'const effectivePan = canvasTool === "pan" || isSpacePressed'
                        in page,
        "panOnDrag": "panOnDrag={effectivePan ? [0, 1] : [1]}" in page,
        "nodesDraggable": 'nodesDraggable={canvasTool === "select" && !effectivePan}'
                          in page,
        "cursorGrab": 'effectivePan ? "cursor-grab bg-[#141414]"' in page,
        "canvasToolInit": "canvasTool: \"select\"," in ui,
        "setCanvasTool": 'setCanvasTool: (tool) => set({ canvasTool: tool })' in ui,
        "uiStoreHook": "window.__libtv_ui_store = useUIStore" in ui,
        "vKey": '=== "v") setCanvasTool("select")' in page,
        "hKey": '=== "h") setCanvasTool("pan")' in page,
        # ⚠ 死属性：全 src/ 只有写入处，零读取方
        "dataCanvasToolWrites": joined.count("data-canvas-tool"),
        "dataCanvasToolReads": len([
            1 for t in all_src
            if "dataset.canvasTool" in t
            or "getAttribute(\"data-canvas-tool\")" in t
            or "getAttribute('data-canvas-tool')" in t
        ]),
        # ToolButton：active 同时接 aria-pressed 与高亮底色
        "toolButtonAriaPressed": "aria-pressed={active}" in ls,
        "toolButtonHighlight": 'active && "bg-white/10 text-white"' in ls,
        # ★ 缺陷根因：同一行里 label 跟 canvasTool、active 跟面板开关
        "mixedStateSources":
            'label={canvasTool === "pan" ? "抓手工具" : "移动"} '
            'active={activePrimaryPanel === "move"}' in ls,
        "selectToolClosesPanel":
            "const selectTool" in ls and "setPrimaryPanel(null);" in ls,
        # 阳性对照：面板内两枚青色圆点确实跟 canvasTool
        "movePanelDotSelect": 'canvasTool === "select" && <span '
                              'className="h-1.5 w-1.5 rounded-full bg-[#09caf5]"' in ls,
        "movePanelDotPan": 'canvasTool === "pan" && <span '
                           'className="h-1.5 w-1.5 rounded-full bg-[#09caf5]"' in ls,
        "movePanelOverlay": 'data-liblib-overlay="primary:move"' in ls,
        "vhKeyHints": ls.count('<span className="text-xs text-[#777]">'),
        "toolButtonDataHooks": ls.count("data-"),
        "toolButtonBodyDataHooks": ls[
            ls.index("function ToolButton"):ls.index("function MoveMenu")
        ].count("data-"),
    }


def raw_side():
    """从原始读数**按正确键名**重算全部派生量。缺文件 → 抛错（判失败而非通过）。"""
    for p in (RAWA, RAWB, RAWC):
        if not p.exists():
            raise FileNotFoundError(str(p))
    a = json.loads(RAWA.read_text())
    b = json.loads(RAWB.read_text())
    c = json.loads(RAWC.read_text())
    ra, rb, rc = a["rounds"][0], b["rounds"][0], c["rounds"][0]

    gd = rb["groupDrag"]
    recomputed = {
        "groupDelta": gd["groupDelta"],
        "childAbsDelta": gd["childAbsDelta"],
        "childRelDelta": gd["childRelDelta"],
        "absDeltaIdenticalToGroup": gd["childAbsDelta"] == gd["groupDelta"],
        "relDeltaIsZero": gd["childRelDelta"] == [0, 0],
        "parentIdKept": gd["parentIdKept"],
        "childStillInsideBox": gd["childStillInsideBox"],
        "pastDelta": gd["pastDelta"],
        "childRelBefore": gd["before"]["childRel"],
        "childRelAfter": gd["after"]["childRel"],
    }
    before, undo = gd["before"], rb["afterUndo"]
    undoRecomputed = {
        "groupRelRestored": undo["groupRel"] == before["groupRel"],
        "groupDomRestored": undo["groupDom"] == before["groupDom"],
        "childRelRestored": undo["childRel"] == before["childRel"],
        "childAbsRestored": undo["childAbs"] == before["childAbs"],
        "pastBackTo": undo["past"],
        "pastBefore": before["past"],
    }
    tm = rb["toolMatrix"]
    matrixRecomputed = {}
    for t in ("select", "pan"):
        cell = tm[t]
        matrixRecomputed[t] = {
            "paneLeftDrag": cell["paneLeft"]["moved"],
            "paneLeftDeltaX": cell["paneLeft"]["deltaX"],
            "paneMiddleDrag": cell["paneMiddle"]["moved"],
            "paneMiddleDeltaX": cell["paneMiddle"]["deltaX"],
            "nodeDragMoved": cell["nodeLeft"]["childMovedAbs"],
            "nodeDragDelta": cell["nodeLeft"]["childDelta"],
            "nodeDragPastDelta": cell["nodeLeft"]["pastDelta"],
            "groupMovedWhileNodeDragged": cell["nodeLeft"]["groupMoved"],
            "dataAttr": cell["toolState"]["attr"],
            "attrCount": cell["toolState"]["attrCount"],
            "nodePoint": cell["nodePoint"],
        }
    # ★ 关键：键名是 `label` / `ariaPressed`（不是 "aria-label" / "aria-pressed"）
    stepsRecomputed = []
    for s in rc["steps"]:
        btn = s["button"]
        tool = s["state"]["canvasTool"]
        label = btn.get("label")
        pressed = btn.get("ariaPressed")
        stepsRecomputed.append({
            "step": s["step"],
            "canvasTool": tool,
            "panelOpen": s["panel"].get("open"),
            "label": label,
            "ariaPressed": pressed,
            "labelMatchesTool": label == ("抓手工具" if tool == "pan" else "移动"),
            "pressedIsTrue": pressed == "true",
            "highlightMatchesTool": (label == "抓手工具") == (pressed == "true"),
        })
    agreeRecomputed = [s["step"] for s in stepsRecomputed
                       if s["highlightMatchesTool"]]
    disagreeRecomputed = [s["step"] for s in stepsRecomputed
                          if not s["highlightMatchesTool"]]
    return {
        "probeA_consistent": a["consistent"],
        "probeB_consistent": b["consistent"],
        "probeC_consistent": c["consistent"],
        "probeA_pan_nodeHit": ra["tool_pan"]["nodeHit"],
        "probeA_withChild_moved": ra["withChild_drag"]["groupMoved"],
        "probeA_empty_moved": ra["empty_drag"]["groupMoved"],
        "recomputed_childFollows": recomputed,
        "recomputed_undo": undoRecomputed,
        "recomputed_matrix": matrixRecomputed,
        "recomputed_steps": stepsRecomputed,
        "recomputed_agree": agreeRecomputed,
        "recomputed_disagree": disagreeRecomputed,
        "panGroupDrag": rb["panGroupDrag"],
        "attrConsumers": rb["attrConsumers"],
        "panelDots": rc["dots"],
    }


def run_checks(a, st, rw):
    """外壳：检查器自身崩掉必须记成**失败**，不能让异常逃出去伪装成通过
    （自己的规矩：崩掉的检查器比失败的更危险）。"""
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    try:
        _body(a, st, rw, ck)
    except Exception as e:
        ck("检查器自身未因结构破坏而崩溃", False, repr(e))
    return checks


def _body(a, st, rw, ck):
    J = {j["no"]: j for j in a["judgments"]}
    a1 = a["judgments"]
    f = a["findings"]

    # ================= 静态层 =================
    ck("静态：page.tsx 的 effectivePan / panOnDrag / nodesDraggable 三件套都在",
       st["effectivePan"] and st["panOnDrag"] and st["nodesDraggable"])
    ck("静态：cursor-grab 由 className 表达式直接算，与 data-canvas-tool 无关",
       st["cursorGrab"])
    ck("静态：uiStore 里 canvasTool 初值 select、setter 存在、挂在 window 上",
       st["canvasToolInit"] and st["setCanvasTool"] and st["uiStoreHook"])
    ck("静态：V/H 快捷键直接 setCanvasTool，界面上没有任何提示文案",
       st["vKey"] and st["hKey"])
    ck("静态：data-canvas-tool 全 src/ 只有 1 处写入、0 处读取（死属性）",
       st["dataCanvasToolWrites"] == 1 and st["dataCanvasToolReads"] == 0,
       [st["dataCanvasToolWrites"], st["dataCanvasToolReads"]])
    ck("静态：ToolButton 把 active 同时接到 aria-pressed 与高亮底色",
       st["toolButtonAriaPressed"] and st["toolButtonHighlight"])
    ck("静态：★ 缺陷根因 —— 同一枚按钮 label 跟 canvasTool、active 跟面板开关",
       st["mixedStateSources"])
    ck("静态：selectTool 里 setPrimaryPanel(null) 会在选中工具后立刻关掉面板",
       st["selectToolClosesPanel"])
    ck("静态：阳性对照成立 —— 面板内两枚青色圆点各自跟 canvasTool",
       st["movePanelDotSelect"] and st["movePanelDotPan"]
       and st["movePanelOverlay"])
    ck("静态：面板里标着 V / H 两枚快捷键角标（与「界面上没提示」形成反差）",
       st["vhKeyHints"] == 2, st["vhKeyHints"])
    ck("静态：ToolButton 函数体自身无 data-* 钩子（钩子只在两个面板容器上）",
       st["toolButtonBodyDataHooks"] == 0, st["toolButtonBodyDataHooks"])

    # ================= 产物层 =================
    ck("产物：判据 14 条且编号连续 1..14",
       len(a1) == 14 and a["judgeCount"] == 14 and sorted(J) == list(range(1, 15)),
       sorted(J))
    ck("产物：三段探针两轮一致",
       a["twoRound"]["allConsistent"] is True
       and all(a["twoRound"][k]["rounds"] == 2
               for k in ("probeA", "probeB", "probeC")))
    ck("产物：写明「两轮一致不能单独证明派生层正确」这条告诫",
       "两轮一致" in a["twoRound"]["caveat"]
       and "不能单独" in a["twoRound"]["caveat"])
    ck("产物：判据 1/2 —— 带子分组与空分组各自可拖",
       J[1]["evidence"]["groupMoved"] and J[2]["evidence"]["groupMoved"]
       and f["groupBoxDraggable"]["bothMovable"])
    ck("产物：判据 3/4 —— 子节点绝对位移与父逐位相同、相对位移恒 [0,0]",
       J[3]["evidence"]["absDeltaIdenticalToGroup"]
       and J[3]["evidence"]["relDeltaIsZero"]
       and J[4]["evidence"]["childRelDelta"] == [0, 0]
       and J[4]["evidence"]["childRelBefore"] == J[4]["evidence"]["childRelAfter"])
    ck("产物：判据 5/6 —— parentId 未变且撤销后四组坐标全复原、past 回到 0",
       J[5]["evidence"]["parentIdKept"] and J[5]["evidence"]["childStillInsideBox"]
       and J[6]["evidence"]["groupRelRestored"]
       and J[6]["evidence"]["groupDomRestored"]
       and J[6]["evidence"]["childRelRestored"]
       and J[6]["evidence"]["childAbsRestored"]
       and J[6]["evidence"]["pastBackTo"] == J[6]["evidence"]["pastBefore"] == 0,
       J[6]["evidence"])
    ck("产物：判据 7 显式写出「收窄 757 的结论」",
       "更正 757" in J[7]["text"] and "单向" in J[7]["text"]
       and J[7]["evidence"]["narrowedClaim"])
    ck("产物：判据 11 明确记下 canvasTool 行为侧**无缺陷**",
       J[11]["evidence"]["defectFound"] is False)
    ck("产物：判据 13 是阳性对照而非否定结论",
       "阳性对照" in J[13]["text"]
       and J[13]["evidence"]["positiveControl"] is not None)
    ck("产物：返工 5 条，含 R34（派生层读错键名）与 R38（阴性对照漏放）",
       len(a["rework"]) == 5
       and any(r["id"] == "R34" for r in a["rework"])
       and any("两轮一致" in r["lesson"] for r in a["rework"])
       and any(r["id"] == "R38" for r in a["rework"]))
    ck("产物：不声称 ≥ 8 条且含「没有与源站对照」",
       len(a["notClaimed"]) >= 8
       and any("源站" in s for s in a["notClaimed"]))

    # ================= 原始读数交叉核对 =================
    ck("原始：探针 a 的 pan 态 nodeHit 确实是 false（760a 的错读要被留痕）",
       rw["probeA_pan_nodeHit"] is False)
    ck("原始：探针 a 两格分组框都移动",
       rw["probeA_withChild_moved"] and rw["probeA_empty_moved"])
    ck("原始：760b 重算的 childAbsDelta 与 groupDelta 逐位相同",
       rw["recomputed_childFollows"]["absDeltaIdenticalToGroup"] is True)
    ck("原始：760b 重算的相对位移确为 [0,0]",
       rw["recomputed_childFollows"]["relDeltaIsZero"] is True)
    ck("原始：产物判据 3/4 的证据与 760b 重算结果一致",
       J[3]["evidence"]["groupDelta"] == rw["recomputed_childFollows"]["groupDelta"]
       and J[3]["evidence"]["childAbsDelta"]
       == rw["recomputed_childFollows"]["childAbsDelta"]
       and J[4]["evidence"]["childRelBefore"]
       == rw["recomputed_childFollows"]["childRelBefore"])
    ck("原始：产物判据 6 的撤销结论与重算一致",
       J[6]["evidence"]["groupRelRestored"]
       == rw["recomputed_undo"]["groupRelRestored"]
       and J[6]["evidence"]["pastBackTo"] == rw["recomputed_undo"]["pastBackTo"])
    ck("原始：pan 态 nodeDragMoved 确为 false（不是探针没送到）",
       rw["recomputed_matrix"]["pan"]["nodeDragMoved"] is False)
    ck("原始：pan 态 nodeDragPastDelta 为 0（连历史都没进）",
       rw["recomputed_matrix"]["pan"]["nodeDragPastDelta"] == 0)
    ck("原始：select 态 nodeDragMoved 为 true 且 groupMovedWhileNodeDragged 为 false",
       rw["recomputed_matrix"]["select"]["nodeDragMoved"] is True
       and rw["recomputed_matrix"]["select"]["groupMovedWhileNodeDragged"] is False)
    ck("原始：产物手势矩阵与重算一致（两态 × 五项）",
       all(J[8 if t == "select" else 9]["evidence"][k]
           == rw["recomputed_matrix"][t][k]
           for t in ("select", "pan")
           for k in ("paneLeftDrag", "paneLeftDeltaX", "paneMiddleDrag",
                     "paneMiddleDeltaX", "nodeDragMoved", "nodeDragDelta",
                     "nodeDragPastDelta", "groupMovedWhileNodeDragged")))
    ck("原始：pan 态分组框不可拖（groupMoved=false、pastDelta=0）",
       rw["panGroupDrag"]["groupMoved"] is False
       and rw["panGroupDrag"]["pastDelta"] == 0
       and J[10]["evidence"]["groupMoved"] is False)
    ck("原始：两态的命中点回到同一坐标（760b 复位生效）",
       rw["recomputed_matrix"]["select"]["nodePoint"]
       == rw["recomputed_matrix"]["pan"]["nodePoint"]
       and isinstance(rw["recomputed_matrix"]["select"]["nodePoint"], dict))

    # ★★ R34 的正主：按**正确键名**重算的派生量，必须与产物逐格相等
    prod_steps = J[12]["evidence"]["steps"]
    rec_steps = rw["recomputed_steps"]
    ck("原始：760c 派生量按正确键名重算 —— 步数与步骤名一致",
       len(prod_steps) == len(rec_steps) == 5
       and [s["step"] for s in prod_steps] == [s["step"] for s in rec_steps],
       [s.get("step") for s in prod_steps])
    ck("原始：产物 labelMatchesTool 与重算逐格一致（应 5/5 全 true）",
       [s["labelMatchesTool"] for s in prod_steps]
       == [s["labelMatchesTool"] for s in rec_steps]
       and all(s["labelMatchesTool"] for s in rec_steps))
    ck("原始：产物 pressedIsTrue 与重算逐格一致（C1 为 true、其余 false）",
       [s["pressedIsTrue"] for s in prod_steps]
       == [s["pressedIsTrue"] for s in rec_steps]
       and [s["step"] for s in rec_steps if s["pressedIsTrue"]]
       == ["C1-面板已开未选工具"])
    ck("原始：★ 产物 highlightMatchesTool 与重算逐格一致"
       "（若派生层读错键名，这里必然不等）",
       [s["highlightMatchesTool"] for s in prod_steps]
       == [s["highlightMatchesTool"] for s in rec_steps])
    ck("原始：高亮不一致的步骤集合与重算一致（3 格：C1/C2/C3）",
       J[12]["evidence"]["highlightDisagrees"] == rw["recomputed_disagree"]
       and len(rw["recomputed_disagree"]) == 3,
       rw["recomputed_disagree"])
    ck("原始：高亮一致的步骤集合与重算一致（2 格，且恰好都是 select）",
       J[12]["evidence"]["highlightAgrees"] == rw["recomputed_agree"]
       and len(rw["recomputed_agree"]) == 2)
    ck("原始：重算确认唯一 pressed 的那一格工具是 select"
       "（即高亮亮着时画布并不在抓手模式）",
       [s["canvasTool"] for s in rec_steps if s["pressedIsTrue"]] == ["select"])
    ck("原始：重算确认工具已是 pan 的两格高亮都灭着",
       all(not s["pressedIsTrue"] for s in rec_steps
           if s["canvasTool"] == "pan"))
    ck("原始：阳性对照读数在（面板开时圆点 [true,false] 对应 select）",
       rw["panelDots"] and rw["panelDots"][0]["dots"] == [True, False]
       and J[13]["evidence"]["positiveControl"]["dots"] == [True, False])
    ck("原始：data-canvas-tool 运行时元素数两态都为 1",
       rw["attrConsumers"] == 1
       and rw["recomputed_matrix"]["select"]["attrCount"] == 1
       and rw["recomputed_matrix"]["pan"]["attrCount"] == 1)
    ck("原始：产物 deadAttr 的运行时计数与读数一致",
       f["deadAttrDataCanvasTool"]["attrCountRuntime"] == rw["attrConsumers"]
       and f["deadAttrDataCanvasTool"]["readersInSrc"] == 0)

    # ---------- 堵 R33 那类洞：同一事实存两份时，两份都要被守住 ----------
    # (a) 「单向跟随」这件事在 findings 与判据 3/4/5 里各存了一份
    ck("结构：findings.childFollowsParent 与判据 3 的证据是同一份读数",
       f["childFollowsParent"] == J[3]["evidence"])
    ck("结构：判据 4/5 的 childRel 与 parentId 也与 findings 同源",
       J[4]["evidence"]["childRelBefore"]
       == f["childFollowsParent"]["childRelBefore"]
       and J[4]["evidence"]["childRelAfter"]
       == f["childFollowsParent"]["childRelAfter"]
       and J[5]["evidence"]["parentIdKept"]
       == f["childFollowsParent"]["parentIdKept"])
    ck("结构：findings.panGroupDrag 与判据 10 的证据是同一份读数",
       f["panGroupDrag"] == J[10]["evidence"])

    # (b) 派生布尔之外，**被派生的原始字段本身**也要跟 /tmp 原始读数对账
    #     （只守派生层 ⟹ 伪造 ariaPressed 能蒙混过关，这是 R33 的老洞）
    RAW_FIELDS = ("canvasTool", "panelOpen", "label", "ariaPressed")
    mismatched = [
        "%s.%s: 产物=%s 原始=%s" % (p["step"], fld, p.get(fld), r.get(fld))
        for p, r in zip(prod_steps, rec_steps)
        for fld in RAW_FIELDS if p.get(fld) != r.get(fld)
    ]
    ck("原始：★ 产物 5 格的原始字段（canvasTool/panelOpen/label/ariaPressed）"
       "逐格与 /tmp 读数相等", not mismatched, mismatched)
    ck("原始：产物每格 pressedIsTrue 与该格 ariaPressed 字段自洽",
       all(p["pressedIsTrue"] == (p["ariaPressed"] == "true")
           for p in prod_steps))
    ck("原始：产物每格 labelMatchesTool 与该格 canvasTool/label 字段自洽",
       all(p["labelMatchesTool"]
           == (p["label"] == ("抓手工具" if p["canvasTool"] == "pan" else "移动"))
           for p in prod_steps))
    ck("原始：产物每格 highlightMatchesTool 由该格 label+ariaPressed 现算得出",
       all(p["highlightMatchesTool"]
           == ((p["label"] == "抓手工具") == (p["ariaPressed"] == "true"))
           for p in prod_steps))
    return None


def negative_controls(a, st, rw):
    """注入式阴性对照：每一条伪造都必须被上面那组检查抓到。"""
    cases = []

    def inj(name, mutate):
        bad = copy.deepcopy(a)
        mutate(bad)
        failed = [c["label"] for c in run_checks(bad, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # 1. 推翻单向跟随的核心读数
    inj("伪造 childAbsDelta 与 groupDelta 不等（推翻判据 3/4）", lambda x:
        x["findings"]["childFollowsParent"].__setitem__(
            "absDeltaIdenticalToGroup", False))

    # 2. ★ R34 复现：派生布尔全刷成 true（只改结论层，不改读数）
    def _r34(x):
        for s in x["judgments"][11]["evidence"]["steps"]:
            s["highlightMatchesTool"] = True
        x["judgments"][11]["evidence"]["highlightDisagrees"] = []
    inj("R34 复现：highlightMatchesTool 全刷 true（不改任何原始读数）", _r34)

    # 3. 伪造 labelMatchesTool
    inj("伪造 labelMatchesTool 第 0 格为 false（与重算矛盾）", lambda x:
        x["judgments"][11]["evidence"]["steps"][0].__setitem__(
            "labelMatchesTool", False))

    # 4. 把「pan 态节点不可拖」说成可拖
    inj("伪造 pan 态 nodeDragMoved=true", lambda x:
        x["judgments"][8]["evidence"].__setitem__("nodeDragMoved", True))

    # 5. 伪造撤销复原
    inj("伪造 groupRelRestored=true 但 past 没回去", lambda x:
        x["judgments"][5]["evidence"].__setitem__("pastBackTo", 1))

    # 6. 伪造死属性有读取方
    inj("伪造 data-canvas-tool 有 1 个读取方", lambda x:
        x["findings"]["deadAttrDataCanvasTool"].__setitem__("readersInSrc", 1))

    # 7. 只改结论不改读数：把判据 7 的更正抹掉
    inj("抹掉判据 7 的「更正 757」措辞", lambda x:
        x["judgments"][6].__setitem__("text", "分组框与成员无关"))

    # 8. 伪造一致性
    inj("伪造三段探针两轮不一致", lambda x:
        x["twoRound"].__setitem__("allConsistent", False))

    # 9. 篡改阳性对照
    inj("伪造阳性对照圆点为 [false,true]", lambda x:
        x["judgments"][12]["evidence"].__setitem__(
            "positiveControl", {"step": "C1-面板已开未选工具",
                                "tool": "select", "dots": [False, True]}))

    # 10. 清空不声称清单
    inj("清空不声称清单", lambda x: x.__setitem__("notClaimed", []))

    # 11. 删一条判据
    inj("删掉判据 12", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["no"] != 12]))

    # 12. 篡改 pan 态分组框拖动结论
    inj("伪造 pan 态分组框可拖", lambda x:
        x["findings"]["panGroupDrag"].__setitem__("groupMoved", True))

    # 13. 篡改 aria-pressed 那一格（伪造成「工具是 pan 时高亮亮着」）
    inj("伪造 C2 的 ariaPressed=true", lambda x:
        x["judgments"][11]["evidence"]["steps"][2].__setitem__(
            "ariaPressed", "true"))

    # 14. 只改 findings 那一份、让两份读数不同源
    inj("伪造 findings 与判据 3 的证据不同源", lambda x:
        x["judgments"][2]["evidence"].__setitem__("groupDelta", [1, 1]))

    # 15. 篡改某格 canvasTool（原始字段，不是派生量）
    inj("伪造 C1 的 canvasTool=pan（原始字段层）", lambda x:
        x["judgments"][11]["evidence"]["steps"][1].__setitem__(
            "canvasTool", "pan"))

    # 16. 只让 pressedIsTrue 与 ariaPressed 自相矛盾
    inj("伪造某格 pressedIsTrue 与 ariaPressed 不同步", lambda x:
        x["judgments"][11]["evidence"]["steps"][3].__setitem__(
            "pressedIsTrue", True))

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
    except Exception as e:  # 缺原始读数 → 判失败，不许通过
        rw, rawErr = {}, str(e)

    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 760, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:160]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 760 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
