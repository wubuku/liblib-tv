#!/usr/bin/env python3
"""batch 725 验收：手工连线是通的 —— 724 那三对全是重复对，被 `valid` 正确挡下

## 起点

724 试了两对连线（照抄一条现有连线的配对、以及一对「新」的），都是 11 → 11，
当时记成「手工连线未成立、成因未取证」，并点名下一步该 instrument
`isValidConnection`。本批做了那件事，得到一个更好的答案。

## 决定性读数

### 我挑的配对全是非法的

`libtvGraphConnection.ts:93-100` 的 `hasUnorderedNodePair` 是**无序**判定：

| 724 试的配对 | 已存在的边 | 判定 |
|---|---|---|
| `i-1FQ9tErTcC → b-bTLLuU4w5q` | 同向已有 | `DUPLICATE_NODE_PAIR` |
| `i-1FQ9tErTcC → i-YDfWhFlthe` | 同向已有 | `DUPLICATE_NODE_PAIR` |
| （725 追加的）`g-EFbbHpwq5w → b-bTLLuU4w5q` | 反向已有 | `DUPLICATE_NODE_PAIR`（无序判定） |

**三对全部是「已经连过了」**，规则在正常工作。724 的读数（11→11）本身没错，
**错的是它顺带说的概括**。

### 配对让探针自己算，别手挑

从 store 的边集复算无序对与有向可达，挑出规则允许的配对：
10 枚节点 11 条边 ⟹ **无序对 11 个、规则允许的候选 60 个**。
（`t-9j2MoccxBj`「剧本」一条边都没有，是最干净的一端。）

### 合法配对：全成

| 试法 | 拖法 | 到目标时的 class | 结果 |
|---|---|---|---|
| 正向 | `g-245IDFh8sB`(source) → `g-EFbbHpwq5w`(target) | source 得 `connectingfrom`；target 得 **`connectingto` + `valid`** | **11 → 12** ✓ |
| 正向 | `g-245IDFh8sB`(source) → `t-9j2MoccxBj`(target) | 同上 | **12 → 13** ✓ |
| **反向** | `g-245IDFh8sB`(**target** 柄) → `i-YDfWhFlthe`(**source** 柄) | 落点得 `connectingto` + `valid` | **13 → 14** ✓，且**方向被翻正**为 `i-YDfWhFlthe → g-245IDFh8sB` |

新增边 id 形如 `e-<source>-<target>-<时间戳>`，与 `page.tsx:617-625` 一致。

**反向拖成立** ⟹ `normalizeLibTVConnection`（`libtvGraphConnection.ts:63-76`）
会把「从 target 柄起手」翻正，所以 `INVALID_HANDLE_DIRECTION` 这条拒绝规则
在实际交互里几乎碰不到。

### 关键：判别合法与否的是 `valid` 这一个 class

| 配对 | 到目标时的 class | 是否新增边 |
|---|---|---|
| 合法 | `connectingto` **+ `valid`** | **是** |
| 重复 | `connectingto` **（无 `valid`）** | **否** |

⟹ **`connectingto` 只说明 react-flow 几何上认出了这个落点；
`valid` 才是 app 自己的 `isValidConnection` 给出的裁决。**

**⟹ 应用对「这条能不能连」给了逐目标的实时视觉反馈，没有静默拒绝。**

### 顺带纠正 724 的探针

724 数的是 `.react-flow__handle.valid` 与 `.react-flow__handle.connecting`，
后者**不是 react-flow 的 class 名** —— 真正会变的是
**`connectingfrom`（起手柄）与 `connectingto`（落点柄）**。
所以「valid 恒 0」在重复对上是对的，在合法对上也是 0 —— **因为当时试的全是重复对**。

## 撤回 724 的结论

- **724 判据 7「hand-drawing-an-edge-never-completes-for-either-pair」测的不是那个东西** ——
  它测的是「重复配对被正确拒绝」。读数存活，**概括连同判据名一起作废**。
- 这与 721 撤 720、723 被 724 纠正，是同一类错误的第三次：
  **判据只覆盖了它挑的那几格，概括却越过了它。**

## 不声称

- **不声称画布的连线行为与源站一致**（源站未测）。
- **不声称 60 个候选全部可连** —— 只测了三对；`DIRECTED_CYCLE` 那条规则
  是探针按源码逻辑复算后**排除**掉的候选，没有单独构造用例验证。
- **不声称 `valid` 的视觉呈现已核对**（本批只读 class 名，未比对源站样式）。

## 方法论

1. **「造出来的值必须是控件能接受的值」** —— 这条早已在方法论里，
   本批**又犯了一次**：手挑的配对恰好全是已存在的无序对。
   **正确做法是让探针从 store 复算规则、再自己挑配对。**
2. **规则的「无序」不是细节** —— `hasUnorderedNodePair` 无序判定，
   所以 `A→B` 已存在时 `B→A` 同样被拒。**挑反方向的对照组会被同一条规则挡下，
   看起来像「反向不支持」。**
3. **要判「被规则拒绝」还是「手势没被接住」，就得找一个能同时解释两者的读数** ——
   `valid` 就是那个读数：几何认出了但校验没过 ⟹ 有 `connectingto` 无 `valid`。
4. **两次作废的结论都是同一类**：721（比错对象）、724（挑的值不合法）。
   **作废的成本远低于写进台账后再改。**
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch725-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

GRAPH_JS = r"""() => {
  const c = window.__libtv_store.getState().getActiveCanvas();
  const nodes = c.nodes.map((n) => ({id: n.id, type: n.type}));
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
  const candidates = [];
  for (const s of nodes) for (const t of nodes) {
    if (s.id === t.id) continue;
    if (unordered.has([s.id, t.id].sort().join('|'))) continue;
    if (reachable(t.id, s.id)) continue;
    candidates.push({source: s.id, target: t.id});
  }
  return {nodes, edges, unordered: [...unordered], candidates};
}"""

EDGES_JS = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .edges.map((e) => ({id: e.id, source: e.source, target: e.target}))"""

