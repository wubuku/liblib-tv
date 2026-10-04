"""batch 755 验收器：画布切换隔离 + 行内菜单可达性（含一处高严重度缺陷）

三层结构（与 753/754 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （容器的 overflow-hidden、行菜单的 top-full 定位、setActiveCanvas 清选中、
      removeCanvas 的软删除与回退、purgeRemovedCanvas 零调用点…）
  2. **产物层** —— 判据条数、两轮一致性、证据链完整性、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb755d.json` 还在，把产物里的关键读数
     与探针原始输出逐个对账。缺失时**判失败而不是通过**。

判据 **14 条**（13 条两轮一致 + 1 条静态）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch755-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAW = pathlib.Path("/tmp/vb755d.json")
GEN = re.compile(r"^(canvas|text|image|g|i)-\d{10,}-[a-z0-9]{6}$")


def _block(text, key):
    """取 `key` 的**实现体**（`=> {` 那一处）到该 action 块结束之间的源码。

    ⚠ `setActiveCanvas:` 在文件里出现**两次**：先是接口里的类型声明
    （`setActiveCanvas: (id: string) => void;`），后是实现
    （`setActiveCanvas: (id: string) => {`）。取第一个会拿到声明 ——
    这正是 batch 750 立过的「同一模式出现多次时先数清有几处」。
    """
    start = 0
    while True:
        i = text.find(key, start)
        if i < 0:
            return None
        seg = text[i:i + 160]
        # 实现体在 `=> {`，声明体是 `=> void;` / `=> SomeType;`
        if re.search(r"=>\s*\{", seg):
            j = text.find("\n  },", i)
            return text[i:j] if j > 0 else text[i:i + 1600]
        start = i + len(key)


def _noop_menu_item(text, label):
    """菜单项的 onClick 是否只有 closeDropdown()（它写在文案之前）。"""
    i = text.find(label)
    if i < 0:
        return False
    head = text[max(0, i - 400):i]
    k = head.rfind("onClick=")
    if k < 0:
        return False
    seg = head[k:k + 200]
    return "closeDropdown()" in seg and "setActiveCanvas" not in seg \
        and "setEditingId" not in seg and "duplicateCanvas" not in seg \
        and "setPendingDelete" not in seg and "removeCanvas" not in seg


def _strip(o):
    if isinstance(o, str):
        return "<generated-id>" if GEN.match(o) else o
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    return o


def static_side():
    dd = (ROOT / "src/components/CanvasTabDropdown.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    proj = (ROOT / "src/app/project/page.tsx").read_text(encoding="utf-8")

    OTHER = ("frameos", "jimeng")

    def in_canvas_tree(p):
        rel = str(p.relative_to(ROOT))
        if p.name in ("frameosStore.ts", "jimengStore.ts"):
            return False
        return not any(f"/{k}" in rel or rel.startswith(f"src/{k}") for k in OTHER)

    purge_hits = []
    for p in sorted(list((ROOT / "src").rglob("*.ts"))
                    + list((ROOT / "src").rglob("*.tsx"))):
        if not in_canvas_tree(p) or p.name == "canvasStore.ts":
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "purgeRemovedCanvas" in line:
                purge_hits.append(f"{p.relative_to(ROOT)}:{i}")

    return {
        "dropdownOverflowHidden": bool(re.search(
            r'data-liblib-overlay="canvas-dropdown"[\s\S]{0,260}?overflow-hidden', dd)),
        "rowMenuTopFull": bool(re.search(
            r'className="absolute right-2 top-full z-50 w-36', dd)),
        "rowMenuItems": [x for x in ("在新窗口打开", "重命名画布", "复制画布",
                                     "删除画布") if x in dd],
        # ⚠ onClick 写在文案**之前**，且带 `type="button"` ⟹ 用「文案之前的
        # 最近一个 onClick」来判定，不要从文案往后找（R19）
        "openInNewWindowIsNoop": _noop_menu_item(dd, "在新窗口打开"),
        "listMaxH60": "max-h-60 overflow-y-auto" in dd,
        "deleteOnlyWhenMoreThanOne": "canvases.length > 1 && (" in dd,
        "deleteCopyUnrecoverable": "此操作不可恢复" in dd,
        "deleteDialogAria": 'aria-label="删除画布"' in dd,
        # ⚠ action 的签名带类型标注（`(id: string) =>`），正则不要写死 `(id)`
        "setActiveCanvasClearsSelection": _block(
            store, "setActiveCanvas:") is not None
            and all(x in _block(store, "setActiveCanvas:") for x in (
                "selectedNodeIds: []", "selectedNodeId: null",
                "selectedEdgeIds: []")),
        "setActiveCanvasBumpsGeneration": bool(
            _block(store, "setActiveCanvas:") and
            "canvasGeneration: state.canvasGeneration + 1"
            in _block(store, "setActiveCanvas:")),
        # ⚠ 动作真名是 `addCanvas`，不是 `createCanvas`（R19）
        "addCanvasNoBump": (
            _block(store, "addCanvas:") is not None
            and "activeCanvasId: newCanvas.id" in _block(store, "addCanvas:")
            and "canvasGeneration" not in _block(store, "addCanvas:")),
        "removeCanvasSoftDelete": (
            _block(store, "removeCanvas:") is not None
            and "removedCanvases: [" in _block(store, "removeCanvas:")),
        "removeCanvasGuard": "if (canvases.length <= 1) return;" in store,
        "removeCanvasFallback": bool(re.search(
            r"const fallbackCanvas = filtered\[Math\.min\(removedIndex, "
            r"filtered\.length - 1\)\];", store)),
        "removeCanvasDropsHistory": bool(re.search(
            r"historyByCanvas: Object\.fromEntries\([\s\S]{0,220}?"
            r"\[canvasId\]\) => canvasId !== id\)", store)),
        "removedAtIsDate": "new Date().toISOString().slice(0, 10)" in store,
        "purgeHits": sorted(purge_hits),
        "restoreCallSites": len(re.findall(r"restoreCanvas\(", proj)),
        "recycleBinTabInProjectPage": "回收站" in proj,
    }


def main():
    if not AUDIT.exists():
        print(f"❌ 缺少 {AUDIT}")
        return 1
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    J = {j["no"]: j for j in audit["judgments"]}
    raw = json.loads(RAW.read_text(encoding="utf-8")) if RAW.exists() else None
    r1 = raw["rounds"][0] if raw else None

    checks = []

    def ck(label, cond, got=None):
        checks.append({"label": label, "pass": bool(cond), "got": got})

    # ---- 1. 静态层 ----
    ck("静态 下拉容器带 overflow-hidden（缺陷的根因条件）",
       st["dropdownOverflowHidden"])
    ck("静态 行内菜单是 absolute right-2 top-full（定位在行的下方）",
       st["rowMenuTopFull"])
    ck("静态 菜单四项文案齐全",
       st["rowMenuItems"] == ["在新窗口打开", "重命名画布", "复制画布", "删除画布"],
       st["rowMenuItems"])
    ck("静态 「在新窗口打开」的 onClick 只有 closeDropdown()",
       st["openInNewWindowIsNoop"])
    ck("静态 画布列表是 max-h-60 overflow-y-auto",
       st["listMaxH60"])
    ck("静态 「删除画布」菜单项受 canvases.length > 1 门控",
       st["deleteOnlyWhenMoreThanOne"])
    ck("静态 删除确认框文案含「此操作不可恢复」且 role/aria 齐全",
       st["deleteCopyUnrecoverable"] and st["deleteDialogAria"])
    ck("静态 setActiveCanvas 清空三个选中字段",
       st["setActiveCanvasClearsSelection"])
    ck("静态 setActiveCanvas 会 canvasGeneration + 1",
       st["setActiveCanvasBumpsGeneration"])
    ck("静态 addCanvas（不是 createCanvas）不 bump canvasGeneration"
       "（口径不一致，静态记录）",
       st["addCanvasNoBump"])
    ck("静态 removeCanvas 是软删除 + 有 <=1 守卫 + removedAt 是日期串",
       st["removeCanvasSoftDelete"] and st["removeCanvasGuard"]
       and st["removedAtIsDate"])
    ck("静态 删除活动画布回退到 filtered[min(removedIndex, len-1)]",
       st["removeCanvasFallback"])
    ck("静态 removeCanvas 会从 historyByCanvas 里滤掉该画布",
       st["removeCanvasDropsHistory"])
    ck("静态 purgeRemovedCanvas 在画布树里零调用点",
       st["purgeHits"] == [], st["purgeHits"])
    ck("静态 restoreCanvas 的调用点在 /project 页，回收站标签也在那儿",
       st["restoreCallSites"] >= 2 and st["recycleBinTabInProjectPage"],
       {"restoreCallSites": st["restoreCallSites"]})

    # ---- 2. 产物层 ----
    ck("判据 14 条", audit.get("judgeCount") == 14 == len(audit["judgments"]),
       audit.get("judgeCount"))
    ck("两轮一致（按生成 id 形态过滤后 diff 为空）",
       audit["twoRound"]["consistent"] is True and audit["twoRound"]["diff"] == {})
    ck("轮间独立性写明是整页 reload", "reload" in audit["twoRound"]["independence"])
    ck("headline 记录了缺陷 + 根因（Tailwind 类名 overflow-hidden）",
       bool(audit["headline"]["defect"])
       and "overflow-hidden" in audit["headline"]["rootCause"]
       and "top-full" in audit["headline"]["rootCause"])
    ck("证据链 5 条齐全（几何/命中/功能/阳性对照/同页并存）",
       len(audit["headline"]["proofChain"]) == 5)
    ck("返工 4 条（R16 行序 / R17 fitView / R19 验收器与动作名 / R18 阳性对照方法）",
       [r["id"] for r in audit["rework"]] == ["R16", "R17", "R19", "R18"])
    ck("不声称清单非空（≥8 条）", len(audit["notClaimed"]) >= 8,
       len(audit["notClaimed"]))
    ck("「删除会清历史」与「恢复按钮没观察到」都进了不声称",
       any("history" in x or "历史" in x for x in audit["notClaimed"])
       and any("恢复" in x for x in audit["notClaimed"]))

    # ---- 3. 运行时读数 ----
    ck("判据2 「在新窗口打开」三项变化全 0",
       J[2]["evidence"]["delta"] == {"nodes": 0, "canvases": 0, "removed": 0})
    ck("判据3 选中态跨画布不保留",
       J[3]["evidence"]["before"] and J[3]["evidence"]["onCanvas1"] == []
       and J[3]["evidence"]["backOnCanvas2"] == []
       and J[3]["evidence"]["survived"] is False)
    ck("判据4 历史栈按 canvasId 隔离（canvas-1 无条目、切回还在）",
       J[4]["evidence"]["afterDrag"] == {"canvas-2": 1}
       and "canvas-1" not in J[4]["evidence"]["onC1"]
       and J[4]["evidence"]["backOnC2"] == {"canvas-2": 1}
       and J[4]["evidence"]["isolated"] is True)
    ck("判据5 viewport 两张画布各自留存",
       J[5]["evidence"]["c1After"] == 1.2
       and J[5]["evidence"]["c2WhileOnC1"] == J[5]["evidence"]["c2AfterBack"]
       and J[5]["evidence"]["c1AfterBack"] == 1.2)
    ck("判据6 canvasGeneration 单调 +1",
       J[6]["evidence"]["steps"] == {"baseline": 1, "onC1": 4, "backOnC2": 5,
                                     "final": 7})
    ck("判据7 2 张画布时菜单只有 1/4 可点",
       J[7]["evidence"]["clickableCount"] == 1
       and J[7]["evidence"]["unreachable"]
       == ["重命名画布", "复制画布", "删除画布"]
       and J[7]["evidence"]["geom"]["menuInsideDropdown"] is False
       and J[7]["evidence"]["geom"]["menuBottom"]
       > J[7]["evidence"]["geom"]["ddBottom"])
    ck("判据7 三项各点一次全部零效果",
       J[7]["evidence"]["functionalProof2Canvases"]["重命名画布"]["inputPresent"]
       is False
       and J[7]["evidence"]["functionalProof2Canvases"]["复制画布"]["canvasesAfter"] == 2
       and J[7]["evidence"]["functionalProof2Canvases"]["删除画布"]
       ["confirmDialogPresent"] is False)
    ck("判据8 阳性对照：6 张时第一行 4/4 可点",
       J[8]["evidence"]["clickableCount"] == 4
       and J[8]["evidence"]["geom"]["menuInsideDropdown"] is True)
    ck("判据8 重命名真的成功（行内 input + 改名结果）",
       (J[8]["evidence"]["renameInput"] or {}).get("present") is True
       and (J[8]["evidence"]["renameInput"] or {}).get("focused") is True
       and "改名成功" in J[8]["evidence"]["namesAfter"])
    ck("判据9 同页并存：顶部行 4/4、末行 0/4",
       J[9]["evidence"]["topRow"]["clickable"] == 4
       and J[9]["evidence"]["bottomRow"]["clickable"] == 0
       and J[9]["evidence"]["topRow"]["id"] != J[9]["evidence"]["bottomRow"]["id"])
    ck("判据10 删除确认框结构与取消零变化",
       J[10]["evidence"]["dialog"]["present"] is True
       and J[10]["evidence"]["dialog"]["dialogAria"] == "删除画布"
       and "此操作不可恢复" in J[10]["evidence"]["dialog"]["text"]
       and {b["t"] for b in J[10]["evidence"]["dialog"]["buttons"]} == {"取消", "确认"}
       and J[10]["evidence"]["afterCancel"]["dialogGone"] is True
       and J[10]["evidence"]["afterCancel"]["canvases"] == 6)
    ck("判据11 删除 = 软删除 + 回退到创建序相邻的前一个",
       J[11]["evidence"]["canvasesAfter"] == J[11]["evidence"]["canvasesBefore"] - 1
       and len(J[11]["evidence"]["removed"]) == 1
       and re.fullmatch(r"\d{4}-\d{2}-\d{2}",
                        J[11]["evidence"]["removed"][0]["removedAt"])
       and J[11]["evidence"]["activeAfter"] != J[11]["evidence"]["activeBefore"])
    ck("判据12a 确认框写「此操作不可恢复」",
       "此操作不可恢复" in J[12]["evidence"]["confirmCopy"])
    ck("判据12b 恢复入口在 /project 的回收站（画布内无提示）",
       J[12]["evidence"]["projectPage"]["hasRecycleBinTab"] is True
       and "回收站" in (J[12]["evidence"]["recycleBinText"] or ""))
    ck("判判13 store 升序 vs DOM 倒序",
       J[13]["evidence"]["storeOrder"] == ["canvas-1", "canvas-2", "canvas-3",
                                           "canvas-4", "canvas-5", "canvas-6"]
       and J[13]["evidence"]["domRowOrder"] == ["canvas-6", "canvas-5", "canvas-4",
                                                "canvas-3", "canvas-2", "canvas-1"])
    ck("判据14 purgeRemovedCanvas 零调用点", J[14]["evidence"]["grepHits"] == [])

    # ---- 4. 原始读数交叉核对 ----
    if r1 is not None:
        # ⚠ 产物里的 evidence 是原始读数的**子集/改名**（例如 raw 的
        # `dropdownOpen` 在产物里叫 `dropdownOpenAfter`），所以只能做**叶子级**核对。
        leaf = [
            ("openInNewWindow.delta", r1["openInNewWindow"]["delta"],
             J[2]["evidence"]["delta"]),
            ("openInNewWindow.dropdownClosed",
             r1["openInNewWindow"]["dropdownOpen"], False),
            ("selection.before", r1["selectionAcrossSwitch"]["before"],
             J[3]["evidence"]["before"]),
            ("selection.backOnCanvas2",
             r1["selectionAcrossSwitch"]["backOnCanvas2"],
             J[3]["evidence"]["backOnCanvas2"]),
            ("selection.survived", r1["selectionAcrossSwitch"]["survived"],
             J[3]["evidence"]["survived"]),
            ("history.backOnC2", r1["history"]["backOnC2"],
             J[4]["evidence"]["backOnC2"]),
            ("history.isolated", r1["history"]["isolated"],
             J[4]["evidence"]["isolated"]),
            ("viewport.c1After", r1["viewport"]["c1After"],
             J[5]["evidence"]["c1After"]),
            ("viewport.c2AfterBack", r1["viewport"]["c2AfterBack"],
             J[5]["evidence"]["c2AfterBack"]),
            ("generation", r1["generation"], J[6]["evidence"]["steps"]),
            ("menu2.clickable", r1["menu2canvases"]["clickableCount"],
             J[7]["evidence"]["clickableCount"]),
            ("menu2.unreachable", r1["menu2canvases"]["unreachable"],
             J[7]["evidence"]["unreachable"]),
            ("menu6.clickable", r1["menu6firstRow"]["clickableCount"],
             J[8]["evidence"]["clickableCount"]),
            ("menu6.renameInput", _strip(r1["menu6firstRow"]["renameInput"]),
             _strip(J[8]["evidence"]["renameInput"])),
            ("menu6.namesAfter", r1["menu6firstRow"]["namesAfter"],
             J[8]["evidence"]["namesAfter"]),
            ("menuLow.clickable", r1["menuLowRow"]["clickableCount"],
             J[9]["evidence"]["bottomRow"]["clickable"]),
            ("deleteCancel.dialogGone", r1["deleteCancel"]["dialogGone"],
             J[10]["evidence"]["afterCancel"]["dialogGone"]),
            ("deleteConfirm.removed", _strip(r1["deleteConfirm"]["removed"]),
             _strip(J[11]["evidence"]["removed"])),
            ("deleteConfirm.activeAfter", r1["deleteConfirm"]["activeAfter"],
             J[11]["evidence"]["activeAfter"]),
            ("six.storeOrder", r1["sixCanvases"]["storeOrder"],
             J[13]["evidence"]["storeOrder"]),
            ("six.domRowOrder", r1["sixCanvases"]["domRowOrder"],
             J[13]["evidence"]["domRowOrder"]),
        ]
        bad = [n for n, a, b in leaf if _strip(a) != _strip(b)]
        ck(f"原始读数叶子级交叉核对 {len(leaf)} 项（/tmp/vb755d.json）",
           not bad, bad)
        ck("原始读数：两轮按生成 id 形态过滤后 diff 为空",
           raw["consistent"] is True and raw["roundDiff"] == {},
           sorted(raw["roundDiff"].keys()))
        ck("原始读数：baseline 两轮相同且是种子",
           r1["baseline"] == raw["rounds"][1]["baseline"]
           and r1["baseline"]["active"] == "canvas-2"
           and r1["baseline"]["nodes"] == 10)
        ck("原始读数：菜单几何三档自洽（2 张 1/4、6 张首行 4/4、末行 0/4）",
           r1["menu2canvases"]["clickableCount"] == 1
           and r1["menu6firstRow"]["clickableCount"] == 4
           and r1["menuLowRow"]["clickableCount"] == 0)
        ck("原始读数：阳性对照下菜单底边 < 容器底边（6 张首行）",
           r1["menu6firstRow"]["geom"]["menuBottom"]
           < r1["menu6firstRow"]["geom"]["ddBottom"])
    else:
        checks.append({"label": "原始读数交叉核对（/tmp/vb755d.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    npass = sum(1 for c in checks if c["pass"])
    report = {"batch": 755, "checks": checks, "passed": npass,
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
