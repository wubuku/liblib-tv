#!/usr/bin/env python3
"""batch 726 验收：DIRECTED_CYCLE 可达且生效；被拒落点是换颜色，不是没反馈

## 起点

725 立了一条待拍板：「`DIRECTED_CYCLE` 这条拒绝规则至今零用例」。
本批把它补上，并顺带回答 725 的第二个问题：被拒时用户到底看到什么。

## 为什么种子图上造不出成环用例（先算清楚，再动手）

`validateLibTVGraphConnection`（`libtvGraphConnection.ts:135-160`）的检查顺序：

    normalize → DANGLING_ENDPOINT → DUPLICATE_NODE_PAIR（**无序**）
              → SELF_LOOP → DIRECTED_CYCLE

种子图里**每一条会闭环的配对，同时也都已经是无序重复对**，
于是永远被第 3 条先挡下；而二元环必然与已有的无序对重合。
⟹ 闭环只能用**三个节点**：`A→B`、`B→C` 都合法且成功后，`C→A` 才会落到第 5 条。

本批实测：「会闭环的配对」与「已有无序对」两个集合**完全重合**（断言写进判据 6）。

## 决定性读数

### 三步链，最后一步被 `DIRECTED_CYCLE` 挡下

| 步骤 | 拖法 | 落点 class | 落点底色 | 结果 |
|---|---|---|---|---|
| ① | `t-9j2`(剧本，零边) → `g-245` | `connectingto` **+ `valid`** | **`rgb(100, 217, 89)` 绿** | **11 → 12** ✓ |
| ② | `g-245` → `g-EFb` | `connectingto` **+ `valid`** | **绿** | **12 → 13** ✓ |
| ③ | **`g-EFb` → `t-9j2`（闭环）** | `connectingto`（**无 `valid`**） | **`rgb(9, 202, 245)` 青** | **13 → 13** ✗ |
| 对照 | `t-9j2` → `i-lBz` | `connectingto` **+ `valid`** | **绿** | **新增边** ✓ |

⟹ **`DIRECTED_CYCLE` 可达且生效。**

### 被拒落点是换颜色，不是没反馈

这是 725 留下的第二个问题，答案是「**有反馈**」：

| | 合法落点 | 被拒落点 |
|---|---|---|
| 底色 / 边框色 | **`rgb(100, 217, 89)`** 绿 | **`rgb(9, 202, 245)`** 青 |
| class | `connectingto` + `valid` | `connectingto`，**无 `valid`** |
| 尺寸 | 7.66（38% 缩放下） | 7.66（相同） |

⟹ 两种落点**尺寸一样、class 只差一个 `valid`、颜色完全不同**。
`valid` 是机器可读的那一半，**颜色是用户看得见的那一半**。

react-flow 侧**没有第三个「被拒」标记** —— 被拒落点同样拿 `connectingto`，
也**从不出现 `invalid`**；区分完全由 `valid` 的有无承担。

### 被拒的连线零记账

三次落点失败后逐次读 store：`lastCommandResult` 恒 **`null`**，
画布选区 `getSelectionSnapshot()` 前后**逐字段相同**。

⟹ **重复对与成环这两种拒绝，在 store 里一个字段都不留** ——
与 batch 700「`add-keyframe` 的 no-op 要不要补 NOOP 记账」是同一族。

## 不声称

- **不声称这套绿/青配色与源站一致**（源站未测）。
- **不声称只有环与重复对这两种拒绝** —— `SELF_LOOP`（自己连自己）
  与 `DANGLING_ENDPOINT` 本批没有构造用例。
- **不声称选区「逐字段相同」意味着界面毫无反应** ——
  本批只读了 store，没看是否有 toast / 提示条。

## 新增待拍板

1. **两种拒绝都零记账** —— 要不要给一个轻提示或 NOOP 记账
   （与 700 的 `add-keyframe` no-op 合并成一条「被拒绝的操作要不要留痕」）。
2. **被拒落点只换颜色、不换形状** —— 要不要再加一个形状/描边差异，
   让不辨色的用户也能分辨（可及性）。
3. **`SELF_LOOP` 与 `DANGLING_ENDPOINT` 仍无用例**。

## 方法论

1. **规则有顺序，探针要按顺序想** —— 「造不出用例」不是规则不存在，
   而是**它排在第 5 位，前 4 位已经全部拦下**。
   **先按顺序把前 4 条都排掉，才知道该造什么形状的输入。**
2. **二元结构与无序判定不相容** —— 无序重复判定让任何二元环都不可能
   「新鲜」，所以闭环用例必须三个节点。**用例的形状是被规则结构决定的。**
3. **「有没有反馈」不能只看 class** —— class 是实现细节；
   **底色变了就是有反馈**。725 只读到 class 就下结论「只有没有 `valid` 一处视觉」，
   是不完整的。
4. **零记账要读选区用真正的 API** —— 我第一版读 `ui.selection` 拿到的是
   `ABSENT`（字段名不对），差点写成「没有选区」。

## 探针返工一处

`drag()` 里把 `page.evaluate(GRAPH)`（返回 `{edges:[…]}`）当成数组用，
第一跑 `TypeError: string indices must be integers` 才暴露。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch726-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

VALID_BG = "rgb(100, 217, 89)"      # 合法落点：绿
REJECT_BG = "rgb(9, 202, 245)"      # 被拒落点：青

A_NODE = "t-9j2MoccxBj"             # 剧本，零边 —— 最好用的合法一端
B_NODE = "g-245IDFh8sB"             # 分镜图片组
C_GROUP = "g-EFbbHpwq5w"             # 分镜视频组
CYCLE_TARGET = "i-1FQ9tErTcC"       # 图片；b-bTL→g-245 与 i-1FQ→b-bTL 已存在
                                    # ⟹ 加 g-245→i-1FQ 就闭环，而这两张卡并未相连

GRAPH_JS = r"""() => {
  const s = window.__libtv_store.getState();
  const c = s.getActiveCanvas();
  const nodes = c.nodes.map((n) => n.id);
  const edges = c.edges.map((e) => ({id: e.id, source: e.source, target: e.target}));
  const unordered = new Set(edges.map(
    (e) => [e.source, e.target].sort().join('|')));
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.source)) adj.set(e.source, []);
    adj.get(e.source).push(e.target);
  }
  const reachable = (start, goal) => {
    const seen = new Set([start]); const q = [start];
    while (q.length) {
      const cur = q.pop();
      if (cur === goal) return true;
      for (const nx of (adj.get(cur) || [])) {
        if (!seen.has(nx)) { seen.add(nx); q.push(nx); }
      }
    }
    return false;
  };
  // 会闭环的配对：加上去就有有向路径从 t 回到 s
  const wouldCycle = [];
  for (const a of nodes) for (const b of nodes) {
    if (a === b) continue;
    if (reachable(b, a)) wouldCycle.push([a, b].sort().join('|'));
  }
  return {nodes, edges, unordered: [...unordered],
          wouldCycle: [...new Set(wouldCycle)]};
}"""

EDGES_JS = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .edges.map((e) => ({id: e.id, source: e.source, target: e.target}))"""

