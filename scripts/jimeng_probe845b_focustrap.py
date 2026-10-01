#!/usr/bin/env python3
"""batch 845 源站探针（第二轮）：把第一轮问不清的三件事一次问完。

第一轮（`jimeng_probe845_focusocclusion.py`）测出源站也有"焦点停在被遮住的控件
上"（搜索 covered_n=7、右键菜单 covered_n=5、右键菜单 40 次 Tab 都进不去），
但它**自己**有两个必须先排掉的疑点，否则结论会建立在错前提上：

  ① **开层那一瞬间焦点在不在层内？** 第一轮一上来就 `blur()`，量的是"冷启动
     要按几次 Tab 才进得去"。用户真实的路径是"点开 → 焦点就该在里面"。
     这两件事不一样，源站和复刻都可能在其中一件上更好。
  ② **源站那层到底多大？** 第一轮的几何判层只认到 `canvas-feature-sidecar`
     （Agent 常驻侧栏），**没认到搜索面板** —— 可是 Tab 第 1 站就落在
     `placeholder="搜索节点..."` 的输入框上，第 2 站"全部 6"，第 4~8 站是结果
     行。面板明明开着，几何判层却没认出来：那它的层壳多半不是"不透明底"，
     或者它**根本不是一个小下拉而是整屏**。而它 covered_by 的是
     `text-flow-node-full`（画布节点的整屏 inner div）—— 一个小下拉遮不住
     画布中央的节点，所以**源站的搜索很可能是整屏面板**，复刻是 242px 下拉。
     几何这一条不确认，"源站更差"这个结论就得推翻。
  ③ **全屏那条第一轮压根没测成**：源站画布上 `[data-id^=rf__node-video]` = None
     （这一份画布实例只有文本节点）。这是**前置态没成立**，不能当成"源站没问题"。

口径与第一轮、与复刻侧 `keyboard_probe` 一致；只是这一轮**不 blur**，先读开层
瞬间的焦点，再决定要不要冷启动。只观察，不点任何付费购买流程。
"""

import json

MAX_TABS = 40

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)


def describe(tag):
    """把"当前有哪些层"摊开讲：几何 + 透明与否 + DOM 位置。

    这里刻意**放宽**几何判层（不要求不透明底），因为第一轮的教训正是：
    判层条件太紧会把"明明开着"的层判没，而判没了之后那一行的测量就是空气。
    """
    return page.evaluate("""(tag) => {
      const SHELL = '.react-flow__renderer, .react-flow__pane, '
                  + '.react-flow__viewport, [id*=react-flow]';
      const out = [];
      for (const e of document.querySelectorAll('body *')) {
        const s = getComputedStyle(e);
        if (s.position !== 'fixed' && s.position !== 'absolute'
            && s.position !== 'sticky') continue;
        if (e.matches(SHELL)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 80 || r.height < 40) continue;
        const bg = s.backgroundColor || '';
        const opaque = bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
        // 只要里面**有可聚焦的东西**，或自己就是浮层容器，就记一笔
        const focusables = e.querySelectorAll(
          'a[href],button,input,select,textarea,[tabindex]').length;
        if (!opaque && !focusables) continue;
        // DOM 序：它前面有多少个可聚焦元素（决定冷启动 Tab 第几站能碰到它）
        let before = 0;
        for (const f of document.querySelectorAll(
              'a[href],button,input,select,textarea,[tabindex]')) {
          if (f === e || e.contains(f)) break;
          before += 1;
        }
        out.push({tag, name: e.tagName,
                  tid: e.getAttribute('data-testid') || '',
                  role: e.getAttribute('role') || '',
                  al: (e.getAttribute('aria-label') || '').slice(0, 44),
                  pos: s.position, z: s.zIndex, bg, opaque,
                  w: Math.round(r.width), h: Math.round(r.height),
                  x: Math.round(r.x), y: Math.round(r.y),
                  focusables, focusablesBefore: before,
                  cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 76)});
      }
      return out;
    }""", tag)


