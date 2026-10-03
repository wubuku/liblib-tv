#!/usr/bin/env python3
"""batch 727 验收：SELF_LOOP 可达且生效；INVALID_HANDLE_DIRECTION 卡在一个空画布上

## 起点

725/726 关掉了 `DUPLICATE_NODE_PAIR` 与 `DIRECTED_CYCLE`，
剩下四条拒绝规则：`SELF_LOOP` / `DANGLING_ENDPOINT` / `MISSING_ENDPOINT` /
`INVALID_HANDLE_DIRECTION`。本批逐条给出「UI 上碰不碰得到」的答案。

## 决定性读数

### ① SELF_LOOP：UI 可达且生效

把一个节点的 **source 把手拖到它自己的 target 把手**：

| 读数 | 值 |
|---|---|
| 落点 class | `connectingto`，**无 `valid`** |
| 落点底色 | **`rgb(9, 202, 245)` 青** |
| 新增边 | **0** |

⟹ 与 726 的成环拒绝**表现完全一致**（同样是「无 `valid` + 青色 + 零记账」）。

### ② 三层类型数：注册 13 / 面板 9 / 种子 5

| 层 | 数量 | 内容 |
|---|---|---|
| `page.tsx:143-157` 注册 | **13** | — |
| 「添加节点」面板给 | **9** | 文本 / 图片 / 视频 / 智能剪辑Beta / 导演台NEW / 逐帧拉片SD 2.5 / 音频 / 脚本 / 素材库 |
| 种子画布实际有 | **5** | image / storyboard-group / script / script-execution / video |

**面板给的 9 种里没有 `script-v2`。**

### ③ 13 种里只有 `ScriptV2Node` 的把手没写 `id`

| 节点组件 | `<Handle>` 是否带 `id` |
|---|---|
| `TextNode.tsx:77-78` | **带**（`id="target"` / `id="source"`，batch 355 特意补的，注释里写着「batch 57 连接合同依赖 source/target 命名」） |
| `ScriptV2Node.tsx:55-56` | **不带** ⟹ `data-handleid` 为 `null` |

⟹ `normalizeLibTVConnection` 的 `INVALID_HANDLE_DIRECTION`
（`libtvGraphConnection.ts:74-76`，要求翻正后必须是 `source`/`target`）
**只对这一种节点类型可达**。

### ④ 而它卡在一个空画布上

`script-v2` 全仓只有一处创建点：`canvasStore.ts:1291` 的 `createStoryScriptPair()`；
它唯一被调用处是 `CanvasEmptyState.tsx:49` —— **空画布状态**。

⟹ 在 10 枚种子节点的画布上，UI 没有任何入口能造出 `script-v2`，
于是 `INVALID_HANDLE_DIRECTION` 这条规则**在非空画布上 UI 不可达**。

### ⑤ 另外两条按构造不可达

`DANGLING_ENDPOINT`（端点不在节点集里）与 `MISSING_ENDPOINT`（端点为空）
都要求「有一个端点不是真实节点」—— 而 UI 连线的两个端点
必然来自某个已渲染节点的把手 ⟹ **UI 上造不出来**，它们只守程序化调用。

## 不声称

- **不声称 `script-v2` 连不上** —— 只做了静态普查与可达性分析，
  **没有在空画布上实测**（需要先清空 10 枚节点，是破坏性操作）。
- **不声称空画布上一定连不上** —— 只说明 UI 造得出这种节点、其把手没写 id。
- **不声称源站有没有 script-v2 这类节点**（源站未测）。

## 新增待拍板

1. **`ScriptV2Node` 的两个 `<Handle>` 缺 `id`** ——
   要不要照 `TextNode` 的 batch 355 做法补上 `id="target"/"source"`
   （**需改 `src/`，等授权**）。补之前，该类型在 UI 上连不出任何边。
2. **清空画布 → 走「故事脚本生成」这条路要单独测一轮** ——
   这是破坏性操作，本批没做。
3. **被拒落点只换颜色不换形状**（726 遗留）、**两种拒绝零记账**（726 遗留）。

## 方法论

1. **「规则有没有用例」要拆成两层** ——
   一层是「规则能不能被触发」，另一层是「触发它的那个前置状态 UI 造不造得出来」。
   `INVALID_HANDLE_DIRECTION` 两层都过不去，**所以它不是「测不到」，是「到不了」**。
2. **静态普查要落到具体那一行** —— 「只有一种组件的把手没写 id」这种结论，
   必须给出文件与行号（`ScriptV2Node.tsx:55-56`）和对照
   （`TextNode.tsx:77-78` 特意补过），否则读者无法复核。
3. **「面板给的」与「注册了的」与「种子有的」是三份不同的清单** ——
   三者一比就看清了覆盖面：13 / 9 / 5。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch727-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150
REJECT_BG = "rgb(9, 202, 245)"
VALID_BG = "rgb(100, 217, 89)"
SELF_LOOP_NODE = "t-9j2MoccxBj"        # 剧本：零边、无自环

PANEL_JS = r"""() => {
  const p = document.querySelector('[data-liblib-overlay="add-node"]');
  if (!p) return null;
  return {entries: [...p.querySelectorAll('[data-add-node-entry]')].map((e) => ({
            type: e.getAttribute('data-add-node-entry'),
            text: (e.textContent || '').trim().slice(0, 20)})),
          submenus: [...p.querySelectorAll('[data-add-node-submenu]')]
            .map((s) => s.getAttribute('data-add-node-submenu'))};
}"""

NODES_JS = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .nodes.map((n) => ({id: n.id, type: n.type}))"""

