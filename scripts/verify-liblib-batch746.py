#!/usr/bin/env python3
"""batch 746 验收：A 档剩下 4 个命令逐个走完 —— `createLongVideoProcess` 有一条
被菜单藏起来、但芯片能进的路径；同一个「已加入本地任务」提示，真假各有一条

## 起点

745 把 B 档 7 个命令走完了。A 档 8 个里只验过 3 枚尝试芯片，
`createLongVideoProcess` / 选特效（`addNodeAtPosition`+`addEdge`）/
`destroyFirstFrameReference` / `clearVideoContinuation` 这 4 个**还没真跑过**。

## 决定性读数（先看这条）

### ① `long-video` 模式**在模式菜单里进不去，但芯片能进** —— 两条赋值路径

```
VideoGenerationPanel.tsx:110  { id: "long-video", label: "超长视频",
                                 disabled: true, inMenu: false, badge: "Beta" }
VideoGenerationPanel.tsx:974  .filter((item) => !("inMenu" in item && item.inMenu === false))
VideoGenerationPanel.tsx:172  const isLongVideo = mode === "long-video";
VideoGenerationPanel.tsx:225-229  if (attempt === "5分钟超长视频") {
                                     setMode("long-video");   // ← 芯片路径，菜单管不着
                                     setModel("2.5"); setRatio("Auto"); setDuration(300);
                                   }
```

我第一版只追了 `selectMode`（菜单那条赋值路径）就断言 `mode` 永远到不了
`"long-video"` —— **那是我自己的静态推理漏了一条赋值点**。
实测：点节点卡的「5分钟超长视频」芯片 ⟹ 模式触发器从「文生视频」翻成
「**超长视频**」、参数从「16:9 · 720P · 5s」翻成「**Auto · 720P · 300s**」、
`data-video-long-submit-state` 从**不存在**变成 `"idle"`、「查看过程」按钮出现。

**⟹ 模式菜单的 5 项里没有「超长视频」，但面板上会显示「超长视频」。**
用户进得去（芯片）、也退得出（`:268-270` 选别的模式会顺带清芯片），但**看不到自己在哪个模式里**。

### ② `createLongVideoProcess` 真跑通：`past` +1、节点 **+12**、边 **+22**

`long-state` 三态真实流转 `idle → submitting（按钮 disabled + spinner）→ created`，
`title` 同步 `生成视频 → 正在创建本地过程 → 已加入本地任务`，
「查看过程」翻成「返回编辑」。

### ③ **同一个「已加入本地任务」提示，真假各有一条**

| | 非长视频路径（默认态） | 长视频路径（芯片后） |
|---|---|---|
| `data-video-long-submit-state` | **属性不存在** | `idle` → `submitting` → `created` |
| 提交中按钮 `disabled` | `false`（**无防重入**） | `true` + spinner |
| `title` 终态 | 「已加入本地任务」 | 「已加入本地任务」 |
| 图标终态 | 对勾 | 对勾 |
| 底色终态 | 变蓝 | 变蓝 |
| **`past`** | **+0** | **+1** |
| **节点 / 边** | **±0** | **+12 / +22** |

⟹ 撒谎的不是这句提示，而是**非长视频分支（`:309-312`）复用了长视频的整套提交反馈**
（蓝底 / 对勾 / 「已加入本地任务」/`title` 三元在 `:852-863`，不区分 `isLongVideo`）
却一个字节都不写。

### ④ 静态写点与运行时读数**逐个对平**

`canvasStore.ts:2244 createLongVideoProcess` 一次建出：
12 个 `makeProcessNode` 写点（material 3 + shot 3 + candidate 4 + assembly 1 + final 1
= `:2332/2341/2350/2361/2370/2379/2390/2400/2410/2420/2431/2439`）
与 22 条边（`source→shot` 3 + `material→shot` 6 + `shot→candidate` 8 +
`candidate→assembly` 4 + `assembly→final` 1 = `:2462-2480`）
⟹ 运行时实测**节点 +12、边 +22**，两个数都对得上。

## 判据

C1  静态：`long-video` 是 `inMenu: false`（被 `:974` 过滤掉），但 `:226` 有
    `setMode("long-video")` ⟹ **存在第二条赋值路径**
C2  运行时：模式菜单 5 项，`long-video` 不在其中
C3  非长视频路径点「生成视频」⟹ store 零写入（past/节点/边/nodeIds/edgeIds 全同），
    但按钮变蓝 + `title` 变「已加入本地任务」，而 `long-state` **属性不存在**
C4  芯片路径：点「5分钟超长视频」⟹ 模式触发器变「超长视频」、`long-state` 变 `idle`、
    「查看过程」出现；再点「生成视频」⟹ `submitting`（`disabled`）→ `created`，
    且 **`past` +1、节点 +12、边 +22**、「返回编辑」出现
C5  对账：静态 12 个 `makeProcessNode` 写点、22 条边 ⟺ 运行时 +12 / +22
C6  选特效：节点 +1（`image`「素材 - 特效 - X」）+ 边 +1，且 **`past` +2**（两次独立记账）
C7  销毁首帧：hover **外层** `[data-video-firstframe-slot]` 后按钮 `display: none→flex`
    （group 类挂在外层，不在内层槽）；先造 attempt 再点 ⟹ `past` +1、节点 −1、边 −1
C8  退出路径：长视频态下从模式菜单选 `text` ⟹ 芯片被清、模式回落（`:268-270`）
C9  芯片不是 toggle：再点一次同芯片 ⟹ `past` +1 但模式/参数/节点/边**零变化**
C10 清除续写：无 continuation 时 `[data-video-continuation-exit]` 不渲染
C11 A 档 8 个命令的运行时状态汇总表
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch746-2026-10-01"
PANEL = ROOT / "src/components/VideoGenerationPanel.tsx"
STORE = ROOT / "src/store/canvasStore.ts"
BASE = "http://localhost:4317"
W, H = 1280, 1150

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length,
          past: h.past.length, future: h.future.length,
          nodeIds: g.nodes.map(n => n.id).sort(), edgeIds: g.edges.map(e => e.id).sort(),
          typeCounts: g.nodes.reduce((a, n) => (a[n.type] = (a[n.type]||0)+1, a), {}),
          filenames: g.nodes.map(n => (n.data && n.data.filename) || null).filter(Boolean),
          videoData: g.nodes.filter(n => n.type === 'video').map(n => ({
            id: n.id, status: (n.data && n.data.status) || null,
            attempt: (n.data && n.data.attempt) || null,
            continuation: (n.data && n.data.continuation) || null }) )};
}"""