def focus_now():
    """开层**那一瞬间**焦点在谁身上（不 blur，不按 Tab）。"""
    return page.evaluate("""() => {
      const a = document.activeElement;
      if (!a) return {who: '(null)'};
      const r = a.getBoundingClientRect();
      return {tag: a.tagName,
              al: (a.getAttribute('aria-label') || '').trim().slice(0, 30),
              tid: a.getAttribute('data-testid') || '',
              txt: (a.innerText || a.getAttribute('placeholder') || '')
                     .trim().replace(/\\s+/g, ' ').slice(0, 30),
              w: Math.round(r.width), h: Math.round(r.height),
              isBody: a === document.body};
    }""")


def cold_tabs(tag):
    """冷启动口径（和第一轮、和复刻侧一致）：blur → 真按 Tab，看焦点去哪。"""
    page.evaluate("""() => { const a = document.activeElement;
        if (a && a.blur) a.blur(); return true; }""")
    covered_n = 0
    first = None
    inside = None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        s = page.evaluate("""() => {
          const a = document.activeElement;
          if (!a || a === document.body) return {state: 'body'};
          const r = a.getBoundingClientRect();
          const hit = r.width >= 1 && r.height >= 1
            ? document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2)
            : null;
          return {state: (hit && !a.contains(hit) && !hit.contains(a))
                          ? 'covered' : 'other',
                  al: (a.getAttribute('aria-label') || '').trim().slice(0, 28),
                  txt: (a.innerText || a.getAttribute('placeholder') || '')
                         .trim().replace(/\\s+/g, ' ').slice(0, 22),
                  tid: a.getAttribute('data-testid') || '',
                  by: (hit && hit.tagName) ? hit.tagName + '/'
                     + (hit.getAttribute('data-testid')
                        || hit.getAttribute('aria-label')
                        || (hit.className || '').toString().slice(0, 40)) : null};
        }""")
        if s["state"] == "covered":
            covered_n += 1
            if first is None:
                first = {"at_tab": i, "al": s.get("al"), "txt": s.get("txt"),
                         "tid": s.get("tid"), "by": s.get("by")}
        hit_in = page.evaluate("""() => {
          const a = document.activeElement;
          for (const e of document.querySelectorAll('body *')) {
            if (!e.contains(a) || e === a) continue;
            const s = getComputedStyle(e);
            if (s.position !== 'fixed' && s.position !== 'absolute'
                && s.position !== 'sticky') continue;
            const r = e.getBoundingClientRect();
            if (r.width < 80 || r.height < 40) continue;
            const bg = s.backgroundColor || '';
            if (bg === 'rgba(0, 0, 0, 0)' || bg.startsWith('rgba(0, 0, 0, 0)'))
              continue;
            return e.getAttribute('data-testid') || e.getAttribute('aria-label')
                   || e.tagName;
          }
          return null;
        }""")
        if hit_in:
            inside = {"at_tab": i, "in": hit_in}
            break
    return {"cold": True, "entered": inside, "entered_tabs": (inside or {}).get("at_tab"),
            "covered_n": covered_n, "first_covered": first,
            "why": None if inside else f"Tab {MAX_TABS} 次都没进到任何不透明层里"}


def reset():
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)


results = {}

# ── ① 顶栏搜索 ────────────────────────────────────────────────────────────
reset()
hit = page.evaluate("""() => {
  const bs = [...document.querySelectorAll('[data-testid=canvas-panel-launcher]')];
  if (!bs.length) return null;
  const r = bs[0].getBoundingClientRect();
  return {n: bs.length, x: Math.round(r.x + r.width / 2),
          y: Math.round(r.y + r.height / 2)};
}""")
print("== 搜索触发器（与生成历史共用 testid，取 DOM 序第一位）==", hit)
if hit:
    page.mouse.click(hit["x"], hit["y"])
    page.wait_for_timeout(1800)
    results["顶栏·搜索"] = {"layers": describe("顶栏·搜索"),
                           "focus_at_open": focus_now(),
                           "probe": cold_tabs("顶栏·搜索")}
    page.screenshot(path="/tmp/b845b-source-search.png", full_page=False)
    reset()

