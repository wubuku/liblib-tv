#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 785 汇编器 —— 用**行锚定字面量**从源码下结论，再与普查输出**对账**

## 三条更正（全部推翻我自己上一批的静态结论）

**C785-1** 784 的「3 有 / 7 没有」⟹ **更正为 4 有 / 6 没有**。两处错：
1. ★ **假阴性**：784 判据只认 `set<S>(null)`，
   而 `setModelLibraryOpen(false)`（`DirectorViewport.tsx:2739`）也是「关掉」。
2. ★ **key `open` 根本不是可写状态**：783 把 `PhoneVcamPanel` 的门记成 `open`
   （那是 **prop**，`:96/:99`），784 直接抄进 `census784.py:57` 的硬编码清单
   ⟹ **两批都从没找过真状态**。真名 `phoneVcamOpen`。
   ★ 而 784 的 raw 里 `open` 记的是 **`[]`** ⟹ **没有发生**「撞名算成有」，
   784 的错是**整个漏掉一个门状态**，恰好落进同一个桶。
   ⟹ 把 `open`「剔除」也会错：那会把 vcam 面板从风险面里**藏起来**。

**C785-2** 4 个外点关闭的事件**全是 pointer 类**（mousedown ×1 + pointerdown ×3）
⟹ **键盘一律绕过**。784 把风险形状写成「逐个手写」，不准确：
**真正的形状是「全都是鼠标」** —— 不是写漏了，是**写的时候只能用鼠标**。

**C785-3** D1i 的**纯鼠标路径**在 782 的 raw 里就有读数（本批**复用**，不跑浏览器）：
导出面板（**无**外点关闭）+ 模型库（pointerdown 外点关闭）⟹
第 1 次 Escape `cap=0, win=0`、模型库关、**导出面板仍在**，第 2 次才关。
⟹ 严重度**维持「中」**，覆盖面比 784 写的**更宽**（不止键盘）。

## 纪律

- 每条结论 = 一个**行锚定字面量**（file:line + 精确 needle），从**源码**断言，
  普查输出只用来**对账** ⟹ 不一致就记成发现，不静默采信。
- 判据的 needle 要**唯一**：`updateCamera(activeCameraId, { followTargetId: null })`
  而不是 `followTargetId`。
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch785-2026-10-01"
CENSUS = REPO / (B + "/raw/census785.json")
C784 = REPO / ("docs/research/liblib-canvas-batch784-2026-10-01"
               "/raw/census784.json")
RAW782 = REPO / ("docs/research/liblib-canvas-batch782-2026-10-01"
                 "/raw/vb782a.json")
OUT = REPO / (B + "/runtime-audit.json")

DV = "src/components/director/DirectorViewport.tsx"
DT = "src/components/director/DirectorTimeline.tsx"
DOT = "src/components/director/DirectorObjectTree.tsx"
DD = "src/components/director/DirectorDesk.tsx"
DI = "src/components/director/DirectorInspector.tsx"
DVP = "src/components/director/DirectorPhoneVcamPanel.tsx"

PE = ("mousedown", "pointerdown", "click", "touchstart")

#: ★ **有**外点关闭的 4 个：`(状态, 监听行, 监听行 needle, 关写行, 关写 needle, 事件, 目标)`
WITH_OUTSIDE_CLOSE = [
    ("contextMenu", DOT, 212,
     'window.addEventListener("mousedown", close);',
     207, "setContextMenu(null);", "mousedown", "window"),
    ("modelLibraryOpen", DV, 2747,
     'document.addEventListener("pointerdown", closeOnOutsidePointerDown);',
     2739, "setModelLibraryOpen(false);", "pointerdown", "document"),
    ("pathMenuLeft", DT, 569,
     'window.addEventListener("pointerdown", close);',
     564, "setPathMenuLeft(null);", "pointerdown", "window"),
    ("presetPanelLeft", DT, 593,
     'window.addEventListener("pointerdown", close);',
     588, "setPresetPanelLeft(null);", "pointerdown", "window"),
]

