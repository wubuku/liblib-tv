#!/usr/bin/env python3
"""batch 728 验收：script-v2 运行时确认两个把手无名 ⟹ 该类型连不出任何边

## 起点

727 的完成度表里只剩一个「⚠️需空画布」：**`INVALID_HANDLE_DIRECTION`**。
本批把那一步真做了。

## 破坏与恢复

- **破坏**：`Shift` + 左键在 pane 上框选全部 10 枚 → 按 `Delete`
  （`selectionOnDrag={false}` 且未改 `selectionKeyCode` ⟹ react-flow 默认
  `Shift` 为框选键；这是用户能做的正常操作）
- **恢复**：`page.reload()` —— 721 已实测 `canvasStore.ts` 零持久化写入，
  画布每次加载都回到 10 枚种子节点 ⟹ **破坏在会话内完全可逆**，
  本批把它写成一条判据

## 决定性读数

### ① 框选与清空

| 步骤 | 读数 |
|---|---|
| 框选 | `nodeIds` 10 枚全中 |
| `Delete` | **nodes 10 → 0**、**edges 11 → 0** |

### ② 空画布的 4 枚芯片

`story-script`（故事脚本生成）/ `character-turnaround`（角色三视图）/
`reference-to-video`（全能参考生视频）/ `audio-to-video`（音频生视频）。

### ③ 「故事脚本生成」成对造节点，且二者间无连线

| 读数 | 值 |
|---|---|
| 新增节点 | **2**：`text-<ts>-<rand>` + `script-v2-<ts>-<rand>` |
| 新增边 | **0** |

⟹ 与 `canvasStore.ts:1272` 的注释一致：「成对创建预填剧本的 text 节点与
script-v2（脚本生成器）节点，**二者间无连线**；单条历史（原子动作）」。

### ④ `script-v2` 的两个把手运行时确认为无名

| 把手 | `data-handleid` | 宽 |
|---|---|---|
| 左（target 位） | **`null`** | 9.81 |
| 右（source 位） | **`null`** | 9.81 |

⟹ 727 的静态普查结论在运行时得到确认。

### ⑤ 从它起手：连接注册了，但落点永远拿不到 `valid`

拖 `script-v2`(右把手) → `text`(左把手)：

| 读数 | 值 |
|---|---|
| 起手柄 | `connectingfrom`，**`id: null`** |
| 落点柄 | `connectingto`，**无 `valid`**，底色 **`rgb(9, 202, 245)` 青** |
| 新增边 | **0** |

⟹ `normalizeLibTVConnection` 的 `INVALID_HANDLE_DIRECTION`
要求翻正后必须是 `"source"` / `"target"`，而这里的 handle id 是 `null` ⟹ 拒绝。

**⟹ `script-v2` 这个节点类型在 UI 上连不出任何边。**
而且它在**两个方向上都会撞同一条规则** —— 无论自己当 source 还是当 target，
它的 handle id 都是 `null`。

## 不声称

- **不声称第二次尝试（text → script-v2）的读数** ——
  那一次 `.react-flow__handle` 的连接态标记**一个都没出现**（marks 为空），
  说明手势根本没进入连接态，原因未取证；**不作为结论依据**。
  已确认的方向是 script-v2 起手那一侧。
- **不声称源站有没有 script-v2 这种节点**（源站未测）。
- **不声称这是「唯一连不出的类型」** —— 只测了这一种。

## 新增待拍板

1. **`ScriptV2Node` 的两个 `<Handle>` 缺 `id`** ——
   照 `TextNode.tsx:77-78` 的 batch 355 做法补 `id="target"/"source"`
   （**需改 `src/`，等授权**）。**在本批的读数下，补之前该类型完全无法连线。**
2. **「故事脚本生成」造出的两个节点之间没有连线** ——
   它们是流程上的先后关系还是并列关系？UI 上无从判断，未取证。

## 方法论

1. **「到不了」要真的走一遍才能定性** —— 727 用静态普查 + 可达性分析
   给出「需要空画布」，本批走完之后结论从「到不了」变成
   **「到了，而且规则确实按预期拒它」**：两件事不能混为一谈。
2. **破坏性操作要先写好恢复路径，再把它变成判据** ——
   `page.reload()` 能恢复这件事本身值得断言（它同时复核了 721 的结论）。
3. **框选的起点必须验证命中的是 pane** —— 我第一版从 (30, 40) 起手，
   那儿是顶栏；按节点包围盒外扩 30px 计算并断言 `startIsPane` 才选中。
4. **同一次实验里失败的那一格不要硬解释** ——
   「text → script-v2」marks 为空，我只记「未取证」，不编一个原因。
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch728-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150
REJECT_BG = "rgb(9, 202, 245)"

NODES = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .nodes.map((n) => ({id: n.id, type: n.type}))"""

