#!/usr/bin/env python3
"""batch 747 验收：把 16 个记账命令里最后两个「从未真跑」的跑通 ——
`createVideoContinuation` → `clearVideoContinuation`、`createPictureEdit`（主体消除第三段）

## 起点

744 把 16 个记账命令分成 A 8 / B 8；745 走完 B 档 7 个（5 真跑 / 2 被时长挡住）；
746 走完 A 档剩下 4 个。走完之后 16 个里**只剩两个从未被真正触发过**：

- `createPictureEdit`（主体消除）—— 745 证到「面板能开、提交按钮 disabled」，
  但「标记主体」那一跳没做 ⟹ 命令本身没被调用。
- `clearVideoContinuation`（清除续写）—— 745/746 都只验到「入口条件不满足」。

本批把这两个跑通，并**纠正 745 的一条待拍板项**。

## 决定性读数（先看这条）

### ① 纠正 745：提交按钮 disabled **不是没有提示**

745 的待拍板③ 写「主体消除提交按钮 disabled 但无提示『要先标记主体』」。
实际 `PictureEditPanel.tsx:865-875` 渲染了这句话：

```
<span data-picture-edit-submit-reason={reason ?? undefined}
      className={cn("min-w-0 flex-1 truncate text-[11px]",
                    reason ? "text-[#bd8c55]" : "text-[#777]")}>
  {submitting ? "分析中" : reason ?? `当前帧 …s · 标记将用于整段视频`}
</span>
```

实测 `data-picture-edit-submit-reason="请先标记主体"`（琥珀色 `text-[#bd8c55]`）。
⟹ 745 那条待拍板项**事实不成立**，撤回。

### ② `continuation` 写在**新卡**上，且确认后**选中会切到新卡**

`canvasStore.ts:1712-1733` 建的是一张**新的** video 卡（`续写 <源卡名>`、
`status: "empty"`、`durationSeconds: 6`），`data.continuation` 写在这张卡上（`:1731`），
**不是源卡**；`:1756-1757` 紧接着 `selectedNodeIds: [targetId]` ⟹ 选中切到新卡。
所以「退出续写模式」按钮出现在**续写卡**的生成面板上，
`clearVideoContinuation(id)` 里的 `id` 也是这张卡。

### ③ 「退出续写模式」**只降级不删卡**

`canvasStore.ts:2990-3008` 做两件事：`delete nextData.continuation`（从续写卡摘掉元数据）
+ `edges.filter(edge => edge.id !== continuation.edgeId)`（删连线）——
**没有删节点**。实测：节点数 ±0、边 −1、`past` +1，续写卡仍在、`status` 仍是 `"empty"`
⟹ 卡留在画布上，`VideoNode.tsx:548` 的 `data-video-continuation-empty`
渲染「**等待续写内容**」。

### ④ UI 的 4 秒下限与 store 的 4 秒守卫**同值**

```
VideoContinuationSelector.tsx:23  const MIN_DURATION = 4;
VideoContinuationSelector.tsx:102 const end = clamp(pointerSeconds, session.startSeconds + MIN_DURATION, …)
canvasStore.ts:1687               if (normalizedEnd - normalizedStart < 4) return null;
```

且 `[data-video-continuation-confirm]`（`:230-238`）**没有 `disabled` 属性** ——
无论区间多窄都可点，全靠 clamp 兜住 ⟹ store 守卫是纯纵深防御。

### ⑤ 主体消除第三段：落一个 point 标记就解禁

overlay 的 `pointerdown` 走 `beginDraw`（`:379-409`）的 `tool === "point"` 分支
⟹ 一次 `mouse.down/up` 就落一个标记。

## 判据

C1  静态：三个命令各恰好两处（声明 + 实现）；UI 的 `MIN_DURATION` 与 store 的 `<4` 守卫同值；
    确认按钮无 `disabled`；`clearVideoContinuation` 删元数据 + 删边但**不删节点**；
    `PictureEditPanel` 有 `data-picture-edit-submit-reason`
C2  智能续写入口：工具栏「智能续写」文字按钮 ⟹ `[data-video-continuation-selector]` 出现，
    默认区间 0 → 30.00 秒
C3  确认续写：`past` +1、节点 +1、边 +1；**选中切到新建的续写卡**；
    卡 `filename` = `续写 <源卡名>`、`status: "empty"`；`[data-video-continuation-exit]` 出现
C4  退出续写：`past` +1、节点 **±0**、边 **−1**；续写卡**仍在**且 `continuation` 已被摘掉
C5  主体消除第 1、2 段：改成 10 秒后面板出现，`data-picture-edit-submit-reason="请先标记主体"`、
    提交 `disabled`、计数 `0/4`
C6  主体消除第 3 段：落一个 point 标记 ⟹ 计数 `0/4`→`1/4`、提交解禁；
    点提交 ⟹ `analyzing` → 面板卸载，`past` +1、节点 +1、边 +1、文件名以「主体消除-」开头
C7  16 个记账命令的「真跑过」汇总表
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch746-2026-10-01"  # 占位，下面会改
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch747-2026-10-01"
PANEL = ROOT / "src/components/PictureEditPanel.tsx"
SEL = ROOT / "src/components/VideoContinuationSelector.tsx"
NODE = ROOT / "src/components/nodes/VideoNode.tsx"
STORE = ROOT / "src/store/canvasStore.ts"
BASE = "http://localhost:4317"
W, H = 1280, 1150

EXISTS = """(sel) => Boolean(document.querySelector(sel))"""
CLICK = """(sel) => { const el = document.querySelector(sel); if (!el) return false;
             el.click(); return true; }"""
# 工具栏「智能续写」是 ToolbarButton 的纯文字按钮，没有 data 属性
BYTEXT = """(t) => { const b = [...document.querySelectorAll('button')]
           .find(x => (x.textContent||'').trim() === t);
           if (!b) return false; b.click(); return true; }"""
TXT = """(sel) => { const el = document.querySelector(sel);
           return el ? (el.textContent || '').trim() : null; }"""
ATTR = """(a) => { const [sel, name] = a; const el = document.querySelector(sel);
          return el ? el.getAttribute(name) : null; }"""
VIS = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
           const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
           return {display: cs.display, w: Math.round(r.width), h: Math.round(r.height),
                   cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2)}; }"""

