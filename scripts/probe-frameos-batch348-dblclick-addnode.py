#!/usr/bin/env python3
"""Batch 348 探针：「双击空白添加节点」是**半成品接线** —— 事件接了，菜单没渲染。

发现（代码审计 + 运行时验证）:
`page.tsx:196-206` 有完整的事件接线，注释明写
「双击空白处打开「选择节点类型」菜单 (Batch 168)」:
  - 监听 `.react-flow__pane` 的 dblclick
  - 跳过落在节点上的双击
  - `setPaneMenuAt({x, y})`

但 **store 外的 `paneMenuAt` 零引用** —— 没有任何组件读它。于是双击空白处:
  状态被写入 → **没有任何东西渲染** → 用户什么都没看到。

这一点还修正了 Batch 346 的一个判断: 当时记录「承诺只说添加节点、没说添加哪一种,
无法实现」并记为保真度差距。**但 Batch 168 的设计已经回答了这个问题** ——
它要的是一个「选择节点类型」**菜单**, 由用户选。所以这不是「无法实现」,
而是「做了一半」: 事件半边在、渲染半边缺。

本探针只测克隆自身事实(双击空白后到底有没有东西出现), 不声称源站菜单长什么样。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch348-dblclick-addnode.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

EMPTY_POINT_JS = """
() => {
  const rects = Array.from(document.querySelectorAll('.react-flow__node'))
    .map((n) => n.getBoundingClientRect());
  for (let y = 140; y < window.innerHeight - 140; y += 40) {
    for (let x = 140; x < window.innerWidth - 140; x += 40) {
      const hit = rects.some(
        (r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
      );
      if (!hit) return { x, y };
    }
  }
  return null;
}
"""

DOM_SNAPSHOT_JS = """
() => ({
  paneMenuAt: window.__frameos_store.getState().paneMenuAt,
  nodeCount: window.__frameos_store.getState().nodes.length,
  addNodeMenuOpen: window.__frameos_store.getState().isAddNodeMenuOpen,
  organizeMenuOpen: window.__frameos_store.getState().isOrganizeMenuOpen,
  contextMenu: document.querySelectorAll('[data-frameos-context-menu]').length,
  // 画面上是否出现了任何新增的浮层
  popovers: Array.from(document.body.children)
    .map((el) => el.tagName.toLowerCase() + '.' + (el.className || ''))
    .filter((s) => !s.startsWith('div.next') && !s.startsWith('script')),
  newNodeText: (document.body.textContent || '').includes('选择节点类型'),
  anyMenuList: document.querySelectorAll('ul, [role="menu"]').length,
})
"""


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        empty = page.evaluate(EMPTY_POINT_JS)
        out["empty_point"] = empty
        out["before"] = page.evaluate(DOM_SNAPSHOT_JS)
        page.mouse.dblclick(empty["x"], empty["y"])
        page.wait_for_timeout(800)
        out["after"] = page.evaluate(DOM_SNAPSHOT_JS)

        # 再点一次空白(测试状态是否被清/被覆盖)
        page.mouse.dblclick(empty["x"] + 60, empty["y"] + 40)
        page.wait_for_timeout(600)
        out["after_second"] = page.evaluate(DOM_SNAPSHOT_JS)

        # Esc 能否关掉
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        out["after_escape"] = page.evaluate(DOM_SNAPSHOT_JS)

        # ── 核心: 选一个类型 → 节点真的加在**双击的那一点**上 ──
        page.mouse.dblclick(empty["x"], empty["y"])
        page.wait_for_timeout(600)
        menu_open = page.locator("[data-frameos-pane-addnode-menu]").count()
        out["menu_open_before_pick"] = menu_open
        n_before = page.evaluate(
            "() => window.__frameos_store.getState().nodes.length"
        )
        page.locator('[data-frameos-pane-addnode-type="text"]').first.click()
        page.wait_for_timeout(700)
        picked = page.evaluate(
            """(pt) => {
              const s = window.__frameos_store.getState();
              const last = s.nodes[s.nodes.length - 1];
              const el = document.querySelector(
                `.react-flow__node[data-id="${last.id}"]`);
              const r = el ? el.getBoundingClientRect() : null;
              return {
                nodeCount: s.nodes.length,
                newId: last.id,
                type: last.type,
                flowPos: last.position,
                screenCenter: r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : null,
                clickedAt: pt,
                menuStillOpen:
                  document.querySelectorAll('[data-frameos-pane-addnode-menu]').length,
                paneMenuAt: s.paneMenuAt,
              };
            }""",
            empty,
        )
        out["picked"] = picked
        out["node_count_before_pick"] = n_before

        # 遮罩点击关闭
        # 重新找空白点: 上一步刚在 empty 处加了个节点, 那个点已经有节点了
        # (双击节点**不**弹菜单 —— 这是正确行为, 不是缺陷)。
        empty2 = page.evaluate(EMPTY_POINT_JS)
        page.mouse.dblclick(empty2["x"], empty2["y"])
        page.wait_for_timeout(500)
        page.locator("[data-frameos-pane-addnode-backdrop]").first.click(
            position={"x": 900, "y": 700}, force=True
        )
        page.wait_for_timeout(400)
        out["after_backdrop_click"] = page.evaluate(DOM_SNAPSHOT_JS)

        out["consoleErrors"] = errors
        browser.close()

    b, a, a2, ae = out["before"], out["after"], out["after_second"], out["after_escape"]
    picked = out["picked"]
    # 节点是否真的落在双击点: 屏幕中心应与双击点重合(容差半个节点)
    landed = False
    if picked.get("screenCenter"):
        landed = (
            abs(picked["screenCenter"]["x"] - picked["clickedAt"]["x"]) <= 160
            and abs(picked["screenCenter"]["y"] - picked["clickedAt"]["y"]) <= 110
        )
    print(f"[选类型后] nodeCount {out['node_count_before_pick']} → {picked['nodeCount']}  "
          f"type={picked['type']} flowPos={picked['flowPos']}")
    print(f"  双击点 {picked['clickedAt']}  节点屏幕中心 {picked['screenCenter']}  "
          f"落在双击点={landed}")
    print(f"  选完菜单关闭: menuInDom={picked['menuStillOpen']} paneMenuAt={picked['paneMenuAt']}")
    print("=== batch348 双击空白添加节点 探针 ===")
    print(f"空白点: {empty}")
    print(f"[双击前] paneMenuAt={b['paneMenuAt']} 节点数={b['nodeCount']}")
    print(f"[双击后] paneMenuAt={a['paneMenuAt']} 节点数={a['nodeCount']} "
          f"出现'选择节点类型'字样={a['newNodeText']} contextMenu={a['contextMenu']}")
    print(f"[二次双击] paneMenuAt={a2['paneMenuAt']}")
    print(f"[Esc 后]   paneMenuAt={ae['paneMenuAt']}")
    print(f"body 顶层子元素: {a['popovers'][:6]}")
    if out["consoleErrors"]:
        print(f"console errors: {out['consoleErrors']}")
    print("\n=== 判定 ===")
    print(json.dumps({
        "state_is_set_by_dblclick": a["paneMenuAt"] is not None,
        "state_updated_on_second_click":
            a2["paneMenuAt"] is not None and a2["paneMenuAt"] != a["paneMenuAt"],
        "no_menu_rendered": a["contextMenu"] == 0 and not a["newNodeText"],
        "no_node_added": a["nodeCount"] == b["nodeCount"],
        "escape_does_not_clear": ae["paneMenuAt"] is not None,
        "HALF_WIRED": a["paneMenuAt"] is not None and a["contextMenu"] == 0
        and not a["newNodeText"],
        "menu_renders_on_dblclick": out["menu_open_before_pick"] == 1,
        "node_added_after_pick": picked["nodeCount"] == n_before + 1,
        "node_landed_at_click_point": landed,
        "menu_closed_after_pick": picked["menuStillOpen"] == 0
        and picked["paneMenuAt"] is None,
        "backdrop_click_closes": out["after_backdrop_click"]["paneMenuAt"] is None,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
