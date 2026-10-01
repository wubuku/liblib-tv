#!/usr/bin/env python3
"""Batch 342 探针：节点搜索「点击结果聚焦」是否把节点真的移到视野中心。

疑点（克隆侧，不依赖源站）:
`FrameosNodeSearch.focusNode()` 用 `getBoundingClientRect()` 取节点的
**屏幕坐标**, 再传给 `useReactFlow().setCenter(x, y, ...)` —— 但 setCenter
要的是**画布流坐标** (flow coordinates)。两者只差一个「视口原点 + 缩放 +
平移」的偏移, 在默认视图下偏移小、容易被当成「差不多对」而放过;
一旦用户缩放/平移过画布, 点击搜索结果就会把视野挪到错误位置。

组件自己的注释写明意图是「选中该节点并把视野缩放聚焦到它」, 所以这是
**克隆自身没兑现自己的意图**, 不需要源站采样即可判定。

探针做法: 先把画布缩放+平移到与默认视图明显不同的状态, 再走完整 UI 路径
(点「搜索节点」→ 输入 → 点结果), 量结果节点最终落在视口的什么位置。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch342-search-focus.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

# 把画布挪到一个「偏移一定很大」的状态: 缩放 0.5 并平移
DISTORT_JS = """
() => {
  const rf = document.querySelector('.react-flow__viewport');
  if (!rf) return null;
  rf.style.transform = 'translate(400px, 260px) scale(0.5)';
  return rf.style.transform;
}
"""

# 量某节点当前在视口里的位置
NODE_SCREEN_JS = """
(id) => {
  const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { left: r.left, top: r.top, w: r.width, h: r.height,
           cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
}
"""

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [], selectedNodeId: null });
  const n = st.getState().nodes[2];   // 第三个节点, 离原点足够远
  return { id: n.id, title: String(n.data.title), position: n.position };
}
"""


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        setup = page.evaluate(SETUP_JS)
        out["setup"] = setup
        page.wait_for_timeout(400)
        out["transform"] = page.evaluate(DISTORT_JS)
        page.wait_for_timeout(400)
        out["before"] = page.evaluate(NODE_SCREEN_JS, setup["id"])

        # ── 完整 UI 路径: 工具条「搜索节点」→ 输入 → 点第一条结果 ──
        btn = page.locator('button[aria-label="搜索节点"]')
        out["searchButton"] = btn.count()
        if out["searchButton"] == 0:
            print("!! 找不到「搜索节点」按钮")
            return 1
        btn.first.click()
        page.wait_for_timeout(400)
        box = page.locator("[data-frameos-node-search-input]")
        if box.count() == 0:
            print("!! 搜索面板未打开")
            return 1
        box.first.fill(setup["title"][:6])
        page.wait_for_timeout(400)
        results = page.locator("[data-frameos-node-search-result]")
        out["resultCount"] = results.count()
        if out["resultCount"] == 0:
            print(f"!! 无搜索结果 (title={setup['title']!r})")
            return 1
        # 点**目标那条**结果, 不是第一条
        target = page.locator(f'[data-frameos-node-search-result="{setup["id"]}"]')
        if target.count() == 0:
            print(f"!! 结果里没有目标节点 {setup['id']}")
            return 1
        target.first.click()
        page.wait_for_timeout(1400)   # 等 600ms 动画 + 余量
        out["after"] = page.evaluate(NODE_SCREEN_JS, setup["id"])
        out["selected"] = page.evaluate(
            "() => window.__frameos_store.getState().selectedNodeId"
        )
        out["zoom"] = page.evaluate(
            "() => { const t = document.querySelector('.react-flow__viewport');"
            " return t ? t.style.transform : null; }"
        )
        out["consoleErrors"] = errors
        browser.close()

    vw, vh = 1600, 950
    before, after = out["before"], out["after"]
    off_x = after["cx"] - vw / 2
    off_y = after["cy"] - vh / 2
    print("=== batch342 搜索聚焦探针 ===")
    print(f"目标节点 {out['setup']['id']} flow 坐标 {out['setup']['position']}")
    print(f"人为扭曲视口: {out['transform']}")
    print(f"点击前屏幕中心: ({before['cx']:.0f}, {before['cy']:.0f})")
    print(f"点击后屏幕中心: ({after['cx']:.0f}, {after['cy']:.0f})")
    print(f"视口中心应为  : ({vw / 2:.0f}, {vh / 2:.0f})")
    print(f"偏离视口中心  : dx={off_x:+.0f}px  dy={off_y:+.0f}px")
    print(f"选中态: {out['selected']} (目标 {out['setup']['id']})")
    print(f"最终 viewport transform: {out['zoom']}")
    if errors:
        print(f"console errors: {errors}")
    print("\n=== 判定 ===")
    print(json.dumps({
        "selected_ok": out["selected"] == out["setup"]["id"],
        "zoom_reached_2_73": "2.73" in (out["zoom"] or ""),
        "offset_x_px": round(off_x),
        "offset_y_px": round(off_y),
        # 视口 1600x950, 节点宽 300 高 200 → 缩到 2.73 后 819x546;
        # 落在视口内且居中意味着 |dx|<=~390, |dy|<=~200
        "centered": abs(off_x) <= 390 and abs(off_y) <= 200,
        "OFF_BY_VIEWPORT_ORIGIN": abs(off_x) > 100 or abs(off_y) > 100,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