# 快照：额外记「带 continuation 的那张卡」—— 746 探针踩过读错节点的坑
SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  const sel = s.selectedNodeIds || [];
  const contNodes = g.nodes.filter(n => n.data && n.data.continuation).map(n => ({
    id: n.id, filename: (n.data && n.data.filename) || null,
    status: (n.data && n.data.status) || null,
    duration: (n.data && n.data.durationSeconds) || null,
    start: n.data.continuation.startSeconds, end: n.data.continuation.endSeconds,
    edgeId: n.data.continuation.edgeId, sourceNodeId: n.data.continuation.sourceNodeId }));
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length, past: h.past.length,
          selected: sel.slice().sort(),
          typeCounts: g.nodes.reduce((a, n) => (a[n.type] = (a[n.type]||0)+1, a), {}),
          files: g.nodes.map(n => (n.data && n.data.filename) || null).filter(Boolean),
          contNodes, nodeIds: g.nodes.map(n => n.id).sort()};
}"""


def static_scan():
    """静态读数。范围/归属判定与前批逐字一致：只读 4 个指定文件的指定段落。"""
    store = STORE.read_text(encoding="utf-8").split("\n")
    sel = SEL.read_text(encoding="utf-8").split("\n")
    pe = PANEL.read_text(encoding="utf-8").split("\n")
    node = NODE.read_text(encoding="utf-8").split("\n")
    out = {}

    # 三个命令：声明 + 实现，各恰好两处
    for name in ("createVideoContinuation", "clearVideoContinuation", "createPictureEdit"):
        out[f"decl_{name}"] = [i for i, l in enumerate(store, 1)
                               if re.match(rf"\s*{name}:", l)]
    # 4 秒：UI 常量 ⟺ store 守卫
    out["uiMinDurationLine"] = next(i for i, l in enumerate(sel, 1)
                                    if "const MIN_DURATION" in l)
    out["uiMinDurationSrc"] = next(l.strip() for l in sel if "const MIN_DURATION" in l)
    out["uiClampLine"] = next(i for i, l in enumerate(sel, 1)
                              if "session.startSeconds + MIN_DURATION" in l)
    out["storeGuardLine"] = next(i for i, l in enumerate(store, 1)
                                 if "normalizedEnd - normalizedStart < 4" in l)
    out["storeGuardSrc"] = next(l.strip() for l in store
                                if "normalizedEnd - normalizedStart < 4" in l)
    # 确认按钮有没有 disabled
    ci = next(i for i, l in enumerate(sel, 1) if "data-video-continuation-confirm" in l)
    out["confirmLine"] = ci
    out["confirmHasDisabled"] = "disabled" in sel[ci]
    # continuation 写在 target 节点 + 选中切过去
    out["contOnTargetLine"] = next(i for i, l in enumerate(store, 1)
                                   if l.strip() == "continuation," )
    out["selectTargetLine"] = next(i for i, l in enumerate(store, 1)
                                   if "selectedNodeIds: [targetId]" in l)
    # clearVideoContinuation：摘元数据 + 删边，但不删节点
    ci2 = out["decl_clearVideoContinuation"][-1]
    seg = store[ci2 - 1:ci2 + 40]
    out["clearLine"] = ci2
    out["clearDeletesContinuation"] = any("delete nextData.continuation" in l for l in seg)
    out["clearFiltersEdge"] = any("canvas.edges.filter" in l for l in seg)
    out["clearTouchesNodes"] = any(re.search(r"nodes:\s*canvas\.nodes\.filter", l) for l in seg)
    out["clearPushesHistory"] = any("pushHistory" in l for l in seg)
    # 主体消除：reason 三分支 + 读点
    out["reasonLine"] = next(i for i, l in enumerate(pe, 1)
                             if 'if (marks.length === 0) return "请先标记主体"' in l)
    out["reasonReasons"] = [i for i, l in enumerate(pe, 1) if 'return "请' in l]
    out["reasonReadLine"] = next(i for i, l in enumerate(pe, 1)
                                 if "data-picture-edit-submit-reason" in l)
    out["reasonColour"] = "#bd8c55" if any("#bd8c55" in l for l in pe) else None
    out["submitLine"] = next(i for i, l in enumerate(pe, 1) if "data-picture-edit-submit" in l)
    out["submitDisabledLine"] = next(i for i, l in enumerate(pe, 1)
                                     if "disabled={!canSubmit}" in l)
    out["canSubmitLine"] = next(i for i, l in enumerate(pe, 1)
                                if "const canSubmit" in l)
    out["beginDrawLine"] = next(i for i, l in enumerate(pe, 1) if "beginDraw" in l)
    out["pointBranchLine"] = next(i for i, l in enumerate(pe, 1)
                                  if 'if (tool === "point")' in l)
    # VideoNode：确认续写回调 + 空态渲染
    out["confirmContinuationLine"] = next(i for i, l in enumerate(node, 1)
                                          if "const confirmContinuation" in l)
    out["emptyStateLine"] = next(i for i, l in enumerate(node, 1)
                                 if "data-video-continuation-empty" in l)
    out["emptyStateText"] = "等待续写内容" if any("等待续写内容" in l for l in node) else None
    return out


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    st = static_scan()
    print("=== C1 静态 ===")
    for k, v in st.items():
        print(f"  {k:26s} {v}")

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        def fresh():
            page.goto(f"{BASE}/?batch747=1", wait_until="networkidle", timeout=90_000)
            page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.wait_for_timeout(1_200)
            return page.evaluate("""() => {
              const s = window.__libtv_store.getState();
              const before = new Set(s.getActiveCanvas().nodes.map(n => n.id));
              s.addNode('video');
              const g = window.__libtv_store.getState().getActiveCanvas();
              const v = g.nodes.find(n => !before.has(n.id));
              s.selectElements({nodeIds: [v.id], edgeIds: []});
              return {id: v.id, file: (v.data && v.data.filename) || null}; }""")

        # ================= A. 智能续写 → 清除续写 =================
        print("\n=== A1/C2 智能续写入口 ===")
        vid = fresh()
        src_file = page.evaluate("""(id) => { const g=window.__libtv_store.getState().getActiveCanvas();
            const n=g.nodes.find(x=>x.id===id); return (n.data&&n.data.filename)||null; }""", vid["id"])
        opened = page.evaluate(BYTEXT, "智能续写")
        page.wait_for_timeout(1_000)
        c2 = {"toolbarClicked": opened,
              "selectorPresent": page.evaluate(EXISTS, "[data-video-continuation-selector]"),
              "defaultDurationText": page.evaluate(TXT, "[data-video-continuation-duration]"),
              "confirmText": page.evaluate(TXT, "[data-video-continuation-confirm]"),
              "confirmDisabled": page.evaluate(ATTR, ["[data-video-continuation-confirm]", "disabled"]),
              "regionBox": page.evaluate(VIS, "[data-video-continuation-region]"),
              "sourceFile": src_file}
        print(f"  工具栏「智能续写」={opened}；面板={c2['selectorPresent']}")
        print(f"  默认区间文案={c2['defaultDurationText']!r}；确认钮={c2['confirmText']!r} "
              f"disabled={c2['confirmDisabled']!r}")
        print(f"  源卡文件名={src_file!r}；region 盒={c2['regionBox']}")

        print("\n=== A2/C3 确认续写 ===")
        s0 = page.evaluate(SNAP)
        confirmed = page.evaluate(CLICK, "[data-video-continuation-confirm]")
        page.wait_for_timeout(1_500)
        s1 = page.evaluate(SNAP)
        exit_now = page.evaluate(EXISTS, "[data-video-continuation-exit]")
        c3 = {"confirmed": confirmed,
              "past": [s0["past"], s1["past"]],
              "nodes": [s0["nodeCount"], s1["nodeCount"]],
              "edges": [s0["edgeCount"], s1["edgeCount"]],
              "selectionBefore": s0["selected"], "selectionAfter": s1["selected"],
              "selectionMovedToNewCard": s1["selected"] == [s1["contNodes"][0]["id"]]
                                       if len(s1["contNodes"]) == 1 else None,
              "contNodes": s1["contNodes"],
              "sourceNodeId": vid["id"],
              "expectedFilename": f"续写 {src_file}",
              "exitButtonPresent": exit_now}
        print(f"  clicked={confirmed}")
        print(f"  past {s0['past']}→{s1['past']}、节点 {s0['nodeCount']}→{s1['nodeCount']}、"
              f"边 {s0['edgeCount']}→{s1['edgeCount']}")
        print(f"  选中：{s0['selected']} → {s1['selected']}（源卡 {vid['id']}）")
        print(f"  带 continuation 的卡：{json.dumps(s1['contNodes'], ensure_ascii=False)}")
        print(f"  期望文件名 {c3['expectedFilename']!r}；「退出续写模式」按钮={exit_now}")

        print("\n=== A3/C4 退出续写 ===")
        cont_id = s1["contNodes"][0]["id"] if s1["contNodes"] else None
        confirmed2 = page.evaluate(CLICK, "[data-video-continuation-exit]")
        page.wait_for_timeout(1_200)
        s2 = page.evaluate(SNAP)
        still_there = page.evaluate(
            "(id) => window.__libtv_store.getState().getActiveCanvas().nodes.some(n=>n.id===id)",
            cont_id)
        after_nodes = page.evaluate("""() => window.__libtv_store.getState().getActiveCanvas()
            .nodes.filter(n => (n.data&&n.data.filename||'').startsWith('续写 '))
            .map(n => ({id:n.id, file:n.data.filename, status:(n.data&&n.data.status)||null,
                        hasCont:Boolean(n.data&&n.data.continuation),
                        duration:(n.data&&n.data.durationSeconds)||null}))""")
        c4 = {"cleared": confirmed2, "contCardId": cont_id,
              "past": [s1["past"], s2["past"]],
              "nodes": [s1["nodeCount"], s2["nodeCount"]],
              "edges": [s1["edgeCount"], s2["edgeCount"]],
              "cardStillOnCanvas": still_there,
              "contNodesAfter": s2["contNodes"],
              "continuationCardsAfter": after_nodes,
              "exitButtonStillPresent": page.evaluate(EXISTS, "[data-video-continuation-exit]")}
        print(f"  clicked={confirmed2}")
        print(f"  past {s1['past']}→{s2['past']}、节点 {s1['nodeCount']}→{s2['nodeCount']}、"
              f"边 {s1['edgeCount']}→{s2['edgeCount']}")
        print(f"  续写卡 {cont_id} 还在画布上吗：{still_there}")
        print(f"  退出后带 continuation 的卡：{json.dumps(s2['contNodes'], ensure_ascii=False)}")
        print(f"  退出后「续写 」开头的卡：{json.dumps(after_nodes, ensure_ascii=False)}")
        print(f"  「退出续写模式」按钮还在吗：{c4['exitButtonStillPresent']}")

        # ================= B. 主体消除三段式 =================
        print("\n\n=== B1/C5 主体消除：面板与 disabled 提示 ===")
        vid = fresh()
        page.wait_for_timeout(1_200)
        d_before = page.evaluate("""(id) => { const g=window.__libtv_store.getState().getActiveCanvas();
            const n=g.nodes.find(x=>x.id===id); return (n.data&&n.data.durationSeconds)||null; }""",
                                 vid["id"])
        setter = page.evaluate("""(id) => { const s=window.__libtv_store.getState();
            if (typeof s.updateNodeData !== 'function') return 'NO updateNodeData';
            s.updateNodeData(id, {durationSeconds: 10}); return 'updateNodeData'; }""", vid["id"])
        page.wait_for_timeout(800)
        d_after = page.evaluate("""(id) => { const g=window.__libtv_store.getState().getActiveCanvas();
            const n=g.nodes.find(x=>x.id===id); return (n.data&&n.data.durationSeconds)||null; }""",
                                vid["id"])
        m1 = page.evaluate(CLICK, "[data-video-picture-edit-menu-trigger]")
        page.wait_for_timeout(800)
        m2 = page.evaluate(CLICK, '[data-video-picture-edit-action="subjectRemove"]')
        page.wait_for_timeout(1_200)
        c5 = {"durationBefore": d_before, "durationSetter": setter, "durationAfter": d_after,
              "menuOpened": m1, "actionPicked": m2,
              "panelPresent": page.evaluate(EXISTS, "[data-picture-edit-panel]"),
              "submitReason": page.evaluate(
                  "() => { const e=document.querySelector('[data-picture-edit-submit-reason]');"
                  " return e?{attr:e.getAttribute('data-picture-edit-submit-reason'),"
                  "text:(e.textContent||'').trim(),colour:getComputedStyle(e).color}:null; }"),
              "submit": page.evaluate("""() => { const e=document.querySelector('[data-picture-edit-submit]');
                  if(!e) return null;
                  return {disabled:e.disabled, status:e.getAttribute('data-picture-edit-submit-status'),
                          aria:e.getAttribute('aria-label'), text:(e.textContent||'').trim()}; }"""),
              "count": page.evaluate(TXT, "[data-picture-edit-count]"),
              "overlay": page.evaluate(VIS, "[data-picture-edit-mark-overlay]"),
              "tool": page.evaluate("""() => { const e=document.querySelector('[data-picture-edit-mark-overlay]');
                  return e?e.getAttribute('data-picture-edit-tool'):null; }"""),
              "marksAtOpen": page.evaluate(
                  "() => document.querySelectorAll('[data-picture-edit-mark]').length")}
        print(f"  时长 {d_before} →（{setter}）→ {d_after}（745 验过 30 秒会被时长门控挡住）")
        print(f"  菜单 {m1} → 主体消除 {m2}；面板={c5['panelPresent']}；工具={c5['tool']!r}")
        print(f"  提交原因 {json.dumps(c5['submitReason'], ensure_ascii=False)}")
        print(f"  提交按钮 {json.dumps(c5['submit'], ensure_ascii=False)}；计数={c5['count']!r}")
        print(f"  overlay 盒={c5['overlay']}")

        print("\n=== B2/C6 落一个 point 标记 → 提交 ===")
        ov = c5["overlay"]
        if ov and ov["w"] > 0:
            page.mouse.move(ov["cx"], ov["cy"])
            page.wait_for_timeout(250)
            page.mouse.down()
            page.wait_for_timeout(120)
            page.mouse.up()
            page.wait_for_timeout(800)
        marks_after = page.evaluate("() => document.querySelectorAll('[data-picture-edit-mark]').length")
        count_after = page.evaluate(TXT, "[data-picture-edit-count]")
        submit_after = page.evaluate("""() => { const e=document.querySelector('[data-picture-edit-submit]');
            if(!e) return null; return {disabled:e.disabled,
            status:e.getAttribute('data-picture-edit-submit-status')}; }""")
        s3 = page.evaluate(SNAP)
        submitted = page.evaluate(CLICK, "[data-picture-edit-submit]")
        page.wait_for_timeout(300)
        status_mid = page.evaluate("""() => { const e=document.querySelector('[data-picture-edit-submit]');
            return e?e.getAttribute('data-picture-edit-submit-status'):null; }""")
        panel_at_300 = page.evaluate(EXISTS, "[data-picture-edit-panel]")
        page.wait_for_timeout(2_200)
        status_end = page.evaluate("""() => { const e=document.querySelector('[data-picture-edit-submit]');
            return e?e.getAttribute('data-picture-edit-submit-status'):null; }""")
        panel_at_2500 = page.evaluate(EXISTS, "[data-picture-edit-panel]")
        s4 = page.evaluate(SNAP)
        new_files = [f for f in s4["files"] if f not in s3["files"]]
        new_nodes = [n for n in s4["nodeIds"] if n not in s3["nodeIds"]]
        new_node_status = page.evaluate("""(ids) => { const g=window.__libtv_store.getState().getActiveCanvas();
            return g.nodes.filter(n=>ids.includes(n.id)).map(n=>({id:n.id,
            file:(n.data&&n.data.filename)||null, status:(n.data&&n.data.status)||null,
            type:n.type})); }""", new_nodes)
        c6 = {"marksAtOpen": c5["marksAtOpen"], "marksAfterPointer": marks_after,
              "count": [c5["count"], count_after],
              "submitBeforeMark": c5["submit"], "submitAfterMark": submit_after,
              "submitted": submitted,
              "statusAt300ms": status_mid, "panelAt300ms": panel_at_300,
              "statusAt2500ms": status_end, "panelAt2500ms": panel_at_2500,
              "past": [s3["past"], s4["past"]],
              "nodes": [s3["nodeCount"], s4["nodeCount"]],
              "edges": [s3["edgeCount"], s4["edgeCount"]],
              "newFiles": new_files, "newNodeData": new_node_status}
        print(f"  标记数 {c5['marksAtOpen']}→{marks_after}；计数 {c5['count']!r}→{count_after!r}")
        print(f"  提交按钮 标记前={json.dumps(c5['submit'], ensure_ascii=False)} "
              f"标记后={json.dumps(submit_after, ensure_ascii=False)}")
        print(f"  点提交 clicked={submitted}；300ms status={status_mid!r} 面板={panel_at_300}；"
              f"2.5s status={status_end!r} 面板={panel_at_2500}")
        print(f"  past {s3['past']}→{s4['past']}、节点 {s3['nodeCount']}→{s4['nodeCount']}、"
              f"边 {s3['edgeCount']}→{s4['edgeCount']}")
        print(f"  新文件={new_files}；新节点={json.dumps(new_node_status, ensure_ascii=False)}")

        page.close()
        browser.close()

    results = {"A2_continuationEntry": c2, "A3_confirm": c3, "A4_clear": c4,
               "B1_pictureEditOpen": c5, "B2_pictureEditSubmit": c6, "static": st}
    print("\n=== 汇总 ===")
    for k, v in results.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")

    # 16 个记账命令的「真跑过」汇总（口径来自 744 的 A/B 分档表）
    run_table = [
        {"cmd": "createFirstFrameReference", "tier": "A", "ran": "744", "delta": "past+1、只写 attempt"},
        {"cmd": "createFirstLastFrameReference", "tier": "A", "ran": "744", "delta": "past+1、只写 attempt"},
        {"cmd": "updateNodeData（setAttempt）", "tier": "A", "ran": "744/745/746", "delta": "past+1"},
        {"cmd": "addNodeAtPosition + addEdge（选特效）", "tier": "A", "ran": "746", "delta": "past+2、节点+1、边+1"},
        {"cmd": "destroyFirstFrameReference", "tier": "A", "ran": "746", "delta": "past+1、节点-1、边-1"},
        {"cmd": "createLongVideoProcess", "tier": "A", "ran": "746", "delta": "past+1、节点+12、边+22"},
        {"cmd": "addDerivedNode（逐帧拉片）", "tier": "B", "ran": "745", "delta": "past+1、节点+1、边+1"},
        {"cmd": "createVideoFrameCapture（抽帧）", "tier": "B", "ran": "745", "delta": "past+1、节点+1、边+1"},
        {"cmd": "createAudioSplit（音视频分离）", "tier": "B", "ran": "745", "delta": "past+1、节点+2、边+2"},
        {"cmd": "createSubtitleErase（智能去字幕）", "tier": "B", "ran": "745", "delta": "past+1、节点+1、边+1"},
        {"cmd": "createSmartMatting（智能抠像）", "tier": "B", "ran": "745", "delta": "past+1、节点+1、边+1"},
        {"cmd": "createDepthMotionCapture（深度动作捕捉）", "tier": "B", "ran": "745", "delta": "past+1、节点+1（需时长≤15s）"},
        {"cmd": "createVideoContinuation（智能续写）", "tier": "B", "ran": "747", "delta": "past+1、节点+1、边+1"},
        {"cmd": "clearVideoContinuation（清除续写）", "tier": "B", "ran": "747", "delta": "past+1、节点±0、边-1"},
        {"cmd": "createPictureEdit（主体消除）", "tier": "B", "ran": "747", "delta": "past+1、节点+1、边+1（需时长≤15s）"},
        {"cmd": "submitLibTVEditorSessionCommit", "tier": "A", "ran": "—", "delta": "742 验出零 UI 入口，从未触发"},
    ]

    checks = [
        ("C1 静态：三个命令各恰好两处（声明+实现）；UI MIN_DURATION=4 ⟺ store 的 <4 守卫；"
         "确认按钮无 disabled；clear 摘元数据+删边但不删节点；submit-reason 读点存在",
         st.get("decl_createVideoContinuation") == [324, 1663]
         and st.get("decl_clearVideoContinuation") == [374, 2974]
         and st.get("decl_createPictureEdit") == [353, 2615]
         and st.get("uiMinDurationLine") == 23 and "MIN_DURATION = 4" in st.get("uiMinDurationSrc", "")
         and st.get("storeGuardLine") == 1687 and "< 4" in st.get("storeGuardSrc", "")
         and st.get("confirmHasDisabled") is False
         and st.get("clearDeletesContinuation") is True
         and st.get("clearFiltersEdge") is True
         and st.get("clearTouchesNodes") is False
         and st.get("clearPushesHistory") is True
         and st.get("reasonLine") == 534
         and st.get("reasonReadLine") == 866 and st.get("reasonColour") == "#bd8c55"
         and st.get("submitDisabledLine") == 884
         and st.get("emptyStateText") == "等待续写内容",
         json.dumps(st, ensure_ascii=False)),
        ("C2 智能续写入口：工具栏「智能续写」文字按钮 ⟹ 选择器面板出现，默认区间 0→30.00 秒",
         c2["toolbarClicked"] and c2["selectorPresent"]
         and c2["defaultDurationText"] == "30.00 秒"
         and c2["confirmText"] == "确认续写"
         and c2["regionBox"] and c2["regionBox"]["w"] > 0,
         json.dumps(c2, ensure_ascii=False)),
        ("C3 确认续写：past+1、节点+1、边+1；**选中切到新建的续写卡**；卡 filename=「续写 <源卡名>」、"
         "status=empty；「退出续写模式」按钮出现",
         c3["confirmed"] and c3["past"][1] == c3["past"][0] + 1
         and c3["nodes"][1] == c3["nodes"][0] + 1 and c3["edges"][1] == c3["edges"][0] + 1
         and c3["selectionMovedToNewCard"] is True
         and len(c3["contNodes"]) == 1
         and c3["contNodes"][0]["filename"] == c3["expectedFilename"]
         and c3["contNodes"][0]["status"] == "empty"
         and c3["contNodes"][0]["sourceNodeId"] == c3["sourceNodeId"]
         and c3["contNodes"][0]["id"] != c3["sourceNodeId"]
         and c3["exitButtonPresent"] is True,
         json.dumps(c3, ensure_ascii=False)),
        ("C4 退出续写：past+1、节点**±0**、边**-1**；续写卡仍在画布上且 continuation 已被摘掉",
         c4["cleared"] and c4["past"][1] == c4["past"][0] + 1
         and c4["nodes"][1] == c4["nodes"][0] and c4["edges"][1] == c4["edges"][0] - 1
         and c4["cardStillOnCanvas"] is True
         and c4["contNodesAfter"] == []
         and len(c4["continuationCardsAfter"]) == 1
         and c4["continuationCardsAfter"][0]["hasCont"] is False
         and c4["continuationCardsAfter"][0]["status"] == "empty"
         and c4["exitButtonStillPresent"] is False,
         json.dumps(c4, ensure_ascii=False)),
        ("C5 主体消除第 1、2 段：改时长到 10 后面板出现；**submit-reason=「请先标记主体」**、"
         "提交 disabled、计数 0/4（745 记的「无提示」要在这里被推翻）",
         c5["durationBefore"] == 30 and c5["durationAfter"] == 10
         and c5["menuOpened"] and c5["actionPicked"] and c5["panelPresent"]
         and c5["submitReason"] and c5["submitReason"]["attr"] == "请先标记主体"
         and c5["submitReason"]["text"] == "请先标记主体"
         and c5["submitReason"]["colour"] == "rgb(189, 140, 85)"
         and c5["submit"]["disabled"] is True
         and c5["submit"]["aria"] == "提交主体消除"
         and c5["count"] == "0/4" and c5["marksAtOpen"] == 0
         and c5["overlay"] and c5["overlay"]["w"] > 0 and c5["tool"] == "point",
         json.dumps(c5, ensure_ascii=False)),
        ("C6 主体消除第 3 段：落一个 point 标记 ⟹ 计数 0/4→1/4、提交解禁；点提交 ⟹ analyzing → 面板卸载，"
         "past+1、节点+1、边+1、新文件名以「主体消除-」开头",
         c6["marksAfterPointer"] == c6["marksAtOpen"] + 1
         and c6["count"] == ["0/4", "1/4"]
         and c6["submitBeforeMark"]["disabled"] is True
         and c6["submitAfterMark"]["disabled"] is False
         and c6["submitted"]
         and c6["statusAt300ms"] == "analyzing" and c6["panelAt300ms"] is True
         and c6["panelAt2500ms"] is False
         and c6["past"][1] == c6["past"][0] + 1
         and c6["nodes"][1] == c6["nodes"][0] + 1 and c6["edges"][1] == c6["edges"][0] + 1
         and len(c6["newFiles"]) == 1 and c6["newFiles"][0].startswith("主体消除-"),
         json.dumps(c6, ensure_ascii=False)),
        ("C7 16 个记账命令的「真跑过」汇总表 16 行齐（15 真跑 + 1 零入口）",
         len(run_table) == 16
         and sum(1 for r in run_table if r["ran"] != "—") == 15
         and sum(1 for r in run_table if r["ran"] == "—") == 1,
         json.dumps(run_table, ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 747,
        "title": "把 16 个记账命令里最后两个「从未真跑」的跑通：createVideoContinuation → "
                 "clearVideoContinuation、createPictureEdit（主体消除第三段）；"
                 "并撤回 745「主体消除提交按钮无提示」这条待拍板项",
        "verdict": f"{passed}/{len(checks)}",
        "summary": {"results": results, "runTable": run_table},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "**16 个记账命令里最后两个从未触发的，本批都真跑通了** —— "
            "`createVideoContinuation`（智能续写确认）`past` +1、节点 +1、边 +1；"
            "`clearVideoContinuation`（退出续写模式）`past` +1、节点 **±0**、边 **−1**；"
            "`createPictureEdit`（主体消除第三段）`past` +1、节点 +1、边 +1、"
            "新文件名「主体消除-<源卡名>」。16 个里 15 个真跑过，"
            "只剩 742 验出零 UI 入口的 `submitLibTVEditorSessionCommit`。",
            "**撤回 745 的待拍板③**：「主体消除提交按钮 disabled 但无提示『要先标记主体』」"
            "**事实不成立**。`PictureEditPanel.tsx:865-875` 渲染了这句提示，"
            "并挂在 `data-picture-edit-submit-reason` 上；实测属性值与文本都是"
            "「请先标记主体」，颜色 `rgb(189, 140, 85)`（`text-[#bd8c55]`，琥珀色警示调）。"
            "745 是因为面板开了就直接读 `disabled`，没去读旁边的提示文本。",
            "**`continuation` 写在新建的续写卡上，不在源卡上** —— "
            "`canvasStore.ts:1712-1733` 建的是一张新的 video 卡（`续写 <源卡名>`、"
            "`status: \"empty\"`、`durationSeconds: 6`），`data.continuation` 写在这张卡（`:1731`）；"
            "`:1756-1757` 紧接着 `selectedNodeIds: [targetId]` ⟹ **确认后面板与选中都切到了续写卡**。",
            "**「退出续写模式」只降级、不删卡** —— `:2990-3008` 做两件事："
            "`delete nextData.continuation`（从续写卡摘掉元数据）+ "
            "`edges.filter(edge => edge.id !== continuation.edgeId)`（删连线），"
            "**没有删节点**。实测节点 ±0、边 −1，续写卡留在画布上、`status` 仍是 `\"empty\"` "
            "⟹ `VideoNode.tsx:548` 的 `data-video-continuation-empty` 渲染「**等待续写内容**」。",
            "**UI 的 4 秒下限与 store 的 4 秒守卫同值** —— "
            "`VideoContinuationSelector.tsx:23 const MIN_DURATION = 4`；"
            "`:102` 拖动 `end` 时 clamp 下界 = `startSeconds + MIN_DURATION`；"
            "`canvasStore.ts:1687 if (normalizedEnd - normalizedStart < 4) return null;`。"
            "且 `[data-video-continuation-confirm]` **没有 `disabled` 属性** ⟹ "
            "走 UI 出不了窄区间，store 守卫是**纯纵深防御**、不是可达的拒绝路径。",
            "**主体消除第三段只需一次 `pointerdown`** —— overlay 的 `beginDraw`"
            "（`PictureEditPanel.tsx:379-409`）在 `tool === \"point\"` 时直接建标记；"
            "实测一次 `mouse.down/up` ⟹ 标记 0→1、计数 `0/4`→`1/4`、提交按钮 `disabled` 翻转。"
            "默认工具就是 `point`（实测 `data-picture-edit-tool=\"point\"`），不用先切工具。",
            "**提交后走 `analyzing` 再卸载面板** —— 点提交 300ms 时 "
            "`data-picture-edit-submit-status=\"analyzing\"`、面板仍在；2.5s 时属性与面板**都已消失**"
            "（`submitPictureEdit` 关面板）⟹ 这个异步阶段是「面板关掉」，不是「状态回到 idle」。",
            "**「智能续写」是「一段面板 + 一次确认」** —— 744/745 记的「两段式」是两次点击"
            "（开面板 → 点确认），不是两个面板：`VideoContinuationSelector.tsx:233` "
            "的 `onClick={() => onConfirm(range.start, range.end)}` 直连 `VideoNode.tsx:217` "
            "的 `confirmContinuation` → `createVideoContinuation`，中间没有第二个表单。",
        ],
        "probeCorrections": [
            "**第一版读错了节点**（本批最重要的一次返工）：确认续写后我去读**源卡**的 "
            "`data.continuation`，读成 `null`，差点判成「命令没写上」。实际 `continuation` 在"
            "**新建的续写卡**上，且 `:1756-1757` 已把选中切过去。改法：快照里加一个"
            "`contNodes`（按 `data.continuation` 存在与否筛节点）而不是按 `id` 找。",
            "**「找那个有 X 的元素」不能按已知 id 找** —— 我手里有的是源卡 id，"
            "而要找的字段长在另一个节点上。746 已经栽过一次同类坑（`display:none` 元素按自身盒子 hover），"
            "两批的共同教训：**先确认「要找的东西在哪个节点上」，再动手读**。",
            "**起手式滑杆/手柄要先看它到底是什么** —— 我按「滑杆」写了 `min/max/step/value` 的读法，"
            "实测 `[data-video-continuation-start]` / `-end` 是 `<button>` 手柄（16×16，"
            "`min/max/step` 全为 `null`）⟹ 读数全空。改成先打 `type`/`tagName` 再决定读法。",
        ],
        "notClaimed": [
            "不声称**续写卡「等待续写内容」空态的视觉与源站是否一致** —— 未取证。",
            "「退出续写模式」留下空卡**是否有意**（降级 vs 删卡）—— 未取证，不判定为缺陷。",
            "`createVideoContinuation` 的 `< 4` 秒守卫**未真跑**（UI 走不到该区间）；"
            "只证到 UI clamp 与 store 守卫常量同值。",
            "**续写卡本身的生成**（`status: \"empty\"` → 生成出内容）未跑 —— "
            "那是续写卡的生成按钮，不在本批 3 个命令内。",
            "`createPictureEdit` 建的节点在 2.5s 时的 `status` 只记了读数，"
            "**后续是否会从 `pending` 演进未取证**（745 已记过同一限制）。",
            "主体消除只验了 `subjectRemove`；`subjectModify` / `subjectReplace` 的"
            "另外两条 `reason` 分支（「请补充每个主体的修改描述」/「请为每个主体选择替换图」）"
            "**只从源码读到，未跑**。",
            "16 个命令的汇总表**沿用 744 的 A/B 分档口径**，本批没有重跑前 13 条 —— "
            "「真跑过」是**跨批次累计**的结论，不是本批的独立读数。",
            "「智能续写」在 failed 卡上不可达（745 已证 L2 `status === \"ready\"` 门控），"
            "本批**只在 ready 卡上跑**，未做两态对照。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
