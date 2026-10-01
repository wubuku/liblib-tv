#!/usr/bin/env python3
"""batch 845 源站探针：浮层开着的时候，Tab 会走到哪？焦点会不会停在**被浮层盖住**
的控件上？

复刻侧 `scripts/jimeng_unclickable_audit.py` 的 `keyboard_probe` 在三个浮层上报出
焦点被遮（`kb_covered` 3 条）。这在**源站**是不是也这样，必须先取证 —— 不然就
分不清「源站也这样（那就照抄，不许擅自改进）」和「复刻自己把焦点接管弄丢了
（那就得修）」。两种结论的处置完全相反。

口径必须和复刻侧**逐条一致**，否则两边数字没得比：
  · 先 `blur()` 冷启动（复刻侧就是这么做的，不做的话复刻侧量的是"从层里往外
    走"，源站量的是"从零开始往里走"，两个不同的量）
  · 再**真按** `Tab`（`page.keyboard.press`），最多 40 次
  · 每一步读 `document.activeElement`：
      在浮层里              → `inside`，记下第几次 Tab，停
      被 `elementFromPoint` 挡 → `covered`，计数 +1，并记下第一个这样的焦点位
      其余                 → `other`
  · 复刻侧是拿浮层的 `data-testid` 判 `inside`；源站这三层的 testid 未必认得，
    所以这里改成**几何判层**（脱离文档流 + 不透明底 + 不是画布自己的壳），
    并把"到底是谁盖住了焦点"一并打出来，好判是不是真·看不见。

只观察，不点任何付费购买流程。
"""

import json

MAX_TABS = 40

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)


# ── 几何判层：复刻侧 open_layer() 的同口径版本 ──────────────────────────────
#     要同时满足「脱离文档流」+「不透明底（真能盖住焦点环）」+「不是画布壳」。
def open_layers():
    return page.evaluate("""() => {
      const SHELL = '.react-flow__renderer, .react-flow__pane, '
                  + '.react-flow__viewport, .react-flow__nodes, [id*=react-flow], '
                  + '.semi-canvas, .canvas-container, main';
      const out = [];
      for (const e of document.querySelectorAll('body *')) {
        const s = getComputedStyle(e);
        if (s.position !== 'fixed' && s.position !== 'absolute'
            && s.position !== 'sticky') continue;
        if (e.matches(SHELL)) continue;
        const bg = s.backgroundColor || '';
        const opaque = bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
        if (!opaque) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 80 || r.height < 40) continue;
        out.push({tag: e.tagName,
                  tid: e.getAttribute('data-testid') || '',
                  role: e.getAttribute('role') || '',
                  al: (e.getAttribute('aria-label') || '').slice(0, 40),
                  pos: s.position, z: s.zIndex, bg,
                  w: Math.round(r.width), h: Math.round(r.height),
                  x: Math.round(r.x), y: Math.round(r.y),
                  cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 70)});
      }
      return out;
    }""")


def focus_probe(tag):
    """冷启动 + 真按 Tab，逐步判断焦点落在哪、会不会被浮层盖住。"""
    layers = open_layers()
    if not layers:
        return {"state": tag, "why": "这一层没打开（几何上找不到）"}

    page.evaluate("""() => { const a = document.activeElement;
        if (a && a.blur) a.blur(); return true; }""")

    covered_n = 0
    first = None
    trail = []
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        step = page.evaluate("""() => {
          const a = document.activeElement;
          if (!a || a === document.body) return {state: 'body'};
          const r = a.getBoundingClientRect();
          const al = (a.getAttribute('aria-label') || '').trim().slice(0, 30);
          const tid = a.getAttribute('data-testid') || '';
          const txt = (a.innerText || a.getAttribute('placeholder') || '')
                        .trim().replace(/\\s+/g, ' ').slice(0, 24);
          if (r.width < 1 || r.height < 1)
            return {state: 'other', al, tid, txt, w: Math.round(r.width),
                    h: Math.round(r.height)};
          const hit = document.elementFromPoint(r.x + r.width / 2,
                                                r.y + r.height / 2);
          const occluded = !!(hit && !a.contains(hit) && !hit.contains(a));
          return {state: occluded ? 'covered' : 'other', al, tid, txt,
                  w: Math.round(r.width), h: Math.round(r.height),
                  by: occluded ? (hit.tagName + '/'
                        + (hit.getAttribute('data-testid')
                           || hit.getAttribute('aria-label')
                           || (hit.className || '').toString().slice(0, 46))
                        || (hit.innerText || '').trim().slice(0, 16)) : null};
        }""")
        # 「在不在某个浮层里」：走到任意一个开着的不透明层内部就算进去
        if step.get("state") in ("other", "covered"):
            inside = page.evaluate("""() => {
              const a = document.activeElement;
              const SHELL = '.react-flow__renderer, .react-flow__pane, '
                          + '.react-flow__viewport, [id*=react-flow]';
              const out = [];
              for (const e of document.querySelectorAll('body *')) {
                const s = getComputedStyle(e);
                if (s.position !== 'fixed' && s.position !== 'absolute'
                    && s.position !== 'sticky') continue;
                if (e.matches(SHELL)) continue;
                const bg = s.backgroundColor || '';
                if (bg === 'rgba(0, 0, 0, 0)'
                    || bg.startsWith('rgba(0, 0, 0, 0)')) continue;
                const r = e.getBoundingClientRect();
                if (r.width < 80 || r.height < 40) continue;
                if (e.contains(a))
                  out.push(e.getAttribute('data-testid')
                           || (e.getAttribute('aria-label') || '').slice(0, 30)
                           || e.tagName);
              }
              return out;
            }""")
            if inside:
                return {"state": tag, "ok": True, "tabs": i,
                        "covered_n": covered_n, "covered": first,
                        "in": inside, "layers": layers, "trail": trail}
        if step.get("state") == "covered":
            covered_n += 1
            if first is None:
                first = {"at_tab": i, "al": step.get("al"), "tid": step.get("tid"),
                         "txt": step.get("txt"),
                         "size": f"{step.get('w')}x{step.get('h')}",
                         "covered_by": step.get("by")}
        if len(trail) < 8:
            trail.append({"tab": i, "state": step.get("state"),
                          "al": step.get("al"), "txt": step.get("txt")})
    return {"state": tag, "ok": False, "tabs": MAX_TABS,
            "covered_n": covered_n, "covered": first, "layers": layers,
            "trail": trail, "why": f"Tab {MAX_TABS} 次都没进到任何浮层里"}


