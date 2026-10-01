#!/usr/bin/env python3
"""batch 847 源站探针（测量轮）：把 846 那张基线表从 2 层扩到能扩的层。

发现轮（`jimeng_probe847b_discover.py`）已经认领到源站实名，其中两条**推翻了
预设**：

  · 顶栏·更多菜单   层 = `DIV` fixed z=120 **200×84 @[1211,56]**，
                   **无 testid / 无 role / 无 aria-label**，3 个可聚焦；
                   焦点落在**层自己**（`tabindex=-1`）—— 和搜索面板同一个模式
  · 顶栏·分享面板   层 = **`canvas-share-panel-surface`** fixed z=30
                   **400×251 @[1100,56]**；焦点**留在触发器**
                   `canvas-share-trigger` 上 —— **它压根不接管焦点**

第二条是「所有面板开层即接管焦点」这个预设的直接反例。没取样就写不出这句话。

量法与 846b 完全一致（**每个测量从重开的层起手**，真按键盘读 `activeElement`）：
  · 开层那一瞬间焦点在不在层里
  · 层内连按 Tab 会不会跑出去（第几次 / 跑到哪 / 回不回来）
  · 层内方向键动不动
  · Esc 关不关得掉、焦点回哪

「更多菜单」那层**没有 testid**，所以层的认领走**开前/开后差分**（新出现的
fixed 元素），不靠猜 testid。

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
              tag: e.tagName, tid: e.getAttribute('data-testid') || '',
              role: e.getAttribute('role') || '',
              al: (e.getAttribute('aria-label') || '').slice(0, 40),
              pos: s.position, z: s.zIndex, opaque,
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y), focusables: f,
              ti: e.getAttribute('tabindex')});
  }
  return out;
}"""

TIDS = []


def snap():
    return page.evaluate(SNAP_JS, SHELL)


def find_by_tid(t):
    return page.evaluate("""(t) => {
      const e = document.querySelector(`[data-testid="${t}"]`);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return {w: Math.round(r.width), h: Math.round(r.height)};
    }""", t)


def in_layer():
    if not TIDS:
        return None
    return page.evaluate("""(tids) => {
      const a = document.activeElement;
      for (const t of tids) {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (e && e.contains(a)) return t;
      }
      return null;
    }""", TIDS)


def focus_now():
    d = page.evaluate("""() => {
      const a = document.activeElement;
      if (!a || a === document.body) return {who: 'body'};
      const r = a.getBoundingClientRect();
      return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
                || a.getAttribute('aria-label')
                || (a.innerText || '').trim().slice(0, 12) || a.tagName)),
              al: (a.getAttribute('aria-label') || '').trim().slice(0, 24),
              tid: a.getAttribute('data-testid') || '',
              tabindex: a.getAttribute('tabindex'),
              w: Math.round(r.width), h: Math.round(r.height)};
    }""")
    d["in"] = in_layer()
    return d


def layer_present():
    return bool(TIDS) and bool(find_by_tid(TIDS[0]))