POSITION_JS = r"""([a, sa, b, sb]) => {
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


def marks(page: Page) -> list[dict[str, Any]]:
    return page.evaluate(r"""() => [...document.querySelectorAll(
        '.react-flow__handle')]
      .map((h) => ({nodeId: h.getAttribute('data-nodeid'),
                    id: h.getAttribute('data-handleid'),
                    extra: h.className.split(' ').filter((c) =>
                      ['connectingfrom', 'connectingto', 'valid',
                       'invalid'].includes(c))}))
      .filter((x) => x.extra.length)""", )


def drag(page: Page, a: str, sa: str, b: str,
         sb: str) -> dict[str, Any]:
    """从 a 的 sa 柄拖到 b 的 sb 柄；返回到达目标时的标记与松手后的边集增量。

    参数顺序永远是 (起手节点, 起手侧, 落点节点, 落点侧)。
    """
    pos = page.evaluate(POSITION_JS, [a, sa, b, sb])
    res: dict[str, Any] = {"plan": [a, sa, b, sb]}
    if not pos["a"] or not pos["b"]:
        res["skipped"] = "拿不到某一侧的 Handle"
        return res
    before = page.evaluate(EDGES_JS)
    page.mouse.move(pos["a"]["x"], pos["a"]["y"])
    page.mouse.down()
    page.wait_for_timeout(300)
    page.mouse.move((pos["a"]["x"] + pos["b"]["x"]) // 2,
                    (pos["a"]["y"] + pos["b"]["y"]) // 2, steps=12)
    page.wait_for_timeout(300)
    page.mouse.move(pos["b"]["x"], pos["b"]["y"], steps=12)
    page.wait_for_timeout(500)
    res["atTarget"] = marks(page)
    res["connExists"] = page.evaluate(
        "() => !!document.querySelector('.react-flow__connection')")
    page.mouse.up()
    page.wait_for_timeout(900)
    res["afterUp"] = marks(page)
    after = page.evaluate(EDGES_JS)
    ids = {e["id"] for e in before}
    res["newEdges"] = [e for e in after if e["id"] not in ids]
    res["nBefore"] = len(before)
    res["nAfter"] = len(after)
    return res


def fit(page: Page) -> None:
    page.evaluate("() => document.querySelector"
                  "('[data-viewport-menu-trigger=\"zoom\"]').click()")
    page.wait_for_timeout(400)
    page.evaluate("() => { const b = document.querySelector"
                  "('[data-zoom-action=\"fit\"]'); if (b) b.click(); }")
    page.wait_for_timeout(900)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_200)
    fit(page)


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {}
    open_canvas(page)
    g = page.evaluate(GRAPH_JS)
    r["graph0"] = g
    r["handleCount"] = page.evaluate(
        "() => document.querySelectorAll('.react-flow__handle').length")

    cands = g["candidates"]
    r["nCandidates"] = len(cands)
    trials: dict[str, Any] = {}
    used: set[str] = set()

    def pick_free() -> dict[str, Any]:
        """挑一条当前仍未连过的无序对，且彼此不撞。"""
        cur = page.evaluate(GRAPH_JS)
        for c in cur["candidates"]:
            key = "|".join(sorted([c["source"], c["target"]]))
            if key in used:
                continue
            used.add(key)
            return c
        raise AssertionError("没有可用的候选配对了")

    c1 = pick_free()
    trials["forward1"] = drag(page, c1["source"], "right", c1["target"], "left")
    c2 = pick_free()
    trials["forward2"] = drag(page, c2["source"], "right", c2["target"], "left")
    c3 = pick_free()
    trials["reverseFromTargetHandle"] = drag(
        page, c3["source"], "left", c3["target"], "right")
    dup = page.evaluate(EDGES_JS)[0]
    trials["duplicateControl"] = drag(
        page, dup["source"], "right", dup["target"], "left")
    r["picked"] = {"forward1": c1, "forward2": c2, "reverse": c3,
                   "duplicateControl": {"source": dup["source"],
                                        "target": dup["target"]}}
    r["trials"] = trials
    page.close()
    return r


def _has(t: dict[str, Any], node: str, handle: str, cls: str) -> bool:
    return any(x["nodeId"] == node and x["id"] == handle and cls in x["extra"]
               for x in t.get("atTarget", []))


def check_1(r: dict[str, Any]) -> None:
    """探针自证配对合法：候选从 store 复算，重复的一律不选。"""
    g = r["graph0"]
    assert len(g["nodes"]) == 10 and len(g["edges"]) == 11, (
        len(g["nodes"]), len(g["edges"]))
    assert len(g["unordered"]) == 11, g["unordered"]
    assert r["handleCount"] == 20, r["handleCount"]
    p = r["picked"]
    for tag in ("forward1", "forward2", "reverse"):
        s, t = p[tag]["source"], p[tag]["target"]
        assert "|".join(sorted([s, t])) not in g["unordered"], (tag, s, t)
        assert s != t, tag
    # 剧本节点一条边都没有，是最干净的一端
    assert not any("t-9j2MoccxBj" in u for u in g["unordered"]), g["unordered"]


def check_2(r: dict[str, Any]) -> None:
    """合法配对拖到目标时：起手柄 connectingfrom、落点柄 connectingto 且 valid。"""
    for tag in ("forward1", "forward2"):
        t, p = r["trials"][tag], r["picked"][tag]
        assert t.get("skipped") is None, (tag, t)
        assert t["connExists"] is True, (tag, t)
        assert _has(t, p["source"], "source", "connectingfrom"), (tag, t)
        assert _has(t, p["target"], "target", "connectingto"), (tag, t)
        assert _has(t, p["target"], "target", "valid"), (tag, t)
        assert not _has(t, p["target"], "target", "invalid"), (tag, t)


def check_3(r: dict[str, Any]) -> None:
    """合法配对松手后新增一条边，id 形如 e-<source>-<target>-<ts>，方向与拖拽一致。"""
    for tag in ("forward1", "forward2"):
        t, p = r["trials"][tag], r["picked"][tag]
        assert len(t["newEdges"]) == 1, (tag, t)
        e = t["newEdges"][0]
        assert (e["source"], e["target"]) == (p["source"], p["target"]), (tag, e)
        assert re.match(r"^e-%s-%s-\d+$" % (re.escape(e["source"]),
                                            re.escape(e["target"])), e["id"]), e
        assert t["nAfter"] == t["nBefore"] + 1, (tag, t)
        assert t["afterUp"] == [], (tag, t["afterUp"])


def check_4(r: dict[str, Any]) -> None:
    """从 target 柄反向起手也能连，且方向被 normalize 翻正。"""
    t, p = r["trials"]["reverseFromTargetHandle"], r["picked"]["reverse"]
    assert t.get("skipped") is None, t
    assert _has(t, p["source"], "target", "connectingfrom"), t
    assert _has(t, p["target"], "source", "connectingto"), t
    assert _has(t, p["target"], "source", "valid"), t
    assert len(t["newEdges"]) == 1, t
    e = t["newEdges"][0]
    # 翻正：起手的是 target 柄，所以边方向应当反过来
    assert (e["source"], e["target"]) == (p["target"], p["source"]), (p, e)


def check_5(r: dict[str, Any]) -> None:
    """对照组：重复配对到目标时只有 connectingto、没有 valid，且不新增边。"""
    t, p = r["trials"]["duplicateControl"], r["picked"]["duplicateControl"]
    assert t.get("skipped") is None, t
    assert "|".join(sorted([p["source"], p["target"]])) in r["graph0"]["unordered"]
    assert _has(t, p["source"], "source", "connectingfrom"), t
    assert _has(t, p["target"], "target", "connectingto"), t
    assert not _has(t, p["target"], "target", "valid"), t
    assert t["newEdges"] == [], t
    assert t["nAfter"] == t["nBefore"], t


def check_6(r: dict[str, Any]) -> None:
    """撤回 724：`connecting` 从来不是 react-flow 的 class，变的是这两个。"""
    allm = [m for t in r["trials"].values() for m in t.get("atTarget", [])]
    seen = {c for m in allm for c in m["extra"]}
    assert "connectingfrom" in seen, seen
    assert "connectingto" in seen, seen
    assert "valid" in seen, seen
    assert "connecting" not in seen, seen
    assert "invalid" not in seen, seen


def check_7(r: dict[str, Any]) -> None:
    """`valid` 是唯一的判别位：几何认出但校验没过 ⟹ 有 connectingto 无 valid。"""
    t = r["trials"]
    for tag in ("forward1", "forward2", "reverseFromTargetHandle"):
        has_valid = any("valid" in m["extra"] for m in t[tag]["atTarget"])
        assert has_valid is True, (tag, t[tag]["atTarget"])
        assert len(t[tag]["newEdges"]) == 1, tag
    dup = t["duplicateControl"]
    has_valid = any("valid" in m["extra"] for m in dup["atTarget"])
    assert has_valid is False, dup["atTarget"]
    assert dup["newEdges"] == [], dup


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
        ("the-picked-pairs-are-proven-free-by-recomputing-the-rule-from-store",
         lambda: check_1(got.get("run", {}))),
        ("a-legal-pair-marks-the-drop-target-connectingto-and-valid",
         lambda: check_2(got.get("run", {}))),
        ("a-legal-pair-creates-exactly-one-edge-with-the-documented-id-shape",
         lambda: check_3(got.get("run", {}))),
        ("dragging-from-a-target-handle-works-and-the-direction-is-normalized",
         lambda: check_4(got.get("run", {}))),
        ("a-duplicate-pair-reaches-the-target-but-is-never-marked-valid",
         lambda: check_5(got.get("run", {}))),
        ("connecting-is-never-a-react-flow-class-only-from-and-to-are",
         lambda: check_6(got.get("run", {}))),
        ("valid-is-the-only-discriminator-between-accepted-and-rejected",
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