#: ★ **没有**外点关闭的 6 个：`(状态, 关写证据 file, line, needle, 人类说明)`
WITHOUT_ANY = [
    ("exportPanelOpen", DD, 558, "setExportPanelOpen(false);",
     "Escape 阶梯第 2 档"),
    ("followTargetId", DD, 565,
     "updateCamera(activeCameraId, { followTargetId: null })",
     "阶梯第 1 档（先退出跟随）"),
    ("activeDirectorNodeId", "src/store/uiStore.ts", 359,
     "set({ activeDirectorNodeId: null, activeDirectorCanvasId: null })",
     "关整张桌"),
    ("motionPathDraft", "src/store/directorStore.ts", 1607,
     "motionPathDraft: null,", "时间轴运镜草稿"),
    ("viewerCaptureId", DI, 404,
     'if (event.key === "Escape") setViewerCaptureId(null);', "取景器"),
    ("phoneVcamOpen", DV, 3081,
     "onClose={() => setPhoneVcamOpen(false)}",
     "★ 784 那个 key `open` 的真身"),
]

#: ★ `open` 是 prop 的**证据链**（784/783 都没走到这一步）
PROP_CHAIN = [
    (DVP, 96, "open,", "面板从参数里解构出 `open`"),
    (DVP, 99, "open: boolean;", "类型标注是 `boolean`、不是 state"),
    (DV, 2544, "const [phoneVcamOpen, setPhoneVcamOpen] = useState(false);",
     "★ 真状态在这里声明"),
    (DV, 3080, "open={phoneVcamOpen}", "父组件以 `open=` 透传"),
    (DV, 3081, "onClose={() => setPhoneVcamOpen(false)}",
     "★ 唯一的**关闭**路径由父组件接上"),
]


def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def check(cid, desc):
    ok, detail = True, []
    for rel, n, needle, *rest in desc:
        code = line_of(rel, n)
        good = needle in code
        ok = ok and good
        detail.append({"file": rel, "line": n, "needle": needle,
                       "ok": good, "code": code.strip()[:110]})
        if not good:
            break
    return {"id": cid, "ok": ok, "n": len(desc), "anchors": detail}


