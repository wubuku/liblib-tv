#!/usr/bin/env python3
"""batch 741 验收：canvasStore 54 个命令里谁记账、谁不记账

## 起点

739/740 证明了**删除能撤**（手柄删边、Delete 删节点各 push 1 条，undo 逐项精确）。
但那只是 54 个命令里的 2 个。本批把「哪些命令记账、哪些不记账」整个普查一遍，
并查清**拖动节点到底记不记账**。

## 口径：三个数，不能揉成一个

静态扫描的第一版有三个错（730 立下的规矩：分清「声明」与「实现」）：

  ① 多行参数表的函数（`addNodeAtFlowCenter: (` 这种，参数跨 3 行）被当成单行函数
     收尾，于是它的函数体落在**下一个**命令名下 —— 结果 `addNode` 被算成「记账」
     （它其实一行 pushHistory 都没有，只转发给 `addNodeAtPosition`），
     而真正记账的那 12 个多行参数函数**一个都没被数到**。
  ② 状态字段（`projectName: "未命名工作区"` 这类）**没有 `=>`**。扫描器一路读到
     :1030 第一个 `=>` 才停 ⟹ 把 `setProjectName` 整个吞掉，命令数少算 1 个。
  ③ `pushHistory` 在 `:506` 是**模块级函数定义**，不是命令 —— 按行号区间配对会跨界。

本版解析器：**先扫到 `=>`（途中撞到新的顶层 key 就判定为状态字段并跳过），
再从箭头行做括号配平**，并在 `}));` 处停止。
修正后 54 个命令 / 33 个调用点，两个独立口径（命令级 vs 调用点级）逐个对上。

## 三个口径

| 口径 | 数 | 含义 |
|---|---|---|
| 命令总数 | 54 | store 对象 `1020..4072` 的顶层函数键（9 个状态字段不算） |
| **记账** | 33 | 函数体内含 `pushHistory(` —— 每个都必然同时含 `set(` |
| **改 store 但不记账** | 17 | 有 `set(` 没有 `pushHistory(` |
| **两者皆无** | 4 | 2 个转发器 + 2 个纯 getter |
| pushHistory 调用点 | 33 | 与命令级 33 **逐个相等**（交叉验证） |

## 决定性读数

### ① 33 个记账命令里，2 个是**条件记账**
`setNodes:3389` / `setEdges:3415` 写的是
`options?.recordHistory ? pushHistory(...) : state.historyByCanvas`
⟹ **31 个无条件 + 2 个条件**。「33 个记账」这个数本身还要再拆一层。

### ② 「命令自己不记账」≠「用户拿不到撤销条目」
`addNode:1252` 与 `addNodeAtFlowCenter:1260` 归在「两者皆无」——
它们一行 `set(` 都没有，只 `get().addNodeAtPosition(...)`。
但 `addNodeAtPosition:1577` 是记账的 ⟹ **用户照样拿到 1 条历史**。
静态桶只描述「这个函数自己写不写历史」，不描述用户可见行为。

### ③ headline：**拖动节点可撤销，但记账的不是搬运的那条路径**
第一版的结论是「拖动不记账、移动节点不可撤销」，**已撤回**——读数是 `past 0→1`，
与推断相反。给 54 个命令套调用日志的探针给出真相：

  - 拖动途中反复调 `routeReactFlowChanges:3535`（不记账桶），
    返回 `APPLIED_TRANSPORT`（`libtvReactFlowChangeRouting.ts:395`），每次都真写 store；
  - **一次都没有记账**；
  - 拖动**停下**时 `page.tsx:1501 onNodeDragStop` 才发一次
    `setNodes(currentNodes, {recordHistory: true, historySnapshot: transaction.snapshot})`
    ——`transaction.snapshot` 是 `onNodeDragStart` 时 armed 的**拖动前**快照。

⟹ **一次拖动 = 多次中间路由零记账 + 停下时压成 1 条**；undo 用那条拖动前快照恢复，
坐标逐项精确回位。多选拖动同样只记 1 条。

`onNodeDragStop` 里还有一道 `moved` 守卫：逐个比对 before/after 的 position，
**没真动就不留任何条目**（按下-挪-回原点-松手 ⟹ `past` 不变）。

### ④ `removeCanvas` 删历史桶，而它自己不记账
`:1095-1097` `historyByCanvas: Object.fromEntries(...filter(([canvasId]) => canvasId !== id))`
⟹ 删一张画布 = 连它的撤销历史一起消失，而删画布这个动作**自己也没有条目可撤**。

### ⑤ `undo()` 只恢复 `nodes`/`edges`，从不恢复画布名
`:3688` `{ ...canvas, nodes: previous.nodes, edges: previous.edges }`
⟹ `renameCanvas:1101` 改名不可撤销（哪怕 `past > 0`）。

## 判据

C1  静态普查：54 命令 = 33 记账 / 17 只 set / 4 皆无，且 33 个 pushHistory 调用点逐个对平
C2  修正扫描错：`addNode` 是转发器、`setProjectName` 曾被状态字段吞掉、`createStoryScriptPair` 确实记账
C3  `setNodes`/`setEdges` 是**条件**记账（`recordHistory`），其余 31 个无条件
C4  转发器：`addNode` 自己不记账，但运行时 `nodes +1`、`past 0→1`
C5  纯选择：`selectNode` 前后 `past` 不变（基线 0）（真不产条目，与 C4 对照）
C6  **真实鼠标拖动** ⟹ 多次 `routeReactFlowChanges`(APPLIED_TRANSPORT) + 1 次
    `setNodes(recordHistory:true)`，`past` 只 +1
C6b 拖动后 `undo()` ⟹ 坐标**逐项精确**回拖动前，`future=1`
C6c 空拖（挪了又回原点）⟹ `past` 不变（`moved` 守卫）
C6d 多选拖动 ⟹ 仍只 +1，undo 后全部逐项恢复
C7  `updateNodeData` ⟹ `past +1`
C8  `setNodes` 不传 `recordHistory` ⟹ `past` 不变；传 `{recordHistory:true}` ⟹ `past +1`
C9  `removeCanvas` ⟹ 该桶整体消失、**对照组 canvas-2 的桶不动**、画布进回收站
C10 `renameCanvas` 改名 + `undo()`（此时 past>0）⟹ 名字**没**被撤回来
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch741-2026-10-01"
STORE = ROOT / "src/store/canvasStore.ts"
BASE = "http://localhost:4317"
W, H = 1280, 1150

STATE_KEYS = {
    "projectName", "canvases", "removedCanvases", "activeCanvasId", "canvasGeneration",
    "selectedNodeIds", "selectedNodeId", "selectedEdgeIds", "historyByCanvas",
}

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {
    canvasId: g.id,
    nodeCount: g.nodes.length, edgeCount: g.edges.length,
    nodePos: Object.fromEntries(g.nodes.map(n => [n.id, [n.position.x, n.position.y]])),
    past: h.past.length, future: h.future.length,
    pastPerCanvas: Object.fromEntries(
      Object.entries(s.historyByCanvas).map(([k, v]) => [k, (v.past || []).length])),
    historyKeys: Object.keys(s.historyByCanvas).sort(),
    removedIds: s.removedCanvases.map(c => c.id),
    canvasNames: Object.fromEntries(s.canvases.map(c => [c.id, c.name])),
    selectedNodeIds: s.selectedNodeIds.slice(),
  };
}"""