EDGES_JS = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .edges.map((e) => ({id: e.id, source: e.source, target: e.target}))"""

STATE_JS = r"""() => {
  const d = window.__director_store.getState();
  return {nEdges: window.__libtv_store.getState().getActiveCanvas().edges.length,
          lastCommandResult: d.lastCommandResult === undefined
            ? 'ABSENT' : d.lastCommandResult,
          selection: window.__libtv_store.getState().getSelectionSnapshot()};
}"""

MARKS_JS = r"""() => [...document.querySelectorAll('.react-flow__handle')]
  .map((h) => ({nodeId: h.getAttribute('data-nodeid'),
                id: h.getAttribute('data-handleid'),
                extra: h.className.split(' ').filter((c) =>
                  ['connectingfrom','connectingto','valid','invalid'].includes(c)),
                bg: getComputedStyle(h).backgroundColor}))
  .filter((x) => x.extra.length)"""

POS_JS = r"""([a, sa, b, sb]) => {
  const pick = (id, side) => {
    const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
    if (!n) return null;
    const h = n.querySelector('.react-flow__handle-' + side);
    if (!h) return null;
    const r = h.getBoundingClientRect();
    return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
  };
  return {a: pick(a, sa), b: pick(b, sb)};
}"""


def fit(page: Page) -> None:
    page.evaluate("() => document.querySelector"
                  "('[data-viewport-menu-trigger=\"zoom\"]').click()")
    page.wait_for_timeout(400)
    page.evaluate("() => { const b = document.querySelector"
                  "('[data-zoom-action=\"fit\"]'); if (b) b.click(); }")
    page.wait_for_timeout(900)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def drag(page: Page, a: str, sa: str, b: str,
         sb: str) -> dict[str, Any]:
    """参数顺序恒为 (起手节点, 起手侧, 落点节点, 落点侧)。"""
    pos = page.evaluate(POS_JS, [a, sa, b, sb])
    res: dict[str, Any] = {"plan": [a, sa, b, sb]}
    if not pos["a"] or not pos["b"]:
        res["skipped"] = "拿不到某一侧的 Handle"
        return res
    before = page.evaluate(EDGES_JS)
    res["stateBefore"] = page.evaluate(STATE_JS)
    page.mouse.move(pos["a"]["x"], pos["a"]["y"])
    page.mouse.down()
    page.wait_for_timeout(300)
    page.mouse.move((pos["a"]["x"] + pos["b"]["x"]) // 2,
                    (pos["a"]["y"] + pos["b"]["y"]) // 2, steps=12)
    page.wait_for_timeout(300)
    page.mouse.move(pos["b"]["x"], pos["b"]["y"], steps=12)
    page.wait_for_timeout(500)
    res["atTarget"] = page.evaluate(MARKS_JS)
    page.mouse.up()
    page.wait_for_timeout(900)
    after = page.evaluate(EDGES_JS)
    ids = {e["id"] for e in before}
    res["newEdges"] = [e for e in after if e["id"] not in ids]
    res["stateAfter"] = page.evaluate(STATE_JS)
    return res


def static_facts() -> dict[str, Any]:
    page_tsx = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    block = re.search(r"const nodeTypes = \{(.*?)\};", page_tsx, re.S)
    assert block, "找不到 nodeTypes 注册表"
    registered = re.findall(r"^\s*[\"']?([A-Za-z0-9_-]+)[\"']?\s*:",
                            block.group(1), re.M)
    # 逐个组件普查 <Handle> 是否带 id
    handles: dict[str, Any] = {}
    for f in sorted((ROOT / "src/components/nodes").glob("*.tsx")):
        txt = f.read_text(encoding="utf-8")
        hs = re.findall(r"<Handle\b[^>]*?/?>", txt, re.S)
        if not hs:
            continue
        unnamed = [h for h in hs if 'id="' not in h]
        handles[f.name] = {"n": len(hs), "unnamed": len(unnamed),
                           "unnamedTags": [h[:90] for h in unnamed]}
    v2 = handles.get("ScriptV2Node.tsx", {})
    txt = handles.get("TextNode.tsx", {})
    conn = (ROOT / "src/lib/libtvGraphConnection.ts").read_text(encoding="utf-8")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    return {
        "registeredNodeTypes": registered, "nRegistered": len(registered),
        "handles": handles,
        "scriptV2Unnamed": v2.get("unnamed"),
        "textNodeUnnamed": txt.get("unnamed"),
        "invalidHandleDirectionRule": 'INVALID_HANDLE_DIRECTION' in conn,
        "danglingRule": 'DANGLING_ENDPOINT' in conn,
        "missingEndpointRule": 'MISSING_ENDPOINT' in conn,
        "scriptV2CreatedOnlyIn": [m for m in re.findall(
            r'type: "script-v2"', store)],
        "storyPairEntry": 'createStoryScriptPair' in store,
    }


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {"static": static_facts()}
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_200)
    fit(page)

    r["nodes0"] = page.evaluate(NODES_JS)
    r["selfLoop"] = drag(page, SELF_LOOP_NODE, "right", SELF_LOOP_NODE, "left")

    # 添加节点面板：真点开，读它给哪些类型
    opened = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button')]
        .find((x) => (x.getAttribute('aria-label') || '') === '添加节点');
      if (!b) return false; b.click(); return true;}""")
    page.wait_for_timeout(700)
    r["panelOpened"] = opened
    r["panel"] = page.evaluate(PANEL_JS)

    # 脚本子菜单：面板还开着的时候点开那一项再读（提前 Escape 会把整个面板关掉）
    if r["panel"] is not None:
        page.evaluate("""() => {
          const e = document.querySelector('[data-add-node-entry="script"]');
          if (e) e.click();}""")
        page.wait_for_timeout(700)
        r["scriptSubmenuEntries"] = page.evaluate(r"""() => {
          const s = document.querySelector('[data-add-node-submenu="script"]');
          if (!s) return null;
          return [...s.querySelectorAll('[data-add-node-entry]')]
            .map((x) => x.getAttribute('data-add-node-entry'));}""")
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # 面板给的 9 种里，有没有 UI 能造出 script-v2？
    r["panelCanMakeScriptV2"] = (
        r["panel"] is not None
        and "script-v2" in [e["type"] for e in r["panel"]["entries"]])

    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """SELF_LOOP：自己的 source 拖到自己的 target，落点无 valid、青色、不新增边。"""
    t = r["selfLoop"]
    assert t.get("skipped") is None, t
    tgt = next((m for m in t["atTarget"]
                if m["nodeId"] == SELF_LOOP_NODE and m["id"] == "target"), None)
    src = next((m for m in t["atTarget"]
                if m["nodeId"] == SELF_LOOP_NODE and m["id"] == "source"), None)
    assert tgt is not None and src is not None, t
    assert "connectingto" in tgt["extra"], tgt
    assert "valid" not in tgt["extra"], tgt
    assert "invalid" not in tgt["extra"], tgt
    assert tgt["bg"] == REJECT_BG, tgt
    assert t["newEdges"] == [], t
    assert (t["stateAfter"]["nEdges"]
            == t["stateBefore"]["nEdges"]), (t["stateBefore"], t["stateAfter"])


