"""batch 754 验收器：剩下 5 个可跑的记账命令 + 2 个零入口命令的定性

与 753 同样的三层结构：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （`createImageHdPreset` 的 +320/−60 与 430/452、去重返回 accepted、
      拉片结果的 x/y 递推与 48 间距、故事脚本对的选中集、两个零入口 profile…）
  2. **产物层** —— 判据条数、两轮一致性、生成 id 过滤规则、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb754c.json` 还在，把产物里的关键读数
     与探针原始输出逐个对账（**数字不许手抄**）。缺失时**判失败而不是通过**。

判据 **16 条**（14 条两轮一致 + 2 条静态）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch754-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAW_C = pathlib.Path("/tmp/vb754c.json")   # 两轮
RAW_D = pathlib.Path("/tmp/vb754d.json")   # 提示时间序列
RAW_B = pathlib.Path("/tmp/vb754b.json")   # 单轮（源节点偏移）


def static_side():
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    panel = (ROOT / "src/components/AddNodePanel.tsx").read_text(encoding="utf-8")
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    img = (ROOT / "src/components/nodes/ImageNode.tsx").read_text(encoding="utf-8")
    sb = (ROOT / "src/components/nodes/ShotBreakdownNode.tsx").read_text(
        encoding="utf-8")
    res = (ROOT / "src/lib/shotBreakdownResults.ts").read_text(encoding="utf-8")
    empty = (ROOT / "src/components/CanvasEmptyState.tsx").read_text(encoding="utf-8")
    ingress = (ROOT / "src/lib/libtvMediaIngress.ts").read_text(encoding="utf-8")

    cats = re.findall(r'category:\s*"([a-z]+)"', res)
    defs = len(cats)

    # REGISTERED_ASSET_ATTACH 的 UI 调用点（排除类型/表/声明）
    reg_hits = []
    for p in sorted(list((ROOT / "src").rglob("*.ts"))
                    + list((ROOT / "src").rglob("*.tsx"))):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "REGISTERED_ASSET_ATTACH" not in line:
                continue
            # 类型联合行 / profile 表的键名行与 profileId 行 / store 的类型声明，
            # 都不是 UI 调用点（R14：漏了键名行那一处）
            if re.search(r"\|\s*\"REGISTERED_ASSET_ATTACH\"|profileId:"
                         r"\s*\"REGISTERED_ASSET_ATTACH\"|"
                         r"\"GENERATED_HISTORY_ATTACH\"\s*\|\s*"
                         r"\"REGISTERED_ASSET_ATTACH\"|"
                         r"^\s*REGISTERED_ASSET_ATTACH:\s*\{", line):
                continue
            reg_hits.append(f"{p.relative_to(ROOT)}:{i}")

    return {
        "hd_groupGeom": bool(re.search(
            r"position: \{ x: source\.position\.x \+ 320, "
            r"y: source\.position\.y - 60 \}", store))
        and "width: 430" in store and "height: 452" in store,
        "hd_childGeom": bool(re.search(
            r"position: \{ x: 40, y: 60 \},\s*width: 340,\s*height: 330", store)),
        "hd_title": '"预设 - 图片高清"' in store,
        "hd_selectsGroup": "selectedNodeIds: [groupId]" in store,
        "hd_entry": 'data-image-attempt="图片高清"' in img
        and "createImageHdPreset(id)" in img,
        "emptyStateGate": "flowNodes.length === 0 && <CanvasEmptyState />" in page,
        "storyChip": 'data-canvas-empty-chip={chip.id}' in empty
        and 'chip.id === "story-script"' in empty
        and "createStoryScriptPair()" in empty,
        "storySelectsBoth": "selectedNodeIds: [textNode.id, scriptNode.id]" in store,
        "storyXOffset": "x: scriptPos.x + 350" in store,
        "attachSkippedReturnsAccepted": bool(re.search(
            r"if \(attachedAssets\.length === 0\) \{\s*return \{\s*"
            r"status: \"accepted\"", store, re.S)),
        "attachDedupe": "already-referenced" in store or "attachedAssetIds" in store,
        "attachProfileCallSites": panel.count("attachAssetReferences("),
        "cohortSingleTransaction": bool(re.search(
            r"if \(result\.status === \"accepted\"\) \{\s*setStatus\(", panel, re.S)),
        "cohortAutoClose": "window.setTimeout(closePanel, 600)" in panel,
        "cohortStatusText": "个资源" in panel,
        "cohortEntry": 'data-add-node-resource="upload"' in panel,
        "cohortAccept": 'accept="image/png,image/jpeg,image/webp"' in panel,
        "historyEntry": ('data-history-asset="0"' in panel
                         and 'data-history-asset="1"' in panel
                         and "GENERATED_HISTORY_ATTACH" in panel),
        "registeredAssetCallSites": reg_hits,
        "sbDefinitionsByCategory": {c: cats.count(c) for c in set(cats)},
        "sbDefinitionsTotal": defs,
        "sbResultX": "const resultX = sourcePosition.x + nodeWidth(source) + 120;" in store,
        "sbResultYStart": "let resultY = sourcePosition.y - 80;" in store,
        "sbResultYStep": "resultY += definition.dimensions.height + 48;" in store,
        "sbResultXIsSource": True,
        "sbEdgeId": "id: `e-${sourceId}-${node.id}`" in store,
        "sbExistingGuard": "if (existingResults.length > 0) return state;" in store,
        "sbEmptyDimGuard": "if (definitions.length === 0) return state;" in store,
        "sbStartGuards": all(x in sb for x in (
            'status === "empty"', 'status === "complete"',
            "isRunning", "activeDimensions.length === 0")),
        "sbDelay": "}, 700);" in sb,
        "sbStartAttr": "data-shot-breakdown-start" in sb,
        "sbDimsDefault": 'data.dimensions ?? ["storyboard", "motion", "music"]' in sb,
        "sbChooseCanvasVideo": 'status: "ready"' in sb,
        "ingressProfiles": re.findall(r'"([A-Z_]+_ATTACH)"', ingress),
    }


def main():
    if not AUDIT.exists():
        print(f"❌ 缺少 {AUDIT}")
        return 1
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    J = {j["no"]: j for j in audit["judgments"]}
    rc = json.loads(RAW_C.read_text(encoding="utf-8")) if RAW_C.exists() else None
    rd = json.loads(RAW_D.read_text(encoding="utf-8")) if RAW_D.exists() else None
    rb = json.loads(RAW_B.read_text(encoding="utf-8")) if RAW_B.exists() else None
    r1 = rc["rounds"][0] if rc else None

    checks = []

    def ck(label, cond, got=None):
        checks.append({"label": label, "pass": bool(cond), "got": got})

    # ---- 1. 静态层 ----
    ck("静态 高清预设几何 source+(320,−60) / 430×452 / 子 340×330@(40,60)",
       st["hd_groupGeom"] and st["hd_childGeom"])
    ck("静态 高清组 title=预设 - 图片高清 且选中集切到组",
       st["hd_title"] and st["hd_selectsGroup"])
    ck("静态 高清预设入口在 ImageNode 的图片高清芯片上",
       st["hd_entry"])
    ck("静态 空态门 flowNodes.length === 0 才挂 CanvasEmptyState",
       st["emptyStateGate"])
    ck("静态 故事脚本对：芯片 story-script → createStoryScriptPair",
       st["storyChip"])
    ck("静态 故事脚本对把两个节点都放进选中集 + script x 偏移 350",
       st["storySelectsBoth"] and st["storyXOffset"])
    ck("静态 attach 全被跳过时返回 status: accepted（判据5 的根因）",
       st["attachSkippedReturnsAccepted"])
    ck("静态 attach 有去重（attachedAssetIds 语义）", st["attachDedupe"])
    ck("静态 生成历史入口是 data-history-asset + GENERATED_HISTORY_ATTACH",
       st["historyEntry"])
    ck("静态 REGISTERED_ASSET_ATTACH 无 UI 调用点",
       st["registeredAssetCallSites"] == [], st["registeredAssetCallSites"])
    ck("静态 拉片结果 x = 源x+宽+120，y 起 源y−80，每张 +高+48",
       st["sbResultX"] and st["sbResultYStart"] and st["sbResultYStep"])
    ck("静态 拉片结果边 id 形如 e-${sourceId}-${node.id}", st["sbEdgeId"])
    ck("静态 拉片两条守卫：已有结果不重跑 / 定义为空不建节点",
       st["sbExistingGuard"] and st["sbEmptyDimGuard"])
    ck("静态 拉片开始按钮四道门齐全", st["sbStartGuards"])
    ck("静态 拉片延迟 700ms、按钮带 data-shot-breakdown-start、"
       "默认三维度、从画布选择置 ready",
       st["sbDelay"] and st["sbStartAttr"] and st["sbDimsDefault"]
       and st["sbChooseCanvasVideo"])
    ck("静态 拉片定义表 storyboard3 + motion1 + music1 = 5（判据11 的根据）",
       st["sbDefinitionsByCategory"] == {"storyboard": 3, "motion": 1, "music": 1}
       and st["sbDefinitionsTotal"] == 5, st["sbDefinitionsByCategory"])
    ck("静态 cohort 入口是 upload 按钮 + 隐藏 file input（accept 三种图格式）",
       st["cohortEntry"] and st["cohortAccept"])

    # ---- 2. 产物层 ----
    ck("判据 16 条", audit.get("judgeCount") == 16 == len(audit["judgments"]),
       audit.get("judgeCount"))
    ck("两轮一致（按生成 id 形态过滤后 diff 为空）",
       audit["twoRound"]["consistent"] is True and audit["twoRound"]["diff"] == {})
    ck("过滤规则写明是 createNodeId 的 <prefix>-<epoch>-<rand6> 形态",
       "createNodeId" in audit["twoRound"]["filter"]
       and "generated-id" in audit["twoRound"]["filter"])
    ck("轮间独立性写明是整页 reload", "reload" in audit["twoRound"]["independence"])
    ck("返工条目 8 条（全是我自己的错）", len(audit.get("rework", [])) == 8,
       len(audit.get("rework", [])))
    ck("返工覆盖 R8 选择器引擎 / R9 路径表 / R10 accept 绕过 / R11 同 tick 连点 / "
       "R12 正面样本 / R13 时间序列 / R14 验收器正则 / R15 测试顺序污染",
       {r["id"] for r in audit["rework"]}
       == {"R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15"})
    ck("不声称清单非空（≥8 条）", len(audit.get("notClaimed", [])) >= 8,
       len(audit.get("notClaimed", [])))
    ck("accept 拒绝路径明确进了不声称而不是判据",
       any("accept" in x and "没测成" in x for x in audit["notClaimed"]))

    # ---- 3. 运行时读数 ----
    ck("判据1 种子 0 枚芯片 → 加空图片节点后 2 枚",
       J[1]["evidence"]["chipsOnSeedImageNodes"] == 0
       and len(J[1]["evidence"]["chipsAfterAddEmptyImage"]) == 2
       and {c["id"] for c in J[1]["evidence"]["chipsAfterAddEmptyImage"]}
       == {"图生图", "图片高清"})
    ck("判据2 高清预设记账 节点+2 边±0 past+1 选中集=新组",
       J[2]["evidence"]["deltas"] == {"nodeD": 2, "edgeD": 0, "pastD": 1}
       and J[2]["evidence"]["selectionIsNewGroup"] is True)
    ck("判据3 高清预设几何 430×452 + 子 340×330@(40,60)",
       (lambda g: g["group"] and g["group"]["w"] == 430
        and g["group"]["h"] == 452 and g["group"]["x"] == 1666
        and g["group"]["y"] == 687
        and g["child"] and g["child"]["w"] == 340 and g["child"]["h"] == 330
        and g["child"]["x"] == 40 and g["child"]["y"] == 60
        and g["child"]["parentIsGroup"] is True)(J[3]["evidence"]["geom"]))
    ck("判据3 组相对源节点 +(320,−60) 实测自洽",
       J[3]["evidence"]["sourceToGroupOffset"]["dx"] == 320
       and J[3]["evidence"]["sourceToGroupOffset"]["dy"] == -60)
    ck("判据4 attach 记账 节点+1 past+1 且提示是绿色成功",
       J[4]["evidence"]["deltas"] == {"nodeD": 1, "edgeD": 0, "pastD": 1}
       and J[4]["evidence"]["added"][0]["filename"] == "fixture-hist-0"
       and any("已从生成历史添加资源" == x["t"]
               for x in J[4]["evidence"]["status"]))
    ck("判据5 重复 attach 零变化但仍显示成功文案（缺陷成立）",
       J[5]["evidence"]["deltas"] == {"nodeD": 0, "edgeD": 0, "pastD": 0}
       and J[5]["evidence"]["saysSuccessButZeroChange"] is True)
    ck("判据6 换 asset 对照 节点+1",
       J[6]["evidence"]["deltas"]["nodeD"] == 1)
    ck("判据7 REGISTERED_ASSET_ATTACH 零调用点", J[7]["evidence"]["registeredCallSites"] == 0)
    ck("判据8 cohort 节点+2 但 past 只+1（单个图事务）",
       J[8]["evidence"]["deltas"] == {"nodeD": 2, "edgeD": 0, "pastD": 1}
       and len({n["filename"] for n in J[8]["evidence"]["added"]}) == 2)
    ck("判据8 cohort 面板自动关闭", J[8]["evidence"]["panelOpenAfter900ms"] is False)
    ck("判据9 成功提示只活到面板关闭（时间序列：早期有、717ms 已空）",
       (lambda t: any("已添加 2 个资源" == x["text"] for x in t)
        and t[-1]["text"] == "")(J[9]["evidence"]["timeline"]))
    ck("判据10 拉片门链 empty→disabled / ready→enabled / 拉片中 / 拉片完成",
       (lambda i, r, d, f: i[0]["startDisabled"] is True
        and r[0]["startDisabled"] is False
        and "拉片中" in (d[0]["startText"] or "")
        and "拉片完成" in (f[0]["startText"] or ""))(
            J[10]["evidence"]["initial"], J[10]["evidence"]["ready"],
            J[10]["evidence"]["during"], J[10]["evidence"]["after"]))
    ck("判据11 维度数→结果数 3 维出 5 条 / 1 维出 1 条",
       J[11]["evidence"]["threeDims"]["deltas"]["nodeD"] == 5
       and J[11]["evidence"]["threeDims"]["resultEdges"] == 5
       and J[11]["evidence"]["threeDims"]["keys"]
       == ["storyboard-01", "storyboard-02", "storyboard-03", "motion", "music"]
       and J[11]["evidence"]["oneDim"]["allHitsOk"] is True
       and J[11]["evidence"]["oneDim"]["deltas"] == {"nodeD": 1, "edgeD": 1,
                                                      "pastD": 1}
       and J[11]["evidence"]["oneDim"]["keys"] == ["motion"])
    ck("判据12 结果几何 x 相同、y 逐张 = 上一张+高+48、跨 3 种高度",
       J[12]["evidence"]["xAllEqual"] is True
       and J[12]["evidence"]["yRecurrence"] is True
       and len(J[12]["evidence"]["ySeq"]) == 5
       and sorted(J[12]["evidence"]["sizes"])
       == sorted([[1040, 220], [1040, 350], [1040, 680]])
       or sorted(tuple(x) for x in J[12]["evidence"]["sizes"])
       == sorted([(1040, 350), (1040, 680), (324, 220)]))
    ck("判据13 两条守卫：二次 start 零变化 / 维度全关后 disabled",
       J[13]["evidence"]["secondStartNoop"] is True
       and J[13]["evidence"]["allDimsOff"] is True
       and J[13]["evidence"]["startDisabledAfterAllOff"] is True)
    ck("判据14 故事脚本对 节点+2 且选中集=2（第四条多选入口）",
       J[14]["evidence"]["deltas"]["nodeD"] == 2
       and J[14]["evidence"]["deltas"]["edgeD"] == 0
       and J[14]["evidence"]["deltas"]["pastD"] == 1
       and J[14]["evidence"]["selectedN"] == 2
       and len(J[14]["evidence"]["emptyChips"]) == 4)
    ck("判据14 故事脚本对几何：中心 y 相同、script x = text x + 350",
       J[14]["evidence"]["geom"]["sameCenterY"] is True
       and J[14]["evidence"]["geom"]["scriptXIsTextXPlus350"] is True)
    ck("判据15 另 3 枚空态芯片点 1 枚 → 节点+0 + 未接入提示",
       J[15]["evidence"]["deltas"]["nodeD"] == 0
       and any("本地原型：快速生成入口未接入" in x["t"]
               for x in J[15]["evidence"]["status"]))
    ck("判据15 两枚芯片 textContent 含 SD 2.5 角标（精确文本匹配会漏）",
       sum(1 for c in J[15]["evidence"]["otherChips"] if "SD 2.5" in c["t"]) == 2)
    ck("判据16 duplicateNode/removeNode 零入口沿用 753 的静态断言",
       J[16]["evidence"]["hits"] == []
       and "753" in J[16]["evidence"]["concludedIn"])

    # ---- 4. 原始读数交叉核对 ----
    if r1 is not None:
        pairs = [
            ("chips_onSeed", 0), ("hd_deltas", {"nodeD": 2, "edgeD": 0, "pastD": 1}),
            ("hd_hit", True), ("hd_selectionIsNewGroup", True), ("hd_chipsAfter", 0),
            ("attach1_deltas", {"nodeD": 1, "edgeD": 0, "pastD": 1}),
            ("reattach_deltas", {"nodeD": 0, "edgeD": 0, "pastD": 0}),
            ("reattach_saysSuccessButZeroChange", True),
            ("attach2_deltas", {"nodeD": 1, "edgeD": 0, "pastD": 1}),
            ("cohort_deltas", {"nodeD": 2, "edgeD": 0, "pastD": 1}),
            ("cohort_panelOpenAfter900ms", False),
            ("sb3_deltas", {"nodeD": 5, "edgeD": 5, "pastD": 1}),
            ("sb3_resultEdges", 5), ("sb3_xAllEqual", True),
            ("sb3_yRecurrence", True), ("sb_secondStartNoop", True),
            ("pair_deltas", {"nodeD": 2, "edgeD": 0, "pastD": 1}),
            ("pair_selectedN", 2), ("pair_geom", J[14]["evidence"]["geom"]),
        ]
        bad = [(k, want, r1.get(k)) for k, want in pairs if r1.get(k) != want]
        ck(f"原始读数交叉核对 {len(pairs)} 项（/tmp/vb754c.json）", not bad, bad)
        # 与汇编器用**同一个**过滤实现重算，不采信探针自己的路径表结果（R14）
        GEN = re.compile(
            r"^(text|script-v2|image|g|i|group|add-resource|asset-reference|"
            r"shot-breakdown|shot-breakdown-result|node|resource|"
            r"storyboard)-\d{10,}-[a-z0-9]{6}$")

        def _strip(o):
            if isinstance(o, str):
                return "<generated-id>" if GEN.match(o) else o
            if isinstance(o, dict):
                return {k: _strip(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_strip(v) for v in o]
            return o

        q1, q2 = rc["rounds"][0], rc["rounds"][1]
        recomputed = {k for k in set(q1) | set(q2)
                      if k != "log" and _strip(q1.get(k)) != _strip(q2.get(k))}
        ck("原始读数：两轮按生成 id 形态过滤后 diff 为空（验收器内重算，"
           "不采信探针的路径表结果）",
           recomputed == set(), sorted(recomputed))
        ck("原始读数：探针自报的三处「不一致」全部只含生成 id",
           set(rc["roundDiff"].keys()) <= {"hd_added", "pair_selectedIds",
                                           "sb3_results"},
           sorted(rc["roundDiff"].keys()))
        ck("原始读数：baseline 两轮都是 canvas-2 / 10 节点 / 11 边",
           r1["baseline"] == rc["rounds"][1]["baseline"]
           == {"canvasId": "canvas-2", "nodes": 10, "edges": 11, "past": 0, "n": 0})
    else:
        checks.append({"label": "原始读数交叉核对（/tmp/vb754c.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    RE_754E = pathlib.Path("/tmp/vb754e.json")
    if RE_754E.exists():
        e = json.loads(RE_754E.read_text(encoding="utf-8"))
        S = e["summary"]
        ck("原始读数：754e 两格各自两轮一致（/tmp/vb754e.json）",
           S["one-dim"]["consistent"] and S["all-dims-off"]["consistent"]
           and not S["one-dim"]["diff"] and not S["all-dims-off"]["diff"])
        ck("原始读数：1 维差分 = 只留 motion ⟹ 1 个结果 + 1 条边",
           S["one-dim"]["round1"]["allHitsOk"] is True
           and S["one-dim"]["round1"]["deltas"] == {"nodeD": 1, "edgeD": 1,
                                                    "pastD": 1}
           and S["one-dim"]["round1"]["newResultKeys"] == ["motion"],
           S["one-dim"]["round1"])
        ck("原始读数：三维全关 ⟹ start disabled 且零节点变化",
           S["all-dims-off"]["round1"]["allHitsOk"] is True
           and S["all-dims-off"]["round1"]["allDimsOff"] is True
           and S["all-dims-off"]["round1"]["startDisabled"] is True
           and S["all-dims-off"]["round1"]["nodeDeltaWhileAllOff"] == 0,
           S["all-dims-off"]["round1"])
    else:
        checks.append({"label": "754e 两格交叉核对（/tmp/vb754e.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    if rd is not None:
        def _txt(s):
            return (s["panelStatus"].get("t")
                    or (s["anyStatus"][0]["t"] if s["anyStatus"] else ""))

        t = rd["samples"]                       # 原始探针的键是 elapsed
        seen = [s for s in t if "已添加 2 个资源" in _txt(s)]
        gone = [s for s in t if "已添加 2 个资源" not in _txt(s)]
        ck("原始读数：提示在早期采样点可见、后期消失（/tmp/vb754d.json）",
           len(seen) >= 3 and len(gone) >= 3
           and seen[-1]["elapsed"] < gone[0]["elapsed"],
           {"visibleAtMs": [s["elapsed"] for s in seen],
            "goneAtMs": [s["elapsed"] for s in gone]})
    else:
        checks.append({"label": "提示时间序列交叉核对（/tmp/vb754d.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    if rb is not None:
        a3 = [s for s in rb["steps"] if s["tag"].startswith("A3")][0]
        a1 = [s for s in rb["steps"] if s["tag"].startswith("A1")][0]
        src = a1["added"][0]
        grp = next(n for n in a3["added"] if n["type"] == "storyboard-group")
        ck("原始读数：组偏移实测 == 源码里的 +(320,−60)",
           grp["x"] - src["x"] == 320 and grp["y"] - src["y"] == -60,
           {"dx": grp["x"] - src["x"], "dy": grp["y"] - src["y"]})
    else:
        checks.append({"label": "单轮组偏移交叉核对（/tmp/vb754b.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    npass = sum(1 for c in checks if c["pass"])
    report = {"batch": 754, "checks": checks, "passed": npass,
              "total": len(checks), "static": st}
    (OUTDIR / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"判据 {npass}/{len(checks)}")
    for c in checks:
        print(("  ✅ " if c["pass"] else "  ❌ ") + c["label"][:110])
        if not c["pass"] and c["got"] not in (None, "SKIPPED — 不算通过"):
            print("       got=" + json.dumps(c["got"], ensure_ascii=False)[:220])
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