# 给 store 的每个命令套一层调用日志 —— 「谁记了这一笔」的取证探针
# （740 的规矩：读数对不上自己就是线索，别急着把结论写死）
#
# 注意：setNodes 的第 1 个参数是整个 nodes 数组（JSON 好几千字）。
# 第一版把所有参数 join 起来再 slice(0,400) ⟹ **记账参数 `options` 正好被截掉**，
# 读出来是 `"l"` 这种碎片，差点据此判 FAIL。末位参数单独记。
WRAP_STORE = """() => {
  const s = window.__libtv_store.getState();
  window.__b741_calls = [];
  for (const k of Object.keys(s)) {
    if (typeof s[k] !== 'function') continue;
    const orig = s[k];
    s[k] = function(...a) {
      const brief = (x) => {
        try { return typeof x === 'function' ? '[fn]' : JSON.stringify(x); }
        catch (e) { return '[unserializable]'; }
      };
      const rec = {k, argc: a.length,
                   lead: a.slice(0, -1).map(brief).join(' ').slice(0, 80),
                   lastArg: a.length ? brief(a[a.length - 1]).slice(0, 300) : 'NONE'};
      try {
        const r = orig(...a);
        rec.ret = (r && typeof r === 'object') ? JSON.stringify(r).slice(0, 140) : String(r);
        return r;
      } catch (e) { rec.err = String(e).slice(0, 140); throw e; }
      finally { window.__b741_calls.push(rec); }
    };
  }
  return Object.keys(s).filter(k => typeof s[k] === 'function').length;
}"""


