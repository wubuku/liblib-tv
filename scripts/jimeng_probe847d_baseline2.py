#!/usr/bin/env python3
"""batch 847 源站探针（第四轮）：无 testid 的层改用**矩形**当身份，把测量补上。

第三轮（`847c`）拿到了五条硬事实，但**陷阱/方向键两栏一个都没测到** —— 原因
是认层逻辑有 bug：它拿**复刻的** testid 去**源站**找（`topbar-share-panel` 在
源站叫 `canvas-share-panel-surface`），于是全落进「认不出 testid」分支。

而源站这几层**真的没有 testid**：

  · 顶栏·更多菜单  `DIV` fixed z=120 200×84 @[1211,56]  ← 无 testid / 无 role
  · 顶栏·账号菜单  外层 `DIV` fixed z=120 240×312 @[1260,56] 无 testid
                  （但**内层**有：焦点落到的那个就是 `canvas-user-menu`）
  · 缩放菜单      外层 `DIV` fixed z=120 200×292 @[16,599]  无 testid
                  （内层有 `canvas-zoom-percent-input`）

所以层的身份改成**矩形**：每次重开该层，重新做一次开前/开后差分拿到它的矩形，
「焦点在不在层里」= `activeElement` 的框落在那个矩形里。矩形在**单次打开内**
是稳定的，够用；而且它对「有没有 testid」这件事**免疫** —— 这正是判据该有的
形状：认层不许依赖一个可能不存在的锚。

`topbar-history-menu` 第三轮点开是「积分明细」、0 个新层 ⇒ **前置态没成立**，
这一轮换个点法再试一次；还是不成，就如实留在 not_sampled。

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

SHELL = (".react-flow__renderer, .react-flow__pane, .react-flow__viewport, "
         ".react-flow__nodes, [id*=react-flow], [class*=canvas-main-region], "
         "header[aria-label='Canvas top bar'], main, section")

SNAP_JS = """(SHELL) => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed' && s.position !== 'sticky') continue;
    if (e.matches(SHELL)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 30) continue;
    const bg = s.backgroundColor || '';
    const opaque = bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
    const f = e.querySelectorAll('a[href],button,input,select,textarea,'
      + '[tabindex],[role=menuitem],[role=option]').length;
    if (!opaque && f === 0) continue;
    out.push({sig: e.tagName + '|' + s.position + '|' + s.zIndex + '|'
               + Math.round(r.width) + 'x' + Math.round(r.height) + '|'
               + Math.round(r.x) + ',' + Math.round(r.y),
              tid: e.getAttribute('data-testid') || '',
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y), focusables: f,
              z: s.zIndex});
  }
  return out;
}"""

RECT = None   # 当前层的矩形（层身份）


def snap():
    return page.evaluate(SNAP_JS, SHELL)


def focus_now():
    d = page.evaluate("""(R) => {
      const a = document.activeElement;
      if (!a || a === document.body) return {who: 'body', in: false};
      const r = a.getBoundingClientRect();
      // 层身份 = 矩形：焦点框落在层矩形内（含 1px 容差）
      const inR = !!R && r.left >= R.x - 1 && r.top >= R.y - 1
                  && r.right <= R.x + R.w + 1 && r.bottom <= R.y + R.h + 1;
      return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
                || a.getAttribute('aria-label')
                || (a.innerText || '').trim().replace(/\\s+/g,' ').slice(0, 14)
                || a.tagName)),
              al: (a.getAttribute('aria-label') || '').trim().slice(0, 24),
              tid: a.getAttribute('data-testid') || '',
              tabindex: a.getAttribute('tabindex'),
              w: Math.round(r.width), h: Math.round(r.height),
              in: inR};
    }""", RECT)
    return d


def layer_alive():
    return bool(RECT) and bool(page.evaluate("""(R) => {
      const e = document.elementFromPoint(R.x + R.w / 2, R.y + Math.min(12, R.h / 2));
      return !!e;
    }""", RECT))


def open_and_claim(kind, key):
    """开层 + 用**矩形**认领它。返回 (矩形 or None)。"""
    global RECT
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    page.mouse.move(700, 520)
    page.wait_for_timeout(200)
    RECT = None
    if kind == "al":
        p = page.evaluate("""(k) => {
          const b = [...document.querySelectorAll('button,[role=button]')]
            .find(x => (x.getAttribute('aria-label') || '') === k);
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", key)
    elif kind == "al_prefix":
        p = page.evaluate("""(k) => {
          const b = [...document.querySelectorAll('button,[role=button]')]
            .find(x => (x.getAttribute('aria-label') || '').startsWith(k));
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", key)
    elif kind == "tid":
        p = page.evaluate("""(k) => {
          const b = document.querySelector(`[data-testid="${k}"]`);
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", key)
    else:  # nth launcher
        p = page.evaluate("""(k) => {
          const bs = [...document.querySelectorAll('[data-testid=canvas-panel-launcher]')];
          if (bs.length <= k) return null;
          const r = bs[k].getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", int(key))
    if not p:
        return None
    before = {L["sig"] for L in snap()}
    page.mouse.click(p["x"], p["y"])
    page.wait_for_timeout(1600)
    fresh = [L for L in snap() if L["sig"] not in before]
    cand = [L for L in fresh if L["focusables"] > 0]
    if not cand:
        return None
    best = max(cand, key=lambda L: L["focusables"])
    RECT = {"x": best["x"], "y": best["y"], "w": best["w"], "h": best["h"]}
    return {"entry": p, "layer": best}


def ensure_inside():
    if focus_now().get("in"):
        return True
    return bool(page.evaluate("""(R) => {
      const e = document.elementFromPoint(R.x + 4, R.y + 4);
      if (!e) return false;
      const it = e.closest('*').querySelector
        ? null : null;
      // 直接在该层矩形内找一个可聚焦元素
      const all = document.querySelectorAll('a[href],button,input,select,'
        + 'textarea,[tabindex],[role=menuitem],[role=option]');
      for (const x of all) {
        const r = x.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) continue;
        if (r.left >= R.x - 1 && r.top >= R.y - 1
            && r.right <= R.x + R.w + 1 && r.bottom <= R.y + R.h + 1) {
          x.focus();
          return true;
        }
      }
      return false;
    }""", RECT))


def probe_tab():
    esc_at, landed = None, None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        f = focus_now()
        if not f.get("in"):
            esc_at = i
            landed = f
            break
    return {"escaped_at": esc_at, "trapped": esc_at is None, "landed": landed}


def probe_key(k):
    seq = []
    for _ in range(MAX_KEYS):
        page.keyboard.press(k)
        f = focus_now()
        seq.append({"who": f.get("who"), "in": f.get("in")})
    return {"moved": len({s["who"] for s in seq}) > 1,
            "stayed_in_layer": all(s["in"] for s in seq),
            "seq": [s["who"] for s in seq]}


TARGETS = [
    ("顶栏·更多菜单", "topbar-more-menu", ("al", "更多")),
    ("顶栏·分享面板", "topbar-share-panel", ("tid", "canvas-share-trigger")),
    ("顶栏·账号菜单", "canvas-user-menu", ("tid", "canvas-user-menu-trigger")),
    ("顶栏·生成历史", "topbar-history-menu", ("nth", 1)),
    ("缩放菜单", "canvas-zoom-menu", ("al_prefix", "Zoom options")),
]

out = {}
for name, clone_tid, (kind, key) in TARGETS:
    print("=" * 74)
    print(f"【{name}】")
    claimed = open_and_claim(kind, key)
    if not claimed:
        out[name] = {"clone_tid": clone_tid,
                     "why": "这一层开不出来（找不到入口，或开出来没有新的 fixed 层）"
                            "—— **前置态没成立**，不是「源站没问题」"}
        print("   ⚠", out[name]["why"])
        continue
    rec = {"clone_tid": clone_tid, "rect": RECT,
           "src_layer": claimed["layer"], "entry": claimed["entry"]}
    rec["at_open"] = focus_now()
    print("   层矩形:", json.dumps(RECT, ensure_ascii=False),
          "| 源站层:", json.dumps(claimed["layer"], ensure_ascii=False)[:150])
    print("   开层那一瞬间焦点:", json.dumps(rec["at_open"], ensure_ascii=False)[:190])
    if not rec["at_open"].get("in"):
        print("   ⚠ 开层时焦点**不在层里** —— 这本身就是一条事实（源站也不接管）")
    ensure_inside()
    rec["tab"] = probe_tab()
    ensure_inside()
    rec["arrow_down"] = probe_key("ArrowDown")
    ensure_inside()
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    rec["after_escape"] = focus_now()
    print(f"   层内 Tab: 逃出={rec['tab']['escaped_at']} "
          f"陷阱={rec['tab']['trapped']}"
          + (f" 落在 al={(rec['tab']['landed'] or {}).get('al')!r}"
             if rec["tab"]["landed"] else ""))
    print(f"   方向键: moved={rec['arrow_down']['moved']} "
          f"始终层内={rec['arrow_down']['stayed_in_layer']} "
          f"轨迹={rec['arrow_down']['seq'][:3]}")
    print(f"   Esc 后焦点: {json.dumps(rec['after_escape'], ensure_ascii=False)[:170]}")
    out[name] = rec

with open("/tmp/b847-measure2.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b847-measure2.json")