# ── ② 画布右键菜单 ────────────────────────────────────────────────────────
spot = page.evaluate("""() => {
  for (const [x, y] of [[430, 620], [420, 660], [450, 700], [400, 580]]) {
    const e = document.elementFromPoint(x, y);
    if (!e || e.closest('[data-id]')) continue;
    if (!e.closest('.react-flow__pane, .react-flow__renderer, '
                 + '[class*=pane], [class*=canvas]')) continue;
    return {x, y, hit: e.tagName + '/'
                  + (e.className || '').toString().slice(0, 46)};
  }
  return null;
}""")
print("== 空画布落点（先验 elementFromPoint 落在 pane 上，别开到节点去）==", spot)
if spot:
    page.mouse.click(spot["x"], spot["y"], button="right")
    page.wait_for_timeout(1400)
    results["画布右键菜单"] = {"layers": describe("画布右键菜单"),
                               "focus_at_open": focus_now(),
                               "probe": cold_tabs("画布右键菜单")}
    reset()

# ── ③ 视频全屏：这一轮**不猜** testid，改成"谁的工具条里有「全屏编辑」就点谁"
reset()
vid = page.evaluate("""() => {
  const nodes = [...document.querySelectorAll('[data-id]')];
  for (const n of nodes) {
    const b = [...n.querySelectorAll('button,[role=menuitem]')]
      .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
    if (!b) continue;
    const rn = n.getBoundingClientRect();
    const rb = b.getBoundingClientRect();
    return {nodeId: n.getAttribute('data-id'),
            node: {x: Math.round(rn.x + rn.width / 2),
                    y: Math.round(rn.y + rn.height / 2),
                    w: Math.round(rn.width), h: Math.round(rn.height)},
            btn: {al: b.getAttribute('aria-label'),
                  x: Math.round(rb.x + rb.width / 2),
                  y: Math.round(rb.y + rb.height / 2)}};
  }
  return {none: true, ids: nodes.slice(0, 8).map(n => n.getAttribute('data-id'))};
}""")
print("== 带「全屏编辑」的那个节点 ==", json.dumps(vid, ensure_ascii=False))
if vid and not vid.get("none"):
    page.mouse.click(vid["node"]["x"], vid["node"]["y"])
    page.wait_for_timeout(1600)
    re = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button,[role=menuitem]')]
        .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return {al: b.getAttribute('aria-label'),
              x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
    }""")
    print("== 选中后再找「全屏编辑」==", re)
    if re:
        page.mouse.click(re["x"], re["y"])
        page.wait_for_timeout(2800)
        results["视频全屏"] = {"layers": describe("视频全屏"),
                               "focus_at_open": focus_now(),
                               "probe": cold_tabs("视频全屏")}
        page.screenshot(path="/tmp/b845b-source-fullscreen.png", full_page=False)
else:
    results["视频全屏"] = {"skipped": "源站这一份画布上没有任何节点带「全屏编辑」入口"
                                      "（前置态没成立，**不是**'源站没问题'）",
                           "node_ids": (vid or {}).get("ids")}

print("\n\n===== 源站焦点接管（第二轮）=====")
for k, v in results.items():
    print("=" * 74)
    print("【%s】" % k)
    if v.get("skipped"):
        print("  SKIPPED:", v["skipped"], "| 画布上的节点:", v.get("node_ids"))
        continue
    print("  开层瞬间焦点:", json.dumps(v["focus_at_open"], ensure_ascii=False))
    print("  认到的层（放宽几何后）:")
    for L in v["layers"]:
        print("    ", json.dumps(L, ensure_ascii=False)[:230])
    p = v["probe"]
    print("  冷启动 → 进到层里:", json.dumps(p.get("entered"), ensure_ascii=False),
          f"（第 {p.get('entered_tabs')} 次 Tab）" if p.get("entered_tabs") else "")
    print("  冷启动 → 焦点被遮的次数:", p.get("covered_n"),
          "| 首个:", json.dumps(p.get("first_covered"), ensure_ascii=False))
    if p.get("why"):
        print("  ", p["why"])

print("\n截图 /tmp/b845b-source-search.png /tmp/b845b-source-fullscreen.png")
