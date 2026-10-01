#!/usr/bin/env python3
"""batch 846 源站探针：**焦点陷阱**、方向键、Esc 焦点归位。

§63 留下的范围限制：批 845 只测了**冷启动**（blur 之后按 Tab 找不找得到层），
没测「焦点**已经在层里**的时候，按 Tab 会不会跑出去」。源站右键菜单那一格当初
只能写"探不到"，正是因为缺这一条 —— 冷启动探不到 ≠ 层内出不来，两回事。

所以这一轮把三件事一次问全，口径与前几轮一致（真按键盘，读 `activeElement`）：

  ① **焦点陷阱**：先把焦点弄进层里，然后连按 Tab（以及 Shift+Tab），记录
     「第几次按出去、出去后停在哪个控件上、还回不回来」。
  ② **方向键**：层内按 ArrowDown / ArrowUp，焦点在层内**移动**还是不动？
     ARIA menu 的标准做法是漫游 tabindex + 上下键；源站菜单实测就是漫游
     tabindex（2 项 0、6 项 -1），那方向键到底走不走。
  ③ **Esc 焦点归位**：Esc 关掉层之后，焦点回到哪？（触发器？body？画布？）
     这是键盘用户唯一的"我还在哪"的锚。

只观察，不点任何付费购买流程。
"""

import json

MAX_TABS = 12
MAX_KEYS = 4

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)