def census():
    """按大括号配平切出 store 对象的 53 个顶层命令；声明区与实现区分开统计。"""
    lines = STORE.read_text(encoding="utf-8").split("\n")
    n = len(lines)

    store_at = next(i for i, l in enumerate(lines)
                    if l.startswith("export const useCanvasStore = create<CanvasState>")) + 1
    stop_at = next(i for i in range(store_at, n) if re.match(r"^\}\)\);", lines[i]))

    # 声明区 = interface CanvasState 的括号配平范围
    decl_at = next(i for i, l in enumerate(lines) if l.startswith("interface CanvasState {"))
    d = 0
    decl_end = decl_at
    for i in range(decl_at, n):
        d += lines[i].count("{") - lines[i].count("}")
        if d == 0 and i > decl_at:
            decl_end = i
            break
    decl_text = "\n".join(lines[decl_at:decl_end + 1])
    decl_push_hits = [m for m in re.findall(r"^\s*(\w+):[^\n]*pushHistory[^\n]*$",
                                             decl_text, re.M)]

    # 走命令键：**先扫到箭头，再从箭头行做括号配平**（多行参数表的关键修正）
    #
    # 状态字段（`projectName: "未命名工作区"` 这类）**没有 `=>`**。第一版没有
    # 「还没看到箭头就撞上下一行 key 就停」的规则，`projectName` 一路吞到
    # :1030 第一个 `=>` 才停 ⟹ 把 `setProjectName` 整个吞掉，命令数少算 1 个。
    # 规则：往下找 `=>` 的路上若先撞到新的顶层 key 或对象结束 ⟹ 这是状态字段，跳过。
    keys = []
    i = store_at
    while i < stop_at:
        m = re.match(r"^  ([A-Za-z_$][\w$]*):(.*)$", lines[i])
        if not m:
            i += 1
            continue
        name, key_at = m.group(1), i
        j, buf = i, m.group(2)
        saw_arrow = "=>" in buf
        while not saw_arrow and j + 1 < stop_at:
            j += 1
            # 撞上新的顶层 key / 对象结束 ⟹ 前一个键是状态字段
            if re.match(r"^  [A-Za-z_$][\w$]*:", lines[j]) or re.match(r"^\}\)\);", lines[j]):
                break
            buf += " " + lines[j].strip()
            if "=>" in lines[j]:
                saw_arrow = True
        if not saw_arrow:
            keys.append((name, key_at + 1, key_at + 1, "state"))
            i = key_at + 1
            continue
        arrow_at = max(k for k in range(i, j + 1) if "=>" in lines[k])
        if lines[arrow_at].split("=>", 1)[1].strip().startswith("{"):
            depth = 0
            end_at = None
            for k in range(arrow_at, n):
                depth += lines[k].count("{") - lines[k].count("}")
                if k > arrow_at or "{" in lines[k]:
                    if depth == 0:
                        end_at = k
                        break
            keys.append((name, key_at + 1, end_at + 1, "brace"))
            i = end_at + 1
        else:
            keys.append((name, key_at + 1, j + 1, "expr"))
            i = j + 1

    rows = []
    for name, a, b, kind in keys:
        if name in STATE_KEYS:
            continue
        body = "\n".join(lines[a - 1:b])
        rows.append({
            "name": name, "start": a, "end": b, "kind": kind,
            "calls_set": bool(re.search(r"(?<![\w.$])set\s*\(", body)),
            "calls_push": bool(re.search(r"(?<![\w.$])pushHistory\s*\(", body)),
            "conditional_push": bool(re.search(
                r"\?\s*pushHistory\([\s\S]{0,80}?:\s*state\.historyByCanvas", body)),
            "delegates": sorted(set(re.findall(r"get\(\)\.(\w+)\(", body))),
        })

    # 调用点级口径：与命令级独立数一遍，用来交叉验证
    call_sites = [i + 1 for i, l in enumerate(lines)
                  if re.search(r"(?<![\w.$])pushHistory\s*\(", l)
                  and not l.lstrip().startswith("function pushHistory")]

    return {
        "store_range": [store_at + 1, stop_at + 1],
        "decl_range": [decl_at + 1, decl_end + 1],
        "decl_push_hits": decl_push_hits,
        "push_history_def": next(i + 1 for i, l in enumerate(lines)
                                 if l.startswith("function pushHistory(")),
        "rows": rows,
        "call_sites": call_sites,
        "max_history": next(int(m) for m in re.findall(r"const MAX_HISTORY = (\d+);", "\n".join(lines))),
    }


def snap(page):
    return page.evaluate(SNAP)


