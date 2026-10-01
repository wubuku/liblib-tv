#!/usr/bin/env python3
"""batch 846 源站探针（第二轮）：**每个测量都从重开的层起手**。

第一轮把三个测量串着跑：`Tab 陷阱 → 方向键 → Esc`，可第一个测量是**破坏性**的
—— 按 Tab 已经把焦点赶出了层，于是方向键和 Esc 两栏**全都测在层外**，数据是
废的。**一个探针串着跑三个破坏性测量，等于只测了第一个。**

所以这一轮给每个测量一个 `with_layer()`：重开该层、把焦点弄回层内、再测。
三栏互不污染。

已取到的源站基线（第一轮，未污染的部分）：

  · 右键菜单   开层即接管（第一项「新建节点」），**第 1 次 Tab 就跑出去**（无陷阱）
  · 搜索面板   开层即接管（ASIDE 自己，tabindex=-1），**第 10 次 Tab 跑出去**（无陷阱）
  · 时间线全屏 开层即接管（dialog 自己），**12 次 Tab 全在层内**（**有陷阱**），
                ArrowDown 不移动焦点（它不是菜单），**Esc 关不掉**（焦点仍在层内）

方向键与 Esc 归位两栏这一轮重测。

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

FOCUS_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body) return {who: 'body'};
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
            || (a.className || '').toString().replace(/\\s+/g, ' ').slice(0, 32))
            || (a.innerText || '').trim().slice(0, 14)),
          al: (a.getAttribute('aria-label') || '').trim().slice(0, 26),
          tid: a.getAttribute('data-testid') || '',
          tabindex: a.getAttribute('tabindex'),
          txt: (a.innerText || a.getAttribute('placeholder') || '')
                 .trim().replace(/\\s+/g, ' ').slice(0, 18),
          ring_hidden: edges === EDGE.length, edges: edges + '/' + EDGE.length};
}"""

TIDS = []


def in_layer():
    return page.evaluate("""(tids) => {
      const a = document.activeElement;
      for (const t of tids) {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (e && e.contains(a)) return t;
      }
      return null;
    }""", TIDS)


def focus_now():
    d = page.evaluate(FOCUS_JS)
    d["in"] = in_layer()
    return d


def layer_open():
    return bool(TIDS) and bool(page.evaluate(
        "(tids) => tids.some(t => !!document.querySelector(`[data-testid=\"${t}\"]`))",
        TIDS))


def open_layer():
    """重开该层（三个测量各自的起手式）。"""
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    if layer_open():
        return True
    if "canvas-context-menu" in TIDS:
        spot = page.evaluate("""() => {
          for (const [x, y] of [[430, 620], [420, 660], [450, 700]]) {
            const e = document.elementFromPoint(x, y);
            if (!e || e.closest('[data-id]')) continue;
            if (!e.closest('.react-flow__pane, .react-flow__renderer')) continue;
            return {x, y};
          }
          return null;
        }""")
        if not spot:
            return False
        page.mouse.click(spot["x"], spot["y"], button="right")
        page.wait_for_timeout(1300)
    elif "canvas-feature-panel" in TIDS:
        t = page.evaluate("""() => {
          const bs = [...document.querySelectorAll(
            '[data-testid=canvas-panel-launcher]')];
          const r = bs[0].getBoundingClientRect();
          return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
        }""")
        page.mouse.click(t["x"], t["y"])
        page.wait_for_timeout(1700)
    elif "timeline-fullscreen-editor" in TIDS:
        n = page.evaluate("""() => {
          for (const x of document.querySelectorAll('[data-id]')) {
            const b = [...x.querySelectorAll('button,[role=menuitem]')]
              .find(y => (y.getAttribute('aria-label')||'').includes('全屏编辑'));
            if (!b) continue;
            const rn = x.getBoundingClientRect();
            return {x: Math.round(rn.x + rn.width/2), y: Math.round(rn.y + rn.height/2)};
          }
          return null;
        }""")
        if not n:
            return False
        page.mouse.click(n["x"], n["y"])
        page.wait_for_timeout(1500)
        b = page.evaluate("""() => {
          const b = [...document.querySelectorAll('button,[role=menuitem]')]
            .find(x => (x.getAttribute('aria-label')||'').includes('全屏编辑'));
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""")
        if not b:
            return False
        page.mouse.click(b["x"], b["y"])
        page.wait_for_timeout(2700)
    return layer_open()


def ensure_focus_inside():
    """把焦点弄回层内（层开着自己不管，就手动 focus 第一个可聚焦项）。"""
    if in_layer():
        return focus_now()
    page.evaluate("""(tids) => {
      for (const t of tids) {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (!e) continue;
        const it = e.querySelector(
          'input,button,a[href],select,textarea,[tabindex]');
        if (it) { it.focus(); return; }
        e.focus && e.focus();
        return;
      }
    }""", TIDS)
    page.wait_for_timeout(300)
    return focus_now()


