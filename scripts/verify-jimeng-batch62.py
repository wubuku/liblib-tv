"""Jimeng clone batch 62 verifier — multi-select toolbar + capture-frame direct image.

Contract:
- shift+click 2 nodes → combined toolbar「2 节点 ｜ 编组 ｜ 布局∨ ｜ 下载(禁用)」
  centered above selection; nodesselection-rect styled bg white/4% +
  1px dashed white/20 + r40; empty-node gen panel hidden during multi-select.
- 编组 click links data-group-id; ⌘⇧G clears.
- 布局 → 自动排列 lines selection into one row (y aligned), single undo step.
- per-node toolbar 截取帧 → 首帧 directly creates an image node (poster,
  title 「… 首帧」) at the free slot right of the row (avoidance), with
  lineage edge; both endpoints selected → edge stroke rgb(35,108,172) 1px.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def flow_pos(page, node_id: str) -> dict:
    return page.evaluate(
        """(id) => {
            const el = document.querySelector(`[data-id="${id}"]`);
            if (!el) return null;
            // node world position lives in the transform of .react-flow__node
            const t = el.style.transform || "";
            const m = t.match(/translate\\(([-\\d.]+)px,\\s*([-\\d.]+)px\\)/);
            return m ? {x: parseFloat(m[1]), y: parseFloat(m[2])} : null;
        }""",
        node_id,
    )


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    diag_logs: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.on("console", lambda m: diag_logs.append(m.text[:150]))
        page.on("pageerror", lambda e: diag_logs.append(f"pageerror: {str(e)[:200]}"))
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # Batch 398 SOURCE_FACT: Agent 面板常驻——本验证器不测面板，
        # 载入后先收起以避免遮挡画布交互
        _collapse = page.locator('button[aria-label="收起"]')
        if _collapse.count():
            _collapse.click()
            page.wait_for_timeout(400)

        n0 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

        def center(page, node_id):
            return page.evaluate(
                """(id) => { const n = document.querySelector(`[data-id="${id}"]`);
                    const r = n.getBoundingClientRect();
                    return {x: r.x + 60, y: r.y + 20}; }""",
                node_id,
            )

        # ---- multi-select both nodes (retry: batch 54 known timing flake) ----
        for _attempt in range(3):
            page.mouse.click(300, 750)
            page.wait_for_timeout(300)
            c_local = center(page, "video-local-1")
            c_empty = center(page, "video-empty-1")
            page.mouse.click(c_local["x"], c_local["y"])
            page.wait_for_timeout(300)
            page.keyboard.down("Shift")
            page.mouse.click(c_empty["x"], c_empty["y"])
            page.keyboard.up("Shift")
            page.wait_for_timeout(800)
            selected = page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length"
            )
            if selected == 2:
                break
        if selected != 2:
            failures.append(f"multi-select failed: selected={selected}")

        # combined toolbar
        mt = page.locator('[data-testid="jimeng-multi-toolbar"]')
        if mt.count() != 1:
            failures.append(f"multi toolbar missing: {mt.count()}")
        else:
            txt = mt.inner_text()
            if "2 节点" not in txt or "编组" not in txt or "布局" not in txt:
                failures.append(f"multi toolbar text wrong: {txt!r}")
            dl = mt.locator('[data-testid="multi-download"]')
            # Batch 66: 下载受保存状态门控 — 选中本身不脏化画布，先拖拽 1px
            # 制造未保存变更，断言禁用；自动保存后恢复可用
            c_local = center(page, "video-local-1")
            page.mouse.move(c_local["x"] + 150, c_local["y"] + 150)
            page.mouse.down()
            page.mouse.move(c_local["x"] + 152, c_local["y"] + 151, steps=3)
            page.mouse.up()
            page.mouse.move(c_local["x"] + 152, c_local["y"] + 151)
            page.mouse.down()
            page.mouse.move(c_local["x"] + 150, c_local["y"] + 150, steps=3)
            page.mouse.up()
            page.wait_for_timeout(300)
            if not dl.is_disabled():
                failures.append("multi download not disabled while saving")
            if dl.get_attribute("title") != "导出前请保存画布":
                failures.append(
                    f"download title wrong: {dl.get_attribute('title')!r}"
                )
            page.wait_for_timeout(2600)
            if dl.is_disabled():
                failures.append("multi download still disabled after autosave")
            # centered above bbox
            box = mt.bounding_box()
            rects = page.evaluate(
                """() => [...document.querySelectorAll('.react-flow__node.selected')]
                    .map(n => n.getBoundingClientRect())"""
            )
            bx = min(r["x"] for r in rects), max(r["x"] + r["width"] for r in rects)
            bt = min(r["y"] for r in rects)
            if box:
                cx = box["x"] + box["width"] / 2
                if abs(cx - (bx[0] + bx[1]) / 2) > 12:
                    failures.append(
                        f"toolbar not centered: {cx} vs {(bx[0] + bx[1]) / 2}"
                    )
                if abs((box["y"] + box["height"]) - (bt - 36)) > 12:
                    failures.append(
                        f"toolbar gap wrong: bottom={box['y'] + box['height']} vs {bt - 36}"
                    )

        # all node toolbars hidden during multi-select (media toolbar + gen panel;
        # xyflow keeps hidden DOM with visibility:hidden, so check rects/visibility)
        gen = page.evaluate(
            """() => {
                for (const el of document.querySelectorAll('.react-flow__node-toolbar')) {
                    const cs = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    if (cs.visibility !== 'hidden' && r.width > 0 && r.height > 0
                        && cs.display !== 'none') return true;
                }
                return false;
            }"""
        )
        if gen:
            failures.append("a node toolbar/gen panel visible during multi-select")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch62-multiselect.png")
        )

        # selection outline (shift+click path; native nodesselection-rect only
        # renders after marquee in v12): styles + geometry = cards bbox ± 40px
        nsr = page.evaluate(
            """() => {
                const el = document.querySelector('[data-testid="jimeng-selection-outline"]');
                if (!el) return null;
                const cs = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                const cards = [...document.querySelectorAll('.react-flow__node.selected')]
                    .map(n => n.getBoundingClientRect());
                return {
                    bg: cs.backgroundColor,
                    border: cs.borderTopWidth + ' ' + cs.borderTopStyle + ' ' + cs.borderTopColor,
                    radius: cs.borderRadius,
                    box: {x: r.x, y: r.y, w: r.width, h: r.height},
                    cards: {l: Math.min(...cards.map(c => c.x)), t: Math.min(...cards.map(c => c.y)),
                            r: Math.max(...cards.map(c => c.x + c.width)),
                            b: Math.max(...cards.map(c => c.y + c.height))},
                };
            }"""
        )
        if not nsr:
            failures.append("selection outline not rendered")
        else:
            if nsr["bg"] != "rgba(255, 255, 255, 0.04)":
                failures.append(f"outline bg wrong: {nsr['bg']}")
            if "dashed" not in nsr["border"] or "0.2" not in nsr["border"]:
                failures.append(f"outline border wrong: {nsr['border']}")
            if nsr["radius"] != "40px":
                failures.append(f"outline radius wrong: {nsr['radius']}")
            # source geometry: cards bbox expanded 40px on all sides
            c = nsr["cards"]
            want = {"x": c["l"] - 40, "y": c["t"] - 40,
                    "w": c["r"] - c["l"] + 80, "h": c["b"] - c["t"] + 80}
            got = nsr["box"]
            if any(abs(got[k] - want[k]) > 2 for k in ("x", "y", "w", "h")):
                failures.append(
                    f"outline geometry wrong: {got} want {want} (cards bbox ±40px)"
                )

        # ---- 编组 → group ids linked ----
        mt.locator('[data-testid="multi-group"]').click()
        page.wait_for_timeout(700)
        linked = page.evaluate(
            """() => {
                const a = document.querySelector('[data-id="video-local-1"] [data-group-id]');
                const b = document.querySelector('[data-id="video-empty-1"] [data-group-id]');
                return !!a && !!b
                    && a.getAttribute('data-group-id') === b.getAttribute('data-group-id');
            }"""
        )
        if not linked:
            failures.append("编组 click did not link group ids")

        # ---- ⌘⇧G ungroup → cleared ----
        page.keyboard.press("Meta+Shift+g")
        page.wait_for_timeout(700)
        gids = page.evaluate(
            """() => ['video-local-1', 'video-empty-1'].map(id => {
                const n = document.querySelector(`[data-id="${id}"] [data-group-id]`);
                return n ? n.getAttribute('data-group-id') : null;
            })"""
        )
        if any(gids):
            failures.append(f"ungroup did not clear: {gids}")

        # ---- 布局 → 智能布局 (batch 63 改名: 原「自动排列」) ----
        mt.locator('[data-testid="multi-layout"]').click()
        page.wait_for_timeout(400)
        arrange = page.locator('[data-testid="multi-arrange-smart"]')
        if arrange.count() != 1:
            failures.append("布局 dropdown missing 智能布局")
        else:
            arrange.click()
            page.wait_for_timeout(600)
            p1 = flow_pos(page, "video-local-1")
            p2 = flow_pos(page, "video-empty-1")
            if not p1 or not p2:
                failures.append("arrange: node positions unreadable")
            else:
                if abs(p1["y"] - p2["y"]) > 0.5:
                    failures.append(f"arrange: y not aligned {p1} {p2}")
                if abs((p2["x"] - p1["x"]) - 649.0) > 1.0:
                    failures.append(
                        f"arrange: spacing wrong {p2['x'] - p1['x']} (want 649)"
                    )
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch62-arrange.png")
            )
            # single undo step restores
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(600)
            p2u = flow_pos(page, "video-empty-1")
            if not p2u or abs(p2u["x"] - 1442.1) > 2.5 or abs(p2u["y"] - 323.2) > 2.5:
                failures.append(f"arrange undo failed: {p2u}")

        # ---- deselect, then capture-frame 首帧 ----
        page.mouse.click(300, 750)
        page.wait_for_timeout(400)
        c_local = center(page, "video-local-1")
        page.mouse.click(c_local["x"], c_local["y"])
        page.wait_for_timeout(600)
        # per-node toolbar → open 截取帧 dropdown (portal: global query)
        cap = page.evaluate(
            """() => {
                const t = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .find(t => t.textContent.includes('截取帧'));
                if (!t) return null;
                const btn = [...t.querySelectorAll('button')]
                    .find(b => b.textContent.trim() === '截取帧');
                if (!btn) return null;
                const r = btn.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }"""
        )
        if not cap:
            failures.append("截取帧 button not found in per-node toolbar")
        else:
            page.mouse.click(cap["x"], cap["y"])
            page.wait_for_timeout(400)
            first = page.evaluate(
                """() => {
                    const btn = [...document.querySelectorAll('button')]
                        .find(b => b.textContent.trim() === '首帧'
                            && b.getBoundingClientRect().height < 50);
                    if (!btn) return null;
                    const r = btn.getBoundingClientRect();
                    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                }"""
            )
            if not first:
                failures.append("首帧 menu item not found")
            else:
                page.mouse.click(first["x"], first["y"])
                page.wait_for_timeout(700)
                n_now = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__node').length"
                )
                if n_now != n0 + 1:
                    failures.append(f"首帧 did not add image node: {n_now} vs {n0}")
                else:
                    img = page.evaluate(
                        """() => {
                            const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                            const el = nodes[nodes.length - 1];
                            if (!el) return null;
                            const img = el.querySelector('img');
                            const t = el.style.transform || '';
                            const m = t.match(/translate\\(([-\\d.]+)px,\\s*([-\\d.]+)px\\)/);
                            return {hasPoster: !!img,
                                    title: (el.textContent || '').trim().slice(0, 60),
                                    x: m ? parseFloat(m[1]) : null,
                                    y: m ? parseFloat(m[2]) : null};
                        }"""
                    )
                    if not img:
                        failures.append("image node missing after 首帧")
                    else:
                        if not img["hasPoster"]:
                            failures.append("image node has no poster img")
                        if "首帧" not in img["title"]:
                            failures.append(f"image node title wrong: {img['title']!r}")
                        # avoidance: video-empty-1 blocks first slot → x = 1442.1+569+80
                        if abs(img["x"] - 2091.1) > 2.5 or abs(img["y"] - 280.5) > 2.5:
                            failures.append(
                                f"image node placement wrong: ({img['x']}, {img['y']}) "
                                "want (2091.1, 280.5)"
                            )
                    page.screenshot(
                        path=str(REFERENCE_DIR / "jimeng-clone-batch62-firstframe.png")
                    )
                    # ---- both endpoints selected → blue edge ----
                    img_id = page.evaluate(
                        """() => {
                            const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                            return nodes.length
                                ? nodes[nodes.length - 1].getAttribute('data-id') : null;
                        }"""
                    )
                    c_img = center(page, img_id)
                    page.keyboard.down("Shift")
                    page.mouse.click(c_img["x"], c_img["y"])
                    page.keyboard.up("Shift")
                    page.wait_for_timeout(700)
                    edge = page.evaluate(
                        """() => {
                            const pth = document.querySelector('.react-flow__edge path');
                            if (!pth) return null;
                            const cs = getComputedStyle(pth);
                            return {stroke: cs.stroke, w: cs.strokeWidth};
                        }"""
                    )
                    if not edge:
                        failures.append("lineage edge not rendered")
                    elif edge["stroke"] != "rgb(35, 108, 172)":
                        failures.append(
                            f"edge stroke wrong when both ends selected: {edge['stroke']}"
                        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        for l in diag_logs[-8:]:
            print(" [diag]", l)
        raise SystemExit(1)
    print("PASS: jimeng batch 62 multi-select toolbar + capture-frame contract")


if __name__ == "__main__":
    main()
