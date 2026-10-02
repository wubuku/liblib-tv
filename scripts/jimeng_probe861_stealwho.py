#!/usr/bin/env python3
"""batch 861：**二分定位**「重渲染把焦点抢回面板」的执行者。

§78 证实了效应（E2 抢焦点 / E3 不抢），但**归因错了**：换掉 `autoFocus`
照样抢。而 §78 自己留了一条**必须补的对照**：

> E2 用「在搜索框里打字」来触发重渲染，这**同时**改了 `query` state。
> 抢焦点究竟由「重渲染」还是由「`query` 变化」引起，本批**没有分开测**
> （对照组该是「触发一次不改变任何 state 的重渲染」）。⚠️ 这条不补上，
> 下一批的结论会站不稳。

这一批把四件事**分开**测，每一件都能单独判红：

  T1 **纯重渲染**（不改任何 state）：改**别的**组件的 state
     （例如缩放百分比），让画布重渲染 —— 面板订阅 `nodes` 才重渲染，
     所以这一步要看**面板到底重不重渲染**。用 MutationObserver 数。
  T2 **改 query**：真的在搜索框里打字（与 §78 的 E2 同款）。
  T3 **不重渲染、只等**：E3 对照。
  T4 **画布变动**：真的让画布节点变动（选一个节点）⇒ 面板订阅的
     `nodes` 变 ⇒ 面板必然重渲染。

同时给每一步**数一次面板重渲染次数**（MutationObserver 挂在面板根上），
这样「重渲染」就不再是推测而是**观测量**。

⚠️ 本探针**只诊断，不改产品**。跑法（需 dev server 在跑）：

    /opt/miniconda3/bin/python3 scripts/jimeng_probe861_stealwho.py
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright  # noqa: E402

URL = "http://localhost:4317/jimeng/canvas/demo"
LAYER = "jimeng-search-overlay"

WHO_JS = """(tid) => {
  const L = document.querySelector(`[data-testid="${tid}"]`);
  const a = document.activeElement;
  if (!a || a === document.body)
    return {who: 'body', in_layer: false, tid: ''};
  return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
            || a.getAttribute('aria-label') || '')
            .toString().slice(0, 26)),
          in_layer: !!(L && L.contains(a)),
          tid: a.getAttribute('data-testid') || ''};
}"""

# 数面板重渲染次数：挂 MutationObserver，childList/subtree/characterData 全算
COUNT_JS = """(tid) => {
  const L = document.querySelector(`[data-testid="${tid}"]`);
  if (!L) return {ok: false};
  window.__reRender = 0;
  if (window.__obs) window.__obs.disconnect();
  window.__obs = new MutationObserver((ms) => {
    window.__reRender += ms.length;
  });
  window.__obs.observe(L, {childList: true, subtree: true,
                           characterData: true, attributes: true});
  return {ok: true};
}"""

READ_JS = """() => ({reRender: window.__reRender || 0})"""


def who(pg):
    return pg.evaluate(WHO_JS, LAYER)


def arm(pg):
    pg.evaluate(COUNT_JS, LAYER)


def re_render(pg):
    return (pg.evaluate(READ_JS) or {}).get("reRender", -1)


def land_outside(pg):
    """把焦点放到一个**确定的层外**控件上（顶栏「更多」）。"""
    pg.evaluate("() => { const a = document.activeElement;"
                " if (a && a.blur) a.blur(); }")
    for _ in range(60):
        pg.keyboard.press("Tab")
        w = who(pg)
        if w.get("tid") == "canvas-more-trigger":
            return w
    return None


def step(pg, name, action, res):
    landed = land_outside(pg)
    if not landed:
        res[name] = {"why": "走不到层外锚点 canvas-more-trigger"}
        print(f"  {name:<22} ⚠ {res[name]['why']}")
        return
    arm(pg)                       # 从**焦点落位之后**开始数，避免计入落位过程
    before = who(pg)
    action(pg)
    pg.wait_for_timeout(600)
    after = who(pg)
    n = re_render(pg)
    stolen = (not before["in_layer"]) and after["in_layer"]
    res[name] = {"before": before, "after": after,
                 "reRender": n, "stolen": bool(stolen)}
    print(f"  {name:<22} 重渲染 {n:>4} 次｜抢焦点={stolen!s:<5} "
          f"before={before['who']!r} after={after['who']!r}")


def run(pg):
    out = {"url": URL}
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    pg.set_viewport_size({"width": 1512, "height": 1200})
    pg.wait_for_timeout(1500)

    trg = pg.locator('button[aria-label="搜索"]')
    if not trg.count():
        out["verdict"] = "no_search_button"
        print("!! 找不到搜索按钮")
        return out
    trg.first.click(timeout=8000)
    pg.wait_for_timeout(1000)
    if not pg.locator(f'[data-testid="{LAYER}"]').count():
        out["verdict"] = "panel_not_open"
        print("!! 面板开不出来")
        return out
    out["layer_open"] = True
    res = {}

    # ⚠️ 批 861b：直接量审计的**那一次** Tab（blur 之后立刻按，不做任何别的）。
    #    §79 查出的「tabs:1」 mystery 就在这里 —— 探针之前每次都是先 Tab 很多
    #    次找锚点，把起点冲掉了；审计是 blur 后**第一次**就按键。
    print("\n-- T0：blur() 之后**第一次** Tab 落在哪（复刻审计口径）--")
    arm(pg)
    pg.evaluate("() => { const a = document.activeElement;"
                " if (a && a.blur) a.blur(); }")
    pg.wait_for_timeout(120)
    b0 = who(pg)
    pg.keyboard.press("Tab")
    pg.wait_for_timeout(200)
    a0 = who(pg)
    res["T0_first_tab"] = {"before": b0, "after": a0,
                           "first_tab_inside": bool(a0.get("in_layer")),
                           "reRender": re_render(pg)}
    print(f"  T0 第一次 Tab: before={b0['who']!r} → after={a0['who']!r} "
          f"in_layer={a0.get('in_layer')}")

    print("\n-- T3 对照：什么都不做，只等 600ms --")
    step(pg, "T3_no_op", lambda p: None, res)

    print("\n-- T2：真的在搜索框里打字（改 query）--")
    def typing(p):
        inp = p.locator(f'[data-testid="{LAYER}"] input').first
        if inp.count():
            inp.fill("审")
    step(pg, "T2_type_query", typing, res)

    # ⚠️⚠️ 批 861b 补的关键对照：`fill()` **自己就会把焦点放进输入框**。
    #    所以 T2 的「抢焦点」很可能**是实验自己造成的**，不是产品行为。
    #    这一步用**不碰输入框**的方式改同一个 state：直接派发原生 input 事件。
    print("\n-- T2b：改 query 但**完全不碰输入框**（原生事件注入）--")
    def typing_native(p):
        p.evaluate("""(tid) => {
          const L = document.querySelector(`[data-testid="${tid}"]`);
          const inp = L && L.querySelector('input');
          if (!inp) return;
          // 用原生 setter 改值 + 派发 input 事件：走的是 React 的 onChange，
          // 但**不产生任何真实用户焦点**，activeElement 不会被挪动。
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
          setter.call(inp, '审');
          inp.dispatchEvent(new Event('input', {bubbles: true}));
        }""", LAYER)
    step(pg, "T2b_native_no_focus", typing_native, res)

    print("\n-- T1：改**别的**组件的 state（缩放），面板订阅的是 nodes --")
    def zoom(p):
        z = p.locator('header[aria-label="Canvas top bar"] '
                      'button[aria-label^="Zoom options"]')
        if z.count():
            z.first.click(timeout=5000)
            p.wait_for_timeout(300)
            p.keyboard.press("Escape")
    step(pg, "T1_zoom_only", zoom, res)

    print("\n-- T4：真的让画布节点变动（选中节点）⇒ 订阅的 nodes 变 --")
    def pick_node(p):
        n = p.locator('.react-flow__node').first
        if n.count():
            n.click(timeout=5000)
    step(pg, "T4_canvas_change", pick_node, res)

    out["steps"] = res
    # 判决：只有 T2 抢 ⇒ 跟 query 有关；T4 抢 ⇒ 跟 nodes 订阅重渲染有关；
    #       T1/T3 都抢 ⇒ 跟「等」本身有关（异步焦点归还）
    stolen = {k: v.get("stolen") for k, v in res.items() if "stolen" in v}
    out["stolen"] = stolen
    out["verdict"] = stolen
    print(f"\n== 抢焦点的步：{[k for k, v in stolen.items() if v] or '无'} ==")
    return out


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1512, "height": 1200})
        pg = ctx.new_page()
        try:
            res = run(pg)
        finally:
            b.close()
    with open("/tmp/b861-stealwho.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n== 已写 /tmp/b861-stealwho.json ==")


if __name__ == "__main__":
    main()