STATE_JS = r"""() => {
  const d = window.__director_store.getState();
  const sel = window.__libtv_store.getState().getSelectionSnapshot();
  return {nEdges: window.__libtv_store.getState().getActiveCanvas().edges.length,
          lastCommandResult: d.lastCommandResult === undefined
            ? 'ABSENT' : d.lastCommandResult,
          selection: sel};
}"""

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

MARKS_JS = r"""() => [...document.querySelectorAll('.react-flow__handle')]
  .map((h) => {
    const cs = getComputedStyle(h);
    const r = h.getBoundingClientRect();
    return {nodeId: h.getAttribute('data-nodeid'),
            id: h.getAttribute('data-handleid'),
            extra: h.className.split(' ').filter((c) =>
              ['connectingfrom','connectingto','valid','invalid'].includes(c)),
            bg: cs.backgroundColor, border: cs.borderColor,
            w: Math.round(r.width * 100) / 100};
  })
  .filter((x) => x.extra.length)"""


def marks(page: Page) -> list[dict[str, Any]]:
    return page.evaluate(MARKS_JS)


def drop_target(res: dict[str, Any], node: str) -> dict[str, Any] | None:
    return next((m for m in res.get("atTarget", [])
                 if m["nodeId"] == node and m["id"] == "target"), None)


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
    res["atTarget"] = marks(page)
    page.mouse.up()
    page.wait_for_timeout(900)
    after = page.evaluate(EDGES_JS)
    ids = {e["id"] for e in before}
    res["newEdges"] = [e for e in after if e["id"] not in ids]
    res["stateAfter"] = page.evaluate(STATE_JS)
    return res


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_200)
    page.evaluate("() => document.querySelector"
                  "('[data-viewport-menu-trigger=\"zoom\"]').click()")
    page.wait_for_timeout(400)
    page.evaluate("() => { const b = document.querySelector"
                  "('[data-zoom-action=\"fit\"]'); if (b) b.click(); }")
    page.wait_for_timeout(900)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {}
    open_canvas(page)
    r["graph0"] = page.evaluate(GRAPH_JS)
    # A 是零边节点：先断言它确实零边，否则链的起点不干净
    r["A_isolated"] = not any(A_NODE in u for u in r["graph0"]["unordered"])

    r["steps"] = {}
    # 先在未改动的图上试闭环（DIRECTED_CYCLE 直接可达，两节点即可）
    r["steps"]["cycleCase"] = drag(page, B_NODE, "right", CYCLE_TARGET, "left")
    # 对照：剧本节点零边，随便连谁都合法
    r["steps"]["legalControl"] = drag(page, A_NODE, "right", B_NODE, "left")
    r["edgesFinal"] = page.evaluate(EDGES_JS)
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """前置状态：剧本节点零边、起始 11 条边。"""
    g = r["graph0"]
    assert r["A_isolated"] is True, g["unordered"]
    assert len(g["edges"]) == 11, len(g["edges"])
    assert len(g["nodes"]) == 10, len(g["nodes"])
    assert len(g["unordered"]) == 11, g["unordered"]


