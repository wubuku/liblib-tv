"""Jimeng clone batch 39 verifier — grouping (⌘G / ⌘⇧G) with linked movement.

Contract: select both base nodes → ⌘G groups them (same data-group-id);
dragging one node moves the other by the same delta; ⌘⇧G ungroups
(data-group-id cleared) and dragging no longer links them.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def node_info(page) -> list:
    return page.evaluate(
        """() => [...document.querySelectorAll('.react-flow__node')]
            .map(n => { const r = n.getBoundingClientRect();
                return {id: n.getAttribute('data-id'),
                        gid: n.querySelector('[data-group-id]')?.getAttribute('data-group-id') ?? null,
                        x: r.x, y: r.y}; })"""
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

        # select both base nodes (non-overlapping)
        centers = page.evaluate(
            """() => [
                (() => { const n = document.querySelector('[data-id="video-local-1"]');
                    const r = n.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; })(),
                (() => { const n = document.querySelector('[data-id="video-empty-1"]');
                    const r = n.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; })(),
            ]"""
        )
        page.mouse.click(centers[0]["x"] - 120, centers[0]["y"] - 60)  # 避开中央播放钮
        page.wait_for_timeout(300)
        page.keyboard.down("Shift")
        page.mouse.click(centers[1]["x"], centers[1]["y"])
        page.keyboard.up("Shift")
        page.wait_for_timeout(400)
        selected = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        )
        if selected != 2:
            print(f"[diag] multi-selected: {selected}")
            raise SystemExit(1)

        # ⌘G group
        # Meta+g 偶发与选择竞争：轮询等待编组属性渲染
        page.keyboard.press("Meta+g")
        linked = False
        for _ in range(10):
            page.wait_for_timeout(300)
            linked = page.evaluate(
                """() => {
                    const gids = [...document.querySelectorAll('[data-group-id]')]
                        .map(e => e.getAttribute('data-group-id'));
                    return gids.length >= 2 && new Set(gids).size === 1;
                }"""
            )
            if linked:
                break
        infos = node_info(page)
        g0 = next(n["gid"] for n in infos if n["id"] == "video-local-1")
        g1 = next(n["gid"] for n in infos if n["id"] == "video-empty-1")
        if not g0 or g0 != g1:
            failures.append(f"group ids not linked: {g0!r} vs {g1!r}")

        # drag local-1 → empty-1 follows with same delta
        before = {n["id"]: (n["x"], n["y"]) for n in node_info(page)}
        c0 = centers[0]
        page.mouse.move(c0["x"] - 150, c0["y"] - 80)
        page.mouse.down()
        page.mouse.move(c0["x"] - 70, c0["y"] - 30, steps=8)
        page.mouse.up()
        page.wait_for_timeout(600)
        after = {n["id"]: (n["x"], n["y"]) for n in node_info(page)}
        d0 = (after["video-local-1"][0] - before["video-local-1"][0],
              after["video-local-1"][1] - before["video-local-1"][1])
        d1 = (after["video-empty-1"][0] - before["video-empty-1"][0],
              after["video-empty-1"][1] - before["video-empty-1"][1])
        if abs(d0[0] - d1[0]) > 3 or abs(d0[1] - d1[1]) > 3:
            failures.append(f"group drag deltas differ: {d0} vs {d1}")
        if abs(d0[0]) < 40:
            failures.append(f"group drag did not move nodes: {d0}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch39-group-drag-1680.png")
        )

        # ⌘⇧G ungroup → ids cleared
        page.keyboard.press("Meta+Shift+g")
        page.wait_for_timeout(1000)
        gids_after = page.evaluate(
            """() => ['video-local-1', 'video-empty-1'].map(id => {
                const n = document.querySelector(`[data-id="${id}"]`);
                return n?.innerHTML.includes('data-group-id')
                    ? n.innerHTML.match(/data-group-id="([^"]+)"/)?.[1] ?? null
                    : null;
            })"""
        )
        if any(gids_after):
            failures.append(f"ungroup did not clear group ids: {gids_after}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        for l in diag_logs[-8:]:
            print(" [diag]", l)
        raise SystemExit(1)
    print("PASS: jimeng batch 39 grouping contract")


if __name__ == "__main__":
    main()