# 读焦点：身份 + 边界框 + 是否被不透明的外人盖住（四代判据，第 4 代）
FOCUS_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body)
    return {who: 'body', inside: null};
  const r = a.getBoundingClientRect();
  const paintsOver = (e) => {
    for (let n = e; n && n !== document.body; n = n.parentElement) {
      if (n === a || (n.contains && n.contains(a))) return false;
      const bg = getComputedStyle(n).backgroundColor || '';
      if (bg !== 'rgba(0, 0, 0, 0)'
          && !bg.startsWith('rgba(0, 0, 0, 0)')) return true;
    }
    return false;
  };
  const EDGE = [[r.left - 1, r.top + r.height / 2],
                [r.right + 1, r.top + r.height / 2],
                [r.x + r.width / 2, r.top - 1],
                [r.x + r.width / 2, r.bottom + 1]];
  let edges = 0, top = null;
  for (const [ex, ey] of EDGE) {
    const st = document.elementsFromPoint(ex, ey) || [];
    const t = st[0] || null;
    if (!t || t === a || a.contains(t) || (t.contains && t.contains(a))) continue;
    if (!paintsOver(t)) continue;
    edges += 1;
    if (!top) top = t;
  }
  return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
            || a.getAttribute('aria-label')
            || (a.className || '').toString().replace(/\\s+/g, ' ').slice(0, 34))
            || (a.innerText || '').trim().slice(0, 14)),
          al: (a.getAttribute('aria-label') || '').trim().slice(0, 26),
          tid: a.getAttribute('data-testid') || '',
          tabindex: a.getAttribute('tabindex'),
          txt: (a.innerText || a.getAttribute('placeholder') || '')
                 .trim().replace(/\\s+/g, ' ').slice(0, 20),
          w: Math.round(r.width), h: Math.round(r.height),
          ring_hidden: edges === EDGE.length, edges: edges + '/' + EDGE.length,
          hidden_by: top ? (top.tagName + '/' + (top.getAttribute('data-testid')
            || top.getAttribute('aria-label') || '')) : null};
}"""


def in_layer(tids):
    return page.evaluate("""(tids) => {
      const a = document.activeElement;
      for (const t of tids) {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (e && e.contains(a)) return t;
      }
      return null;
    }""", tids)


def get_focus():
    d = page.evaluate(FOCUS_JS)
    d["in"] = in_layer(TIDS)
    return d


def press_tabs(label, tids, max_n=MAX_TABS, shift=False):
    """从「焦点在层里」出发连按 Tab，看第几次按出去、出去后停哪、回不回来。"""
    out = {"label": label, "steps": [], "escaped_at": None,
           "landed": None, "came_back": False}
    key = "Shift+Tab" if shift else "Tab"
    for i in range(1, max_n + 1):
        page.keyboard.press(key)
        f = get_focus()
        inside = bool(f.get("in"))
        out["steps"].append({"i": i, "inside": inside, "who": f.get("who"),
                             "al": f.get("al"), "ring_hidden": f.get("ring_hidden")})
        if not inside and out["escaped_at"] is None:
            out["escaped_at"] = i
            out["landed"] = {k: f.get(k) for k in
                             ("who", "al", "tid", "txt", "ring_hidden",
                              "edges", "hidden_by")}
        if out["escaped_at"] and inside:
            out["came_back"] = True
            out["back_at"] = i
            break
    return out


def press_keys(label, key, max_n=MAX_KEYS):
    """连按一个方向键，看焦点在层内**移动**还是不动。"""
    seq = []
    for _ in range(max_n):
        page.keyboard.press(key)
        f = get_focus()
        seq.append({"who": f.get("who"), "al": f.get("al"),
                    "in": bool(f.get("in"))})
    uniq = len({s["who"] for s in seq})
    return {"label": label, "key": key, "seq": seq,
            "moved": uniq > 1, "stayed_in_layer": all(s["in"] for s in seq)}


def reset():
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)


TIDS = []
results = {}

# ── ① 画布右键菜单（源站 role=menu，漫游 tabindex 实测 2 项 0 / 6 项 -1）──
reset()
spot = page.evaluate("""() => {
  for (const [x, y] of [[430, 620], [420, 660], [450, 700]]) {
    const e = document.elementFromPoint(x, y);
    if (!e || e.closest('[data-id]')) continue;
    if (!e.closest('.react-flow__pane, .react-flow__renderer')) continue;
    return {x, y};
  }
  return null;
}""")
if spot:
    page.mouse.click(spot["x"], spot["y"], button="right")
    page.wait_for_timeout(1400)
    TIDS = ["canvas-context-menu"]
    at_open = get_focus()
    # 焦点已经在层里就动手；不在就先点第一个可聚焦项（模拟用户点进去）
    if not at_open.get("in"):
        page.evaluate("""() => {
          const m = document.querySelector('[data-testid=canvas-context-menu]');
          const it = m && m.querySelector('[role=menuitem],button');
          if (it) it.focus();
        }""")
        page.wait_for_timeout(300)
    entered = get_focus()
    results["画布右键菜单"] = {
        "at_open": at_open, "entered": entered,
        "tab": press_tabs("Tab", TIDS),
        "arrow_down": press_keys("ArrowDown", "ArrowDown"),
        "arrow_up": press_keys("ArrowUp", "ArrowUp"),
    }
    page.keyboard.press("Escape")
    page.wait_for_timeout(900)
    results["画布右键菜单"]["after_escape"] = get_focus()
    reset()

# ── ② 顶栏搜索（源站 role=dialog 320×504，开层即拿焦点）────────────────
TIDS = ["canvas-feature-panel"]
hit = page.evaluate("""() => {
  const bs = [...document.querySelectorAll('[data-testid=canvas-panel-launcher]')];
  const r = bs[0].getBoundingClientRect();
  return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
}""")
page.mouse.click(hit["x"], hit["y"])
page.wait_for_timeout(1800)
at_open = get_focus()
if not at_open.get("in"):
    page.evaluate("""() => {
      const p = document.querySelector('[data-testid=canvas-feature-panel]');
      const it = p && p.querySelector('input,button,[tabindex]');
      if (it) it.focus();
    }""")
    page.wait_for_timeout(300)
entered = get_focus()
results["顶栏·搜索"] = {
    "at_open": at_open, "entered": entered,
    "tab": press_tabs("Tab", TIDS),
    "arrow_down": press_keys("ArrowDown", "ArrowDown"),
}
page.keyboard.press("Escape")
page.wait_for_timeout(900)
results["顶栏·搜索"]["after_escape"] = get_focus()
reset()

# ── ③ 时间线全屏（源站 role=dialog 1512×950，开层即拿焦点）────────────
node = page.evaluate("""() => {
  for (const n of document.querySelectorAll('[data-id]')) {
    const b = [...n.querySelectorAll('button,[role=menuitem]')]
      .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
    if (!b) continue;
    const rn = n.getBoundingClientRect(), rb = b.getBoundingClientRect();
    return {nx: Math.round(rn.x + rn.width / 2), ny: Math.round(rn.y + rn.height / 2),
            bx: Math.round(rb.x + rb.width / 2), by: Math.round(rb.y + rb.height / 2)};
  }
  return null;
}""")
if node:
    page.mouse.click(node["nx"], node["ny"])
    page.wait_for_timeout(1600)
    b2 = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button,[role=menuitem]')]
        .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
    }""")
    if b2:
        page.mouse.click(b2["x"], b2["y"])
        page.wait_for_timeout(2800)
        TIDS = ["timeline-fullscreen-editor"]
        at_open = get_focus()
        if not at_open.get("in"):
            page.evaluate("""() => {
              const p = document.querySelector(
                '[data-testid=timeline-fullscreen-editor]');
              const it = p && p.querySelector(
                'input,button,[tabindex]:not([tabindex="-1"])');
              if (it) it.focus();
            }""")
            page.wait_for_timeout(300)
        entered = get_focus()
        results["时间线全屏"] = {
            "at_open": at_open, "entered": entered,
            "tab": press_tabs("Tab", TIDS),
            "arrow_down": press_keys("ArrowDown", "ArrowDown"),
        }
        page.keyboard.press("Escape")
        page.wait_for_timeout(900)
        results["时间线全屏"]["after_escape"] = get_focus()
        page.screenshot(path="/tmp/b846-source-fullscreen.png", full_page=False)

print("\n\n===== 源站：焦点陷阱 / 方向键 / Esc 归位 =====")
for k, v in results.items():
    print("=" * 74)
    print(f"【{k}】")
    print("  开层瞬间焦点:", json.dumps(v["at_open"], ensure_ascii=False)[:230])
    print("  起测时焦点  :", json.dumps(v["entered"], ensure_ascii=False)[:230])
    t = v["tab"]
    print(f"  焦点陷阱：第 {t['escaped_at']} 次 Tab 按出层外"
          f"（回得来={t['came_back']}）")
    print("     落在:", json.dumps(t["landed"], ensure_ascii=False)[:230])
    print("     轨迹:", " → ".join(
        f"{s['who'][:22]}{'·内' if s['inside'] else '·外'}"
        f"{'·环隐' if s['ring_hidden'] else ''}"
        for s in t["steps"][:8]))
    for kk in ("arrow_down", "arrow_up"):
        if kk in v:
            a = v[kk]
            print(f"  {kk}: 按了 4 次，焦点移动={a['moved']} "
                  f"始终在层内={a['stayed_in_layer']}")
            print("     ", " → ".join(s["who"][:20] for s in a["seq"]))
    print("  Esc 之后焦点:", json.dumps(v.get("after_escape"),
                                       ensure_ascii=False)[:230])