EDGES = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .edges.map((e) => ({id: e.id, source: e.source, target: e.target}))"""

SELECTION = r"""() => window.__libtv_store.getState().getSelectionSnapshot()"""

CHIPS = r"""() => [...document.querySelectorAll('[data-canvas-empty-chip]')]
  .map((b) => ({id: b.getAttribute('data-canvas-empty-chip'),
                text: (b.textContent || '').trim().slice(0, 24)}))"""

EMPTY_STATE = r"""() => {
  const chips = [...document.querySelectorAll('[data-canvas-empty-chip]')];
  const host = chips[0] ? chips[0].closest('div') : null;
  return {chipCount: chips.length,
          emptyVisible: chips.length > 0,
          hostText: host ? (host.textContent || '').trim().slice(0, 60) : null};
}"""

HANDLES = r"""(ids) => ids.map((id) => {
  const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!n) return {id: id, missing: true};
  const hs = Array.from(n.querySelectorAll('.react-flow__handle'));
  return {
    id: id,
    nHandles: hs.length,
    handles: hs.map((h) => ({
      handleId: h.getAttribute('data-handleid'),
      w: Math.round(h.getBoundingClientRect().width * 100) / 100
    }))
  };
})"""

MARKS = r"""() => [...document.querySelectorAll('.react-flow__handle')]
  .map((h) => ({nodeId: h.getAttribute('data-nodeid'),
                id: h.getAttribute('data-handleid'),
                extra: h.className.split(' ').filter((c) =>
                  ['connectingfrom','connectingto','valid','invalid'].includes(c)),
                bg: getComputedStyle(h).backgroundColor}))
  .filter((x) => x.extra.length)"""

POS = r"""([a, sa, b, sb]) => {
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

MARQUEE_JS = r"""() => {
  const rs = [...document.querySelectorAll('.react-flow__node')]
    .map((n) => n.getBoundingClientRect());
  const minX = Math.min(...rs.map((r) => r.x));
  const minY = Math.min(...rs.map((r) => r.y));
  const maxX = Math.max(...rs.map((r) => r.right));
  const maxY = Math.max(...rs.map((r) => r.bottom));
  const sx = Math.max(4, Math.floor(minX) - 30);
  const sy = Math.max(60, Math.floor(minY) - 30);
  const ex = Math.min(window.innerWidth - 4, Math.ceil(maxX) + 30);
  const ey = Math.min(window.innerHeight - 120, Math.ceil(maxY) + 30);
  const hit = document.elementFromPoint(sx, sy);
  return {sx, sy, ex, ey,
          startIsPane: !!(hit && hit.classList.contains('react-flow__pane'))};
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


def load(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_200)
    fit(page)


def drag(page: Page, a: str, sa: str, b: str, sb: str) -> dict[str, Any]:
    """参数顺序恒为 (起手节点, 起手侧, 落点节点, 落点侧)。"""
    pos = page.evaluate(POS, [a, sa, b, sb])
    res: dict[str, Any] = {"plan": [a, sa, b, sb]}
    if not pos["a"] or not pos["b"]:
        res["skipped"] = "拿不到某一侧的 Handle"
        return res
    before = page.evaluate(EDGES)
    page.mouse.move(pos["a"]["x"], pos["a"]["y"])
    page.mouse.down()
    page.wait_for_timeout(300)
    page.mouse.move((pos["a"]["x"] + pos["b"]["x"]) // 2,
                    (pos["a"]["y"] + pos["b"]["y"]) // 2, steps=12)
    page.wait_for_timeout(300)
    page.mouse.move(pos["b"]["x"], pos["b"]["y"], steps=12)
    page.wait_for_timeout(500)
    res["atTarget"] = page.evaluate(MARKS)
    page.mouse.up()
    page.wait_for_timeout(900)
    after = page.evaluate(EDGES)
    ids = {e["id"] for e in before}
    res["newEdges"] = [e for e in after if e["id"] not in ids]
    return res


def static_facts() -> dict[str, Any]:
    v2 = (ROOT / "src/components/nodes/ScriptV2Node.tsx").read_text(
        encoding="utf-8")
    txt = (ROOT / "src/components/nodes/TextNode.tsx").read_text(
        encoding="utf-8")
    conn = (ROOT / "src/lib/libtvGraphConnection.ts").read_text(encoding="utf-8")
    return {
        "v2Handles": re.findall(r"<Handle\b[^>]*?/?>", v2, re.S),
        "textHandles": re.findall(r"<Handle\b[^>]*?/?>", txt, re.S),
        "requiresNamedHandle": 'sourceHandleId !== "source"' in conn,
    }


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {"static": static_facts()}
    load(page)
    r["nodes0"] = page.evaluate(NODES)
    r["edges0"] = page.evaluate(EDGES)

    # ① 框选 + Delete
    pl = page.evaluate(MARQUEE_JS)
    r["marqueePlan"] = pl
    assert pl["startIsPane"] is True, pl
    page.keyboard.down("Shift")
    page.mouse.move(pl["sx"], pl["sy"])
    page.mouse.down()
    page.mouse.move(pl["ex"], pl["ey"], steps=25)
    page.wait_for_timeout(500)
    page.mouse.up()
    page.wait_for_timeout(700)
    page.keyboard.up("Shift")
    page.wait_for_timeout(400)
    r["selection"] = page.evaluate(SELECTION)
    page.keyboard.press("Delete")
    page.wait_for_timeout(900)
    r["nodesAfterDelete"] = page.evaluate(NODES)
    r["edgesAfterDelete"] = page.evaluate(EDGES)

    # ② 空画布
    r["emptyState"] = page.evaluate(EMPTY_STATE)
    r["chips"] = page.evaluate(CHIPS)
    r["chipClicked"] = page.evaluate("""() => {
      const b = document.querySelector('[data-canvas-empty-chip="story-script"]');
      if (!b) return false; b.click(); return true;}""")
    page.wait_for_timeout(1_400)
    r["nodesAfterChip"] = page.evaluate(NODES)
    r["edgesAfterChip"] = page.evaluate(EDGES)

    # ③ 把手与连线
    v2 = [n for n in r["nodesAfterChip"] if n["type"] == "script-v2"]
    r["v2Id"] = v2[0]["id"] if v2 else None
    r["textId"] = next((n["id"] for n in r["nodesAfterChip"]
                        if n["type"] == "text"), None)
    if v2:
        fit(page)
        r["v2Handles"] = page.evaluate(HANDLES, [v2[0]["id"]])
        if r["textId"]:
            r["dragFromV2"] = drag(page, v2[0]["id"], "right",
                                   r["textId"], "left")
            r["dragTextToV2"] = drag(page, r["textId"], "right",
                                     v2[0]["id"], "left")
            r["edgesFinal"] = page.evaluate(EDGES)

    # ④ 恢复
    page.reload(wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.wait_for_timeout(1_200)
    r["nodesAfterReload"] = page.evaluate(NODES)
    r["edgesAfterReload"] = page.evaluate(EDGES)
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """框选全部 + Delete 清空：节点 10→0、边 11→0。"""
    assert len(r["nodes0"]) == 10, r["nodes0"]
    assert len(r["edges0"]) == 11, r["edges0"]
    assert r["marqueePlan"]["startIsPane"] is True, r["marqueePlan"]
    assert len(r["selection"]["nodeIds"]) == 10, r["selection"]
    assert r["nodesAfterDelete"] == [], r["nodesAfterDelete"]
    assert r["edgesAfterDelete"] == [], r["edgesAfterDelete"]


def check_2(r: dict[str, Any]) -> None:
    """空画布出现，四枚芯片逐一枚举。"""
    assert r["emptyState"]["emptyVisible"] is True, r["emptyState"]
    assert r["emptyState"]["chipCount"] == 4, r["emptyState"]
    ids = [c["id"] for c in r["chips"]]
    assert ids == ["story-script", "character-turnaround",
                   "reference-to-video", "audio-to-video"], ids


def check_3(r: dict[str, Any]) -> None:
    """「故事脚本生成」成对造 text + script-v2，且二者间无连线。"""
    assert r["chipClicked"] is True, r["chipClicked"]
    types = sorted(n["type"] for n in r["nodesAfterChip"])
    assert types == ["script-v2", "text"], r["nodesAfterChip"]
    assert len(r["nodesAfterChip"]) == 2, r["nodesAfterChip"]
    assert r["edgesAfterChip"] == [], r["edgesAfterChip"]


def check_4(r: dict[str, Any]) -> None:
    """script-v2 的两个把手 data-handleid 均为 null（运行时确认 727 的静态结论）。"""
    assert r["v2Id"] is not None, r["nodesAfterChip"]
    h = r["v2Handles"][0]
    assert h.get("missing") is not True, h
    assert h["nHandles"] == 2, h
    assert [x["handleId"] for x in h["handles"]] == [None, None], h
    st = r["static"]
    assert all('id="' not in t for t in st["v2Handles"]), st["v2Handles"]
    assert all('id="' in t for t in st["textHandles"]), st["textHandles"]


def check_5(r: dict[str, Any]) -> None:
    """从 script-v2 起手：连接注册、落点永远无 valid、青色、零新增边。"""
    d = r["dragFromV2"]
    assert d.get("skipped") is None, d
    froms = [m for m in d["atTarget"] if "connectingfrom" in m["extra"]]
    tos = [m for m in d["atTarget"] if "connectingto" in m["extra"]]
    assert len(froms) == 1 and froms[0]["id"] is None, d["atTarget"]
    assert froms[0]["nodeId"] == r["v2Id"], d["atTarget"]
    assert len(tos) == 1 and tos[0]["nodeId"] == r["textId"], d["atTarget"]
    assert "valid" not in tos[0]["extra"], tos
    assert tos[0]["bg"] == REJECT_BG, tos
    assert d["newEdges"] == [], d
    assert r["static"]["requiresNamedHandle"] is True, r["static"]


def check_6(r: dict[str, Any]) -> None:
    """第二次尝试（text → script-v2）没有进入连接态 —— 记为未取证，不当结论。"""
    d = r.get("dragTextToV2") or {}
    assert d.get("skipped") is None, d
    assert d["newEdges"] == [], d
    # 明确记录它「没有连接态标记」，供读者自行判断这条读数能用到什么程度
    r["reverseMarksEmpty"] = (d["atTarget"] == [])


def check_7(r: dict[str, Any]) -> None:
    """破坏可逆：刷新后回到 10 枚种子节点、11 条边（同时复核 721）。"""
    assert len(r["nodesAfterReload"]) == 10, len(r["nodesAfterReload"])
    assert len(r["edgesAfterReload"]) == 11, len(r["edgesAfterReload"])
    assert r["edgesFinal"] == [], r["edgesFinal"]


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
        ("shift-marquee-then-delete-empties-the-canvas",
         lambda: check_1(got.get("run", {}))),
        ("the-empty-canvas-offers-four-chips",
         lambda: check_2(got.get("run", {}))),
        ("story-script-creates-a-text-plus-script-v2-pair-with-no-edge-between",
         lambda: check_3(got.get("run", {}))),
        ("both-script-v2-handles-are-null-at-runtime",
         lambda: check_4(got.get("run", {}))),
        ("dragging-from-script-v2-registers-but-is-never-valid",
         lambda: check_5(got.get("run", {}))),
        ("the-reverse-attempt-recorded-as-unmeasured-not-as-a-conclusion",
         lambda: check_6(got.get("run", {}))),
        ("the-destruction-is-reversible-by-reload",
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
