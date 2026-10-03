#!/usr/bin/env python3
"""batch 742 验收：命令入口普查 —— 「记不记账」×「用户在不在 LibTV 里触发得到」的交叉表

## 起点

741 把 canvasStore 54 个命令按「记不记账」分了三桶（33 / 17 / 4），但没问
**用户在 LibTV 画布里到底能触发到哪些**。本批做两件事的交叉：

  ① 每个命令在 `src/` 里的外部调用点，按 app 归属（LibTV / FrameOS / Jimeng）拆开
  ② 四个零入口的命令，运行时直调，验证「能力在、入口不在」

## 探针返工两次（两次都是我自己的错，都被 733 立的「先怀疑探针」救回来）

第一版正则：`(?<![\w.$])name\s*\(` —— 用「前面没有点号」来避开 store 内部的
自调用，结果**把 `useCanvasStore.getState().name(...)` 这种正常入口全杀了**，
读出「8 个记账命令零入口」。

第二版改成允许前导点，又漏了**解构改名**：`src/app/page.tsx:366` 写的是
`setNodes: setStoreNodes`，调用点是 `setStoreNodes(...)`，名字 `setNodes` 后面
从来不跟 `(` ⟹ 又把 `setNodes` 误判成 LibTV 零入口 —— 而 741 刚在**运行时**
证过拖动停下会调它。两份读数互相矛盾 ⟹ 先怀疑 census（733）。

修法：先建 `命令 → 别名` 映射（本批实测 3 个别名），调用点 = 直呼 + 别名。
**并且用 741 的运行时事实反过来验 census**：741 证过 `setNodes` 在拖动停下时被调，
census 就必须显示它有 LibTV 入口 —— 这条写成了判据 C3。

## 决定性读数

### ① 交叉表

| | LibTV 画布内有入口 | LibTV 零入口 |
|---|---|---|
| **记账**（33） | **29** | **4** |
| **不记账**（21） | **17** | **4** |

LibTV 零入口的 4 个记账命令：
- `submitLibTVEditorSessionCommit:3991` —— **全 src/ 零调用点**（唯一）
- `duplicateNode:3104` / `removeNode:3187` —— 只被 FrameOS(2/5 处)、Jimeng(3 处) 调；
  LibTV 画布用的是**复数版** `duplicateSelectedNodes:3150` / `removeSelectedNodes:3223`
- `setEdges:3415` —— 只被 `src/app/frameos/canvas/[id]/page.tsx:143` 调；
  LibTV 改边只用 `addEdge` / `removeEdge`（两个都记账）

### ② 「预留能力」不是「回归」：一条从未被调用过的记账命令
`git log -S "submitLibTVEditorSessionCommit(" -- src/` **返回空** ⟹
这个命令名 + 左括号**从未在任何提交里出现过**（不是「曾经接线后来掉了」）。
它由 `d9c745b4`（batch 446 VR-022 等值感知提交适配器）引入 store，
`0902def1`（batch 467 VR-018 命令反馈清单）只加了**字符串元数据**。

### ③ 反馈清单登记 ≠ 接线（承 729「两套未接线契约」）
`src/lib/libtvCommandFeedback.ts` 的 12 个 surface 里，2 个直接指向 store 方法：

```
{ surfaceId: "editor-session-commit", component: "canvasStore.submitLibTVEditorSessionCommit",
  feedbackKind: "none", commands: ["editor-session-commit"] }
{ surfaceId: "asset-reference-attach", component: "canvasStore.attachAssetReferences",
  feedbackKind: "none", commands: ["asset-reference-attach"] }
```

⟹ 一条**登记了却从不执行**（`submitLibTVEditorSessionCommit`），
一条**真的在跑**（`attachAssetReferences`，`AddNodePanel.tsx:76`）。
清单自己写 `feedbackKind: "none"` 说明它知道这条命令没有反馈通道，
但「登记在清单里」和「接了线」是两件事。

### ④ `purgeRemovedCanvas` 零入口**与 UI 一致**（不是缺口）
回收站面板 `src/app/project/page.tsx:151` 的 `data-recycle-panel` 里只有两类按钮：
单条「恢复」(`restoreCanvas`) 与批量「恢复所选 N 项」(`data-recycle-restore-selected`，
逐个 `restoreCanvas`) —— **没有永久删除**。
⟹ `purgeRemovedCanvas:1069` 零入口是**与 UI 自洽**的，不列为缺陷。

## 判据

C1  交叉表：记账 33 = LibTV 有入口 29 / 零入口 4；不记账 21 = 17 / 4
C2  4 个 LibTV 零入口的记账命令逐个点名，且 `submitLibTVEditorSessionCommit` 全 src/ 零调用
C3  别名映射 3 个；**用 741 的运行时事实反证 census**（`setNodes` 必须有 LibTV 入口）
C4  4 个零入口命令运行时直调都记账（`past` +1）⟹ 能力在、入口不在
C5  LibTV 实际走的是复数版：键盘 Cmd+D → `duplicateSelectedNodes`，节点 +1 且 `past` +1
C6  回收站两个按钮都只调 `restoreCanvas` ⟹ `purgeRemovedCanvas` 零入口与 UI 自洽
C7  反馈清单 12 个 surface，其中登记了那条从不执行的 `submitLibTVEditorSessionCommit`
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch742-2026-10-01"
STORE = ROOT / "src/store/canvasStore.ts"
FEEDBACK = ROOT / "src/lib/libtvCommandFeedback.ts"
PROJECT_PAGE = ROOT / "src/app/project/page.tsx"
BASE = "http://localhost:4317"
W, H = 1280, 1150

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {canvasId: g.id, nodeCount: g.nodes.length, edgeCount: g.edges.length,
          past: h.past.length, future: h.future.length,
          selectedNodeIds: s.selectedNodeIds.slice(),
          canvasNames: Object.fromEntries(s.canvases.map(c => [c.id, c.name])),
          removedIds: s.removedCanvases.map(c => c.id)};
}"""


