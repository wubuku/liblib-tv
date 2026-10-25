"""batch 753 验收器：画布多选态可达性 + 选择/图记账命令真跑

本批与 741–751 的验收结构相同（与 752 不同，752 的源站读数是一次性现场快照）：
运行时读数由 `/tmp/dbg753{a..h}.py` 采集、汇编进
`docs/research/liblib-canvas-batch753-2026-10-01/runtime-audit.json`，
本验收器**只读已落盘的产物 + 直接从 `src/` 复核静态实现**。

三层校验：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （`includeExternalEdges` 表达式、`children.length < 2` 硬门、
      `selectedNodeIds: childIds`、`panOnDrag` 键号数组、`setEdges` 零调用点…）。
     这一层不依赖任何运行时读数，是判据的「实现对账」半边。
     （第一版这里假失败过 3 次 —— 排除范围只按文件名、漏了 frameos 路由页，
      见 audit 的 rework R7。）
  2. **产物层** —— 判据条数、两轮一致性、易变字段剔除、返工条目、不声称清单。
  3. **原始读数交叉核对** —— 若 `/tmp/vb753h.json` 还在（本机环境），
     把产物里的关键读数与探针原始输出逐个对账，
     防止汇编时抄错（**数字不许手抄**，751/752 立）。
     该层缺失时降级为「跳过」而不是「通过」。

★ ★★ Batch 867 修正：★ 旧实现把「跳过」**当成失败**（`pass: False` 且**计入分母**）
⟹ ⟹ ⟹ ⟹ **门禁永远红** ⟹ ⟹ 而那 13 条真判据其实**全绿**。
⟹ ⟹ ★ 现在「跳过」**真的跳过** ⟹ ⟹ **不计入分母** ⟹ ⟹ 但在报告里
⟹ ⟹   ⟹ ⟹ `skipped` 清单**显式留痕** ⟹ ⟹ 且退出码仍由**真正跑了的那几条**决定。
⟹ ⟹ ★ **不是**改成「通过」 ⟹ ⟹ 那是**掩盖**。

判据 **13 条**（★ 另有 1 条交叉核对层**可能跳过**）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch753-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAW = pathlib.Path("/tmp/vb753h.json")


def static_side():
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    # ★ ★★ Batch 867：★ **剥掉注释**的源码 ⟹ ⟹ 用于「某串**没有**被使用」这类判据
    #   ⟹ ⟹ ★ 因为源码的注释里会**提到**那个名字 ⟹ ⟹ 「全文不含」会被骗到
    #   ⟹ ⟹ ★ 这与 batch 866 的 `785` docstring 坑**完全同型**
    #   ⟹ ⟹ ★ 而 `758` 已经在做同一件事（★ `onPaneDoubleClick` 那条）
    _page_code = re.sub(r"/\*[\s\S]*?\*/", " ", page)
    _page_code = re.sub(r"//[^\n]*", " ", _page_code)
    routing = (ROOT / "src/lib/libtvReactFlowChangeRouting.ts").read_text(
        encoding="utf-8")
    edge = (ROOT / "src/components/nodes/DeletableEdge.tsx").read_text(
        encoding="utf-8")

    # 只扫**画布自己的树**：frameos / jimeng 是另外两个原型，各有同名的
    # store action 与路由页，按文件名排除 store 是不够的
    # （第一版就漏了 src/app/frameos/canvas/[id]/page.tsx，静态断言假失败 —— rework R7）。
    OTHER_APP = ("frameos", "jimeng")
    OTHER_STORE = ("frameosStore.ts", "jimengStore.ts")

    def in_canvas_tree(p):
        rel = str(p.relative_to(ROOT))
        if p.name in OTHER_STORE:
            return False
        if any(f"/{k}" in rel or rel.startswith(f"src/{k}")
               for k in OTHER_APP):
            return False
        return True

    def scan(pattern, skip_declaration_file=None):
        hits = []
        for p in sorted(list((ROOT / "src").rglob("*.ts"))
                        + list((ROOT / "src").rglob("*.tsx"))):
            if not in_canvas_tree(p):
                continue
            if skip_declaration_file and p.name == skip_declaration_file:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(pattern, line):
                    hits.append(f"{p.relative_to(ROOT)}:{i}")
        return sorted(hits)

    set_edges_hits = scan(r"\bsetEdges\b")
    dup_node_hits = scan(r"\bduplicateNode\b", "canvasStore.ts")
    remove_node_hits = scan(r"\bremoveNode\b", "canvasStore.ts")

    # ★ ★★ Batch 867：★ 「声明 vs 实现」靠**形态**区分 ⟹ ⟹ **不靠行号**
    #   ⟹ ⟹ （★ `store` 在这里才拿得到 ⟹ ⟹ 所以必须放进 `static_side()` 的返回值）
    set_edges_is_decl = any(
        re.search(r"^\s*setEdges:\s*\(edges: Edge\[\], options\?: SetGraphOptions\)\s*=>\s*void;\s*$",
                  line)
        for line in store.split("\n"))
    set_edges_is_impl = any(
        re.search(r"^\s*setEdges:\s*\(edges: Edge\[\], options\?: SetGraphOptions\)\s*=>\s*\{",
                  line)
        for line in store.split("\n"))

    return {
        "dupIncludeExternal": bool(re.search(
            r"requestedIds\.length === 1 && !includesGroup", store)),
        "dupEdgeFilterBoth": "sourceCopied && targetCopied" in store.replace(" ", " "),
        "dupEdgeFilterEither": "sourceCopied || targetCopied" in store,
        "groupHardGate": bool(re.search(
            r"if \(children\.length < 2\) return state;", store)),
        "ungroupSelectsChildren": bool(re.search(
            r"selectedNodeIds: childIds", store)),
        "removeSelectedNoHistoryGuard": bool(re.search(
            r"if \(!currentCanvas \|\| requestedIds\.size === 0\) return state;", store)),
        "withDescendantIds": "const removedIds = withDescendantIds(currentCanvas" in store,
        "setEdgesHits": sorted(set_edges_hits),
        "setEdgesIsDecl": set_edges_is_decl,
        "setEdgesIsImpl": set_edges_is_impl,
        "duplicateNodeHits": sorted(set(dup_node_hits)),
        "removeNodeHits": sorted(set(remove_node_hits)),
        "panOnDrag": bool(re.search(
            r"panOnDrag=\{effectivePan \? \[0, 1\] : \[1\]\}", page)),
        "nodesDraggable": bool(re.search(
            r"nodesDraggable=\{canvasTool === \"select\" && !effectivePan\}", page)),
        "selectionOnDragFalse": "selectionOnDrag={false}" in page,
        "noOnNodeClickMeta": bool(re.search(
            r"onNodeClick=\{\(event, node\) => \{\s*if \(!event\.metaKey", page)),
        # ★ ★★ Batch 867：★ 用**剥注释后**的源码 ⟹ ⟹ 免得被注释里的提及骗到
        "noOnEdgeClick": "onEdgeClick" not in _page_code,
        "deleteEdgeEvent": 'window.addEventListener("delete-edge", handler)' in page,
        "edgeBtnGate": (
            'isActive\n                ? "opacity-100 scale-100 pointer-events-auto"' in edge
            and '? "opacity-100 scale-100 pointer-events-auto"\n'
                '                : "opacity-0 scale-50 pointer-events-none"' in edge
            and "hovered || selected" in edge),
        "edgeBtnAria": 'aria-label="删除连线"' in edge,
        "routingSelectToggles": "selectedIds.push(delta.elementId)" in routing,
        "routingSelectCase": 'case "select"' in routing,
    }


def main():
    if not AUDIT.exists():
        print(f"❌ 缺少 {AUDIT}")
        return 1
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    J = {j["no"]: j for j in audit["judgments"]}
    raw = json.loads(RAW.read_text(encoding="utf-8")) if RAW.exists() else None
    if raw:
        r1 = raw["rounds"][0]
    else:
        r1 = None

    checks = []

    def ck(label, cond, got=None, skipped=False):
        """★ Batch 867：★ 加 `skipped` ⟹ ⟹ 「跳过」**不计入分母**。

        ★ ★★ 修的是**声明与实现不一致**：★ 本文件的文档头写的是
        ⟹ ⟹ 「该层缺失时降级为『跳过』而不是『通过』」
        ⟹ ⟹ ★ 而旧实现是 `pass: False` **且计入分母**
        ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ **「跳过」被实现成了「失败」**
        ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 门禁**永远红** ⟹ ⟹ 而那 13 条真判据其实**全绿**。

        ★ ★★ 为什么**不是**改成「通过」：★ 那是**掩盖**。
        ⟹ ⟹ 「原始读数交叉核对」这层的**存在意义**就是「数字不许手抄」
        ⟹ ⟹ 它没跑 ⟹ ⟹ 就该**明说没跑** ⟹ ⟹ 而不是假装通过。
        ⟹ ⟹ ⇒ **跳过 ⟹ ⟹ 不计入分母 ⟹ ⟹ 但在报告里显式留痕**
        ⟹ ⟹   ⟹ ⟹ （`skipped: true` ＋ 单独的 `skipped` 清单）
        ⟹ ⟹   ⟹ ⟹ 且**退出码**仍由**真正跑了的那几条**决定。
        """
        checks.append({"label": label, "pass": bool(cond), "got": got,
                       "skipped": bool(skipped)})

    # ---- 1. 静态层：实现事实 ----
    ck("静态 includeExternalEdges 表达式在位（N=1/N=2 差分的根据）",
       st["dupIncludeExternal"])
    ck("静态 边过滤两分支都在（|| 与 &&）",
       st["dupEdgeFilterEither"] and st["dupEdgeFilterBoth"],
       {"either": st["dupEdgeFilterEither"], "both": st["dupEdgeFilterBoth"]})
    ck("静态 groupSelectedNodes 的 children.length<2 硬门在位",
       st["groupHardGate"])
    ck("静态 ungroupSelectedNodes 把选中集设成全部子节点",
       st["ungroupSelectsChildren"])
    ck("静态 withDescendantIds 级联在位", st["withDescendantIds"])
    ck("静态 panOnDrag 是键号数组 [1]/[0,1]", st["panOnDrag"])
    ck("静态 nodesDraggable 门在位", st["nodesDraggable"])
    ck("静态 selectionOnDrag={false} 在位（框选是 Shift+拖 另一条路）",
       st["selectionOnDragFalse"])
    ck("静态 onNodeClick 带 metaKey/ctrlKey 时短路 selectNode",
       st["noOnNodeClickMeta"])
    ck("静态 page.tsx 确实没有 onEdgeClick（但边仍可选中 ⟹ 走 onEdgesChange）",
       st["noOnEdgeClick"])
    ck("静态 delete-edge 事件桥在位", st["deleteEdgeEvent"])
    ck("静态 删边按钮的 opacity/pointer-events 真门在位", st["edgeBtnGate"])
    ck("静态 删边按钮 aria-label=删除连线", st["edgeBtnAria"])
    ck("静态 变更路由对 select 走 toggle（多选的活路）",
       st["routingSelectCase"] and st["routingSelectToggles"])
    # ★ ★★ Batch 867：★ 去掉**写死的行号**。
    #   ⟹ ⟹ 旧写法 `all(h.endswith(("canvasStore.ts:387", "canvasStore.ts:3415")))`
    #   ⟹ ⟹ ★ **行号当断言** ⟹ ⟹ 源码一改（声明挪一行、实现挪二百多行）就漂
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 门禁红 ⟹ ⟹ 而那个红**与它要验的性质毫无关系**
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 它要验的是「**零调用点**」⟹ ⟹ 那仍然成立
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 与 batch 866 整改的 `785` **完全同型**。
    #   ⟹ ⟹ ★ 修法：★ **按性质断言** ⟹ ⟹
    #   ⟹ ⟹   ① 命中数仍是 2（声明 + 实现）；
    #   ⟹ ⟹   ② 两处**都在 canvasStore.ts 里**（不是别的文件）；
    #   ⟹ ⟹   ③ 一处是**接口声明**、一处是**实现**（靠「有没有 `=>`」区分，
    #   ⟹ ⟹      ⟹ ⟹ **不靠行号** ⟹ ⟹ ⟹ ★ 行号只当提示）。
    set_edges_files = {h.rsplit(":", 1)[0] for h in st["setEdgesHits"]}
    ck("静态 canvasStore.setEdges 全应用只剩声明+实现（零调用点死 action）",
       len(st["setEdgesHits"]) == 2
       and set_edges_files == {"src/store/canvasStore.ts"}
       and st["setEdgesIsDecl"] and st["setEdgesIsImpl"],
       st["setEdgesHits"])
    ck("静态 canvasStore.duplicateNode 无 UI 调用点",
       st["duplicateNodeHits"] == [], st["duplicateNodeHits"])
    ck("静态 canvasStore.removeNode 无 UI 调用点",
       st["removeNodeHits"] == [], st["removeNodeHits"])

    # ---- 2. 产物层 ----
    ck("判据 13 条", audit.get("judgeCount") == 13 == len(audit["judgments"]),
       audit.get("judgeCount"))
    ck("两轮一致（剔除易变字段后 diff 为空）",
       audit["twoRound"]["consistent"] is True
       and audit["twoRound"]["diff"] == {})
    ck("易变字段只有 group_geom.id，且原始比对里只有它跳出来",
       audit["twoRound"]["volatileExcluded"] == ["group_geom.id"]
       and audit["twoRound"]["rawDiffBeforeVolatileFilter"] == ["group_geom"],
       {"excluded": audit["twoRound"]["volatileExcluded"],
        "raw": audit["twoRound"]["rawDiffBeforeVolatileFilter"]})
    ck("轮间独立性写明是整页 reload", "reload" in audit["twoRound"]["independence"])
    ck("返工条目 7 条（全是探针/判据/验收器自己的错）",
       len(audit.get("rework", [])) == 7, len(audit.get("rework", [])))
    ck("返工覆盖 R1 被覆盖元素 / R2 起点落节点 / R3 选框退化 / "
       "R4 拖动循环没乘 i / R5 口头数字 / R6 静态死锁 / R7 验收器排除范围",
       {r["id"] for r in audit["rework"]}
       == {"R1", "R2", "R3", "R4", "R5", "R6", "R7"})
    ck("不声称清单非空", len(audit.get("notClaimed", [])) >= 5)
    ck("本批明确解掉了多选不可达那条挂起项（判据1/2/3 三条都在讲多选，"
       "且判据3 自己声明了两轮一致）",
       all(k in J[n]["title"] for n, k in
           ((1, "加选"), (2, "Meta"), (3, "框选")))
       and "推翻" in J[1]["why"] and J[3]["twoRound"] is True)

    # ---- 3. 运行时读数 ----
    ck("判据1 Meta+点击加选 → n=2", J[1]["evidence"]["multi_MetaClick"] == 2)
    ck("判据2 只有 Meta 累加，Ctrl/Shift 都是 1",
       J[2]["evidence"]["multi_CtrlClick"] == 1
       and J[2]["evidence"]["multi_ShiftClick"] == 1)
    ck("判据3 Shift+拖框选一次选满 10 个",
       J[3]["evidence"]["boxSelect_n"] == 10
       and J[3]["evidence"]["coversAll"] is True)
    ck("判据4 Cmd+D 差分 N1 边+3 / N2 边+1（节点 +1 / +2）",
       J[4]["evidence"]["N1"] == {"nodeDelta": 1, "edgeDelta": 3}
       and J[4]["evidence"]["N2"] == {"nodeDelta": 2, "edgeDelta": 1},
       J[4]["evidence"])
    ck("判据5 G 的硬门：N=1 零变化", J[5]["evidence"]["group_N1_noop"] is True)
    ck("判据6 组几何 (100,-219,1350,874) 四项与 ±32 包围盒对平",
       (lambda g: g["x"] == 100 and g["y"] == -219
        and g["w"] == 1350 and g["h"] == 874
        and g["title"] == "组合节点" and g["kind"] == "selection"
        and g["z"] == -1001 and sorted(g["children"]) ==
        ["b-bTLLuU4w5q", "i-1FQ9tErTcC"])(J[6]["evidence"]["geom"]),
       J[6]["evidence"]["geom"])
    ck("判据7 解组后选中集 = 全部子节点（第三条多选入口）",
       J[7]["evidence"]["ungroup_selectedN"] == 2
       and sorted(J[7]["evidence"]["ids"])
       == ["b-bTLLuU4w5q", "i-1FQ9tErTcC"])
    ck("判据8 多选删除存活 3 条边且与静态清单逐项一致",
       J[8]["evidence"]["nodeDelta"] == -2
       and J[8]["evidence"]["edgeDelta"] == -8
       and J[8]["evidence"]["keptMatchesStaticList"] is True,
       J[8]["evidence"]["kept"])
    ck("判据9 级联删分组：节点-2 边-4，另一个分组还在",
       J[9]["evidence"]["nodeDelta"] == -2
       and J[9]["evidence"]["edgeDelta"] == -4
       and J[9]["evidence"]["groupsLeft"] == ["g-245IDFh8sB"])
    ck("判据10 删边按钮门 opacity 0→1 / pointer-events none→auto / topIsBtn",
       J[10]["evidence"]["btnBefore"]["opacity"] == "0"
       and J[10]["evidence"]["btnBefore"]["pe"] == "none"
       and J[10]["evidence"]["btnBefore"]["topIsBtn"] is False
       and J[10]["evidence"]["btnAfter"]["opacity"] == "1"
       and J[10]["evidence"]["btnAfter"]["pe"] == "auto"
       and J[10]["evidence"]["btnAfter"]["topIsBtn"] is True)
    ck("判据10 删边记账：边-1、past+1、该边从选中集清空",
       J[10]["evidence"]["edgeDelta"] == -1
       and J[10]["evidence"]["pastDelta"] == 1
       and J[10]["evidence"]["stillSelected"] is False
       and J[10]["evidence"]["edge_selected"] is True)
    ck("判据11 拖节点 3/3 抓点 moved 且 past+1",
       len(J[11]["evidence"]["dragNode"]) == 3
       and all(x["moved"] and x["pastDelta"] == 1
               for x in J[11]["evidence"]["dragNode"]))
    ck("判据11 Alt+Shift+F 整理 9/10 节点移位 + 出现「还原」48×32",
       J[11]["evidence"]["organize_movedCount"] == 9
       and J[11]["evidence"]["organize_pastDelta"] == 1
       and J[11]["evidence"]["restoreBtn"]
       and J[11]["evidence"]["restoreBtn"][0]["w"] == 48
       and J[11]["evidence"]["restoreBtn"][0]["h"] == 32)
    ck("判据13 中键拖 viewport 变 / 左键拖不变",
       J[13]["evidence"]["middleDrag_vpChanged"] is True
       and J[13]["evidence"]["leftDrag_vpChanged"] is False)

    # ---- 4. 原始读数交叉核对（数字不许手抄）----
    if r1 is not None:
        pairs = [
            ("multi_MetaClick", 2), ("multi_CtrlClick", 1), ("multi_ShiftClick", 1),
            ("boxSelect_n", 10),
            ("dup_N1_nodeDelta", 1), ("dup_N1_edgeDelta", 3),
            ("dup_N2_nodeDelta", 2), ("dup_N2_edgeDelta", 1),
            ("group_N1_noop", True), ("group_N1_pastDelta", 0),
            ("group_N2_nodeDelta", 1), ("group_N2_edgeDelta", 0),
            ("group_N2_selectedN", 1),
            ("ungroup_selectedN", 2),
            ("del_N2_nodeDelta", -2), ("del_N2_edgeDelta", -8),
            ("del_N2_pastDelta", 1),
            ("delGroup_nodeDelta", -2), ("delGroup_edgeDelta", -4),
            ("edge_selected", True), ("removeEdge_edgeDelta", -1),
            ("removeEdge_pastDelta", 1), ("removeEdge_edgeStillSelected", False),
            ("organize_movedCount", 9), ("organize_pastDelta", 1),
            ("middleDrag_vpChanged", True), ("leftDrag_vpChanged", False),
            ("edgeCountInDom", 11),
        ]
        bad = [(k, want, r1.get(k)) for k, want in pairs if r1.get(k) != want]
        ck(f"原始读数交叉核对 {len(pairs)} 项（/tmp/vb753h.json）",
           not bad, bad)
        ck("原始读数：删 N=2 存活边清单逐项一致",
           sorted(r1["del_N2_keptEdges"]) ==
           ["e-VQACH36eJC", "e-XmiJkHfFAL", "e-xNVTHNFZZl"])
        ck("原始读数：撤销后回到种子 10 节点 / 11 边",
           r1["afterUndos"] == {"nodes": 10, "edges": 11}, r1["afterUndos"])
        ck("原始读数：两轮除 group_geom 外全同",
           set(raw["roundDiff"].keys()) == {"group_geom"},
           list(raw["roundDiff"].keys()))
    else:
        # ★ ★★ Batch 867：★ 真的**跳过** ⟹ ⟹ 不计入分母 ⟹ ⟹ 但显式留痕
        ck("原始读数交叉核对（/tmp/vb753h.json 不在本机）",
           True, got="SKIPPED — 该层未跑（探针原始读数不在本机）⟹ ⟹ 不计入分母",
           skipped=True)

    # ★ ★★ Batch 867：★ 分母 = **真正跑了的那几条** ⟹ ⟹ 跳过的不算
    ran = [c for c in checks if not c.get("skipped")]
    skipped = [c for c in checks if c.get("skipped")]
    npass = sum(1 for c in ran if c["pass"])
    report = {
        "batch": 753,
        "checks": checks,
        "passed": npass,
        "total": len(ran),
        # ★ ★★ 跳过的**单独列出** ⟹ ⟹ 报告里**看得见**「有东西没验」
        "skipped": [{"label": c["label"], "got": c["got"]} for c in skipped],
        "skippedCount": len(skipped),
        "static": st,
    }
    (OUTDIR / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"判据 {npass}/{len(ran)}" + (f"（另有 {len(skipped)} 条跳过）" if skipped else ""))
    for c in checks:
        if c.get("skipped"):
            print("  ⏭ " + c["label"][:110] + "  ⟵ " + str(c["got"])[:80])
            continue
        print(("  ✅ " if c["pass"] else "  ❌ ") + c["label"][:110])
        if not c["pass"] and c["got"] not in (None, "SKIPPED — 不算通过"):
            print("       got=" + json.dumps(c["got"], ensure_ascii=False)[:200])
    return 0 if npass == len(ran) else 1


if __name__ == "__main__":
    sys.exit(main())