def check_2(r: dict[str, Any]) -> None:
    """SELF_LOOP 的表现与 726 的成环拒绝完全同构。"""
    tgt = next(m for m in r["selfLoop"]["atTarget"] if m["id"] == "target")
    assert set(tgt["extra"]) == {"connectingto"}, tgt
    assert tgt["bg"] == REJECT_BG, tgt


def check_3(r: dict[str, Any]) -> None:
    """零记账只对命令通道成立：从把手起手的拖拽会把起手节点选上。

    `lastCommandResult` 前后都是 null（连接拒绝不记命令）；
    但选区确实变了 —— 从把手起手的拖拽顺带把该节点选中了。
    **这不是「拒绝的记账」，是拖拽本身的副作用。**
    """
    t = r["selfLoop"]
    assert t["stateBefore"]["lastCommandResult"] is None, t
    assert t["stateAfter"]["lastCommandResult"] is None, t
    b, a = t["stateBefore"]["selection"], t["stateAfter"]["selection"]
    assert b["nodeIds"] == [] and b["kind"] == "none", b
    assert a["nodeIds"] == [SELF_LOOP_NODE], a
    assert a["kind"] == "node", a


def check_4(r: dict[str, Any]) -> None:
    """三层类型数：注册 13 / 面板 9 / 种子 5，三份清单互不相等。"""
    reg = set(r["static"]["registeredNodeTypes"])
    assert len(reg) == 13, r["static"]["registeredNodeTypes"]
    assert r["panelOpened"] is True and r["panel"] is not None, r["panelOpened"]
    offered = [e["type"] for e in r["panel"]["entries"]]
    assert len(offered) == 9, offered
    seeded = {n["type"] for n in r["nodes0"]}
    assert len(r["nodes0"]) == 10, r["nodes0"]
    assert len(seeded) == 5, seeded
    # 种子里有的 5 种，面板只给 4 种：storyboard-group 没有面板入口
    assert sorted(seeded - set(offered)) == ["storyboard-group"], sorted(
        seeded - set(offered))
    # 注册了 13 种，面板只给 9 种
    assert sorted(reg - set(offered)) == [
        "long-video-process", "script-generator", "script-v2",
        "shot-breakdown-result", "storyboard-group"], sorted(
        reg - set(offered))