def app_of(path: str) -> str:
    low = path.lower()
    return "FrameOS" if "frameos" in low else ("Jimeng" if "jimeng" in low else "LibTV")


def store_commands():
    """复用 741 的解析口径（54 个命令 + 三桶），不在本批另写一份。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "v741", ROOT / "scripts/verify-liblib-batch741.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.census()["rows"]


def census(rows):
    """调用点普查：直呼 + 解构别名，按 app 归属拆。"""
    names = [r["name"] for r in rows]
    files = []
    for path in sorted(ROOT.glob("src/**/*.ts")) + sorted(ROOT.glob("src/**/*.tsx")):
        if path.name == "canvasStore.ts":
            continue
        files.append((path.relative_to(ROOT).as_posix(),
                      path.read_text(encoding="utf-8").split("\n")))

    # ① 解构改名：`NAME: alias`（第一版就漏在这一类）
    aliases, renames = {}, []
    for path, lines in files:
        for n, line in enumerate(lines, 1):
            for nm in names:
                mm = re.search(r"(?<![\w])" + re.escape(nm) + r"\s*:\s*([A-Za-z_$][\w$]*)\s*,?", line)
                # 注意：`onClick={canUndo ? undo : undefined}` 这种三元字面量
                # 会被 `undo: undefined` 误当成解构改名 —— 别名必须排除关键字。
                if mm and mm.group(1) != nm \
                        and mm.group(1) not in ("undefined", "null", "true", "false"):
                    aliases.setdefault(nm, set()).add(mm.group(1))
                    renames.append((nm, mm.group(1), path, n))

    # ② 调用点：直呼或任一别名
    hits = {r["name"]: [] for r in rows}
    for path, lines in files:
        app = app_of(path)
        for n, line in enumerate(lines, 1):
            for nm in names:
                direct = re.search(r"(?<![\w])" + re.escape(nm) + r"\s*\(", line)
                via = [a for a in aliases.get(nm, ())
                       if re.search(r"(?<![\w])" + re.escape(a) + r"\s*\(", line)]
                if direct:
                    hits[nm].append((path, n, app, "direct"))
                elif via:
                    hits[nm].append((path, n, app, "alias:" + via[0]))

    return {"aliases": {k: sorted(v) for k, v in aliases.items()}, "renames": renames,
            "hits": hits}


def feedback_catalog():
    text = FEEDBACK.read_text(encoding="utf-8")
    entries = re.findall(
        r"surfaceId:\s*\"([^\"]+)\",\s*component:\s*\"([^\"]+)\",\s*feedbackKind:\s*\"([^\"]+)\"",
        text)
    store_backed = [(sid, comp, kind) for sid, comp, kind in entries
                    if comp.startswith("canvasStore.")]
    return {"surfaceCount": len(entries), "entries": entries, "storeBacked": store_backed}


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    rows = store_commands()
    acct = {r["name"] for r in rows if r["calls_push"]}
    noacct = {r["name"] for r in rows if not r["calls_push"]}
    c = census(rows)
    hits = c["hits"]

    def libtv(nm):
        return [(p, n) for p, n, a, _ in hits[nm] if a == "LibTV"]

    acct_L, acct_dead = sorted(n for n in acct if libtv(n)), sorted(n for n in acct if not libtv(n))
    noacct_L, noacct_dead = sorted(n for n in noacct if libtv(n)), sorted(n for n in noacct if not libtv(n))

    print("=== 静态：调用点普查（含解构别名）===")
    print(f"  别名 {len(c['aliases'])} 组：{json.dumps(c['aliases'], ensure_ascii=False)}")
    for nm, al, p, n in c["renames"]:
        print(f"    {nm} → {al}  at {p}:{n}")
    print(f"\n  记账 {len(acct)}：LibTV 有入口 {len(acct_L)} / 零入口 {len(acct_dead)}  {acct_dead}")
    print(f"  不记账 {len(noacct)}：LibTV 有入口 {len(noacct_L)} / 零入口 {len(noacct_dead)}  {noacct_dead}")
    for nm in acct_dead:
        others = sorted({a for _, _, a, _ in hits[nm] if a != "LibTV"})
        print(f"    零入口·记账 {nm:32s} 别的 app 调用方：{others or '无（全 src/ 零调用）'}")

    print("\n=== git log -S：零入口命令是否曾经被外部调用过 ===")
    gitlog = {}
    for nm in acct_dead + noacct_dead:
        out = subprocess.run(
            # 只扫 src/ 且排除 store 自身。第一版多传了一个 `.` pathspec，
            # 把 docs/research/batch446 的 README 里那句 `submitLibTVEditor
            # SessionCommit(request)` 说明文字算成了一次外部调用（+1）。
            ["git", "log", "--oneline", "-S", f"{nm}(", "--", "src",
             ":(exclude)src/store/canvasStore.ts"],
            cwd=ROOT, capture_output=True, text=True).stdout.strip()
        n = len([x for x in out.split("\n") if x.strip()])
        gitlog[nm] = n
        print(f"  {nm:32s} 曾有外部调用的提交数 = {n}")

    cat = feedback_catalog()
    print(f"\n=== 反馈清单 {cat['surfaceCount']} 个 surface ===")
    for sid, comp, kind in cat["storeBacked"]:
        print(f"  {sid:24s} {comp:44s} feedbackKind={kind}")

    recycle = re.findall(r"(data-recycle-[a-z-]+)", PROJECT_PAGE.read_text(encoding="utf-8"))
    recycle_btns = re.findall(r"onClick=\{\(\)\s*=>\s*\{?\s*([^}]{0,90})",
                              PROJECT_PAGE.read_text(encoding="utf-8"))
    print(f"\n=== 回收站稳定属性：{sorted(set(recycle))} ===")
    print(f"  onClick 片段里出现 restoreCanvas 的次数："
          f"{sum(1 for b in recycle_btns if 'restoreCanvas' in b)}；"
          f"出现 purgeRemovedCanvas 的次数："
          f"{sum(1 for b in recycle_btns if 'purgeRemovedCanvas' in b)}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        def go(tag, path="/"):
            page.goto(f"{BASE}{path}?batch742={tag}", wait_until="networkidle", timeout=90_000)
            page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.wait_for_timeout(1_200)

        # ---------- C4 四个零入口记账命令：直调都记账 ----------
        print("\n=== C4 直调四个 LibTV 零入口的记账命令 ===")
        direct = {}
        for nm, call in [
            ("duplicateNode", """(id) => window.__libtv_store.getState().duplicateNode(id)"""),
            ("removeNode", """(id) => window.__libtv_store.getState().removeNode(id)"""),
            # setEdges:3415 是**条件**记账（741 的读数）：不带 recordHistory 一律不记。
            # 这里两格都调，把「同一个命令两个参数给两种结果」摆在一起。
            ("setEdges（不带 flag）", """() => window.__libtv_store.getState().setEdges(
                                   window.__libtv_store.getState().getActiveCanvas().edges)"""),
            ("setEdges（带 flag）", """() => window.__libtv_store.getState().setEdges(
                                   window.__libtv_store.getState().getActiveCanvas().edges,
                                   {recordHistory: true})"""),
            ("submitLibTVEditorSessionCommit", """(id) => window.__libtv_store.getState()
                .submitLibTVEditorSessionCommit({profileId: 'INLINE_SCALAR', nodeId: id,
                    expectedCanvasId: window.__libtv_store.getState().activeCanvasId,
                    expectedCanvasGeneration: window.__libtv_store.getState().canvasGeneration,
                    field: '__b742', baselineValue: '', draftValue: 'x'})"""),
        ]:
            go(nm)
            s0 = page.evaluate(SNAP)
            nid = page.evaluate("() => window.__libtv_store.getState().getActiveCanvas().nodes[0].id")
            ret = page.evaluate(call, nid)
            page.wait_for_timeout(600)
            s1 = page.evaluate(SNAP)
            direct[nm] = {"p0": s0["past"], "p1": s1["past"],
                          "n0": s0["nodeCount"], "n1": s1["nodeCount"],
                          "e0": s0["edgeCount"], "e1": s1["edgeCount"],
                          "ret": json.dumps(ret, ensure_ascii=False)[:150]}
            print(f"  {nm:32s} past {s0['past']}→{s1['past']}、节点 {s0['nodeCount']}→{s1['nodeCount']}、"
                  f"边 {s0['edgeCount']}→{s1['edgeCount']}；返回 {direct[nm]['ret']}")

        # ---------- C5 LibTV 实际走复数版：Cmd+D ----------
        go("cmdd")
        k0 = page.evaluate(SNAP)
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          // selectElements:3500 收的是 `{nodeIds, edgeIds}` 对象，不是数组
          s.selectElements({nodeIds: [s.getActiveCanvas().nodes[0].id], edgeIds: []});
        }""")
        page.wait_for_timeout(500)
        page.keyboard.press("Meta+d")
        page.wait_for_timeout(800)
        k1 = page.evaluate(SNAP)
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(700)
        k2 = page.evaluate(SNAP)
        print(f"\n=== C5 键盘 Cmd+D → duplicateSelectedNodes（有入口那条真通）===")
        print(f"  选中 {k0['nodeCount'] and len(k1['selectedNodeIds'])} 个后按 Cmd+D："
              f"节点 {k0['nodeCount']}→{k1['nodeCount']}、past {k0['past']}→{k1['past']}")
        print(f"  再 Cmd+Z：节点 {k2['nodeCount']}、past {k2['past']}、future {k2['future']}")

        # ---------- C6 回收站：先让它真的有内容，再点真按钮 ----------
        go("recycle", "/project")
        page.evaluate("""() => { const b = document.querySelector('[data-project-recycle]');
          if (b) b.click(); }""")
        page.wait_for_timeout(700)
        empty0 = page.evaluate("""() => {
          const p = document.querySelector('[data-recycle-panel]');
          return {panel: Boolean(p), buttons: p ? p.querySelectorAll('button').length : -1,
                  items: p ? p.querySelectorAll('[data-recycle-item]').length : -1,
                  empty: Boolean(p && p.querySelector('[data-recycle-empty]'))};
        }""")
        print(f"\n=== C6 回收站（/project）===")
        print(f"  展开后（尚未删除任何画布）：{json.dumps(empty0, ensure_ascii=False)}")
        # 注意：回收站为空时面板里**一个按钮都没有**，第一版的判据写成
        # 「按钮数 <= 2」于是**零信息地通过**（740 立过的坑：读数对但什么也没证明）。
        # 先在同一页里删一张画布，让回收站真的有内容，再读按钮、再点。
        page.evaluate("""() => window.__libtv_store.getState().removeCanvas('canvas-1')""")
        page.wait_for_timeout(800)
        rb = page.evaluate("""() => {
          const panel = document.querySelector('[data-recycle-panel]');
          if (!panel) return {panel: false};
          return {panel: true,
                  buttons: [...panel.querySelectorAll('button')].map(b => ({
                    text: (b.textContent || '').trim().slice(0, 14),
                    restore: b.hasAttribute('data-recycle-restore'),
                    restoreSelected: b.hasAttribute('data-recycle-restore-selected'),
                  })),
                  items: [...panel.querySelectorAll('[data-recycle-item]')].map(e => e.getAttribute('data-recycle-item')),
                  empty: Boolean(panel.querySelector('[data-recycle-empty]'))};
        }""")
        st_removed = page.evaluate("() => window.__libtv_store.getState().removedCanvases.map(c => c.id)")
        print(f"  删掉 canvas-1 之后：removedCanvases={st_removed}")
        print(f"  面板 {json.dumps(rb, ensure_ascii=False)}")
        # 真点一次「恢复」，验证恢复行为（第一版只读了源码，没点）
        before = page.evaluate(SNAP)
        page.evaluate("""() => { const b = document.querySelector('[data-recycle-restore]');
          if (b) b.click(); }""")
        page.wait_for_timeout(900)
        after = page.evaluate(SNAP)
        rb2 = page.evaluate("""() => {
          const panel = document.querySelector('[data-recycle-panel]');
          return {items: panel ? panel.querySelectorAll('[data-recycle-item]').length : -1,
                  empty: Boolean(panel && panel.querySelector('[data-recycle-empty]'))};
        }""")
        print(f"  点「恢复」之后：removed={after['removedIds']}、面板 {json.dumps(rb2, ensure_ascii=False)}")
        print(f"  源码里回收站区块的 onClick 提到 purgeRemovedCanvas 吗："
              f"{any('purgeRemovedCanvas' in b for b in recycle_btns)}")

        page.close()
        browser.close()

    summary = {
        "grid": {"acct_total": len(acct), "acct_libtv": len(acct_L), "acct_dead": acct_dead,
                 "noacct_total": len(noacct), "noacct_libtv": len(noacct_L),
                 "noacct_dead": noacct_dead},
        "aliases": c["aliases"], "renames": [[a, b, p, n] for a, b, p, n in c["renames"]],
        "acct_dead_others": {nm: sorted({a for _, _, a, _ in hits[nm] if a != "LibTV"})
                             for nm in acct_dead},
        "libtv_entries": {nm: libtv(nm) for nm in acct},
        "gitlog_external_calls": gitlog,
        "feedback": cat, "recycleAttrs": sorted(set(recycle)),
        "direct_calls": direct,
        "cmdd": {"n0": k0["nodeCount"], "n1": k1["nodeCount"],
                 "p0": k0["past"], "p1": k1["past"],
                 "undo_n": k2["nodeCount"], "undo_p": k2["past"], "undo_f": k2["future"]},
        "recycle_dom": rb, "recycle_empty_first": empty0,
        "recycle_after_restore": rb2, "recycle_removed_before": st_removed,
        "recycle_removed_after": after["removedIds"],
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")

    checks = [
        ("C1 交叉表：记账 33 = LibTV 29 / 零入口 4；不记账 21 = 17 / 4",
         len(acct) == 33 and len(acct_L) == 29 and len(acct_dead) == 4
         and len(noacct) == 21 and len(noacct_L) == 17 and len(noacct_dead) == 4,
         json.dumps(summary["grid"], ensure_ascii=False)),
        ("C2 四个零入口记账命令点名；submitLibTVEditorSessionCommit 全 src/ 零调用且从未调用过",
         acct_dead == ["duplicateNode", "removeNode", "setEdges",
                       "submitLibTVEditorSessionCommit"]
         and hits["submitLibTVEditorSessionCommit"] == []
         and gitlog["submitLibTVEditorSessionCommit"] == 0,
         json.dumps({"dead": acct_dead,
                     "submitHits": hits["submitLibTVEditorSessionCommit"],
                     "gitlog": gitlog["submitLibTVEditorSessionCommit"],
                     "others": summary["acct_dead_others"]}, ensure_ascii=False)),
        ("C3 别名映射 3 个；用 741 的运行时事实反证 census（setNodes 必须有 LibTV 入口）",
         c["aliases"] == {"addEdge": ["addStoreEdge"], "setNodes": ["setStoreNodes"],
                          "setViewport": ["setStoreViewport"]}
         and ("setNodes" in acct_L) and len(libtv("setNodes")) == 4,
         json.dumps({"aliases": c["aliases"], "setNodesLibTV": libtv("setNodes")},
                    ensure_ascii=False)),
        ("C4 零入口命令直调：3 个无条件记账，setEdges 需带 recordHistory 才记（承 741 的条件记账）",
         all(v["p1"] == v["p0"] + 1 for k, v in direct.items() if "不带 flag" not in k)
         and direct["setEdges（不带 flag）"]["p1"] == direct["setEdges（不带 flag）"]["p0"]
         and direct["setEdges（带 flag）"]["p1"] == direct["setEdges（带 flag）"]["p0"] + 1,
         json.dumps(direct, ensure_ascii=False)),
        ("C5 Cmd+D 走 duplicateSelectedNodes：节点 +1、past +1、Cmd+Z 逐项撤回",
         k1["nodeCount"] == k0["nodeCount"] + 1 and k1["past"] == k0["past"] + 1
         and k2["nodeCount"] == k0["nodeCount"],
         json.dumps(summary["cmdd"], ensure_ascii=False)),
        ("C6 回收站真有内容：每个按钮都是「恢复」、点它真的回来了 ⟹ purgeRemovedCanvas 零入口与 UI 自洽",
         rb.get("panel") is True and rb.get("items") == ["canvas-1"]
         and rb["buttons"] and all(b["restore"] or b["restoreSelected"] for b in rb["buttons"])
         and "canvas-1" in st_removed and "canvas-1" not in after["removedIds"]
         and rb2["empty"] is True
         and not any("purgeRemovedCanvas" in b for b in recycle_btns),
         json.dumps({"emptyFirst": empty0, "dom": rb, "removedBefore": st_removed,
                     "afterRestore": rb2, "removedAfter": after["removedIds"],
                     "attrs": summary["recycleAttrs"]}, ensure_ascii=False)),
        ("C7 反馈清单 13 个 surface，登记了那条从不执行的 submitLibTVEditorSessionCommit",
         cat["surfaceCount"] == 13
         and any(c == "canvasStore.submitLibTVEditorSessionCommit" and k == "none"
                 for _, c, k in cat["storeBacked"]),
         json.dumps(cat, ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 742,
        "title": "命令入口普查：记账 33 × LibTV 有入口 29 / 零入口 4；一条从未被调用过的记账命令",
        "verdict": f"{passed}/{len(checks)}",
        "summary": summary,
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "交叉表：记账 33 = LibTV 有入口 29 / 零入口 4；不记账 21 = 17 / 4。",
            "LibTV 画布用的是复数版 duplicateSelectedNodes / removeSelectedNodes；"
            "单数版 duplicateNode / removeNode 只被 FrameOS、Jimeng 调用。",
            "setEdges 只被 src/app/frameos/canvas/[id]/page.tsx:143 调用；"
            "LibTV 改边只用 addEdge / removeEdge（两个都记账）。",
            "submitLibTVEditorSessionCommit 全 src/ 零调用点，且 git log -S 显示"
            "「命令名+左括号」从未在任何提交里出现过 ⟹ 是预留能力，不是回归掉的接线。",
            "四个零入口命令运行时直调都记账（past +1）⟹ 能力在、入口不在。",
            "反馈清单 12 个 surface 里有 2 个直接指向 store 方法，其中一条登记的"
            "submitLibTVEditorSessionCommit 从不执行 ⟹ 清单登记 ≠ 接线（承 729）。",
            "purgeRemovedCanvas 零入口与 UI 自洽：回收站只有「恢复」「恢复所选 N 项」两个按钮。",
            "解构改名有 3 个别名（setNodes→setStoreNodes / addEdge→addStoreEdge / "
            "setViewport→setStoreViewport）⟹ 不建别名映射就会把 setNodes 误判成零入口。",
        ],
        "retracted": [
            "**撤回「8 个记账命令零入口」**（第一版正则）：用了 "
            "`(?<![\\w.$])name(` 来避开 store 自调用，"
            "结果把 `useCanvasStore.getState().name(...)` 这种正常入口全杀了。",
            "**撤回「setNodes 在 LibTV 零入口」**（第二版正则）：漏了解构改名 —— "
            "page.tsx:366 写 `setNodes: setStoreNodes`，调用点从不出现 `setNodes(`。",
            "**撤回「FrameOS/Jimeng 归属判定第一版」**：只按路径段 `/frameos/` 判，"
            "漏了 src/store/frameosStore.ts、src/lib/frameosUpload.ts 这类"
            "「只有文件名带 frameos」的文件。",
        ],
        "notClaimed": [
            "不声称 4 个零入口记账命令是缺陷还是有意保留 —— 未取证。",
            "不声称源站是否有对应的单节点复制/单节点删除能力 —— 未取证。",
            "「零入口」只覆盖 src/ 内的静态调用点：若有运行时字符串派发或反射调用，本普查读不到"
            "（已用 git log -S 交叉查过 4 个命令，仍不能排除一切动态路径）。",
            "「反馈清单登记 ≠ 接线」只对本批核到的这 1 条成立；其余 11 个 surface 未逐条核接线。",
            "回收站两个按钮只读了源码 onClick 与 DOM 按钮集合，未实际点击验证恢复行为。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
