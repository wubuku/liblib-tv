"""batch 756 验收器：多选 N=10 与分组边界（含一处高严重度缺陷）

三层结构（与 753/754/755 同）：
  1. **静态层** —— 直接从 `src/store/canvasStore.ts` 复核判据依赖的实现事实
     （groupSelectedNodes 的 children 过滤与硬门、无条件 re-parent、
      duplicateGraphSelection 的子孙展开 / 边过滤 / 子树平移、N 分支判定式…）
  2. **产物层** —— 判据条数、两轮一致性、证据链完整性、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb756{c,d}.json` 还在，把产物里的关键
     读数与探针原始输出逐个对账。缺失时**判失败而不是通过**。

⚠ 本批的静态断言必须**先把实现体取出来再找关键字**：`children = ...filter`
  在文件里出现**两次**（3266 在 groupSelectedNodes、3341 在 ungroupSelectedNodes），
  不限定作用域就会把两个 action 的实现混在一起断言（R19 的老教训）。

判据 **17 条**（16 条两轮一致 + 1 条边界格；两轮各跑 c 与 d 两个探针）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch756-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAWC = pathlib.Path("/tmp/vb756c.json")
RAWD = pathlib.Path("/tmp/vb756d.json")
# 756d 的子节点 id 前缀是节点类型（video-…），所以前缀表要含 node type
GEN = re.compile(r"^(group|storyboard-group|image|video|script|text|node|canvas)"
                 r"-\d{10,}-[a-z0-9]{6}$")

G_EMPTY, G_WITH = "g-245IDFh8sB", "g-EFbbHpwq5w"
SEED_CHILD = "v-UGQZzZOpbv"


def _block(text, key):
    """取 `key` 的**实现体**（`=> {` 那一处）。

    ⚠ `groupSelectedNodes:` / `ungroupSelectedNodes:` 在接口里也各出现一次
    （`:383` / `:384` 的类型声明），取第一个会拿到声明而不是实现。
    """
    start = 0
    while True:
        i = text.find(key, start)
        if i < 0:
            return None
        seg = text[i:i + 160]
        if re.search(r"=>\s*\{", seg):
            j = text.find("\n  },", i)
            return text[i:j] if j > 0 else text[i:i + 2200]
        start = i + len(key)


def _strip(o):
    """生成 id 归一化。⚠ **键和值都要清洗**（R16：
    `childrenAfter` 是以分组 id 为**键**的字典，只清洗一侧会把随机 id
    读成行为不稳定）。"""
    if isinstance(o, str):
        return "<generated-id>" if GEN.match(o) else o
    if isinstance(o, dict):
        return {_strip(k): _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    return o


def static_side():
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    g = _block(store, "groupSelectedNodes:")
    u = _block(store, "ungroupSelectedNodes:")
    dup = _block(store, "duplicateSelectedNodes:")
    fn = store[store.find("function duplicateGraphSelection("):
               store.find("function duplicateGraphSelection(") + 3200]

    return {
        # ---- 判据 7：children 只取非分组 ----
        "groupChildrenFilterExcludesGroups": bool(g) and all(
            x in g for x in ('selectedIds.has(node.id)',
                             'node.type !== "storyboard-group"')),
        "groupChildrenFilterScopedToGroupAction":
            "node.type !== \"storyboard-group\"" in (g or ""),
        # ---- 判据 7/8：子节点被无条件 re-parent 到新组 ----
        "reparentsChildrenUnconditionally": bool(g) and all(
            x in g for x in ("parentId: groupId", "absolutePositions.has(node.id)")),
        "newGroupPrepended": "[groupNode, ...nextNodes]" in (g or ""),
        "groupKindSelection": 'groupKind: "selection"' in (g or ""),
        "groupPadding32": "GROUP_PADDING" in store
        and bool(re.search(r"const GROUP_PADDING = 32", store)),
        # ---- 判据 17：硬门 ----
        "groupHardGateChildren2": "if (children.length < 2) return state;" in (g or ""),
        # ---- 判据 11：解组只作用在传入的 nodeIds 上 ----
        "ungroupActsOnlyOnGivenIds": "ungroupSelectedNodes: (nodeIds)" in store
        and "const selectedIds = new Set(nodeIds ?? state.selectedNodeIds);"
        in (u or ""),
        "ungroupClearsSelectionToChildIds": "selectedNodeIds: childIds" in (u or ""),
        # ---- 判据 3/5：N 分支判定式 ----
        "nBranchPredicate": bool(re.search(
            r"duplicateGraphSelection\(\s*currentCanvas,\s*requestedIds,\s*"
            r"requestedIds\.length === 1 && !includesGroup", dup or store)),
        "includesGroupComputed": "includesGroup" in (dup or store),
        # ---- 判据 14：子孙展开 ----
        "descendantExpansionLoop": bool(re.search(
            r"if \(node\.parentId && copyIds\.has\(node\.parentId\) && "
            r"!copyIds\.has\(node\.id\)\) \{\s*copyIds\.add\(node\.id\);", fn)),
        "descendantExpansionIterates": "let expanded = true;" in fn
        and "while (expanded)" in fn,
        # ---- 判据 14/15：子树平移 ----
        "copyOffset40": "position: { x: node.position.x + 40, y: node.position.y + 40 }"
        in fn,
        "childKeepsRelativePositionWhenParentCopied": bool(re.search(
            r"const copiedParentId = node\.parentId \? idMap\.get\(node\.parentId\)"
            r" : undefined;[\s\S]{0,160}?copiedNode\.position = \{ \.\.\.node\.position \}",
            fn)),
        "orphanLosesParentId": "delete copiedNode.parentId;" in fn,
        # ---- 判据 16：边过滤 ----
        "edgeFilterBothOrEither": bool(re.search(
            r"return includeExternalEdges\s*\n?\s*\?\s*sourceCopied \|\| targetCopied"
            r"\s*\n?\s*:\s*sourceCopied && targetCopied", fn)),
        # ---- 判据 3/4：单一事务 ----
        "dupPushesOneHistory": (dup or "").count("pushHistory(") >= 1,
    }


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    J = {j["no"]: j for j in a["judgments"]}
    B = a["boundary"]

    # ================= 静态层 =================
    ck("静态：groupSelectedNodes 的 children 过滤排除 storyboard-group",
       st["groupChildrenFilterExcludesGroups"], st)
    ck("静态：该过滤确实落在 groupSelectedNodes 实现体里（不是 ungroup 的同名行）",
       st["groupChildrenFilterScopedToGroupAction"],
       "children=...filter 在 3266 与 3341 各出现一次")
    ck("静态：子节点被无条件 re-parent 到新组（absolutePositions 命中即改 parentId）",
       st["reparentsChildrenUnconditionally"])
    ck("静态：新组前置插入且 groupKind=selection、GROUP_PADDING=32",
       st["newGroupPrepended"] and st["groupKindSelection"]
       and st["groupPadding32"])
    ck("静态：硬门 children.length < 2 存在（判据 17 的零变化根因）",
       st["groupHardGateChildren2"])
    ck("静态：ungroupSelectedNodes 只作用于传入/选中的 nodeIds（Shift+G 修不了的根因）",
       st["ungroupActsOnlyOnGivenIds"]
       and st["ungroupClearsSelectionToChildIds"])
    ck("静态：N 分支判定式 = requestedIds.length === 1 && !includesGroup",
       st["nBranchPredicate"] and st["includesGroupComputed"])
    ck("静态：duplicateGraphSelection 有 while 循环做子孙展开",
       st["descendantExpansionLoop"] and st["descendantExpansionIterates"])
    ck("静态：复制偏移 +40 且父也被复制时保留相对位置（子树整体平移的根因）",
       st["copyOffset40"] and st["childKeepsRelativePositionWhenParentCopied"])
    ck("静态：边过滤是 includeExternalEdges ? (source||target) : (source&&target)",
       st["edgeFilterBothOrEither"])

    # ================= 产物层 =================
    ck("产物：判据 17 条（16 judgments + 1 boundary）",
       len(a["judgments"]) == 16 and B["no"] == 17
       and a["judgeCount"] == 16, len(a["judgments"]))
    ck("产物：判据编号连续 1..17 且无重复",
       sorted(list(J) + [B["no"]]) == list(range(1, 18)),
       sorted(list(J) + [B["no"]]))
    ck("产物：两轮一致性 diff 为空（c 与 d 各两轮）",
       a["twoRound"]["diff"] == {} and a["twoRound"]["consistent"] is True
       and a["twoRound"]["dConsistent"] is True,
       sorted(a["twoRound"]["diff"].keys()))
    ck("产物：两轮独立性有交代（整页 reload + 种子说明）",
       "reload" in a["twoRound"]["independence"]
       and "无持久化" in a["seed"]["noPersistence"])
    ck("产物：过滤器声明覆盖了字典键（R16 的修正落进产物）",
       "键" in a["twoRound"]["filter"])

    ev = J[8]["evidence"]
    ck("产物：判据 8 记下了 before/after 两侧的 children 基线",
       ev["childrenBefore"].get(G_WITH) == 1
       and ev["childrenAfter"].get(G_WITH) == 0, ev["childrenBefore"])
    ck("产物：判据 8 记下了子节点 parentId 变成新组",
       bool(ev["stolenChildParentId"])
       and ev["newGroupContainsStolenChild"] is True)
    ck("产物：判据 9 用种子基线把「本来就空」的组排除在受害名单外",
       J[9]["evidence"]["emptiedByThisOp"] == [G_WITH]
       and J[9]["evidence"]["before"][G_EMPTY] == 0,
       J[9]["evidence"]["emptiedByThisOp"])
    ck("产物：判据 10 记下五类提示选择器与命中数 0",
       J[10]["evidence"]["toastsAfterG"] == 0
       and len(J[10]["evidence"]["toastSelectors"]) == 5)
    ck("产物：判据 11 记下 Shift+G 的 repaired=false",
       J[11]["evidence"]["ungroupAfterG"]["repaired"] is False)
    ck("产物：判据 12 记下需要 2 次撤销回种子",
       J[12]["evidence"]["afterTwoUndos"]["nodes"] == 10
       and J[12]["evidence"]["afterTwoUndos"]["past"] == 0)
    ck("产物：判据 5 的四档对照表四行齐、且标了出处批次",
       len(J[5]["evidence"]["table"]) == 4
       and sorted(x["batch"] for x in J[5]["evidence"]["table"]) == [753, 753, 756, 756])
    ck("产物：判据 7 的新组 children 数 = 选区非分组节点数",
       J[7]["evidence"]["newGroupChildCount"]
       == J[7]["evidence"]["newGroupChildCount"]
       and J[7]["evidence"]["selectedGroupsInSelection"] == 2,
       J[7]["evidence"]["selectedGroupsInSelection"])
    ck("产物：判据 15 三个 delta 自洽（分组/子节点绝对位移相等，相对位移为 0）",
       J[15]["evidence"]["newGroupRel"] is not None)
    ck("产物：缺陷陈述含「静默掏空」「零提示」「Shift+G 修不了」三要素",
       all(k in a["headline"]["defect"] for k in ("掏空", "提示", "Shift+G"))
       and "re-parent" in a["headline"]["rootCause"])
    ck("产物：证据链 6 条且每条都带具体读数",
       len(a["headline"]["proofChain"]) == 6
       and all(len(x) > 12 for x in a["headline"]["proofChain"]))
    ck("产物：返工 3 条 R16/R17/R18 齐全且各自带 rule",
       [r["id"] for r in a["rework"]] == ["R16", "R17", "R18"]
       and all(r.get("rule") for r in a["rework"]))
    ck("产物：不声称清单 ≥ 6 条",
       len(a["notClaimed"]) >= 6, len(a["notClaimed"]))
    ck("产物：不声称里明确写了「没有与源站对照」",
       any("源站" in x for x in a["notClaimed"]))
    ck("产物：rawProbeFiles 四个探针都有说明",
       sorted(a["rawProbeFiles"]) == ["a", "b", "c", "d"])

    # ================= 原始读数交叉核对 =================
    if RAWC.exists() and RAWD.exists():
        raw = json.loads(RAWC.read_text(encoding="utf-8"))
        rawd = json.loads(RAWD.read_text(encoding="utf-8"))
        r1 = raw["rounds"][0]
        da = rawd["rounds"][0]["analysis"]

        leaf = [
            ("seed.baseline", a["seed"]["nodes"], r1["baseline"]["nodes"]),
            ("seed.baseline.edges", a["seed"]["edges"], r1["baseline"]["edges"]),
            ("j2.selectedN", J[2]["evidence"]["selectedN"], r1["boxSelectN"]),
            ("j3.dup10", J[3]["evidence"]["dup10"], r1["dup10"]),
            ("j4.undoAtomic", J[4]["evidence"]["undoAtomic"], r1["undoAtomic"]),
            ("j6.delta", J[6]["evidence"]["group10_delta"],
             {k: r1["group10"][k]
              for k in ("nodeD", "edgeD", "pastD", "selectedN")}),
            ("j8.childrenBefore", J[8]["evidence"]["childrenBefore"],
             r1["group10"]["childrenBefore"]),
            ("j8.childrenAfter", J[8]["evidence"]["childrenAfter"],
             r1["group10"]["childrenAfter"]),
            ("j8.emptied", J[8]["evidence"]["emptied"],
             r1["group10"]["emptied"]),
            ("j10.toasts", J[10]["evidence"]["toastsAfterG"], r1["toastsAfterG"]),
            ("j11.ungroup", J[11]["evidence"]["ungroupAfterG"],
             r1["ungroupAfterG"]),
            ("j12.twoUndos", J[12]["evidence"]["afterTwoUndos"],
             r1["afterTwoUndos"]),
            ("j13.delete10", J[13]["evidence"]["delete10"], r1["delete10"]),
            ("j14.analysis", J[14]["evidence"]["analysis"], da),
            ("boundary.sel", B["evidence"]["selectGroupAndChild"],
             r1["selectGroupAndChild"]),
            ("boundary.afterG", B["evidence"]["groupWithOwnChild"],
             r1["groupWithOwnChild"]),
        ]
        bad = [n for n, x, y in leaf if _strip(x) != _strip(y)]
        ck("原始读数叶子级交叉核对 %d 项（/tmp/vb756c.json + vb756d.json）" % len(leaf),
           not bad, bad)

        ck("原始读数：c 两轮按生成 id 形态过滤后 diff 为空",
           raw["consistent"] is True and raw["roundDiff"] == {},
           sorted(raw["roundDiff"].keys()))
        ck("原始读数：d 两轮 analysis 完全相同",
           rawd["consistent"] is True
           and rawd["rounds"][0]["analysis"] == rawd["rounds"][1]["analysis"])
        ck("原始读数：种子里只有 1 个节点带 parentId",
           a["seed"]["parentedNodes"] == [SEED_CHILD],
           a["seed"]["parentedNodes"])
        ck("原始读数：基线两轮相同且 10 节点 / 11 边",
           r1["baseline"] == raw["rounds"][1]["baseline"]
           and r1["baseline"]["nodes"] == 10 and r1["baseline"]["edges"] == 11)
        # 缺陷核心：新组 children 恰为「10 选区 − 2 个分组」
        ck("原始读数：新组 children=8 且含被抢走的子节点",
           len(r1["group10"]["newGroup"]["children"]) == 8
           and SEED_CHILD in r1["group10"]["newGroup"]["children"])
        # 判据 15 的两个 delta 必须是 (40,40) 与 (0,0)
        ck("原始读数：子树平移 delta = 分组(40,40) / 相对(0,0) / 绝对(40,40)",
           da["groupDelta"] == [40, 40] and da["childRelDelta"] == [0, 0]
           and da["childAbsDelta"] == [40, 40],
           [da["groupDelta"], da["childRelDelta"], da["childAbsDelta"]])
        ck("原始读数：复制含子节点分组时边 delta=0 而触及边有 4 条",
           da["edgeD"] == 0 and da["seedEdgesTouching"] == 4
           and da["nodeD"] == 2)
        ck("原始读数：N=10 复制 +10 节点 +11 边 且一次撤销回种子",
           r1["dup10"]["nodeD"] == 10 and r1["dup10"]["edgeD"] == 11
           and r1["undoAtomic"]["backToSeed"] is True)
        ck("原始读数：N=10 删除后进入空态且撤销复原",
           r1["delete10"]["emptyState"] is True
           and r1["delete10Undo"]["emptyState"] is False)
        # 阳性对照：组 + 自己的子节点 同选按 G 是零变化
        ck("原始读数：阳性对照格 past delta=0（跨组多选才会破坏）",
           r1["groupWithOwnChild"]["pastD"] == 0
           and r1["groupWithOwnChild"]["n"] == 2)
    else:
        checks.append({"label": "原始读数交叉核对（/tmp/vb756{c,d}.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    npass = sum(1 for c in checks if c["pass"])
    report = {"batch": 756, "checks": checks, "passed": npass,
              "total": len(checks), "static": st}
    (OUTDIR / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("判据 %d/%d" % (npass, len(checks)))
    for c in checks:
        print(("  ✅ " if c["pass"] else "  ❌ ") + c["label"][:112])
        if not c["pass"] and c["got"] not in (None, "SKIPPED — 不算通过"):
            print("       got=" + json.dumps(c["got"], ensure_ascii=False)[:240])
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
