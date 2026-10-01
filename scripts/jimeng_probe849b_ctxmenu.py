#!/usr/bin/env python3
"""batch 849b：`画布右键菜单` 的「Tab 60 次都进不去」到底是**真缺陷**还是**判据量错了对象**。

§849 那轮把键盘覆盖面从 12 层补到 21 层，顺带冒出**一条新缺陷**：
`[画布右键菜单] 浮层='canvas-context-menu' Tab 60 次都没进到 canvas-context-menu 里`。
而 844/845/846/847/848 五轮同一份产品代码都是 0 缺陷。

第一次归因是「下拉没关干净、漏到后面污染了 Tab 序列」——**被证伪**：修好 `close_open()`
的 scope 之后，「没把层收掉」一条也没报，那条缺陷**照样在**。归因错了就不该继续猜。

这一轮只看**轨迹**：每按一次 Tab，落在哪个元素、在不在层里、层有**几个**。
`keyboard_probe` 用的是 `document.querySelector('[data-testid="…"]')` ——
**只取第一个**。而复刻里 `canvas-context-menu` 这个 testid 是
`JimengContextMenu`（节点菜单）和 `JimengPaneContextMenu`（空画布菜单）**共用**的
（批 828 有意照抄源站同名）。DOM 里若同时有两个，判据量的那个和焦点进的
那个可能不是同一个 ⇒ 报「进不去」。这是**判据量错对象**，不是产品缺陷。

跑法：复刻 demo，右键点空画布，然后按 60 次 Tab 逐次记落点。
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"

out: dict = {}

# 与 jimeng_unclickable_audit.py 的 open_layer() 逐字同款
OPEN_LAYER_JS = """() => {
  const SHELL = 'react-flow__renderer, react-flow__pane, '
              + 'react-flow__viewport, react-flow__nodes, '
              + 'react-flow__node, react-flow__node-toolbar';
  const LAYER = '.react-flow__node-panel, [role=menu], [role=listbox], '
              + '[role=dialog], [role=popover], [data-testid$="-listbox"], '
              + '[data-testid$="-menu"], [data-testid$="-panel"], '
              + '[data-testid$="-palette"]';
  for (const e of document.querySelectorAll(LAYER)) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 20) continue;
    if (e.closest(SHELL)) continue;
    if (e.closest('nextjs-portal')) continue;
    const hasFocusable = e.querySelector(
      'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"]),'
      + '[role=menuitem],[role=option]');
    if (!hasFocusable) continue;
    return e.getAttribute('data-testid')
        || e.getAttribute('aria-label') || e.getAttribute('role') || '?';
  }
  return '';
}"""

# 每一步：焦点是谁、在不在**每一个**同名层里、层一共几个
STEP_JS = """(tid) => {
  const layers = [...document.querySelectorAll(`[data-testid="${tid}"]`)];
  const a = document.activeElement;
  const name = (e) => !e ? '(null)'
    : ((e.getAttribute('data-testid') || e.getAttribute('aria-label')
        || (e.innerText || '').trim().replace(/\\s+/g,' ').slice(0,14)
        || e.tagName));
  return {
    n_layers: layers.length,
    layer_tids: layers.map(L => (L.getAttribute('data-testid') || '')
                        + (L.querySelector('[data-testid^="pane-menu"]')
                           ? '(pane)' : L.querySelector('[data-testid$="-menu-item"]')
                             ? '(node)' : '(?)')),
    active: a ? {tag: a.tagName, tid: a.getAttribute('data-testid') || '',
                 al: (a.getAttribute('aria-label') || '').slice(0, 24),
                 txt: (a.innerText || '').trim().replace(/\\s+/g,' ').slice(0,14),
                 tabindex: a.getAttribute('tabindex') || '(null)'}
               : null,
    // 判据口径：querySelector 只取**第一个**
    in_first: layers.length ? !!layers[0].contains(a) : false,
    in_any: layers.some(L => L.contains(a)),
  };
}"""


def main() -> int:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        c = b.new_context(viewport={"width": 1680, "height": 1050})
        pg = c.new_page()
        pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(9000)

        # 落点必须先验是**空画布**（840 踩过：硬点坐标落到节点上，
        # 开出来的是节点菜单，不是画布菜单）
        spot = pg.evaluate("""() => {
          for (const [x, y] of [[840,640],[700,700],[900,560],[600,800],[1000,760]]) {
            const t = document.elementFromPoint(x, y);
            if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
              return [x, y, t.tagName];
          }
          return null;
        }""")
        print("== 右键落点 ==", spot, "（必须落在 .react-flow__pane 且不在节点里）")
        out["spot"] = spot
        if not spot:
            print("!! 找不到空画布落点（前置态没成立）")
            c.close(); b.close()
            return 2

        pg.mouse.click(spot[0], spot[1], button="right")
        pg.wait_for_timeout(900)
        lt = pg.evaluate(OPEN_LAYER_JS)
        n = pg.locator('[data-testid="canvas-context-menu"]').count()
        print(f"open_layer() = {lt!r}；DOM 里 canvas-context-menu 有 {n} 个")
        out["open_layer"], out["n_menus"] = lt, n
        if not n:
            print("!! 右键菜单没开（前置态没成立）")
            c.close(); b.close()
            return 2

        # 开层那一瞬间的焦点（blur 之前）
        at_open = pg.evaluate(STEP_JS, "canvas-context-menu")
        print(f"开层焦点: active={at_open['active']}")
        print(f"          in_first={at_open['in_first']} in_any={at_open['in_any']} "
              f"n_layers={at_open['n_layers']} {at_open['layer_tids']}")

        # 冷启动：blur 之后按 60 次 Tab，**逐次记落点**
        pg.evaluate("() => { const a = document.activeElement;"
                    " if (a && a.blur) a.blur(); }")
        seq = []
        for i in range(1, 61):
            pg.keyboard.press("Tab")
            s = pg.evaluate(STEP_JS, "canvas-context-menu")
            s["i"] = i
            seq.append(s)
            a = s["active"] or {}
            flag = "IN-any" if s["in_any"] else ("IN-first" if s["in_first"] else "——")
            print(f"  Tab {i:>2} [{flag:<7}] tid={a.get('tid',''):<22} "
                  f"al={a.get('al',''):<24} txt={a.get('txt','')!r} "
                  f"tabindex={a.get('tabindex')}")

        hits_first = [s["i"] for s in seq if s["in_first"]]
        hits_any = [s["i"] for s in seq if s["in_any"]]
        print("\n== 判决 ==")
        print(f"  落在**第一个**同名层里（判据口径）：{hits_first or '一次都没有'}")
        print(f"  落在**任一**同名层里（真实口径）  ：{hits_any or '一次都没有'}")
        print(f"  DOM 里 canvas-context-menu 个数：{seq[0]['n_layers'] if seq else '?'}")
        if hits_any and not hits_first:
            print("  ⇒ **判据量错了对象**：焦点确实进了层，但进的是**另一个**"
                  "同名层（querySelector 只取第一个）⇒ 这是判据缺陷，不是产品缺陷")
        elif not hits_any:
            print("  ⇒ 焦点 60 次**一次都没进**任何同名层 ⇒ 要么真缺陷，"
                  "要么层不可聚焦（看上面 tabindex 列）")
        else:
            print("  ⇒ 判据口径与真实口径一致，不是同名层混淆")

        out["at_open"] = at_open
        out["seq"] = seq
        out["hits_first"], out["hits_any"] = hits_first, hits_any

        # 对照实验：审计那轮跑到右键菜单时，画布上**已经插了文本和音频节点**
        # （还开过 9 个下拉）。干净画布 Tab 34 次就进得去 —— 那审计那轮
        # 为什么会「60 次都没进到」？两个可能，处置完全相反：
        #   (a) 元素多了、要按的次数超过 **max_tabs=60 这个上限**
        #       ⇒ 判据把「上限不够」报成了「进不去」，方向就错了
        #   (b) 真的进不去（前面某状态留下了什么）
        # 不猜：插进同样的节点，再量一次，上限提到 120。
        print("\n== 对照：先插文本 + 音频节点，再量同一件事 ==")
        for kind in ("文本", "音频"):
            loc = pg.locator(f'button[aria-label="{kind}"]')
            if loc.count():
                try:
                    loc.first.click(timeout=8000)
                    pg.wait_for_timeout(1600)
                    print(f"  插入了 {kind}")
                except Exception as e:
                    print(f"  ⚠ 插 {kind} 失败 {type(e).__name__}")
        n_nodes = pg.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length")
        n_focus = pg.evaluate("""() => {
          const sels = 'button,[href],input,select,textarea,[tabindex]';
          return [...document.querySelectorAll(sels)].filter(e => {
            if (e.disabled) return false;
            if (e.getAttribute('tabindex') === '-1') return false;
            const st = getComputedStyle(e);
            if (st.display === 'none' || st.visibility === 'hidden') return false;
            const r = e.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
          }).length;
        }""")
        print(f"  画布节点 {n_nodes} 个、文档里可聚焦元素 {n_focus} 个")
        out["after_insert"] = {"nodes": n_nodes, "focusables": n_focus}

        pg.keyboard.press("Escape")
        pg.wait_for_timeout(400)
        spot2 = pg.evaluate("""() => {
          for (const [x, y] of [[840,640],[700,700],[900,560],[600,800],[1000,760]]) {
            const t = document.elementFromPoint(x, y);
            if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
              return [x, y];
          }
          return null;
        }""")
        print("  第二个右键落点 ==", spot2)
        out["spot2"] = spot2
        if not spot2:
            print("  !! 插完节点后找不到空画布落点 ⇒ 对照实验前置态没成立")
            c.close(); b.close()
            return 2
        pg.mouse.click(spot2[0], spot2[1], button="right")
        pg.wait_for_timeout(900)
        print(f"  open_layer() = {pg.evaluate(OPEN_LAYER_JS)!r}")
        pg.evaluate("() => { const a = document.activeElement;"
                    " if (a && a.blur) a.blur(); }")
        seq2, hit2 = [], None
        for i in range(1, 121):            # ⚠️ 上限提到 120，看它到底要走多少
            pg.keyboard.press("Tab")
            s = pg.evaluate(STEP_JS, "canvas-context-menu")
            s["i"] = i
            seq2.append(s)
            if s["in_any"]:
                hit2 = i
                break
        print(f"  ⇒ 上限 120 时，第 {hit2} 次 Tab 进得去"
              f"（60 次上限{'够' if (hit2 or 999) <= 60 else '**不够**'}）")
        out["hit2_max120"] = hit2
        out["seq2"] = seq2

        c.close(); b.close()

    with open("/tmp/b849b-ctxmenu.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n明细 /tmp/b849b-ctxmenu.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