def reset():
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)


results = []

# ── ① 顶栏搜索：源站搜索触发器与「生成历史」**共用** `canvas-panel-launcher`
#      （README §26 / census 白名单记着这条），按 DOM 序第一位区分。
reset()
hit = page.evaluate("""() => {
  const bs = [...document.querySelectorAll('[data-testid=canvas-panel-launcher]')];
  if (!bs.length) return null;
  const b = bs[0];
  const r = b.getBoundingClientRect();
  return {n: bs.length, x: Math.round(r.x + r.width / 2),
          y: Math.round(r.y + r.height / 2)};
}""")
print("== 搜索触发器 ==", hit)
if hit:
    page.mouse.click(hit["x"], hit["y"])
    page.wait_for_timeout(1600)
    results.append(focus_probe("顶栏·搜索"))
    reset()

# ── ② 画布右键菜单：先确认落点是**空画布**（复刻侧 843 栽过：硬点会开到节点上）
reset()
spot = page.evaluate("""() => {
  for (const [x, y] of [[430, 620], [420, 660], [450, 700], [400, 580]]) {
    const e = document.elementFromPoint(x, y);
    if (!e) continue;
    if (e.closest('[data-id]')) continue;              // 节点，跳过
    if (!e.closest('.react-flow__pane, .react-flow__renderer, '
                 + '[class*=pane], [class*=canvas]')) continue;
    return {x, y, hit: e.tagName + '/'
                  + (e.className || '').toString().slice(0, 50)};
  }
  return null;
}""")
print("== 空画布落点 ==", spot)
if spot:
    page.mouse.click(spot["x"], spot["y"], button="right")
    page.wait_for_timeout(1200)
    results.append(focus_probe("画布右键菜单"))
    reset()

# ── ③ 视频全屏：源站实名「全屏编辑」，需要先选中一个视频节点
reset()
sel = page.evaluate("""() => {
  const n = document.querySelector('[data-id^=rf__node-video]');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return {id: n.getAttribute('data-id'),
          x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
}""")
print("== 视频节点 ==", sel)
if sel:
    page.mouse.click(sel["x"], sel["y"])
    page.wait_for_timeout(1500)
    btn = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button,[role=menuitem]')]
        .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return {al: b.getAttribute('aria-label'),
              x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
    }""")
    print("== 全屏编辑按钮 ==", btn)
    if btn:
        page.mouse.click(btn["x"], btn["y"])
        page.wait_for_timeout(2500)
        results.append(focus_probe("视频全屏"))
        page.screenshot(path="/tmp/b845-source-fullscreen.png", full_page=False)

print("\n\n===== 源站焦点被遮测量 =====")
for r in results:
    print(json.dumps(r, ensure_ascii=False, indent=1)[:2600])
    print("-" * 70)

print("\n== 汇总 ==")
for r in results:
    print(f"  {r['state']:<14} ok={r.get('ok')} tabs={r.get('tabs')} "
          f"covered_n={r.get('covered_n')} 首个被遮={r.get('covered')}")
print("\n截图 /tmp/b845-source-fullscreen.png")