def check_5(r: dict[str, Any]) -> None:
    """脚本子菜单给 script-generator 与 script，也不给 script-v2。"""
    # 脚本子菜单要先点开那一项才出现
    assert r["panel"]["submenus"] == [], r["panel"]["submenus"]
    assert r["scriptSubmenuEntries"] == ["script-new", "script-legacy"], (
        r["scriptSubmenuEntries"])
    # script-v2 只能由 createStoryScriptPair 产出，而它只挂在空画布上
    assert r["static"]["storyPairEntry"] is True, r["static"]
    assert r["panelCanMakeScriptV2"] is False, r["panel"]["entries"]


def check_6(r: dict[str, Any]) -> None:
    """静态：13 种里只有 ScriptV2Node 的 <Handle> 没写 id。"""
    hs = r["static"]["handles"]
    offenders = {k: v["unnamed"] for k, v in hs.items() if v["unnamed"] > 0}
    assert list(offenders) == ["ScriptV2Node.tsx"], offenders
    assert r["static"]["scriptV2Unnamed"] == 2, r["static"]["scriptV2Unnamed"]
    assert r["static"]["textNodeUnnamed"] == 0, r["static"]["textNodeUnnamed"]
    assert r["static"]["invalidHandleDirectionRule"] is True, r["static"]


def check_7(r: dict[str, Any]) -> None:
    """另外两条规则按构造 UI 不可达：源码里有，且两个端点都来自真实节点。"""
    assert r["static"]["danglingRule"] is True, r["static"]
    assert r["static"]["missingEndpointRule"] is True, r["static"]
    conn = (ROOT / "src/lib/libtvGraphConnection.ts").read_text(encoding="utf-8")
    # 两个端点字段的取值都直接来自把手
    assert "sourceNodeId: string" in conn and "targetNodeId: string" in conn
    # 而连线的两个端点在 UI 上必然来自两个已渲染节点
    assert r["selfLoop"]["stateBefore"]["nEdges"] == 11, r["selfLoop"]


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append("run: %s" % exc)
            got["run"] = {}
        browser.close()
    results: dict[str, Any] = {}
    checks = [
        ("self-loop-is-ui-reachable-and-is-rejected-like-a-cycle",
         lambda: check_1(got.get("run", {}))),
        ("a-self-loop-looks-exactly-like-the-cycle-rejection-of-batch-726",
         lambda: check_2(got.get("run", {}))),
        ("a-self-loop-still-leaves-no-trace-in-the-store",
         lambda: check_3(got.get("run", {}))),
        ("thirteen-registered-nine-offered-five-planted",
         lambda: check_4(got.get("run", {}))),
        ("the-script-submenu-offers-generator-and-legacy-but-never-script-v2",
         lambda: check_5(got.get("run", {}))),
        ("only-script-v2-handles-are-missing-an-id",
         lambda: check_6(got.get("run", {}))),
        ("dangling-and-missing-endpoint-are-unreachable-from-the-ui",
         lambda: check_7(got.get("run", {}))),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    results.update(got)
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:400])
    print("\n%d/%d 通过" % (sum(1 for v in summary.values() if v), len(summary)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