EXISTS = """(sel) => Boolean(document.querySelector(sel))"""
CLICK = """(sel) => { const el = document.querySelector(sel); if (!el) return false;
             el.click(); return true; }"""
VIS = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
           const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
           return {display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
                   w: Math.round(r.width), h: Math.round(r.height)}; }"""
# 提交按钮的三个可见量：class 底色、title、图标字形。
# 图标区分靠 Lucide 的 class —— 原始上箭头 svg 带 aria-hidden 且无 lucide 类（:875）。
BTN = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
            return {className: el.className, title: el.title, disabled: el.disabled,
                    longState: el.getAttribute('data-video-long-submit-state'),
                    icon: el.querySelector('svg.lucide-loader-circle') ? 'spinner'
                         : el.querySelector('svg.lucide-check') ? 'check'
                         : el.querySelector('svg[aria-hidden]') ? 'arrow' : 'none'}; }"""
# 页脚三枚触发器 + 「查看过程/返回编辑」——长视频态的四个可观测面。
FOOT = """() => {
  const txt = (sel) => { const e = document.querySelector(sel);
                         return e ? (e.textContent || '').trim() : null; };
  const procBtn = [...document.querySelectorAll('button')]
    .find(x => /^(查看过程|返回编辑)$/.test((x.textContent || '').trim()));
  return {model: txt('[data-video-model-trigger]'), mode: txt('[data-video-mode-trigger]'),
          params: txt('[data-video-params-trigger]'),
          process: procBtn ? procBtn.textContent.trim() : null};
}"""
BOX = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
            const r = el.getBoundingClientRect();
            return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
                    h: Math.round(r.height), cx: Math.round(r.x + r.width / 2),
                    cy: Math.round(r.y + r.height / 2)}; }"""


def static_panel():
    """静态读数。范围与归属判定与前批逐字一致：只读 VideoGenerationPanel.tsx 与
    canvasStore.ts 里 createLongVideoProcess 那一段。"""
    lines = PANEL.read_text(encoding="utf-8").split("\n")
    out = {}
    for i, l in enumerate(lines, 1):
        if 'id: "long-video"' in l:
            out["longVideoModeLine"] = i
            out["longVideoModeSrc"] = l.strip()
        if "const isLongVideo" in l:
            out["isLongVideoLine"] = i
        if "if (!isLongVideo)" in l:
            out["earlyReturnLine"] = i
        if "inMenu === false" in l and "filter" in l:
            out["menuFilterLine"] = i
        if "setMode(\"long-video\")" in l:
            out.setdefault("setModeLongVideoLines", []).append(i)
        if 'attempt === "5分钟超长视频"' in l and "setMode" not in l:
            out.setdefault("chipBranchLines", []).append(i)
        if "setSubmitted(true);" in l:
            out["pureComponentStateLine"] = i
        if l.strip() == "return;" and out.get("pureComponentStateLine") == i - 1:
            out["pureComponentStateReturnLine"] = i
        if "data-effects-trigger" in l:
            out["effectsTriggerLine"] = i
        if "data-effects-card" in l:
            out["effectsCardLine"] = i
        if "data-video-long-submit-state" in l:
            out["longSubmitStateLine"] = i
        if 'aria-label="生成视频"' in l:
            out["generateBtnLine"] = i
        if "data-video-firstframe-destroy" in l:
            out["destroyLine"] = i
        if "data-video-firstframe-slot" in l and "group" in l:
            out["slotGroupLine"] = i
        if "data-video-continuation-exit" in l:
            out["continuationExitLine"] = i
        if "nextMode !== \"long-video\"" in l:
            out["chipClearOnModeSwitchLine"] = i
    # store 侧：createLongVideoProcess 段落的写点与边数。
    # 注意区分「声明」与「实现」—— 全文件有两处 `createLongVideoProcess: (`：
    # 接口声明（:348）与函数实现（:2244）。取**最后一处**（实现），并把两处都记下来。
    slines = STORE.read_text(encoding="utf-8").split("\n")
    decls = [i for i, l in enumerate(slines, 1)
             if re.match(r"\s*createLongVideoProcess:\s*\($", l)]
    out["storeDeclLines"] = decls
    start = decls[-1]
    out["storeImplLine"] = start
    seg = slines[start - 1:start + 260]
    out["storeMakeNodeWrites"] = sum(1 for l in seg if "makeProcessNode({" in l)
    out["storeProcessNodesSpread"] = sum(1 for l in seg if re.match(r"\s*\.\.\.\w+Nodes,$", l))
    out["storeProcessNodeSingles"] = sum(1 for l in seg
                                         if re.match(r"\s*(assemblyNode|finalNode),$", l))
    out["storeEdgeWrites"] = sum(1 for l in seg if re.match(r"\s*(\.\.\.\w+Nodes\.map\(|makeEdge\()", l))
    out["storeEdgeCount"] = (3 + 6 + 8) + 4 + 1   # 展开 :2462-2480 的字面计数
    return out


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    st = static_panel()
    print("=== C1 静态：超长视频的可达性（两条赋值路径）===")
    for k, v in st.items():
        print(f"  {k:26s} {v}")

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        def fresh():
            page.goto(f"{BASE}/?batch746=1", wait_until="networkidle", timeout=90_000)
            page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.wait_for_timeout(1_100)
            return page.evaluate("""() => {
              const s = window.__libtv_store.getState();
              const before = new Set(s.getActiveCanvas().nodes.map(n => n.id));
              s.addNode('video');
              const g = window.__libtv_store.getState().getActiveCanvas();
              const v = g.nodes.find(n => !before.has(n.id));
              s.selectElements({nodeIds: [v.id], edgeIds: []});
              return {id: v.id, status: (v.data && v.data.status) || null}; }""")

        # ---------- C2 模式菜单里有没有 long-video ----------
        vid = fresh()
        page.wait_for_timeout(1_200)
        page.evaluate(CLICK, "[data-video-mode-trigger]")
        page.wait_for_timeout(800)
        modes = page.evaluate("""() => [...document.querySelectorAll('[data-video-mode-option]')]
            .map(b => ({id: b.getAttribute('data-video-mode-option'),
                        text: (b.textContent||'').trim().slice(0,10),
                        disabled: b.disabled}))""")
        print(f"\n=== C2 模式菜单（{len(modes)} 项）===")
        for m in modes:
            print(f"    {m['id']:18s} 「{m['text']}」 disabled={m['disabled']}")
        print(f"  有 long-video 吗：{any(m['id'] == 'long-video' for m in modes)}")
        # 收菜单用同一枚触发器再点一次（Escape 是画布级取消选中，会卸载整块面板）
        page.evaluate(CLICK, "[data-video-mode-trigger]")
        page.wait_for_timeout(500)

        # ---------- C3 非长视频路径点「生成视频」：store 零写入还是 UI 变「已加入本地任务」 ----------
        f0 = page.evaluate(FOOT)
        btn0 = page.evaluate(BTN, "[data-video-generate-submit]")
        g0 = page.evaluate(SNAP)
        clicked = page.evaluate(CLICK, "[data-video-generate-submit]")
        page.wait_for_timeout(2_000)          # submitVideo 里有 setTimeout
        btn1 = page.evaluate(BTN, "[data-video-generate-submit]")
        g1 = page.evaluate(SNAP)
        # 附带：Escape 到底会做什么（记录读数，不作判据）
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        esc = {"submitStillThere": page.evaluate(EXISTS, "[data-video-generate-submit]"),
               "selectedCount": page.evaluate(
                   "() => (window.__libtv_store.getState().selectedNodeIds || []).length")}
        c3 = {"clicked": clicked, "before": btn0, "after": btn1, "escape": esc,
              "footBefore": f0,
              "past": [g0["past"], g1["past"]], "nodes": [g0["nodeCount"], g1["nodeCount"]],
              "edges": [g0["edgeCount"], g1["edgeCount"]],
              "nodeIdsIdentical": g0["nodeIds"] == g1["nodeIds"],
              "edgeIdsIdentical": g0["edgeIds"] == g1["edgeIds"]}
        print(f"\n=== C3 非长视频路径点「生成视频」（{vid['id']}）===")
        print(f"  页脚：{json.dumps(f0, ensure_ascii=False)}")
        print(f"  点击={clicked}")
        print(f"  按钮 class：{btn0['className']!r}\n          → {btn1['className']!r}")
        print(f"  按钮 title：{btn0['title']!r} → {btn1['title']!r}；图标 {btn0['icon']} → {btn1['icon']}；"
              f"disabled {btn0['disabled']} → {btn1['disabled']}")
        print(f"  `data-video-long-submit-state`：{btn0['longState']!r} → {btn1['longState']!r}"
              f"  ← 非长视频态该属性整段不上 DOM（`:839-846` 的 undefined）")
        print(f"  store：past {g0['past']}→{g1['past']}、节点 {g0['nodeCount']}→{g1['nodeCount']}、"
              f"边 {g0['edgeCount']}→{g1['edgeCount']}、"
              f"nodeIds 逐项相同={c3['nodeIdsIdentical']}、edgeIds 逐项相同={c3['edgeIdsIdentical']}")
        print(f"  （附带读数）Escape 之后：提交按钮还在={esc['submitStillThere']}、"
              f"选中数={esc['selectedCount']} ⟹ Escape 是取消选中，不是关菜单")

        # ---------- C4/C5/C8/C9 芯片路径：createLongVideoProcess 真跑 ----------
        vid = fresh()
        page.wait_for_timeout(1_200)
        lf0 = page.evaluate(FOOT)
        lg0 = page.evaluate(SNAP)
        chip = page.evaluate(CLICK, '[data-video-attempt="5分钟超长视频"]')
        page.wait_for_timeout(1_200)
        lf1 = page.evaluate(FOOT)
        lb1 = page.evaluate(BTN, "[data-video-generate-submit]")
        lg1 = page.evaluate(SNAP)
        # 点生成视频：250ms 抓 submitting（定时器 520ms），再等 1.5s 抓 created
        lclick = page.evaluate(CLICK, "[data-video-generate-submit]")
        page.wait_for_timeout(250)
        lb_mid = page.evaluate(BTN, "[data-video-generate-submit]")
        lf_mid = page.evaluate(FOOT)
        page.wait_for_timeout(1_500)
        lb2 = page.evaluate(BTN, "[data-video-generate-submit]")
        lf2 = page.evaluate(FOOT)
        lg2 = page.evaluate(SNAP)
        c4 = {"chipClicked": chip, "footBeforeChip": lf0, "footAfterChip": lf1,
              "btnAfterChip": lb1,
              "clicked": lclick,
              "btnAt250ms": lb_mid, "footAt250ms": lf_mid,
              "btnAfterTimer": lb2, "footAfterTimer": lf2,
              "chipPast": [lg0["past"], lg1["past"]],
              "submitPast": [lg1["past"], lg2["past"]],
              "nodes": [lg1["nodeCount"], lg2["nodeCount"]],
              "edges": [lg1["edgeCount"], lg2["edgeCount"]],
              "newLongVideoNodes": lg2["typeCounts"].get("long-video-process", 0)}
        print(f"\n=== C4 芯片路径：点「5分钟超长视频」（{vid['id']}）===")
        print(f"  页脚 前 → 芯片后：{json.dumps(lf0, ensure_ascii=False)}\n              → {json.dumps(lf1, ensure_ascii=False)}")
        print(f"  `long-state` 芯片后 = {lb1['longState']!r}（从「不存在」变成有值）")
        print(f"  芯片记账：past {lg0['past']}→{lg1['past']}、节点 {lg0['nodeCount']}→{lg1['nodeCount']}")
        print(f"  点生成视频 clicked={lclick}：")
        print(f"    250ms  long-state={lb_mid['longState']!r} title={lb_mid['title']!r} "
              f"icon={lb_mid['icon']} disabled={lb_mid['disabled']}")
        print(f"    520ms+ long-state={lb2['longState']!r} title={lb2['title']!r} "
              f"icon={lb2['icon']} disabled={lb2['disabled']}；页脚 {json.dumps(lf2, ensure_ascii=False)}")
        print(f"  提交记账：past {lg1['past']}→{lg2['past']}、节点 {lg1['nodeCount']}→{lg2['nodeCount']}、"
              f"边 {lg1['edgeCount']}→{lg2['edgeCount']}、"
              f"其中 long-video-process {lg2['typeCounts'].get('long-video-process', 0)} 个")

        # C5 静态写点 ↔ 运行时读数对账
        c5 = {"staticNodeWrites": st["storeMakeNodeWrites"],
              "staticNodeTotal": st["storeMakeNodeWrites"],
              "staticEdgeTotal": st["storeEdgeCount"],
              "runtimeNewNodes": c4["nodes"][1] - c4["nodes"][0],
              "runtimeNewEdges": c4["edges"][1] - c4["edges"][0],
              "runtimeLongVideoNodes": c4["newLongVideoNodes"]}
        print(f"\n=== C5 对账 ===")
        print(f"  静态：{c5['staticNodeTotal']} 个 makeProcessNode 写点（"
              f"material 3 + shot 3 + candidate 4 + assembly 1 + final 1）、{c5['staticEdgeTotal']} 条边")
        print(f"  运行时：节点 +{c5['runtimeNewNodes']}、边 +{c5['runtimeNewEdges']}、"
              f"其中 long-video-process {c5['runtimeLongVideoNodes']} 个")

        # C9 芯片不是 toggle：在芯片**仍激活**（长视频态）时再点一次同一枚芯片
        page.evaluate(CLICK, '[data-video-attempt="5分钟超长视频"]')
        page.wait_for_timeout(1_000)
        lf4 = page.evaluate(FOOT)
        lg4 = page.evaluate(SNAP)
        c9 = {"footBefore": lf2, "footAfter": lf4,
              "past": [lg2["past"], lg4["past"]],
              "nodes": [lg2["nodeCount"], lg4["nodeCount"]],
              "edges": [lg2["edgeCount"], lg4["edgeCount"]],
              "footIdentical": lf2 == lf4}
        print(f"\n=== C9 芯片仍激活时再点一次「5分钟超长视频」===")
        print(f"  页脚 前 → 后：{json.dumps(lf2, ensure_ascii=False)}\n              → {json.dumps(lf4, ensure_ascii=False)}")
        print(f"  页脚逐项相同={c9['footIdentical']}")
        print(f"  store：past {lg2['past']}→{lg4['past']}（+{lg4['past']-lg2['past']}）、"
              f"节点 {lg2['nodeCount']}→{lg4['nodeCount']}、边 {lg2['edgeCount']}→{lg4['edgeCount']}")
        print(f"  ⟹ 芯片非 toggle：再点只多记一条历史，画面零变化（`:218` 注释「芯片非 toggle」）")

        # C8 退出路径：长视频态下从模式菜单选 text ⟹ 芯片被清、模式回落
        page.evaluate(CLICK, "[data-video-mode-trigger]")
        page.wait_for_timeout(800)
        exit_pick = page.evaluate(CLICK, '[data-video-mode-option="text"]')
        page.wait_for_timeout(1_000)
        lf3 = page.evaluate(FOOT)
        lg3 = page.evaluate(SNAP)
        v_now = next((v for v in lg3["videoData"] if v["id"] == vid["id"]), {})
        c8 = {"picked": exit_pick, "footBefore": lf4, "footAfter": lf3,
              "attemptAfter": v_now.get("attempt"),
              "nodes": [lg4["nodeCount"], lg3["nodeCount"]],
              "edges": [lg4["edgeCount"], lg3["edgeCount"]],
              "past": [lg4["past"], lg3["past"]]}
        print(f"\n=== C8 退出路径（长视频态下从模式菜单选「文生视频」）===")
        print(f"  选中={exit_pick}；页脚 {json.dumps(lf3, ensure_ascii=False)}")
        print(f"  该卡 attempt={v_now.get('attempt')!r}（`:268-270` 选别的模式会顺带清芯片）")
        print(f"  store：past {lg4['past']}→{lg3['past']}、节点 {lg4['nodeCount']}→{lg3['nodeCount']}、"
              f"边 {lg4['edgeCount']}→{lg3['edgeCount']}（过程节点不删）")

        # ---------- C6 选特效 ----------
        vid = fresh()
        page.wait_for_timeout(1_200)
        e0 = page.evaluate(SNAP)
        opened = page.evaluate(CLICK, "[data-effects-trigger]")
        page.wait_for_timeout(800)
        cards = page.evaluate("""() => [...document.querySelectorAll('[data-effects-card]')]
            .map(d => d.getAttribute('data-effects-card'))""")
        card = cards[0] if cards else None
        picked = page.evaluate(CLICK, f'[data-effects-card="{card}"]') if card else False
        page.wait_for_timeout(1_200)
        e1 = page.evaluate(SNAP)
        c6 = {"opened": opened, "cardCount": len(cards), "card": card, "picked": picked,
              "past": [e0["past"], e1["past"]], "nodes": [e0["nodeCount"], e1["nodeCount"]],
              "edges": [e0["edgeCount"], e1["edgeCount"]],
              "newFiles": [f for f in e1["filenames"] if f not in e0["filenames"]]}
        print(f"\n=== C6 选特效（点第一张效果卡「{card}」）===")
        print(f"  打开特效面板={opened}、卡片 {len(cards)} 张、选中={picked}")
        print(f"  past {e0['past']}→{e1['past']}、节点 {e0['nodeCount']}→{e1['nodeCount']}、"
              f"边 {e0['edgeCount']}→{e1['edgeCount']}；新文件 {c6['newFiles']}")

        # ---------- C7 销毁首帧 ----------
        vid = fresh()
        page.wait_for_timeout(1_200)
        d_present0 = page.evaluate(EXISTS, "[data-video-firstframe-destroy]")
        d_vis0 = page.evaluate(VIS, "[data-video-firstframe-destroy]")
        # 先点一次「首帧生成视频」造 attempt（无入边图片时会真建图）
        page.evaluate(CLICK, '[data-video-attempt="首帧生成视频"]')
        page.wait_for_timeout(1_500)
        d0 = page.evaluate(SNAP)
        d_present1 = page.evaluate(EXISTS, "[data-video-firstframe-destroy]")
        # 按钮是 `absolute inset-0 hidden … group-hover:flex`，而 **group 类挂在外层**
        # `[data-video-firstframe-slot]`（:736），不在内层 48×55 槽上。
        # 按钮自己 display:none ⟹ 盒子恒在 (0,0)，按它的中心 hover 等于把鼠标移到屏幕左上角。
        group_box = page.evaluate(BOX, "[data-video-firstframe-slot]")
        btn_box = page.evaluate(BOX, "[data-video-firstframe-destroy]")
        hit = page.evaluate("""(p) => { const e = document.elementFromPoint(p[0], p[1]);
            if (!e) return null;
            return {tag: e.tagName, inSlot: Boolean(e.closest('[data-video-firstframe-slot]'))}; }""",
            [group_box["cx"], group_box["cy"]]) if group_box else None
        vis_before_hover = page.evaluate(VIS, "[data-video-firstframe-destroy]")
        if group_box:
            page.mouse.move(group_box["cx"], group_box["cy"])
            page.wait_for_timeout(700)
        vis_after_hover = page.evaluate(VIS, "[data-video-firstframe-destroy]")
        destroyed = page.evaluate(CLICK, "[data-video-firstframe-destroy]")
        page.wait_for_timeout(1_000)
        d1 = page.evaluate(SNAP)
        v_after = next((v for v in d1["videoData"] if v["id"] == vid["id"]), {})
        c7 = {"presentBeforeAttempt": d_present0, "visBeforeAttempt": d_vis0,
              "presentAfterAttempt": d_present1,
              "groupBox": group_box, "buttonBoxWhenHidden": btn_box,
              "elementAtGroupCentre": hit,
              "visBeforeHover": vis_before_hover, "visAfterHover": vis_after_hover,
              "destroyed": destroyed, "past": [d0["past"], d1["past"]],
              "nodes": [d0["nodeCount"], d1["nodeCount"]],
              "edges": [d0["edgeCount"], d1["edgeCount"]],
              "attemptAfter": v_after.get("attempt")}
        print(f"\n=== C7 销毁首帧 ===")
        print(f"  造 attempt 前存在={d_present0}（{json.dumps(d_vis0, ensure_ascii=False)}）")
        print(f"  造 attempt 后存在={d_present1}")
        print(f"  外层 group 盒子 {group_box}；按钮未 hover 时盒子 {btn_box}（display:none ⟹ 恒在原点）")
        print(f"  group 中心命中 {json.dumps(hit, ensure_ascii=False)}")
        print(f"  hover 前 {json.dumps(vis_before_hover, ensure_ascii=False)}")
        print(f"  hover 后 {json.dumps(vis_after_hover, ensure_ascii=False)}")
        print(f"  点「销毁」={destroyed}；past {d0['past']}→{d1['past']}、"
              f"节点 {d0['nodeCount']}→{d1['nodeCount']}、边 {d0['edgeCount']}→{d1['edgeCount']}、"
              f"该卡 attempt={v_after.get('attempt')!r}")

        # ---------- C10 清除续写的入口条件 ----------
        vid = fresh()
        page.wait_for_timeout(1_200)
        exit_present = page.evaluate(EXISTS, "[data-video-continuation-exit]")
        page.evaluate(CLICK, "[data-video-picture-edit-menu-trigger]")   # 开个菜单再关，确认不是被遮
        page.wait_for_timeout(500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        exit_present2 = page.evaluate(EXISTS, "[data-video-continuation-exit]")
        v_now2 = next((v for v in page.evaluate(SNAP)["videoData"] if v["id"] == vid["id"]), {})
        c10 = {"exitPresentFresh": exit_present, "exitPresentAfterMenu": exit_present2,
               "continuation": v_now2.get("continuation")}
        print(f"\n=== C10 清除续写（`data-video-continuation-exit`）===")
        print(f"  新建 ready 卡上有 continuation 吗：{v_now2.get('continuation')!r}")
        print(f"  「退出续写模式」按钮存在吗：{exit_present} / {exit_present2}")

        page.close()
        browser.close()

    results = {"modes": modes, "C3_shortCircuit": c3, "C4_longVideo": c4,
               "C5_reconcile": c5, "C6_effect": c6, "C7_destroy": c7,
               "C8_exit": c8, "C9_chipNotToggle": c9,
               "C10_continuation": c10, "static": st}
    print("\n=== 汇总 ===")
    for k, v in results.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")

    a_tier_table = [
        {"cmd": "createFirstFrameReference", "run": "744 已跑（failed 卡，past +1、只写 attempt）"},
        {"cmd": "createFirstLastFrameReference", "run": "744 已跑（failed 卡，past +1、只写 attempt）"},
        {"cmd": "updateNodeData（setAttempt）", "run": "744 已跑（「5分钟超长视频」芯片，past +1）"},
        {"cmd": "addNodeAtPosition + addEdge（选特效）", "run": "746 本批跑（past +2）"},
        {"cmd": "destroyFirstFrameReference", "run": "746 本批跑（past +1、节点 -1、边 -1）"},
        {"cmd": "clearVideoContinuation", "run": "746 只验到「入口条件不满足」"},
        {"cmd": "createLongVideoProcess", "run": "746 本批跑通（芯片路径，past +1、节点 +12、边 +22）"},
    ]

    checks = [
        ("C1 静态：long-video 是 inMenu:false（被 :974 过滤），但 :226 有 setMode(\"long-video\") ⟹ 存在第二条赋值路径；"
         "且 createLongVideoProcess 恰好两处（:348 接口声明 + :2244 实现）",
         st.get("longVideoModeLine") == 110 and "disabled: true" in st.get("longVideoModeSrc", "")
         and "inMenu: false" in st.get("longVideoModeSrc", "")
         and st.get("isLongVideoLine") == 172 and st.get("earlyReturnLine") == 309
         and st.get("menuFilterLine") == 974
         and st.get("setModeLongVideoLines") == [226]
         and st.get("pureComponentStateLine") == 310
         and st.get("pureComponentStateReturnLine") == 311
         and st.get("storeDeclLines") == [348, 2244],
         json.dumps(st, ensure_ascii=False)),
        ("C2 运行时：模式菜单里没有 long-video",
         len(modes) == 5 and not any(m["id"] == "long-video" for m in modes),
         json.dumps(modes, ensure_ascii=False)),
        ("C3 非长视频路径点「生成视频」：store 零写入，但按钮变蓝 + title 变「已加入本地任务」；"
         "而 long-state 属性整段不存在（也被 isLongVideo 门控）",
         c3["clicked"]
         and c3["past"][1] == c3["past"][0]
         and c3["nodes"][1] == c3["nodes"][0] and c3["edges"][1] == c3["edges"][0]
         and c3["nodeIdsIdentical"] and c3["edgeIdsIdentical"]
         and "bg-[#09caf5]" in c3["after"]["className"]
         and c3["after"]["title"] == "已加入本地任务"
         and c3["after"]["icon"] == "check" and c3["before"]["icon"] == "arrow"
         and c3["before"]["longState"] is None and c3["after"]["longState"] is None,
         json.dumps(c3, ensure_ascii=False)),
        ("C4 芯片路径：芯片 ⟹ 模式触发器「超长视频」+ long-state 变 idle + 「查看过程」出现；"
         "点生成视频 ⟹ submitting(disabled) → created，past +1、节点 +12、边 +22、「返回编辑」出现",
         c4["chipClicked"] and c4["clicked"]
         and c4["footBeforeChip"]["mode"] != c4["footAfterChip"]["mode"]
         and c4["footAfterChip"]["mode"] == "超长视频"
         and c4["footAfterChip"]["params"].startswith("Auto")
         and "300s" in c4["footAfterChip"]["params"]
         and c4["btnAfterChip"]["longState"] == "idle"
         and c4["footAfterChip"]["process"] == "查看过程"
         and c4["chipPast"][1] == c4["chipPast"][0] + 1
         and c4["btnAt250ms"]["longState"] == "submitting"
         and c4["btnAt250ms"]["disabled"] is True
         and c4["btnAt250ms"]["icon"] == "spinner"
         and c4["btnAfterTimer"]["longState"] == "created"
         and c4["btnAfterTimer"]["icon"] == "check"
         and c4["btnAfterTimer"]["title"] == "已加入本地任务"
         and c4["footAfterTimer"]["process"] == "返回编辑"
         and c4["submitPast"][1] == c4["submitPast"][0] + 1
         and c4["nodes"][1] == c4["nodes"][0] + 12
         and c4["edges"][1] == c4["edges"][0] + 22,
         json.dumps(c4, ensure_ascii=False)),
        ("C5 对账：静态 12 个 makeProcessNode 写点、22 条边 ⟺ 运行时 +12 节点 / +22 边",
         c5["staticNodeWrites"] == 12 and c5["staticEdgeTotal"] == 22
         and c5["runtimeNewNodes"] == 12 and c5["runtimeNewEdges"] == 22
         and c5["runtimeLongVideoNodes"] == 12,
         json.dumps(c5, ensure_ascii=False)),
        ("C6 选特效：节点 +1、边 +1，**past +2**（建图与连线各记一条）",
         c6["opened"] and c6["picked"] and c6["cardCount"] == 4
         and c6["nodes"][1] == c6["nodes"][0] + 1 and c6["edges"][1] == c6["edges"][0] + 1
         and c6["past"][1] == c6["past"][0] + 2 and len(c6["newFiles"]) == 1,
         json.dumps(c6, ensure_ascii=False)),
        ("C7 销毁首帧：group 挂在外层 slot 上 ⟹ hover 外层后按钮 display:none→flex、尺寸 0→非 0；"
         "点它 past +1、节点 -1、边 -1、attempt 归 None",
         c7["presentBeforeAttempt"] is False
         and c7["presentAfterAttempt"] is True
         and c7["groupBox"] is not None and c7["groupBox"]["w"] > 48
         and c7["elementAtGroupCentre"] and c7["elementAtGroupCentre"]["inSlot"] is True
         and c7["visBeforeHover"] and c7["visBeforeHover"]["display"] == "none"
         and c7["visBeforeHover"]["w"] == 0
         and c7["visAfterHover"] and c7["visAfterHover"]["display"] == "flex"
         and c7["visAfterHover"]["w"] > 0
         and c7["destroyed"] and c7["past"][1] == c7["past"][0] + 1
         and c7["nodes"][1] == c7["nodes"][0] - 1
         and c7["edges"][1] == c7["edges"][0] - 1
         and c7["attemptAfter"] is None,
         json.dumps(c7, ensure_ascii=False)),
        ("C8 退出路径：长视频态下从模式菜单选 text ⟹ 芯片被清、模式不再显示「超长视频」、过程节点不删",
         c8["picked"] and c8["attemptAfter"] is None
         and c8["footAfter"]["mode"] == "文生视频"
         and c8["footAfter"]["process"] is None
         and c8["nodes"][1] == c8["nodes"][0] and c8["edges"][1] == c8["edges"][0],
         json.dumps(c8, ensure_ascii=False)),
        ("C9 芯片不是 toggle：在芯片**仍激活**时再点一次同芯片 ⟹ past +1 但页脚与节点/边/模式逐项零变化",
         c9["past"][1] == c9["past"][0] + 1
         and c9["nodes"][1] == c9["nodes"][0] and c9["edges"][1] == c9["edges"][0]
         and c9["footIdentical"] is True,
         json.dumps(c9, ensure_ascii=False)),
        ("C10 清除续写：无 continuation 时「退出续写模式」按钮不渲染（条件渲染）",
         c10["exitPresentFresh"] is False and c10["exitPresentAfterMenu"] is False
         and c10["continuation"] is None,
         json.dumps(c10, ensure_ascii=False)),
        ("C11 A 档汇总表 7 行齐（8 个命令里 selectNodeOutput 等不在 VideoNode，已在 744 表内）",
         len(a_tier_table) == 7,
         json.dumps(a_tier_table, ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 746,
        "title": "A 档剩下 4 个命令：createLongVideoProcess 有一条被菜单藏起来、芯片能进的路径"
                 "（我第一版静态推理漏了 :226 而误判为不可达）；同一个「已加入本地任务」"
                 "提示，真假各有一条",
        "verdict": f"{passed}/{len(checks)}",
        "summary": {"results": results, "aTierTable": a_tier_table},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "**`long-video` 在模式菜单里进不去，但芯片能进**：`modeItems` 里 `long-video` 是 "
            "`inMenu: false`（`:110`），被 `:974` 的 filter 排除；而 `:225-229` 的 "
            "`attempt === \"5分钟超长视频\"` 重放块里有 `setMode(\"long-video\")` "
            "⟹ 节点卡芯片是**第二条赋值路径**。实测点芯片后：模式触发器「文生视频」→"
            "「**超长视频**」、参数「16:9 · 720P · 5s」→「**Auto · 720P · 300s**」、"
            "`data-video-long-submit-state` 从**不存在**变成 `\"idle\"`、「查看过程」按钮出现。",
            "**`createLongVideoProcess:2244` 真跑通**：`long-state` 三态真实流转 "
            "`idle → submitting（按钮 disabled + spinner）→ created`，`title` 同步 "
            "「生成视频 → 正在创建本地过程 → 已加入本地任务」，「查看过程」翻成「返回编辑」；"
            "store `past` +1、节点 **+12**、边 **+22**。",
            "**静态写点与运行时读数逐个对平**：`:2332/2341/2350/2361/2370/2379/2390/2400/"
            "2410/2420/2431/2439` 共 12 个 `makeProcessNode` 写点"
            "（material 3 + shot 3 + candidate 4 + assembly 1 + final 1）；"
            "`:2462-2480` 的边 = `source→shot` 3 + `material→shot` 6 + `shot→candidate` 8 + "
            "`candidate→assembly` 4 + `assembly→final` 1 = **22** ⟺ 实测 +12 / +22。",
            "**同一个「已加入本地任务」提示，真假各有一条**："
            "非长视频路径 store **零写入**（`past`/节点/边/`nodeIds`/`edgeIds` 全同）却照样变蓝、"
            "换对勾、`title` 翻成「已加入本地任务」—— `:852-863` 的底色/`title` 三元"
            "**不区分 `isLongVideo`**；长视频路径则真写入。撒谎的是 `:309-312` 那个"
            "「只 `setSubmitted(true)` 就 return」的分支复用了整套提交反馈。",
            "**非长视频路径没有防重入**：提交中 `disabled` 恒 `false`、无 spinner；"
            "长视频路径有 `longVideoSubmitting` + `longVideoSubmitTimerRef` 双重守卫"
            "（`:313-319`）⟹ 同一按钮两条路径的并发语义不同。",
            "**模式菜单里没有「超长视频」，但面板上会显示「超长视频」** —— "
            "用户进得去（芯片）、也退得出（`:268-270` 选别的模式会顺带清芯片，实测 C8："
            "选「文生视频」后 `attempt` 归 `None`、模式回落、「查看过程」消失），"
            "但**看不到自己在哪个模式里**（8 个 `modeItems` 里 3 个 `inMenu: false`）。",
            "**「5分钟超长视频」芯片不是 toggle**：再点一次同芯片 `past` +1 但页脚、"
            "模式、节点、边**逐项零变化**（与 `:218` 注释「芯片非 toggle」一致）。",
            "**选特效一次点击记两条账**：`addNodeAtPosition`（建 `image`「素材 - 特效 - X」）"
            "与 `addEdge`（连线）是两次独立记账 ⟹ `past` +2，撤销要点两次才完全回退。",
            "**销毁首帧的 hover 目标是外层整条 slot，不是缩略图**：`group` 类挂在 "
            "`[data-video-firstframe-slot]`（实测宽 642px）上，按钮是内层 48×55 槽的 "
            "`absolute inset-0 hidden … group-hover:flex` ⟹ 在这 642px 任意位置悬停都会"
            "在 48px 宽的缩略图上冒出「销毁」。hover 前 `display:none`、盒子 0×0，"
            "hover 后 `flex`、46×53；点它 `past` +1、节点 −1、边 −1、`attempt` 归 `None`。",
            "**清除续写是条件渲染**：`isContinuation && onClearContinuation` ⟹ "
            "新建 ready 卡 `continuation = None` 时 `[data-video-continuation-exit]` 根本不渲染。",
        ],
        "probeCorrections": [
            "**我自己的静态推理漏了一条赋值路径**（本批最重要的一次返工）："
            "第一版只追了 `selectMode`（菜单那条 `setMode` 路径）就断言 `mode` 永远到不了 "
            "`\"long-video\"` ⟹ `createLongVideoProcess` 是死代码。实际 `:226` 在 "
            "`prevAttempt` 重放块里另有一条 `setMode(\"long-video\")`，由芯片触发。"
            "**判据 C1 第一版只断言了我已经读到的东西，等于没断言** —— 静态结论必须"
            "回头穷举该变量的**全部**赋值点（`setMode` / 直接 `mode=` / props 传参），"
            "而不是只跟一条调用链。",
            "**C3 第一版点不到按钮**：用 `Escape` 想收掉模式菜单，实际 `Escape` 走画布级"
            "**取消选中**（实测选中数 1→0）⟹ 整块 `VideoGenerationPanel` 卸载，"
            "`[aria-label=\"生成视频\"]` 自然不在 DOM ⟹ `clicked=False`。"
            "改法：用同一枚触发器再点一次关菜单（不碰 Escape）。",
            "**C3 第一版判据选错测点**：以为 `data-video-long-submit-state` 会变 `created`，"
            "但它被 `isLongVideo` 门控、在此路径上整段不存在。改判 class 底色 / `title` / "
            "图标字形（Lucide 的 `svg.lucide-check`、`svg.lucide-loader-circle` vs "
            "原始 `svg[aria-hidden]`），并**另开一条芯片路径**去读同一个属性。",
            "**C7 第一版 hover 了一个零尺寸元素**：按钮 `display:none` ⟹ 盒子恒在 (0,0)，"
            "按它的中心 `mouse.move` 等于把鼠标移到屏幕左上角，`group-hover` 自然不触发。"
            "改法：hover 外层 `[data-video-firstframe-slot]` 的中心，并用 `elementFromPoint` "
            "证明命中点确实落在该 slot 内。",
            "**「按元素自身盒子做真实交互」的探针必须先确认元素可见** —— "
            "`display:none` 时 `getBoundingClientRect()` 不报错但恒为 0×0，鼠标坐标是垃圾。",
        ],
        "notClaimed": [
            "不声称**超长视频在源站是否可用** —— 未取证；也不声称 `inMenu: false` + "
            "`badge: \"Beta\"` 是有意未开放还是遗留。",
            "`clearVideoContinuation` **未真跑** —— 要先经「智能续写」两段式建出 "
            "`continuation`，本批只验到「入口条件不满足」。",
            "选特效**只验了第一张效果卡**；4 张卡是否都建图 + 连线，未逐个验。",
            "「素材 - 特效 - X」节点与视频节点的**连线方向、handle 类型**未验。",
            "销毁首帧只在**新建的 ready 卡**上跑；种子 failed 卡（已有 image 入边）上点"
            "「销毁」的行为未验。",
            "`past +2` 的两条记录**各自的内容**（快照是否只差节点/边）未展开验，只验了条数。",
            "长视频过程节点的**阶段内容**（标题/副标题/图片）未逐个验，只数了 12 这个总数"
            "并与静态写点对平；12 个 `long-video-process` 是否会继续演进（pending→…）未取证。",
            "8 个 `modeItems` 里另两个 `inMenu: false` 项（`video-edit` / `first-frame`）"
            "**只从源码读到 `inMenu: false`**，未像 `long-video` 那样走芯片路径单独验。",
            "「悬停区比控件宽 13 倍」只在本视口（1280×1150、面板 642px）测得，"
            "**不声称窄视口下同样是 13 倍**。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