def with_layer(fn):
    """**每个测量都从重开的层起手** —— 三个破坏性测量串着跑，只有第一个是准的。"""
    if not open_layer():
        return {"why": "这一层重开不了（前置态没成立）"}
    start = ensure_focus_inside()
    if not start.get("in"):
        return {"why": "重开后焦点进不了层（前置态没成立）", "at_start": start}
    return fn(start)


def probe_tab(start):
    esc_at, landed, steps = None, None, []
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        f = focus_now()
        steps.append({"i": i, "in": f.get("in"), "who": f.get("who"),
                      "ring_hidden": f.get("ring_hidden")})
        if not f.get("in"):
            esc_at = i
            landed = {k: f.get(k) for k in ("who", "al", "tid", "txt",
                                            "ring_hidden", "edges")}
            break
    return {"start": start, "escaped_at": esc_at, "landed": landed,
            "trapped": esc_at is None, "steps": steps,
            "why": None if esc_at is None
                   else f"焦点在层里时按第 {esc_at} 次 Tab 跑出去了"}


def probe_shift_tab(start):
    esc_at, landed = None, None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Shift+Tab")
        f = focus_now()
        if not f.get("in"):
            esc_at = i
            landed = {k: f.get(k) for k in ("who", "al", "tid", "txt")}
            break
    return {"start": start, "escaped_at": esc_at, "landed": landed,
            "trapped": esc_at is None,
            "why": None if esc_at is None
                   else f"Shift+Tab 第 {esc_at} 次跑出去了"}


def probe_key(start, key):
    seq = []
    for _ in range(MAX_KEYS):
        page.keyboard.press(key)
        f = focus_now()
        seq.append({"who": f.get("who"), "al": f.get("al"), "in": f.get("in")})
    uniq = len({s["who"] for s in seq})
    return {"start": start, "key": key, "seq": seq, "moved": uniq > 1,
            "stayed_in_layer": all(s["in"] for s in seq),
            "first": seq[0]["who"] if seq else None}


def probe_escape(start):
    """Esc 之后焦点回哪 —— 并且**层到底关没关**（两件事，不许混成一件）。"""
    before = focus_now()
    page.keyboard.press("Escape")
    page.wait_for_timeout(900)
    after = focus_now()
    return {"before": before, "after": after,
            "layer_closed": not layer_open(),
            "focus_came_back": bool(after.get("in"))}


LAYERS = [
    ("画布右键菜单", ["canvas-context-menu"]),
    ("顶栏·搜索", ["canvas-feature-panel"]),
    ("时间线全屏", ["timeline-fullscreen-editor"]),
]

out = {}
for name, tids in LAYERS:
    TIDS = tids
    rec = {}
    rec["tab"] = with_layer(probe_tab)
    rec["shift_tab"] = with_layer(probe_shift_tab)
    rec["arrow_down"] = with_layer(lambda s: probe_key(s, "ArrowDown"))
    rec["arrow_up"] = with_layer(lambda s: probe_key(s, "ArrowUp"))
    rec["escape"] = with_layer(probe_escape)
    out[name] = rec
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)

print("\n\n===== 源站：焦点陷阱 / 方向键 / Esc（每项各自重开层）=====")
for k, v in out.items():
    print("=" * 76)
    print(f"【{k}】")
    for kk, label in (("tab", "Tab"), ("shift_tab", "Shift+Tab"),
                      ("arrow_down", "ArrowDown"), ("arrow_up", "ArrowUp"),
                      ("escape", "Esc")):
        r = v.get(kk) or {}
        if r.get("why") and "start" not in r:
            print(f"  {label:<11} SKIPPED: {r['why']}")
            continue
        if kk in ("tab", "shift_tab"):
            print(f"  {label:<11} 跑出去={r.get('escaped_at')} "
                  f"有陷阱={r.get('trapped')}"
                  + (f"  落在={json.dumps(r.get('landed'), ensure_ascii=False)[:150]}"
                     if r.get('landed') else ""))
        elif kk.startswith("arrow"):
            print(f"  {label:<11} 焦点移动={r.get('moved')} "
                  f"始终在层内={r.get('stayed_in_layer')}")
            print(f"              {' → '.join((s['who'] or '')[:18] for s in r.get('seq', []))}")
        else:
            print(f"  {label:<11} 层关掉了={r.get('layer_closed')} "
                  f"焦点还在层内={r.get('focus_came_back')}")
            print(f"              Esc 前焦点={(r.get('before') or {}).get('who')}")
            print(f"              Esc 后焦点={json.dumps(r.get('after'), ensure_ascii=False)[:190]}")