def entry(sel_kind, key):
    """按源站实名定位入口：tid / aria-label / 第 N 个同 tid。"""
    if sel_kind == "tid":
        return page.evaluate("""(k) => {
          const b = document.querySelector(`[data-testid="${k}"]`);
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", key)
    if sel_kind == "al":
        return page.evaluate("""(k) => {
          const b = [...document.querySelectorAll('button,[role=button]')]
            .find(x => (x.getAttribute('aria-label') || '') === k);
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", key)
    if sel_kind == "nth":
        n = int(key)
        return page.evaluate("""(n) => {
          const bs = [...document.querySelectorAll(`[data-testid="${n.tid}"]`)];
          if (bs.length <= n.i) return null;
          const r = bs[n.i].getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""", {"tid": "canvas-panel-launcher", "i": n})
    return None


TARGETS = [
    # (复刻层名, 复刻 testid, 入口定位, 层认领)
    ("顶栏·更多菜单", "topbar-more-menu", ("al", "更多"), "diff"),
    ("顶栏·分享面板", "topbar-share-panel", ("tid", "canvas-share-trigger"), "tid"),
    ("顶栏·账号菜单", "canvas-user-menu", ("tid", "canvas-user-menu-trigger"), "diff"),
    ("顶栏·生成历史", "topbar-history-menu", ("nth", 1), "diff"),
    ("缩放菜单", "canvas-zoom-menu", ("al_prefix", "Zoom options"), "diff"),
]

out = {}
for name, clone_tid, (kind, key), claim in TARGETS:
    print("=" * 74)
    print(f"【{name}】")
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    page.mouse.move(700, 520)
    page.wait_for_timeout(200)

    if kind == "al_prefix":
        p = page.evaluate("""(k) => {
          const b = [...document.querySelectorAll('button,[role=button]')]
            .find(x => (x.getAttribute('aria-label') || '').startsWith(k));
          if (!b) return null;
          const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                  al: b.getAttribute('aria-label')};
        }""", key)
    else:
        p = entry(kind, key)
    if not p:
        out[name] = {"clone_tid": clone_tid,
                     "why": f"源站上找不到入口（{kind}:{key}）—— 前置态没成立"}
        print("   SKIPPED:", out[name]["why"])
        continue

    before = {L["sig"] for L in snap()}
    page.mouse.click(p["x"], p["y"])
    page.wait_for_timeout(1600)
    after = snap()
    fresh = [L for L in after if L["sig"] not in before]
    print(f"   入口 @({p['x']},{p['y']}) · 新出现的 fixed/sticky 层 {len(fresh)} 个")
    for L in fresh:
        print("     ", json.dumps(L, ensure_ascii=False)[:200])

    if claim == "tid":
        TIDS = [clone_tid] if find_by_tid(clone_tid) else []
    else:
        cand = [L for L in fresh if L["focusables"] > 0]
        if cand:
            best = max(cand, key=lambda L: L["focusables"])
            TIDS = [best["tid"]] if best["tid"] else []
            out.setdefault(name, {})["layer_no_tid"] = best
        else:
            TIDS = []
    if not TIDS:
        out.setdefault(name, {})["why"] = (
            "层开出来了但**认不出 testid**（源站这一层没有 testid）⇒ 无法稳定"
            "指认，焦点类测量在这里**判据盲区**，如实记账，不硬猜。")
        out[name]["clone_tid"] = clone_tid
        out[name]["fresh"] = fresh
        out[name]["focus_at_open"] = focus_now()
        print("   ⚠", out[name]["why"])
        print("   开层焦点:", json.dumps(out[name]["focus_at_open"],
                                       ensure_ascii=False)[:200])
        continue

    at_open = focus_now()
    print("   开层那一瞬间焦点:", json.dumps(at_open, ensure_ascii=False)[:200])
    rec = {"clone_tid": clone_tid, "src_tid": TIDS[0], "at_open": at_open}

    def ensure_inside():
        if in_layer():
            return
        page.evaluate("""(t) => {
          const e = document.querySelector(`[data-testid="${t}"]`);
          if (!e) return;
          const it = e.querySelector('input,button,a[href],[tabindex]:not([tabindex="-1"])');
          if (it) it.focus();
        }""", TIDS[0])
        page.wait_for_timeout(250)

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

    ensure_inside()
    rec["tab"] = probe_tab()
    ensure_inside()
    rec["arrow_down"] = probe_key("ArrowDown")
    ensure_inside()
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    rec["layer_closed_by_esc"] = not layer_present()
    rec["after_escape"] = focus_now()
    print(f"   层内 Tab: 逃出={rec['tab']['escaped_at']} 陷阱={rec['tab']['trapped']}"
          + (f" 落在 al={(rec['tab']['landed'] or {}).get('al')!r}" if rec["tab"]["landed"] else ""))
    print(f"   方向键: moved={rec['arrow_down']['moved']} "
          f"始终层内={rec['arrow_down']['stayed_in_layer']} "
          f"轨迹={rec['arrow_down']['seq'][:3]}")
    print(f"   Esc: 关掉={rec['layer_closed_by_esc']} "
          f"焦点={json.dumps(rec['after_escape'], ensure_ascii=False)[:170]}")
    out[name] = rec

with open("/tmp/b847-measure.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b847-measure.json")
