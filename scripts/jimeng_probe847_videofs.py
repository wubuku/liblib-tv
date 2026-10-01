#!/usr/bin/env python3
"""batch 847 源站探针：把**视频全屏**这一格取到样。

846 留下的唯一卡点：`video-fullscreen-preview` 在复刻侧**开层不接管焦点**
（§63 发现），而复刻侧那一格留在 `keyboard_not_sampled` 里 —— 因为探针
846b 按 `aria-label` 含「全屏编辑」去找入口，撞到的是**时间线**节点，开出来的
是 `timeline-fullscreen-editor`。**拿时间线全屏的行为替视频全屏下结论 =
拿证据不足当证据**，所以那一批没判。

这一轮不猜标签：先把画布上**每个节点**、以及**选中每个节点后它工具条上有哪些
按钮**全部 dump 出来，从里面读出视频节点那个全屏入口的实名，再开它、量焦点。

量法与 846b **完全一致**（每个测量从重开的层起手，真按键盘读 `activeElement`）：
  · 开层那一瞬间焦点在不在层里
  · 层内连按 Tab 会不会跑出去（第几次、跑到哪、回不回来）
  · 层内方向键动不动
  · Esc 关不关得掉、焦点回哪

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
  return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
            || a.getAttribute('aria-label')
            || (a.className || '').toString().replace(/\\s+/g, ' ').slice(0, 32))
            || (a.innerText || '').trim().slice(0, 14)),
          al: (a.getAttribute('aria-label') || '').trim().slice(0, 26),
          tid: a.getAttribute('data-testid') || '',
          tabindex: a.getAttribute('tabindex'),
          w: Math.round(r.width), h: Math.round(r.height)};
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
        "(t) => !!document.querySelector(`[data-testid=\"${t}\"]`)", TIDS[0]))


def reset():
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)


# ── ① 先把画布上的节点和它们的工具条按钮全 dump 出来（不猜标签）──────────
print("== 画布上的节点 ==")
nodes = page.evaluate("""() => [...document.querySelectorAll('[data-id]')].map(n => {
  const r = n.getBoundingClientRect();
  return {id: n.getAttribute('data-id'),
          al: n.getAttribute('aria-label') || '',
          role: n.getAttribute('role') || '',
          x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
          w: Math.round(r.width), h: Math.round(r.height),
          btns: [...n.querySelectorAll('button,[role=menuitem]')]
                  .map(b => b.getAttribute('aria-label') || (b.innerText||'').trim().slice(0,10))
                  .filter(Boolean)};
})""")
for n in nodes:
    print(f"  {n['id']:<32} al={n['al']!r}")
    print(f"     工具条按钮(未选中时): {n['btns']}")

print("\n== 逐个选中，看工具条按钮（选中后才挂载）==")
for n in nodes:
    if n["w"] < 20 or n["h"] < 20:
        continue
    reset()
    page.mouse.click(n["x"], n["y"])
    page.wait_for_timeout(1300)
    # 选中后按钮可能挂在**节点之外**（react-flow 的 NodeToolbar 是 portal）
    got = page.evaluate("""(id) => {
      const n = document.querySelector(`[data-id="${id}"]`);
      if (!n) return null;
      const own = [...n.querySelectorAll('button,[role=menuitem]')]
        .map(b => b.getAttribute('aria-label') || (b.innerText||'').trim().slice(0,10))
        .filter(Boolean);
      // 工具条常常是兄弟/portal，另按 aria 找一遍
      const all = [...document.querySelectorAll('button,[role=menuitem]')]
        .filter(b => /全屏|预览|编辑/.test(b.getAttribute('aria-label') || ''))
        .map(b => b.getAttribute('aria-label'));
      return {own, fullscreenish: all,
              selected: n.className.includes('selected')
                || n.getAttribute('data-selected') === 'true'};
    }""", n["id"])
    print(f"  {n['id']:<32} own={got['own'] if got else None}")
    print(f"     全屏/预览/编辑类按钮(全页): {got['fullscreenish'] if got else None}")
reset()

# ── ② 锁定「视频」节点：按 al 含「视频」挑，取它**自己的**全屏入口 ────────
vid = next((n for n in nodes if "视频" in (n["al"] or "")), None)
print(f"\n== 锁定的视频节点: {vid['id'] if vid else None} al={vid['al'] if vid else None!r} ==")
if not vid:
    raise SystemExit("!! 这一版画布上没有视频节点 —— 前置态没成立，如实记账")

page.mouse.click(vid["x"], vid["y"])
page.wait_for_timeout(1500)
entry = page.evaluate("""(id) => {
  const n = document.querySelector(`[data-id="${id}"]`);
  const scope = n || document;
  const bs = [...scope.querySelectorAll('button,[role=menuitem]')];
  const pick = bs.filter(b => {
    const al = b.getAttribute('aria-label') || '';
    return /全屏|预览/.test(al);
  });
  return pick.map(b => {
    const r = b.getBoundingClientRect();
    return {al: b.getAttribute('aria-label'), tid: b.getAttribute('data-testid') || '',
            x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
            w: Math.round(r.width), h: Math.round(r.height)};
  });
}""", vid["id"])
print("== 视频节点的全屏类入口 ==", json.dumps(entry, ensure_ascii=False))
if not entry:
    raise SystemExit("!! 视频节点上没有全屏类入口 —— 前置态没成立")
print("== 选中后该节点工具条全部按钮 ==", page.evaluate("""(id) => {
  const n = document.querySelector(`[data-id="${id}"]`);
  return n ? [...n.querySelectorAll('button,[role=menuitem]')]
    .map(b => b.getAttribute('aria-label') || (b.innerText||'').trim().slice(0,10))
    .filter(Boolean) : null; }""", vid["id"]))

# ── ③ 开它，然后按 846b 的口径量 ────────────────────────────────────────
page.mouse.click(entry[0]["x"], entry[0]["y"])
page.wait_for_timeout(3000)

layers = page.evaluate("""() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 200 || r.height < 200) continue;
    const bg = s.backgroundColor || '';
    out.push({tag: e.tagName, tid: e.getAttribute('data-testid') || '',
              role: e.getAttribute('role') || '',
              al: (e.getAttribute('aria-label') || '').slice(0, 40),
              z: s.zIndex, bg,
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y),
              focusables: e.querySelectorAll(
                'a[href],button,input,select,textarea,[tabindex]').length,
              cls: (e.className||'').toString().replace(/\\s+/g,' ').slice(0,70)});
  }
  return out;
}""")
print("\n== 点开之后 fixed 且 ≥200×200 的元素 ==")
for L in layers:
    print("  ", json.dumps(L, ensure_ascii=False)[:210])
page.screenshot(path="/tmp/b847-source-video-fullscreen.png", full_page=False)

TIDS = [L["tid"] for L in layers if L["tid"]] or []
print("\n拿这些 testid 当候选层:", TIDS)
if not TIDS:
    raise SystemExit("!! 开了但认不出层（无 testid）—— 判据盲区，如实记账")

at_open = focus_now()
print("\n== 开层那一瞬间焦点 ==", json.dumps(at_open, ensure_ascii=False))


def ensure_inside():
    if in_layer():
        return focus_now()
    page.evaluate("""(tids) => {
      for (const t of tids) {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (!e) continue;
        const it = e.querySelector('input,button,a[href],[tabindex]:not([tabindex="-1"])');
        if (it) { it.focus(); return; }
        e.focus && e.focus(); return;
      }
    }""", TIDS)
    page.wait_for_timeout(300)
    return focus_now()


def probe_tab():
    esc_at, landed, steps = None, None, []
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        f = focus_now()
        steps.append({"i": i, "in": f.get("in"), "who": f.get("who")})
        if not f.get("in"):
            esc_at = i
            landed = f
            break
    return {"escaped_at": esc_at, "trapped": esc_at is None, "landed": landed,
            "steps": steps}


def probe_key(key):
    seq = []
    for _ in range(MAX_KEYS):
        page.keyboard.press(key)
        f = focus_now()
        seq.append({"who": f.get("who"), "in": f.get("in")})
    return {"key": key, "moved": len({s["who"] for s in seq}) > 1,
            "stayed_in_layer": all(s["in"] for s in seq), "seq": seq}


out = {"at_open": at_open, "layers": layers, "tids": TIDS}
reset()
if page.evaluate("(t) => !!document.querySelector(`[data-testid=\"${t}\"]`)",
                  TIDS[0]):
    ensure_inside()
    out["tab"] = probe_tab()
    ensure_inside()
    out["arrow_down"] = probe_key("ArrowDown")
    ensure_inside()
    out["arrow_up"] = probe_key("ArrowUp")
    ensure_inside()
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    out["layer_closed_by_esc"] = not layer_open()
    out["after_escape"] = focus_now()
else:
    out["why"] = "Esc 之后层已经关了（说明 Esc 能关），没法人工重开再量"

print("\n\n===== 源站：视频全屏的焦点行为 =====")
for k, v in out.items():
    if k in ("layers",):
        continue
    print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")

with open("/tmp/b847-source-video-fs.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n截图 /tmp/b847-source-video-fullscreen.png")
print("明细 /tmp/b847-source-video-fs.json")