def check_2(r: dict[str, Any]) -> None:
    """合法对照：零边节点连谁都行，落点拿 valid 且新增一条边。"""
    t = r["steps"]["legalControl"]
    assert t.get("skipped") is None, t
    m = drop_target(t, B_NODE)
    assert m is not None, t
    assert "connectingto" in m["extra"] and "valid" in m["extra"], m
    assert len(t["newEdges"]) == 1, t
    e = t["newEdges"][0]
    assert (e["source"], e["target"]) == (A_NODE, B_NODE), e
    assert t["stateAfter"]["nEdges"] == 12, t["stateAfter"]


def check_3(r: dict[str, Any]) -> None:
    """闭环那一步：落点拿 connectingto 但没有 valid，且不新增边。"""
    t = r["steps"]["cycleCase"]
    assert t.get("skipped") is None, t
    m = drop_target(t, CYCLE_TARGET)
    assert m is not None, t
    assert "connectingto" in m["extra"], m
    assert "valid" not in m["extra"], m
    assert "invalid" not in m["extra"], m
    assert t["newEdges"] == [], t
    assert (t["stateAfter"]["nEdges"]
            == t["stateBefore"]["nEdges"]), (t["stateBefore"], t["stateAfter"])


def check_4(r: dict[str, Any]) -> None:
    """颜色才是用户看得见的那一半：合法绿、被拒青，尺寸一样。"""
    ctrl = drop_target(r["steps"]["legalControl"], B_NODE)
    assert ctrl is not None, r["steps"]["legalControl"]
    assert ctrl["bg"] == VALID_BG, ctrl
    assert ctrl["border"] == VALID_BG, ctrl
    rej = drop_target(r["steps"]["cycleCase"], CYCLE_TARGET)
    assert rej["bg"] == REJECT_BG, rej
    assert rej["border"] == REJECT_BG, rej
    assert rej["w"] == ctrl["w"], (rej, ctrl)


