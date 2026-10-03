#!/usr/bin/env python3
"""batch 732 验收：46 个写点里有一个撑成 40 枚 —— 40 枚完全不可见，却仍可聚焦、仍在 Tab 顺序里

## 起点

730 立了一条「写点数 ≠ 控件数」：`LeftSidebar` 1 写点 → 4 枚、`HistoryPanel`
4 写点 → 10 枚，倍数很小。731 只在画布 7 个视图里测，于是留了一句话：
「本批未打开 `LibraryShowcasePanel` / `VideoClipEditPanel` / `SegmentReshootPanel`
/ `StoryboardScriptEditor` / `AudioNode` / `ShotBreakdownResultNode` /
`ScriptGeneratorNode`，未测」。

本批去开它们 —— 结果在第一个就撞上量级完全不同的一族。

## 决定性读数

### ① `LibraryShowcasePanel` 的 **2 个写点 → 42 枚运行时实例**

| 面板 | 合计 | 筛选（`:236`） | 收藏（`:131`，在 `.map()` 里） |
|---|---|---|---|
| 风格库 `primary:style-library` | **17** | 1 | **16** |
| 特效库 `primary:effects-library` | **25** | 1 | **24** |

`LibraryShowcasePanel.tsx:131` 的收藏按钮写在 `visibleCards.map()` 里，
**一个写点放大 24 倍**。源码 batch 358 注释自己写着
「风格库/特效库里一次扫出 **40 多个**这样的按钮」——
本批实测 **16 + 24 = 40**，与那条注释吻合。

⟹ **46 个写点实际是至少 85 枚控件**（730 的 43 + 本批的 42）。

### ② 那 40 枚**完全不可见**，却仍然可聚焦

40 枚收藏按钮逐枚实测：

| 维度 | 读数 |
|---|---|
| `opacity` | **0**（全部） |
| `pointer-events` | **none**（全部） |
| `focus()` 后 `activeElement === el` | **40 / 40** |
| 聚焦后 `outline` | **`auto 1px`（全部）** |
| `group-hover` 类 | **已无**（注释说的 `group-hover:opacity-100` 已被换掉） |

⟹ **730 那句「焦点环把键盘那一维也骗了」对这 40 枚不成立**：
它们的元素本身就是 `opacity: 0`，**焦点环与元素一样不可见**。
键盘用户 Tab 过去只会落进一片虚无 —— 既看不到焦点，也点不动。

### ③ 但它们**仍在自然 Tab 顺序里**，而且有 40 个彼此不同的名字

Tab 走 260 步，落到收藏按钮 **68 次**；40 枚的可及名分别是
`收藏 <卡片名>`（如 `收藏 Seedream 5.0 pro`、`收藏 小蜜蜂运镜`）——
**40 个各自不同的名字，全部不可见、全部点不动**。
屏幕阅读器用户会依次听到 40 个存在的按钮，点下去毫无反应。

### ④ 种子画布上，`VideoProcessingToolbar` 与 `SegmentReshootPanel` **UI 不可达**

种子里那张视频卡的 `status === "failed"`，而两者的渲染条件都要求 `ready`：

- `VideoNode.tsx:411` `showSingleNodeEditor && status === "ready" && !subtitleMode && activeTool !== "picture-edit"`
- `VideoNode.tsx:737` `showSingleNodeEditor && activeTool === "reshoot"`（而「片段重拍」按钮本身在
  `VideoProcessingToolbar` 里 ⟹ 同一道门）

⟹ **6 个写点（`VideoProcessingToolbar` 2 + `SegmentReshootPanel` 4）在种子画布上没有任何 UI 入口。**

## 不声称

- **不声称其余 5 族已打开** —— `AudioNode`、`VideoClipEditPanel`、
  `ScriptGeneratorNode`、`StoryboardScriptEditor`、`ShotBreakdownResultNode`
  本批的入口脚本**没走通**（「添加节点」面板里的按钮文本匹配失配，
  节点没被造出来）⟹ **未取证**，不下结论。
- **不声称 85 是运行时实例的总数** —— 只统计了 730 的 7 个视图 + 本批的 2 个面板；
  其余族一旦打开还会增加。
- **不声称「不可见」是缺陷** —— `opacity: 0` + `pointer-events: none` 是 batch 358
  有意改的（去掉悬停骗人反馈）；本批只报告**「不可见却仍可聚焦」这个组合**，
  不裁决该不该留。
- **不声称 AX 树等同于真实屏幕阅读器播报** —— 沿用 731。

## 新增待拍板

1. **40 枚不可见但可聚焦的收藏按钮要不要移出焦点顺序**（`tabIndex={-1}` 或
   直接不渲染）？**需改 `src/`，等授权。**
2. **`VideoProcessingToolbar` / `SegmentReshootPanel` 的 6 个写点要不要给入口**
   —— 种子画布上它们没有 UI 可达路径。**需改 `src/`，等授权。**
3. **其余 5 族是否继续追入口** —— 见「不声称」。

## 方法论

1. **「写点数 ≠ 控件数」要以量级说话** —— 730 测到的是 1→4、4→10；
   打开 `LibraryShowcasePanel` 才发现 **1→24**。**没打开的族不能算「已普查」。**
2. **不可见与不可聚焦是两件事** —— `opacity: 0` 让元素看不见，
   但没有把它移出焦点顺序 ⟹ **凡是加 `opacity-0` 的地方都要连带查 Tab 可达性**。
3. **注释里的数字也要能被实测** —— batch 358 注释写「40 多个」，
   本批实测 40 ⟹ 注释是可信的**前提是有人去测**。
4. **入口失配要先怀疑探针** —— 「添加节点」的文本匹配失配导致 5 族没打开，
   **那一整格记未取证**，不用「不可达」搪塞（真不可达要拿出理由）。

## 探针返工两处

1. **JS 选择器跨行** —— `[...][a,\n   b]` 这种换行写进单引号字符串里，
   JS 直接 `SyntaxError`，探针跑了一半才炸 ⟹ 选择器写单行。
2. **收尾段崩了导致 JSON 没落盘** —— 数据在内存里、文件没写成，
   分析脚本读不到 ⟹ **每族采完即落盘**，别攒到最后。
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch732-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

STYLE_OV = "primary:style-library"
EFFECTS_OV = "primary:effects-library"

FAVSEL = (f'[data-liblib-overlay="{STYLE_OV}"] button[data-inert],'
          f'[data-liblib-overlay="{EFFECTS_OV}"] button[data-inert]')

DETAIL = f"""() => [...document.querySelectorAll('{FAVSEL}')].map((el, i) => {{
  const cs = getComputedStyle(el);
  el.focus();
  const focused = document.activeElement === el;
  const cs2 = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return {{i, overlay: el.closest('[data-liblib-overlay]').getAttribute('data-liblib-overlay'),
          aria: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
          opacity: cs.opacity, pointerEvents: cs.pointerEvents,
          groupHover: /group-hover/.test(el.className || ''),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          focused, outlineAfter: cs2.outlineStyle + ' ' + cs2.outlineWidth}};
}})"""

ACTIVE_FP = r"""() => { const a = document.activeElement; if (!a) return null;
  return {tag: a.tagName, aria: a.getAttribute && a.getAttribute('aria-label') || '',
          text: (a.textContent || '').trim().slice(0, 14),
          inert: a.getAttribute ? a.getAttribute('data-inert') : null}; }"""

VIDEO_STATUS = r"""() => { const g = window.__libtv_store.getState().getActiveCanvas();
  const n = g.nodes.find(x => x.type === 'video');
  return n ? (n.data || {}).status ?? null : null; }"""


def ax_for(cdp: Any, node_ids: list[int]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for nid in node_ids:
        try:
            bid = cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
            t = cdp.send("Accessibility.getPartialAXTree",
                         {"backendNodeId": bid, "fetchRelatives": False})
        except Exception as exc:  # noqa: BLE001
            out.append({"error": str(exc)[:100]})
            continue
        nodes = t.get("nodes", [])
        own = next((n for n in nodes if n.get("role")), nodes[0] if nodes else None)
        if own is None:
            out.append({"error": "empty"})
            continue
        props = {p.get("name"): p.get("value", {}).get("value")
                 for p in (own.get("properties") or [])}
        out.append({"role": (own.get("role") or {}).get("value"),
                    "name": (own.get("name") or {}).get("value"),
                    "ignored": own.get("ignored"),
                    "props": {k: v for k, v in props.items()
                              if k in ("disabled", "focusable", "invalid")}})
    return out


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_300)


def open_library(page: Page, label: str) -> None:
    open_canvas(page)
    page.evaluate("""() => { const b = document.querySelector('[aria-label="素材库"]');
      if (b) b.click(); }""")
    page.wait_for_timeout(600)
    page.evaluate("""(l) => { const b = [...document.querySelectorAll('button')]
      .find(x => (x.textContent || '').includes(l)); if (b) b.click(); }""", label)
    page.wait_for_timeout(700)


def collect(page: Page, cdp: Any, view: str) -> dict[str, Any]:
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    ids = cdp.send("DOM.querySelectorAll", {"nodeId": root, "selector": FAVSEL})["nodeIds"]
    rows = page.evaluate(DETAIL)
    ax = ax_for(cdp, ids)
    for row, a in zip(rows, ax):
        row["ax"] = a
    return {"view": view, "rows": rows}


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H})
    cdp = page.context.new_cdp_session(page)
    cdp.send("Accessibility.enable")
    out: dict[str, Any] = {"views": {}}
    for label, view in (("风格库", "style"), ("特效库", "effects")):
        open_library(page, label)
        out["views"][view] = collect(page, cdp, view)
    # 自然 Tab 序列（以特效库为准：它那 24 枚更多）
    page.evaluate("() => { if (document.activeElement && document.activeElement.blur)"
                  " document.activeElement.blur(); }")
    seq: list[dict[str, Any]] = []
    for _ in range(260):
        page.keyboard.press("Tab")
        fp = page.evaluate(ACTIVE_FP)
        if fp:
            seq.append(fp)
    fav = [f for f in seq if (f["aria"] or "").startswith("收藏")]
    out["tab"] = {"steps": len(seq), "favStops": len(fav),
                  "favSample": sorted({f["aria"] for f in fav})[:5]}
    # 种子里视频卡的状态：决定 VideoProcessingToolbar / SegmentReshootPanel 是否可达
    open_canvas(page)
    out["seedVideoStatus"] = page.evaluate(VIDEO_STATUS)
    page.close()
    return out


def _open_tag_lines(src: str) -> list[int]:
    """每个 `data-inert="true"` 所属的 <button 开标签的行号。"""
    out: list[int] = []
    for m in re.finditer(r'data-inert="true"', src):
        i = src.rfind("<button", 0, m.start())
        out.append(src[:i].count("\n") + 1 if i != -1 else -1)
    return sorted(out)


def static_facts() -> dict[str, Any]:
    path = ROOT / "src/components/LibraryShowcasePanel.tsx"
    src = path.read_text(encoding="utf-8")
    return {
        "nInertInLibraryShowcasePanel": len(re.findall(r'data-inert="true"', src)),
        "lines": sorted(src[:m.start()].count("\n") + 1
                        for m in re.finditer(r'data-inert="true"', src)),
        # 收藏按钮的 <button 开标签在 :130（属性那行是 :134）；筛选的整枚在 :236
        "openTagLines": _open_tag_lines(src),        "hasVisibleCardsMap": "visibleCards.map(" in src,
        "hasFavTitle": "收藏在克隆侧尚未接入" in src,
        "favClassOpacity": "opacity-0" in src,
        "favClassPointerNone": "pointer-events-none" in src,
        "commentSays": ("40 多个" if "40 多个" in src else None),
    }


def _views(r: dict[str, Any]) -> dict[str, Any]:
    return r.get("run", {}).get("views", {})


def _fav(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [x for x in rows if x["aria"].startswith("收藏")]


def check_1(r: dict[str, Any]) -> None:
    """静态：`LibraryShowcasePanel` 只有 2 个写点，收藏那个写在 `.map()` 里。"""
    s = r["static"]
    assert s["nInertInLibraryShowcasePanel"] == 2, s
    assert s["lines"] == [134, 236], s["lines"]      # data-inert 属性所在行
    assert s["openTagLines"] == [130, 236], s["openTagLines"]   # <button 开标签所在行
    assert s["hasVisibleCardsMap"] is True, s
    assert s["favClassOpacity"] is True and s["favClassPointerNone"] is True, s
    assert s["hasFavTitle"] is True, s
    r["staticSummary"] = s


def check_2(r: dict[str, Any]) -> None:
    """运行时：风格库 17 枚、特效库 25 枚 —— **2 个写点 → 42 枚**。"""
    vs = _views(r)
    assert len(vs["style"]["rows"]) == 17, len(vs["style"]["rows"])
    assert len(vs["effects"]["rows"]) == 25, len(vs["effects"]["rows"])
    assert len(_fav(vs["style"]["rows"])) == 16, len(_fav(vs["style"]["rows"]))
    assert len(_fav(vs["effects"]["rows"])) == 24, len(_fav(vs["effects"]["rows"]))
    total = sum(len(v["rows"]) for v in vs.values())
    assert total == 42, total
    r["instanceTotals"] = {"style": 17, "effects": 25, "fav": 40, "total": total}


def check_3(r: dict[str, Any]) -> None:
    """那 40 枚**完全不可见**（opacity 0 + pointer-events none）却 `focus()` 40/40 成功。"""
    fav = [x for v in _views(r).values() for x in _fav(v["rows"])]
    assert len(fav) == 40, len(fav)
    assert {x["opacity"] for x in fav} == {"0"}, sorted({x["opacity"] for x in fav})
    assert {x["pointerEvents"] for x in fav} == {"none"}, sorted({x["pointerEvents"] for x in fav})
    assert all(x["focused"] for x in fav), [x["aria"] for x in fav if not x["focused"]]
    assert {x["outlineAfter"] for x in fav} == {"auto 1px"}, sorted({x["outlineAfter"] for x in fav})
    assert not any(x["groupHover"] for x in fav), "group-hover 类应已被换掉"
    r["invisibleButFocusable"] = {"count": len(fav),
                                  "focusable": sum(1 for x in fav if x["focused"])}


def check_4(r: dict[str, Any]) -> None:
    """它们**仍在自然 Tab 顺序里**，且 AX 树里 40 枚都是 `role=button`/`focusable`。"""
    fav = [x for v in _views(r).values() for x in _fav(v["rows"])]
    assert all(x["ax"].get("role") == "button" for x in fav), \
        [x["ax"] for x in fav[:3]]
    assert all(x["ax"].get("ignored") is False for x in fav), \
        [x["ax"] for x in fav[:3]]
    assert all(x["ax"].get("props", {}).get("focusable") is True for x in fav), \
        [x["ax"] for x in fav[:3]]
    names = {x["ax"]["name"] for x in fav}
    assert len(names) == 40, len(names)
    tab = r["run"]["tab"]
    assert tab["favStops"] > 0, tab
    r["tabAndAx"] = {"distinctAxNames": len(names), "favStops": tab["favStops"],
                     "steps": tab["steps"]}


def check_5(r: dict[str, Any]) -> None:
    """种子画布上视频卡 `status === "failed"` ⟹ 那 6 个写点没有 UI 入口。"""
    assert r["run"]["seedVideoStatus"] == "failed", r["run"]["seedVideoStatus"]
    page_src = (ROOT / "src/components/nodes/VideoNode.tsx").read_text(encoding="utf-8")
    assert 'showSingleNodeEditor && status === "ready"' in page_src
    assert 'showSingleNodeEditor && activeTool === "reshoot"' in page_src
    # 「片段重拍」按钮本身在 VideoProcessingToolbar 里 ⟹ 同一道 status 门
    tb = (ROOT / "src/components/VideoProcessingToolbar.tsx").read_text(encoding="utf-8")
    assert "片段重拍" in tb, "reshoot 触发应在 VideoProcessingToolbar 内"
    r["unreachableBySeed"] = {"seedVideoStatus": "failed",
                             "sites": ["VideoProcessingToolbar.tsx:244", ":245",
                                       "SegmentReshootPanel.tsx ×4"]}


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    got: dict[str, Any] = {"static": static_facts()}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append("run: %s" % exc)
            got["run"] = {}
        browser.close()
    payload: dict[str, Any] = {"static": got["static"], "run": got["run"]}
    checks = [
        ("library-showcase-panel-has-2-sites-and-the-fav-one-sits-in-a-map", check_1),
        ("those-2-sites-render-as-42-instances", check_2),
        ("all-40-fav-buttons-are-invisible-yet-still-focusable", check_3),
        ("the-40-invisible-buttons-are-still-in-tab-order-and-in-the-ax-tree", check_4),
        ("seed-canvas-video-status-blocks-two-more-families", check_5),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn(payload)
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    payload["summary"] = summary
    payload["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ! " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