def main():
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    old = json.loads(C784.read_text(encoding="utf-8"))
    raw782 = json.loads(RAW782.read_text(encoding="utf-8"))

    checks = []

    # ── A：4 个「有外点关闭」，每个两行锚定 ──
    for st, rel, ln, lneedle, wln, wneedle, ev, tgt in WITH_OUTSIDE_CLOSE:
        c = check("A:" + st, [
            (rel, ln, lneedle),
            (rel, wln, wneedle)])
        c["state"], c["event"], c["target"] = st, ev, tgt
        assert c["ok"], "★ 行锚定失败：%s\n%r" % (st, c["anchors"])
        checks.append(c)
    ev_of = {row[0]: row[6] for row in WITH_OUTSIDE_CLOSE}
    tgt_of = {row[0]: row[7] for row in WITH_OUTSIDE_CLOSE}
    checks.append({
        "id": "A:events-are-pointer-class", "ok": True, "n": 1,
        "detail": {"events": ev_of, "targets": tgt_of,
                   "allInPE": all(e in PE for e in ev_of.values())},
        "claim": "★ 4 个外点关闭**全是 pointer 类** ⟹ 键盘一律绕过",
    })
    assert all(e in PE for e in ev_of.values()), \
        "★ 有非 pointer 类事件 ⟹ C785-2 不成立"

    # ── B：6 个「没有外点关闭」，每个一条关写证据 ──
    for st, rel, ln, needle, why in WITHOUT_ANY:
        c = check("B:" + st, [(rel, ln, needle)])
        c["state"], c["why"] = st, why
        assert c["ok"], "★ 行锚定失败：%s\n%r" % (st, c["anchors"])
        checks.append(c)

    # ── C：`open` 是 prop 的证据链 ──
    c = check("C:open-is-prop", PROP_CHAIN)
    c["claim"] = "★ `open` 是 prop；真状态是 `phoneVcamOpen`"
    assert c["ok"], "★ prop 证据链断了：\n%r" % c["anchors"]
    checks.append(c)

    # ── D：784 的 raw 里 `open` 记的是「没有」⟹ 不是撞名，是**漏掉** ──
    d = {
        "id": "D:784-account", "ok": True, "n": 1,
        "detail": {
            "with": old["statesWithOutsideClose"],
            "without": old["statesWithoutOutsideClose"],
            "openInWithout": "open" in old["statesWithoutOutsideClose"],
            "openInWith": "open" in old["statesWithOutsideClose"],
            "784with": len(old["statesWithOutsideClose"]),
            "784without": len(old["statesWithoutOutsideClose"]),
        },
        "claim": "★ 784 把 `open` 记成**没有**外点关闭 ⟹ "
                 "**没发生撞名**，错在**整个漏掉一个门状态**",
    }
    assert d["detail"]["openInWithout"] is True and \
        d["detail"]["openInWith"] is False, \
        "★ 与预期不符：784 raw 里 `open` 的归属变了 ⟹ 结论要重算"
    checks.append(d)

    # ── E：普查输出与行锚定**对账** ──
    census_with = census["statesWithOutsideClose"]
    census_without = census["statesWithoutOutsideClose"]
    mine_with = sorted(s for s, *_ in WITH_OUTSIDE_CLOSE)
    mine_without = sorted(s for s, *_ in WITHOUT_ANY)
    e = {"id": "E:reconcile-with-census", "ok": True, "n": 1,
         "detail": {"assemblerWith": mine_with, "censusWith": census_with,
                    "assemblerWithout": mine_without,
                    "censusWithout": census_without,
                    "withAgree": mine_with == census_with,
                    "withoutAgree": mine_without == census_without,
                    "countAgree": (len(mine_with), len(mine_without)) ==
                                  (len(census_with), len(census_without))},
         "claim": "★ 汇编器（源码行锚定）与普查器（正则扫描）必须一致"}
    assert e["detail"]["withAgree"] and e["detail"]["withoutAgree"], \
        "★ 对账失败：汇编器与普查器给出不同清单 ⟹ 有一个是错的\n%r" % \
        e["detail"]
    checks.append(e)

    # ── F：纯鼠标 D1i（**复用** 782 的 raw，不重跑）──
    f = check("F:pure-mouse-D1i", [])
    pm = census["pureMouseD1i"]
    f.update({
        "n": 1, "reading": pm,
        "detail": {
            "press1_cap": pm["press1"]["cap"],
            "press1_win": pm["press1"]["win"],
            "press1_targetOpen": pm["press1"]["targetOpen"],
            "press1_exportOpen": pm["press1"]["exportOpen"],
            "press2_exportOpen": pm["press2"]["exportOpen"],
        },
        "claim": "★ 纯鼠标：第 1 次 Escape 把模型库关掉（`cap=0` 阶梯跑不到），"
                 "**导出面板留在原地**；第 2 次才关 ⟹ D1i 纯鼠标可达",
    })
    # ★ 派生字段**重算**（R149）：不看 census 的派生值，直接从 782 raw 重读
    reread = None
    for rd in raw782["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "captureOwner":
                ps = r.get("presses") or []
                if len(ps) >= 2:
                    reread = {
                        "cap": ps[0]["read"].get("cap"),
                        "win": ps[0]["read"].get("win"),
                        "targetOpen": (ps[0].get("state") or {}).get("targetOpen"),
                        "exportOpen": (ps[0].get("state") or {}).get("exportOpen"),
                        "exportOpen2": (ps[1].get("state") or {}).get("exportOpen"),
                    }
                break
        if reread:
            break
    f["detail"]["recomputedFrom782Raw"] = reread
    f["ok"] = (reread is not None
               and reread["cap"] == 0 and reread["win"] == 0
               and reread["targetOpen"] is False
               and reread["exportOpen"] is True
               and reread["exportOpen2"] is False)
    assert f["ok"], "★ 782 raw 重读与预测不符：%r ⟹ C785-3 要重算" % reread
    checks.append(f)

    # ── G：复查时撞见的一条**事实**（结论留给 786）──
    # ★ 查 `phoneVcamOpen` 的可写性时看到：`toggleModelLibrary`
    #   （`DirectorViewport.tsx:2825-2829`）里写着 `setPhoneVcamOpen(false)`
    # ★ 而 vcam 触发器（`:3536-3542` 的内联 `onClick`）里写着
    #   `setModelLibraryOpen(false)` 与 `setPhoneVcamOpen((value) => !value)`
    #   ⟹ 两个方向**都**有交叉写入。
    # ★ 但「这两个状态因此不能共活」是**推论**，静态不可判 ⟹
    #   本批只把**事实**钉死（各一行锚定），推论与运行时验证**留给 786**。
    g = check("G:双向交叉写入（事实）", [
        (DV, 2826, "setPhoneVcamOpen(false);"),
        (DV, 2828, "setModelLibraryOpen((value) => !value);"),
        (DV, 3538, "setModelLibraryOpen(false);"),
        (DV, 3540, "setPhoneVcamOpen((value) => !value);"),
    ])
    g["claim"] = ("★ `phoneVcamOpen` 与 `modelLibraryOpen` 在**两个方向**上"
                  "都有交叉写入；「因此不能共活」是**推论**，静态不可判 ⟹ 留给 786")
    g["conclusionDeferred"] = "batch786：运行时两方向验证 + 重建 783 的 crossWrites 层"
    assert g["ok"], "★ 双向交叉写入的行锚定断了：\n%r" % g["anchors"]
    checks.append(g)

    # ── 汇总 ──
    with_oc = mine_with
    without_oc = mine_without
    out = {
        "batch": 785,
        "claims": {
            "C785-1": {
                "text": "784 的「3 有 / 7 没有」⟹ 更正为 **4 有 / 6 没有**",
                "with": with_oc, "without": without_oc,
                "falseNegative": {
                    "state": "modelLibraryOpen",
                    "line": "src/components/director/DirectorViewport.tsx:2739",
                    "needle": "setModelLibraryOpen(false);",
                    "why": "784 判据只认 `set<S>(null)`",
                },
                "wrongKey": {
                    "key": "open", "realState": "phoneVcamOpen",
                    "declaredAt": "src/components/director/DirectorViewport.tsx:2544",
                    "why": "783 记的是 **prop** 名，784 抄进硬编码清单 ⟹ 两批都没找过真状态",
                    "notCollision": "★ 784 raw 里 `open` 记的是 `[]` ⟹ 没发生撞名",
                },
            },
            "C785-2": {
                "text": "4 个外点关闭**全是 pointer 类**（mousedown ×1 + pointerdown ×3）"
                        "⟹ **键盘一律绕过**；真正的形状不是「写漏了」而是「**只能用鼠标**」",
                "events": ev_of,
                "targets": tgt_of,
            },
            "C785-3": {
                "text": "D1i **纯鼠标可达**：782 raw 的 `captureOwner` 臂已是同一形态"
                        "（导出面板无外点关闭 + 模型库 pointerdown 外点关闭）"
                        "⟹ 严重度**维持中**，覆盖面比 784 更宽",
                "source": "batch782 raw（**复用**，本批不跑浏览器）",
            },
        },
        "states": {
            "withOutsideClose": with_oc, "withoutOutsideClose": without_oc,
            "count": {"with": len(with_oc), "without": len(without_oc),
                      "total": len(with_oc) + len(without_oc)},
        },
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(c.get("n", 0) for c in checks),
                   "failed": sum(0 if c["ok"] else 1 for c in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ C785-1：3 有 / 7 没有 ⟹ **4 有 / 6 没有**")
    print("   有外点关闭：%s" % "、".join(with_oc))
    print("   无外点关闭：%s" % "、".join(without_oc))
    print("★ C785-2：4 个事件全是 pointer 类 ⟹ 键盘一律绕过")
    print("★ C785-3：纯鼠标 D1i 重算 = %s" % json.dumps(reread, ensure_ascii=False))
    print("★ 对账：汇编器（源码行锚定）≡ 普查器（正则扫描）✓")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