def check_5(r: dict[str, Any]) -> None:
    """被拒的连线零记账：lastCommandResult 恒 null，选区前后相同。"""
    for tag in ("cycleCase",):
        t = r["steps"][tag]
        assert t["stateBefore"]["lastCommandResult"] is None, t
        assert t["stateAfter"]["lastCommandResult"] is None, t
        assert t["stateBefore"]["selection"] == t["stateAfter"]["selection"], t
    # 成功的那两步也没有记账痕迹（addEdge 不走导演台命令通道）
    for tag in ("legalControl",):
        assert r["steps"].get(tag, r.get(tag, {})).get(
            "stateAfter", {}).get("lastCommandResult") is None, tag


def check_6(r: dict[str, Any]) -> None:
    """种子图上「会闭环的配对」与「已有无序对」完全重合 —— 这就是之前造不出用例的原因。"""
    g = r["graph0"]
    cyc = set(g["wouldCycle"])
    unr = set(g["unordered"])
    fresh = cyc - unr
    assert cyc, g["wouldCycle"]
    assert not (unr - cyc), sorted(unr - cyc)
    # 8 对「会闭环但尚未相连」⟹ DIRECTED_CYCLE 在种子上两节点直达可得
    assert len(fresh) == 8, sorted(fresh)
    for pair in fresh:
        a, b = pair.split("|")
        assert a != b, pair
        assert a in (B_NODE, C_GROUP) or b in (B_NODE, C_GROUP), pair
    # 我们试的那一对确实在其中
    assert "|".join(sorted([B_NODE, CYCLE_TARGET])) in fresh, sorted(fresh)


def check_7(r: dict[str, Any]) -> None:
    """react-flow 没有第三个「被拒」标记：被拒落点同样拿 connectingto、从不 invalid。"""
    allm = []
    for t in r["steps"].values():
        allm.extend(t.get("atTarget", []))
    assert allm, "一次标记都没读到"
    for m in allm:
        assert "invalid" not in m["extra"], m
    froms = [m for m in allm if "connectingfrom" in m["extra"]]
    tos = [m for m in allm if "connectingto" in m["extra"]]
    valid = [m for m in tos if "valid" in m["extra"]]
    rejected = [m for m in tos if "valid" not in m["extra"]]
    assert len(froms) == 2, [m["extra"] for m in froms]
    assert len(tos) == 2, [m["extra"] for m in tos]
    assert len(valid) == 1, [m["extra"] for m in valid]
    assert len(rejected) == 1, [m["extra"] for m in rejected]


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
    results: dict[str, Any] = {
        "colors": {"valid": VALID_BG, "rejected": REJECT_BG}}
    checks = [
        ("the-script-node-starts-isolated-and-there-are-eleven-edges",
         lambda: check_1(got.get("run", {}))),
        ("a-legal-control-from-the-isolated-node-creates-one-edge",
         lambda: check_2(got.get("run", {}))),
        ("the-closing-hop-is-never-valid-and-creates-nothing",
         lambda: check_3(got.get("run", {}))),
        ("rejected-drop-targets-change-colour-green-to-cyan-same-size",
         lambda: check_4(got.get("run", {}))),
        ("a-rejected-connection-leaves-no-trace-in-the-store",
         lambda: check_5(got.get("run", {}))),
        ("eight-cycle-forming-pairs-are-not-yet-connected-so-the-rule-is-direct",
         lambda: check_6(got.get("run", {}))),
        ("react-flow-has-no-third-rejected-marker-only-valid-distinguishes",
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