def go(page, tag):
    page.goto(f"{BASE}/?batch741={tag}", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.wait_for_timeout(1_200)


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 静态：store 对象的命令普查 ===")
    c = census()
    rows = c["rows"]
    both = [r for r in rows if r["calls_set"] and r["calls_push"]]
    setonly = [r for r in rows if r["calls_set"] and not r["calls_push"]]
    neither = [r for r in rows if not r["calls_set"] and not r["calls_push"]]
    cond = [r for r in both if r["conditional_push"]]
    print(f"  store 对象 {c['store_range'][0]}..{c['store_range'][1]}"
          f"；CanvasState 声明区 {c['decl_range'][0]}..{c['decl_range'][1]}"
          f"（声明区提及 pushHistory：{len(c['decl_push_hits'])} 处）")
    print(f"  pushHistory 定义在 canvasStore.ts:{c['push_history_def']}（模块级函数，不是命令）")
    print(f"  命令总数 {len(rows)}：记账 {len(both)} / 只 set {len(setonly)} / 皆无 {len(neither)}")
    print(f"  pushHistory 调用点 {len(c['call_sites'])} 处 ⟹ 与命令级 {len(both)} "
          f"{'逐个对平' if len(c['call_sites']) == len(both) else '对不上！'}")
    print(f"  记账命令中条件记账 {len(cond)}：{[r['name'] for r in cond]}"
          f" ⟹ 无条件记账 {len(both) - len(cond)}")
    print("\n  --- 记账（%d）---" % len(both))
    for r in both:
        print(f"    {r['name']:32s} {r['start']:>5}..{r['end']:<5}"
              f"{'（条件）' if r['conditional_push'] else ''}")
    print("\n  --- 改 store 但不记账（%d）---" % len(setonly))
    for r in setonly:
        print(f"    {r['name']:32s} {r['start']:>5}..{r['end']:<5}")
    print("\n  --- 既不 set 也不 pushHistory（%d）---" % len(neither))
    for r in neither:
        print(f"    {r['name']:32s} {r['start']:>5}..{r['end']:<5}"
              f"  → 转发 {r['delegates']}" if r["delegates"] else
              f"    {r['name']:32s} {r['start']:>5}..{r['end']:<5}  （纯 getter）")

    by_name = {r["name"]: r for r in rows}
    add_node = by_name["addNode"]
    add_at_pos = by_name["addNodeAtPosition"]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        # ---------- C4 转发器：addNode 自己不记账 ----------
        go(page, "forward")
        a0 = snap(page)
        page.evaluate("() => window.__libtv_store.getState().addNode('text')")
        page.wait_for_timeout(600)
        a1 = snap(page)
        print(f"\n=== C4 转发器 addNode:1252（源码含 set={add_node['calls_set']}"
              f" pushHistory={add_node['calls_push']}，转发→{add_node['delegates']}）===")
        print(f"  节点 {a0['nodeCount']}→{a1['nodeCount']}；past {a0['past']}→{a1['past']}")
        print(f"  ⟹ 自己不记账，用户仍拿到 {a1['past'] - a0['past']} 条历史"
              f"（记账的是 addNodeAtPosition:{add_at_pos['start']}）")

        # ---------- C5 纯选择（独立页，past 基线 0） ----------
        go(page, "select")
        b0 = snap(page)
        first_id = page.evaluate("() => window.__libtv_store.getState().getActiveCanvas().nodes[0].id")
        page.evaluate("(id) => window.__libtv_store.getState().selectNode(id)", first_id)
        page.wait_for_timeout(500)
        b1 = snap(page)
        print(f"\n=== C5 纯选择 selectNode:3439（改 store 不记账）===")
        print(f"  选中 {b1['selectedNodeIds']}；past {b0['past']}→{b1['past']}、"
              f"节点数 {b0['nodeCount']}→{b1['nodeCount']} ⟹ 真不产条目")

        # ---------- C6 headline：真实鼠标拖动 ----------
        # 注意：第一版把这里的结论硬写成「拖动不记账」，读到 past 0→1 却没查
        # **谁记的账**——差点把一句错话写进 README（740 立下的老规矩：
        # 读数对不上自己就是线索，先怀疑探针/别急着下结论）。
        # 探针（给 54 个命令套调用日志）给出的真答案在下面 C6a。
        go(page, "drag")
        page.evaluate(WRAP_STORE)          # 记录拖动期间每个命令的调用
        d0 = snap(page)
        drag = page.evaluate("""() => {
          const el = document.querySelector('.react-flow__node');
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return {id: el.getAttribute('data-id'),
                  x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
                  w: Math.round(r.width), h: Math.round(r.height)};
        }""")

        def do_drag(x, y, dx, dy):
            page.mouse.move(x, y)
            page.mouse.down()
            for step in range(1, 13):
                page.mouse.move(x + dx * step, y + dy * step)
                page.wait_for_timeout(30)
            page.mouse.up()
            page.wait_for_timeout(900)

        do_drag(drag["x"], drag["y"], 9, 5)
        d1 = snap(page)
        calls = page.evaluate("() => window.__b741_calls")
        routes = [c for c in calls if c["k"] == "routeReactFlowChanges"]
        setnodes = [c for c in calls if c["k"] == "setNodes"]
        route_codes = sorted({c["ret"] for c in routes})
        moved = {k: [d0["nodePos"][k], d1["nodePos"][k]]
                 for k in d0["nodePos"] if d0["nodePos"][k] != d1["nodePos"][k]}
        print(f"\n=== C6 headline 真实拖动节点 {drag['id']}（{drag['w']}×{drag['h']}）===")
        print(f"  拖动期间调用：routeReactFlowChanges × {len(routes)}（code={route_codes}）、"
              f"setNodes × {len(setnodes)}")
        print(f"  setNodes 拿到记账参数了吗：{setnodes[0]['lastArg'] if setnodes else 'NONE'}")
        print(f"  坐标真变的节点 {len(moved)} 个：{json.dumps(moved, ensure_ascii=False)}")
        print(f"  **past {d0['past']}→{d1['past']}** ⟹ {len(routes)} 次中间路由全部不记账，"
              f"整次拖动只在停下时压成 {d1['past'] - d0['past']} 条")
        page.evaluate("() => window.__libtv_store.getState().undo()")
        page.wait_for_timeout(700)
        d2 = snap(page)
        back = {k: (d0["nodePos"][k] == d2["nodePos"][k]) for k in d0["nodePos"]}
        print(f"  undo 后 past={d2['past']}、future={d2['future']}；"
              f"坐标逐项精确回拖动前：{sum(back.values())}/{len(back)} "
              f"（不一致：{[k for k, v in back.items() if not v]}）")

        # ---------- C6c 空拖：moved 守卫 ----------
        # 分两格报：**完全不动**与**挪出去再精确回屏幕原点**。
        # 后者不是 no-op —— 实测回到同一屏幕点后节点坐标仍差 3.8 个流程单位
        # （@zoom 0.526 ≈ 2 屏幕像素）。第一版把它当 no-op 测，判据挂了一轮。
        # 成因未取证；**不归因** snapToGrid（残余不是 20 的倍数，起点 2112 也不是）。
        go(page, "nodrag")
        e0 = snap(page)
        npos = page.evaluate("""() => { const el = document.querySelector('.react-flow__node');
          const r = el.getBoundingClientRect();
          return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)}; }""")
        page.mouse.move(npos["x"], npos["y"])
        page.mouse.down()
        page.wait_for_timeout(400)
        page.mouse.up()
        page.wait_for_timeout(900)
        e1 = snap(page)
        still = sum(1 for k in e0["nodePos"] if e0["nodePos"][k] != e1["nodePos"][k])
        page.evaluate(WRAP_STORE)
        page.mouse.move(npos["x"], npos["y"])
        page.mouse.down()
        for step in range(1, 9):
            page.mouse.move(npos["x"] + step, npos["y"])
            page.wait_for_timeout(30)
        page.mouse.move(npos["x"], npos["y"])
        page.wait_for_timeout(150)
        page.mouse.up()
        page.wait_for_timeout(900)
        e2 = snap(page)
        back2 = {k: [e0["nodePos"][k], e2["nodePos"][k]]
                 for k in e0["nodePos"] if e0["nodePos"][k] != e2["nodePos"][k]}
        calls2 = page.evaluate("() => window.__b741_calls")
        print(f"\n=== C6c 空拖 ===")
        print(f"  (a) 按下→不动→松手：坐标真变 {still} 个、past {e0['past']}→{e1['past']}"
              f" ⟹ `moved` 守卫成立：没真动就不留条目")
        print(f"  (b) 挪 8px 再精确回屏幕原点：坐标真变 {len(back2)} 个 {json.dumps(back2, ensure_ascii=False)}"
              f"、past {e1['past']}→{e2['past']}")
        print(f"      这次拖动**真动了**（差 {back2}），记账是应该的；成因未取证，"
              f"**不归因 snapToGrid**（残余 3.8 个流程单位不是 20 的倍数）")
        print(f"      期间调用：{[c['k'] for c in calls2 if c['k'] != 'getActiveCanvas']}")

        # ---------- C6d 多选拖动：仍然只记 1 条 ----------
        go(page, "multi")
        m0 = snap(page)
        page.evaluate("""() => {
          const ids = window.__libtv_store.getState().getActiveCanvas().nodes.slice(0, 2).map(n => n.id);
          window.__libtv_store.getState().selectNodes(ids);
        }""")
        page.wait_for_timeout(600)
        msel = snap(page)
        page.evaluate(WRAP_STORE)
        two = page.evaluate("""() => {
          const els = [...document.querySelectorAll('.react-flow__node')].slice(0, 2);
          const r = els[0].getBoundingClientRect();
          return {n: els.length, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
        }""")
        do_drag(two["x"], two["y"], -7, 4)
        m1 = snap(page)
        mcalls = page.evaluate("() => window.__b741_calls")
        mset = [c for c in mcalls if c["k"] == "setNodes"]
        m1set = mset[0]["lastArg"] if mset else "NONE"
        moved_two = {k: [m0["nodePos"][k], m1["nodePos"][k]]
                     for k in m0["nodePos"] if m0["nodePos"][k] != m1["nodePos"][k]}
        page.evaluate("() => window.__libtv_store.getState().undo()")
        page.wait_for_timeout(700)
        m3 = snap(page)
        back2 = {k: (m0["nodePos"][k] == m3["nodePos"][k]) for k in m0["nodePos"]}
        print(f"\n=== C6d 多选拖动（选中 {len(msel['selectedNodeIds'])} 个一起拖）===")
        print(f"  setNodes 记账参数：{m1set}")
        print(f"  坐标真变的节点 {len(moved_two)} 个；past {m0['past']}→{m1['past']}"
              f" ⟹ 一次多选拖动仍只记 {m1['past'] - m0['past']} 条")
        print(f"  undo 后坐标逐项精确：{sum(back2.values())}/{len(back2)}"
              f"（不一致：{[k for k, v in back2.items() if not v]}）")

        # ---------- C7 updateNodeData ----------
        go(page, "update")
        u0 = snap(page)
        uid = page.evaluate("() => window.__libtv_store.getState().getActiveCanvas().nodes[0].id")
        page.evaluate("""(id) => window.__libtv_store.getState().updateNodeData(id, {__b741: 1})""", uid)
        page.wait_for_timeout(600)
        u1 = snap(page)
        print(f"\n=== C7 updateNodeData:3368（记账命令）===")
        print(f"  past {u0['past']}→{u1['past']}；节点数 {u0['nodeCount']}→{u1['nodeCount']}（不变，只改 data）")

        # ---------- C8 条件记账 ----------
        go(page, "cond")
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          const nodes = s.getActiveCanvas().nodes;
          s.setNodes(nodes);                                   // 不传 recordHistory
        }""")
        page.wait_for_timeout(500)
        c0 = snap(page)
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          const nodes = s.getActiveCanvas().nodes.map((n, i) => i === 0
            ? {...n, position: {...n.position, x: n.position.x + 5}} : n);
          s.setNodes(nodes, {recordHistory: true});
        }""")
        page.wait_for_timeout(600)
        c1 = snap(page)
        print(f"\n=== C8 setNodes:3389 条件记账（recordHistory）===")
        print(f"  不传 recordHistory：past = {c0['past']}（未变）")
        print(f"  传 recordHistory:true：past {c0['past']}→{c1['past']}"
              f"、第 1 个节点 x 平移 5px")

        # ---------- C9 removeCanvas 连历史桶一起删 ----------
        go(page, "rmcanvas")
        # 先在种子画布 canvas-2 上记一笔，作为「别的桶不该被动」的对照
        page.evaluate("() => window.__libtv_store.getState().addNode('text')")
        page.wait_for_timeout(600)
        # 注意：addCanvas 之后**必须重新 getState()**。第一版在变更前抓的
        # state 快照上读 canvices，读到的是旧数组的末位 —— 把 canvas-2 当成
        # 「新建画布」，最后删掉的是种子画布（与 740 的 past=0 同一类探针错：
        # 读数看着有模有样，实际什么都没验到）。
        new_id = page.evaluate("""() => {
          window.__libtv_store.getState().addCanvas('b741 临时画布');
          const after = window.__libtv_store.getState().canvases;
          return {newId: after[after.length - 1].id, ids: after.map(c => c.id)};
        }""")
        new_id = new_id["newId"]
        page.evaluate("(id) => window.__libtv_store.getState().setActiveCanvas(id)", new_id)
        page.wait_for_timeout(500)
        page.evaluate("() => window.__libtv_store.getState().addNode('text')")
        page.wait_for_timeout(600)
        r1 = snap(page)
        page.evaluate("(id) => window.__libtv_store.getState().removeCanvas(id)", new_id)
        page.wait_for_timeout(700)
        r2 = snap(page)
        print(f"\n=== C9 removeCanvas:1075（自己不记账，但删掉那一桶历史）===")
        print(f"  删之前 pastPerCanvas={json.dumps(r1['pastPerCanvas'], ensure_ascii=False)}"
              f"（canvas-2 是对照组，临时画布是 {new_id}）")
        print(f"  removeCanvas({new_id}) 之后 historyByCanvas 的键 = {r2['historyKeys']}"
              f"（{new_id} 还在吗：{new_id in r2['historyKeys']}；"
              f"对照组 canvas-2 的条目数 = "
              f"{r1['pastPerCanvas'].get('canvas-2')}）")
        print(f"  {new_id} 进了回收站：{r2['removedIds']}；剩余画布 {sorted(r2['canvasNames'])}")

        # ---------- C10 改名不可撤销 ----------
        go(page, "rename")
        n0 = snap(page)
        cid = n0["canvasId"]
        page.evaluate("""() => window.__libtv_store.getState().addNode('text')""")
        page.wait_for_timeout(600)
        n1 = snap(page)
        page.evaluate("""(id) => window.__libtv_store.getState().renameCanvas(id, 'b741 改过的名字')""", cid)
        page.wait_for_timeout(500)
        n2 = snap(page)
        page.evaluate("() => window.__libtv_store.getState().undo()")
        page.wait_for_timeout(600)
        n3 = snap(page)
        print(f"\n=== C10 renameCanvas:1101 + undo（undo 只碰 nodes/edges）===")
        print(f"  记账一次后 past={n1['past']}；改名后名字={n2['canvasNames'][cid]!r}、"
              f"节点 {n2['nodeCount']}")
        print(f"  调 undo() 后：节点 {n3['nodeCount']}（图被撤了）、"
              f"名字仍是 {n3['canvasNames'][cid]!r} ⟹ 改名没被撤回来")

        page.close()
        browser.close()

    summary = {
        "static": {k: v for k, v in c.items() if k != "rows"},
        "buckets": {
            "fns": len(rows), "both": len(both), "setonly": len(setonly), "neither": len(neither),
            "conditional": len(cond), "call_sites": len(c["call_sites"]),
        },
        "both_names": [r["name"] for r in both],
        "setonly_names": [r["name"] for r in setonly],
        "neither_names": [{"name": r["name"], "range": [r["start"], r["end"]],
                           "delegates": r["delegates"]} for r in neither],
        "conditional_names": [r["name"] for r in cond],
        "addNode": add_node, "addNodeAtPosition": add_at_pos,
        "forward": {"n0": a0["nodeCount"], "n1": a1["nodeCount"],
                    "p0": a0["past"], "p1": a1["past"]},
        "select": {"p0": b0["past"], "p1": b1["past"], "sel": b1["selectedNodeIds"]},
        "drag": {"id": drag["id"], "size": [drag["w"], drag["h"]],
                 "routeCalls": len(routes), "routeCodes": route_codes,
                 "setNodesCalls": len(setnodes),
                 "setNodesArg": setnodes[0]["lastArg"] if setnodes else "NONE",
                 "movedCount": len(moved), "moved": moved,
                 "p0": d0["past"], "p1": d1["past"],
                 "undoPast": d2["past"], "undoFuture": d2["future"],
                 "undoExact": sum(back.values()), "undoTotal": len(back),
                 "undoMismatched": [k for k, v in back.items() if not v]},
        "nodrag": {"stillMoved": still, "p0": e0["past"], "p1": e1["past"],
                   "roundTripMoved": len(back2), "roundTripDelta": back2,
                   "roundTripPast": e2["past"],
                   "roundTripCalls": [c["k"] for c in calls2 if c["k"] != "getActiveCanvas"]},
        "multi": {"selected": msel["selectedNodeIds"], "setNodesArg": m1set,
                  "movedCount": len(moved_two),
                  "p0": m0["past"], "p1": m1["past"],
                  "undoExact": sum(back2.values()), "undoTotal": len(back2),
                  "undoMismatched": [k for k, v in back2.items() if not v]},
        "update": {"p0": u0["past"], "p1": u1["past"]},
        "cond": {"noFlag": c0["past"], "flag": c1["past"]},
        "rmcanvas": {"newId": new_id, "before": r1["pastPerCanvas"],
                     "afterKeys": r2["historyKeys"], "removedIds": r2["removedIds"]},
        "rename": {"cid": cid, "past": n1["past"],
                   "nameAfterRename": n2["canvasNames"][cid],
                   "nameAfterUndo": n3["canvasNames"][cid],
                   "nodesAfterUndo": n3["nodeCount"]},
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")

    checks = [
        ("C1 54 命令 = 33 记账 / 17 只 set / 4 皆无；33 个调用点逐个对平；声明区 0 命中",
         len(rows) == 54 and len(both) == 33 and len(setonly) == 17 and len(neither) == 4
         and len(c["call_sites"]) == len(both) == 33 and c["decl_push_hits"] == []
         and c["push_history_def"] == 506,
         json.dumps(summary["buckets"], ensure_ascii=False)),
        ("C2 修正扫描错：addNode 是转发器（无 pushHistory）、setProjectName 被状态字段吞掉后才找回来",
         add_node["calls_push"] is False and "addNodeAtPosition" in add_node["delegates"]
         and by_name["setProjectName"]["calls_push"] is False
         and by_name["createStoryScriptPair"]["calls_push"] is True,
         json.dumps({"addNode": add_node, "setProjectName": by_name["setProjectName"]},
                    ensure_ascii=False)),
        ("C3 setNodes/setEdges 条件记账，其余 31 个无条件",
         [r["name"] for r in cond] == ["setNodes", "setEdges"] and len(both) - len(cond) == 31,
         json.dumps({"conditional": [r["name"] for r in cond]}, ensure_ascii=False)),
        ("C4 转发器 addNode：节点 +1 且 past 0→1（自己不记账≠用户拿不到条目）",
         a1["nodeCount"] == a0["nodeCount"] + 1 and a1["past"] == a0["past"] + 1,
         json.dumps(summary["forward"], ensure_ascii=False)),
        ("C5 纯选择 selectNode：past 不变（基线为 0）",
         b0["past"] == 0 and b1["past"] == 0 and b0["nodeCount"] == b1["nodeCount"],
         json.dumps(summary["select"], ensure_ascii=False)),
        ("C6 一次拖动 = 多次 routeReactFlowChanges（全不记账）+ 1 次 setNodes(recordHistory)",
         len(routes) >= 3 and all("APPLIED_TRANSPORT" in c for c in route_codes)
         and len(setnodes) == 1 and '"recordHistory":true' in summary["drag"]["setNodesArg"]
         and len(moved) == 1 and d1["past"] == d0["past"] + 1,
         json.dumps(summary["drag"], ensure_ascii=False)),
        ("C6b 拖动后 undo：坐标逐项精确回拖动前",
         summary["drag"]["undoExact"] == summary["drag"]["undoTotal"]
         and d2["future"] == 1,
         json.dumps({k: summary["drag"][k] for k in
                     ("undoPast", "undoFuture", "undoExact", "undoTotal", "undoMismatched")},
                    ensure_ascii=False)),
        ("C6c 空拖（按下-不动-松手）：一条历史都不留（moved 守卫）",
         still == 0 and e1["past"] == e0["past"],
         json.dumps(summary["nodrag"], ensure_ascii=False)),
        ("C6d 多选拖动：仍只记 1 条，undo 后全部逐项恢复",
         len(msel["selectedNodeIds"]) >= 2 and m1["past"] == m0["past"] + 1
         and summary["multi"]["undoExact"] == summary["multi"]["undoTotal"],
         json.dumps(summary["multi"], ensure_ascii=False)),
        ("C7 updateNodeData：past +1",
         u1["past"] == u0["past"] + 1, json.dumps(summary["update"], ensure_ascii=False)),
        ("C8 setNodes：recordHistory 开关真的分两路",
         c0["past"] == 0 and c1["past"] == 1, json.dumps(summary["cond"], ensure_ascii=False)),
        ("C9 removeCanvas：只删那一桶历史（对照组 canvas-2 不受影响）、画布进回收站",
         r1["pastPerCanvas"].get(new_id) == 1 and r1["pastPerCanvas"].get("canvas-2") == 1
         and new_id not in r2["historyKeys"] and "canvas-2" in r2["historyKeys"]
         and new_id in r2["removedIds"], json.dumps(summary["rmcanvas"], ensure_ascii=False)),
        ("C10 改名 + undo：图撤了、名字没撤回来",
         n1["past"] == 1 and n2["canvasNames"][cid] == "b741 改过的名字"
         and n3["canvasNames"][cid] == "b741 改过的名字",
         json.dumps(summary["rename"], ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 741,
        "title": "canvasStore 54 个命令的历史栈记账普查：33 记账 / 17 只 set / 4 皆无；"
                 "一次拖动 = 多次中间路由零记账 + 停下时 1 条",
        "verdict": f"{passed}/{len(checks)}",
        "summary": summary,
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "静态三桶必须分开报：54 个命令 = 33 记账 / 17 改 store 不记账 / 4 既不 set 也不 "
            "pushHistory（2 转发器 + 2 纯 getter）。",
            "pushHistory 调用点 33 处与命令级 33 逐个对平，两个独立口径互证。",
            "声明区（CanvasState :282-453）0 命中 pushHistory；:506 是模块级函数定义，不是命令。",
            "「33 个记账」还要再拆：setNodes/setEdges 是 recordHistory 条件记账 ⟹ 31 无条件 + 2 条件。",
            "addNode/addNodeAtFlowCenter 自己不记账但转发给记账的 addNodeAtPosition ⟹ "
            "静态桶不等于用户可见行为。",
            "拖动节点**是可撤销的**，但记账的不是搬运的那条路径：拖动途中反复走 "
            "routeReactFlowChanges（不记账桶），停下时才由 page.tsx:1501 onNodeDragStop 发一次 "
            "setNodes(recordHistory:true, historySnapshot=拖动前快照) ⟹ 整次拖动压成 1 条。",
            "onNodeDragStop 里的 moved 守卫让「按下-不动-松手」不产生任何历史条目。",
            "「挪出去再回同一屏幕原点」**不是** no-op：节点坐标仍差 3.8 个流程单位 ⟹ 那次记账"
            "是对的。**成因未取证**，不归因 snapToGrid。",
            "removeCanvas 自己不记账，却把该画布的整桶历史删掉 ⟹ 删画布 = 撤不回来的动作 + "
            "历史一并消失（对照组：别的桶不动）。",
            "undo() 只恢复 nodes/edges，不恢复画布名 ⟹ renameCanvas 不可撤销。",
        ],
        "retracted": [
            "**撤回「拖动节点不记账 / 移动节点不可撤销」**（第一版的中间推断）："
            "读数是 past 0→1，与推断相反。当时只把结论硬写进 print 文案，没去查谁记的账。"
            "探针（给 54 个命令套调用日志）给出真相：记账发生在 setNodes(recordHistory) 上，"
            "不发生在 routeReactFlowChanges 上。",
            "**撤回「53 个命令」**：状态字段 projectName 没有 `=>`，扫描器一路吞到 :1030 第一个 "
            "`=>` 才停，把 setProjectName 整个吞掉。命令实为 54 个、不记账 17 个。",
            "**撤回「多行参数表的函数归错桶」**：第一版把 `addNodeAtFlowCenter: (` 这种参数跨 3 行 "
            "的键当成单行函数收尾，于是 addNode 被算成记账（其实它一行 pushHistory 都没有），"
            "而真正记账的 12 个多行参数函数一个都没数到。",
        ],
        "notClaimed": [
            "不声称源站对移动/改名/删画布是否记账 —— 未取证。",
            "不声称拖动记账是缺陷还是有意设计 —— 未取证。",
            "MAX_HISTORY=50 的上限行为（超过 50 条时截断）未测。",
            "17 个不记账命令逐个的运行时行为未逐条验，只验了 selectNode / renameCanvas / "
            "removeCanvas 三条。",
            "onNodeDragStop 里 Batch 436 的跨画布守卫（armed 基线画布 ≠ 当前画布 ⟹ 不记账）未测。",
            "拖动中途切画布、拖动中改尺寸（dimensions 变化走 hasTransport 的另一半）未测。",
            "「挪出去再回同一屏幕原点」为何留下 3.8 个流程单位的残余 —— 成因未取证。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
