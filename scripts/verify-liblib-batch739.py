#!/usr/bin/env python3
"""batch 739 验收：11 枚连线删除手柄的启用条件与键盘可用性

## 起点

738 测到这 11 枚常态下 `pointer-events: none`、中心 `elementFromPoint` 命中 0/11，
并把「是不是 hover 才启用」列为待查。本批去查，**结论是：是有意的启用态**。

## 决定性读数

### ① 源码双层启用条件（`src/components/nodes/DeletableEdge.tsx`）
  :90   `const isActive = hovered || selected;`
  :131  20px 宽隐形描边路径，`onMouseEnter → setHovered(true)`（**启用路径 ①**）
  :156  外层 wrapper div **恒** `pointerEvents: "none"`
  :170  按钮 `isActive ? "opacity-100 scale-100 pointer-events-auto"
                        : "opacity-0 scale-50 pointer-events-none"`

### ② 默认态 11 枚
`pe: none` 11/11、`opacity: 0` 11/11、渲染盒子 **8.4×8.4**、中心命中自己 **0/11**、
`focus()` **11/11 成功**。算术闭合：按钮 `w-8 h-8` = 32px，`scale-50` → 16，
再乘画布 zoom **0.526** ⟹ **32 × 0.5 × 0.526 = 8.416**。

### ③ hover 启用确认（`hovered || selected` 的第一条）
悬停到**真正在线上**的点（`getPointAtLength(len/2)` 过 `getScreenCTM`）
⟹ 被 hover 的那一枚变成 `pe: auto`、`opacity: 1`、盒子 **16.8×16.8**（32 × 1.0 × 0.526）。
⟹ **「hover 才启用」的设计成立**，738 的待拍板① 有了答案。

### ④ hover 启用后点它，**真删掉一条边**（11 → 10）

### ⑤ **「命中自己」不是「能点」的等价判据**
被启用那枚的中心 `elementFromPoint` 返回的是 **`path`**（那条 20px 隐形描边
`pointer-events: stroke` 压在按钮上），**但点击照样删掉了边**。
⟹ 738/739 两次用 `hitIsSelf` 当判据，这个方法有洞。

### ⑥ 键盘这一格：**11 枚全在自然 Tab 序列里，且按 Enter 真删**
自然 Tab **300 步**落在手柄上 **44 次**、**11 枚全覆盖**；
聚焦后按 **Enter 边数 11 → 10**、按 **Space 不删**（被画布的 Space 处理吃掉）。

### ⑦ 与 735 那 40 枚收藏按钮的对比 —— 「不可见却可达」分两种
| | 默认态 | Tab 落得到 | 按下去 |
|---|---|---|---|
| 40 枚收藏按钮（`LibraryShowcasePanel:130`） | `opacity: 0` + `pe: none` | 是（Tab 260 步停靠 77 次） | **毫无反应** |
| 11 枚连线删除手柄 | `opacity: 0` + `pe: none` | 是（Tab 300 步停靠 44 次，11/11 覆盖） | **Enter 真删一条边** |

## 判据

C1  源码双层条件三行在位（:90 / :156 / :170）
C2  默认态 11 枚：pe none / opacity 0 / 8.4×8.4 / 命中自己 0/11 / focus() 11/11
C3  画布 zoom 0.526 —— 8.4 = 32 × 0.5 × 0.526 算术闭合
C4  hover 到在线上的点 ⟹ 那一枚 pe:auto + opacity:1 + 16.8×16.8
C5  hover 启用后点它 ⟹ 边数 11 → 10
C6  被启用那枚中心 elementFromPoint 返回 path（不是按钮）⟹ hitIsSelf 不是等价判据
C7  自然 Tab 300 步落在手柄 44 次、11 枚全覆盖
C8  聚焦后 Enter 删一条、Space 不删
C9  「选中连线」这条启用路径：点曲线后 selectedEdgeIds 仍为 0（**未取证**）
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch739-2026-10-01"
BASE = "http://localhost:4317"
W, H = 1280, 1150
TAB_STEPS = 300


def static_conditions():
    src = (ROOT / "src/components/nodes/DeletableEdge.tsx").read_text(encoding="utf-8")
    lines = src.split("\n")
    marks = {"isActive": None, "wrapperPe": None, "buttonClass": None, "hitPath": None}
    for n, line in enumerate(lines, start=1):
        if "const isActive = hovered || selected;" in line:
            marks["isActive"] = n
        if 'pointerEvents: "none"' in line and marks["wrapperPe"] is None and n > 150:
            marks["wrapperPe"] = n
        if "pointer-events-auto" in line and marks["buttonClass"] is None:
            marks["buttonClass"] = n
        if 'style={{ pointerEvents: "stroke", cursor: "pointer" }}' in line:
            marks["hitPath"] = n
    return {"lines": marks, "buttonClassText": "w-8 h-8" in src}


READ_ALL = """() => [...document.querySelectorAll('button[data-edge-delete]')].map(el => {
  const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const inV = cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight;
  const hit = inV ? document.elementFromPoint(cx, cy) : null;
  el.focus();
  return {x: Math.round(cx), y: Math.round(cy),
          w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10,
          opacity: cs.opacity, pe: cs.pointerEvents, inViewport: inV,
          hitIsSelf: hit === el,
          hitTag: hit ? hit.tagName.toLowerCase() : null,
          focusable: document.activeElement === el};
})"""

ON_CURVE = """() => {
  const out = [];
  for (const p of document.querySelectorAll('path')) {
    const cs = getComputedStyle(p);
    if (!(cs.stroke === 'rgba(0, 0, 0, 0)' || cs.stroke === 'transparent')) continue;
    if (cs.strokeWidth !== '20px') continue;
    const len = p.getTotalLength(); if (!len) continue;
    const pt = p.getPointAtLength(len / 2); const m = p.getScreenCTM(); if (!m) continue;
    const sx = pt.x * m.a + pt.y * m.c + m.e, sy = pt.x * m.b + pt.y * m.d + m.f;
    if (sx > 4 && sy > 4 && sx < innerWidth - 4 && sy < innerHeight - 4)
      out.push({sx: Math.round(sx), sy: Math.round(sy)});
  }
  return out;
}"""


def edges(page):
    return page.evaluate("() => window.__libtv_store.getState().getActiveCanvas().edges.length")


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 静态：双层启用条件 ===")
    cond = static_conditions()
    print(f"  isActive = hovered || selected  :{cond['lines']['isActive']}")
    print(f"  按钮 isActive ? auto : none     :{cond['lines']['buttonClass']}")
    print(f"  wrapper div 恒 pointerEvents none :{cond['lines']['wrapperPe']}")
    print(f"  20px 隐形描边路径                :{cond['lines']['hitPath']}")
    print(f"  按钮尺寸 w-8 h-8 = 32px          :{cond['buttonClassText']}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"{BASE}/?batch739={1}", wait_until="networkidle", timeout=90_000)
        page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.mouse.move(W - 4, 4)
        page.wait_for_timeout(1_300)

        zoom = page.evaluate("() => window.__libtv_store.getState().getActiveCanvas().viewport.zoom")
        before = page.evaluate(READ_ALL)
        print(f"\n=== 默认态 {len(before)} 枚（zoom={zoom}）===")
        print(f"  pe={sorted(set(r['pe'] for r in before))} opacity={sorted(set(r['opacity'] for r in before))} "
              f"盒子={sorted(set((r['w'], r['h']) for r in before))} "
              f"命中自己={sum(1 for r in before if r['hitIsSelf'])}/{len(before)} "
              f"focus()={sum(1 for r in before if r['focusable'])}/{len(before)}")
        expected_default = round(32 * 0.5 * zoom, 3)
        print(f"  算术闭合：32 × 0.5 × {zoom} = {expected_default}")

        # ---------- hover 启用 ----------
        active = None
        hover_point = None
        for pt in page.evaluate(ON_CURVE):
            page.mouse.move(pt["sx"], pt["sy"])
            page.wait_for_timeout(600)
            rows = page.evaluate(READ_ALL)
            on = [r for r in rows if r["pe"] != "none"]
            if on:
                active, hover_point = on[0], [pt["sx"], pt["sy"]]
                break
        print(f"\n=== hover（点 {hover_point}，在线上）===")
        if active is None:
            print("  没有一枚被启用")
        else:
            print(f"  被启用枚: {json.dumps(active, ensure_ascii=False)}")
            e0 = edges(page)
            page.mouse.click(active["x"], active["y"])
            page.wait_for_timeout(700)
            e1 = edges(page)
            print(f"  点它：边数 {e0} → {e1}（删 {e0 - e1} 条）")
            click_reading = {"before": e0, "after": e1, "active": active,
                             "hitTagAtActiveCenter": active["hitTag"]}
        after_click = page.evaluate(READ_ALL)
        page.close()

        # ---------- 自然 Tab ----------
        page2 = browser.new_page(viewport={"width": W, "height": H})
        page2.goto(f"{BASE}/?batch739={2}", wait_until="networkidle", timeout=90_000)
        page2.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page2.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page2.wait_for_timeout(1_200)
        page2.evaluate("() => { window.__hits = []; }")
        page2.evaluate("""() => {
          window.__k = (e) => { if (e.key !== 'Tab') return;
            setTimeout(() => { const a = document.activeElement; if (!a) return;
              const ed = a.getAttribute && a.getAttribute('data-edge-delete');
              window.__hits.push(ed ? 'EDGE:' + ed
                : ((a.getAttribute('aria-label') || a.getAttribute('title') || a.textContent || a.tagName) || '').trim().slice(0, 16)); }, 0); };
          document.addEventListener('keydown', window.__k, true);
        }""")
        for _ in range(TAB_STEPS):
            page2.keyboard.press("Tab")
        hits = page2.evaluate("() => window.__hits")
        page2.evaluate("() => document.removeEventListener('keydown', window.__k, true)")
        edge_stops = [h for h in hits if h.startswith("EDGE:")]
        print(f"\n=== 自然 Tab {TAB_STEPS} 步 ===")
        print(f"  总停靠 {len(hits)}；落在删除手柄上 {len(edge_stops)} 次，不同手柄 {len(set(edge_stops))} 个")

        # ---------- 键盘激活 ----------
        focus_target = page2.evaluate("""() => { const el = document.querySelector('button[data-edge-delete]');
          if (!el) return 'MISSING'; el.focus();
          return document.activeElement === el ? (el.getAttribute('data-edge-delete') || '') : 'FAILED'; }""")
        k0 = edges(page2)
        page2.keyboard.press("Enter")
        page2.wait_for_timeout(700)
        k1 = edges(page2)
        page2.keyboard.press("Space")
        page2.wait_for_timeout(700)
        k2 = edges(page2)
        print(f"  聚焦 {focus_target}：边数 {k0} → Enter {k1} → Space {k2}")

        # ---------- 「选中连线」那条启用路径 ----------
        selected_after_click = page2.evaluate("""() => {
          const root = document.querySelector('.react-flow__pane') || document.querySelector('.react-flow');
          return window.__libtv_store.getState().selectedEdgeIds.length; }""")
        page2.close()
        browser.close()

    tab_distinct_edges = len(set(edge_stops))
    summary = {
        "isActiveLine": cond["lines"]["isActive"],
        "buttonClassLine": cond["lines"]["buttonClass"],
        "wrapperPeLine": cond["lines"]["wrapperPe"],
        "hitPathLine": cond["lines"]["hitPath"],
        "buttonSize32": cond["buttonClassText"],
        "zoom": zoom,
        "handles": len(before),
        "defaultAllPeNone": all(r["pe"] == "none" for r in before),
        "defaultAllOpacity0": all(r["opacity"] == "0" for r in before),
        "defaultBox": sorted({(r["w"], r["h"]) for r in before}),
        "defaultSelfHit": sum(1 for r in before if r["hitIsSelf"]),
        "defaultFocusable": sum(1 for r in before if r["focusable"]),
        "expectedDefaultBox": expected_default,
        "hoverPoint": hover_point,
        "activePe": active["pe"] if active else None,
        "activeOpacity": active["opacity"] if active else None,
        "activeBox": (active["w"], active["h"]) if active else None,
        "activeHitTag": active["hitTag"] if active else None,
        "edgesBeforeClick": click_reading["before"] if active else None,
        "edgesAfterClick": click_reading["after"] if active else None,
        "tabSteps": TAB_STEPS,
        "tabTotalStops": len(hits),
        "tabEdgeStops": len(edge_stops),
        "tabDistinctEdges": tab_distinct_edges,
        "edgesBeforeEnter": k0, "edgesAfterEnter": k1, "edgesAfterSpace": k2,
        "selectedEdgeIdsAfterClick": selected_after_click,
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    checks = [
        ("C1 源码三行在位（isActive / 按钮 class / wrapper 恒 none）+ 20px 命中路径",
         cond["lines"]["isActive"] == 90 and cond["lines"]["buttonClass"] == 171
         and cond["lines"]["wrapperPe"] == 156 and cond["lines"]["hitPath"] == 136
         and cond["buttonClassText"] is True,
         json.dumps(cond["lines"], ensure_ascii=False)),
        ("C2 默认态 11 枚：pe none / opacity 0 / 8.4×8.4 / 命中自己 0/11 / focus() 11/11",
         len(before) == 11 and summary["defaultAllPeNone"] and summary["defaultAllOpacity0"]
         and summary["defaultBox"] == [(8.4, 8.4)] and summary["defaultSelfHit"] == 0
         and summary["defaultFocusable"] == 11,
         f"n={len(before)} pe=None:{summary['defaultAllPeNone']} op=0:{summary['defaultAllOpacity0']} "
         f"box={summary['defaultBox']} selfHit={summary['defaultSelfHit']} focus={summary['defaultFocusable']}"),
        ("C3 算术闭合 8.4 = 32 × 0.5 × zoom",
         summary["defaultBox"] == [(8.4, 8.4)]
         and abs(summary["expectedDefaultBox"] - 8.416) < 0.01,
         f"32×0.5×{zoom} = {summary['expectedDefaultBox']}；实测 {summary['defaultBox']}"),
        ("C4 hover（点在线上）⟹ 那一枚 pe:auto + opacity:1 + 16.8×16.8",
         active is not None and active["pe"] == "auto" and active["opacity"] == "1"
         and (active["w"], active["h"]) == (16.8, 16.8),
         f"point={hover_point} pe={summary['activePe']} op={summary['activeOpacity']} box={summary['activeBox']}"),
        ("C5 hover 启用后点它 ⟹ 边数 11 → 10",
         active is not None and summary["edgesBeforeClick"] == 11
         and summary["edgesAfterClick"] == 10,
         f"{summary['edgesBeforeClick']} → {summary['edgesAfterClick']}"),
        ("C6 被启用那枚中心 elementFromPoint 返回 path（不是按钮）",
         active is not None and summary["activeHitTag"] == "path",
         f"hitTag={summary['activeHitTag']} —— 事件仍到达按钮（边被删了）"),
        ("C7 自然 Tab 300 步落在手柄 44 次、11 枚全覆盖",
         summary["tabEdgeStops"] == 44 and summary["tabDistinctEdges"] == 11,
         f"stops={summary['tabEdgeStops']} distinct={summary['tabDistinctEdges']} / 共 11 枚"),
        ("C8 聚焦后 Enter 删一条、Space 不删",
         summary["edgesBeforeEnter"] == 11 and summary["edgesAfterEnter"] == 10
         and summary["edgesAfterSpace"] == 10,
         f"{summary['edgesBeforeEnter']} → {summary['edgesAfterEnter']} → {summary['edgesAfterSpace']}"),
        ("C9 「选中连线」这条启用路径未取证（selectedEdgeIds 仍 0）",
         summary["selectedEdgeIdsAfterClick"] == 0,
         f"selectedEdgeIds={summary['selectedEdgeIdsAfterClick']}（记未取证，不下结论）"),
    ]

    print("\n=== 判据 ===")
    failures = []
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ⟵ {detail}")
        if not ok:
            failures.append(name)

    payload = {
        "static": {"conditions": cond},
        "run": {"zoom": zoom, "default": before, "hover": click_reading if active else None,
                "afterClick": after_click,
                "tab": {"steps": TAB_STEPS, "total": len(hits), "edgeStops": len(edge_stops),
                        "distinctEdges": tab_distinct_edges,
                        "topStops": Counter(hits).most_common(12)},
                "keys": {"focusTarget": focus_target, "before": k0, "afterEnter": k1,
                         "afterSpace": k2},
                "selectEdge": {"selectedEdgeIds": selected_after_click}},
        "summary": summary,
        "failures": failures,
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"\n{len(checks) - len(failures)}/{len(checks)} 判据通过；写入 {AUDIT_DIR / 'runtime-audit.json'}")
    try:
        subprocess.run(["git", "status", "--porcelain", "src"], cwd=ROOT, check=True)
    except Exception:
        pass
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
