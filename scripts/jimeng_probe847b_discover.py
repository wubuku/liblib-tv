#!/usr/bin/env python3
"""batch 847 源站探针（发现轮）：那 9 层到底能不能取样、源站开出来叫什么。

846 留下的缺口不是一处：12 个浮层里源站只对照了 **2** 个，另外 10 个全记在
`keyboard_not_sampled` 里 —— 既不下结论也不当通过。`video-fullscreen-preview`
这一格已查实是 **BLOCKED_BY_FIXTURE**（源站那个视频节点选中后工具条只有
`Create connected node before 视频 1` / `Rename 视频 1` / `Add tags` /
`Create connected node after 视频 1` 四枚，**压根没有全屏入口**；全页唯一的
`全屏编辑` 属于时间线节点）。

这一轮先**发现**、不测量：对每个候选入口点开，把源站开出来的层按
「几何 + role + testid」摊开，认领它的**实名**。认不出的、点不开的，如实记账 ——
「没结果」必须和「没问题」分开。

认领结果直接回填审计里那张 `SOURCE_BASELINE` 表，把能判的层变成能判。

只观察，不点任何付费购买流程。
"""

import json

CANVAS = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
          "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list"
          "&from_page=create")

page.goto(CANVAS, wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)

# 源站画布壳：判层时必须排除，否则整屏壳会被当成浮层
SHELL = (".react-flow__renderer, .react-flow__pane, .react-flow__viewport, "
         ".react-flow__nodes, [id*=react-flow], [class*=canvas-main-region], "
         "header[aria-label='Canvas top bar'], "
         "aside[aria-label='Canvas left toolbar']")


def layers_now():
    """当前开着的浮层（脱离文档流 + 有尺寸 + 不是画布壳）。"""
    return page.evaluate("""(SHELL) => {
      const out = [];
      for (const e of document.querySelectorAll('body *')) {
        const s = getComputedStyle(e);
        if (s.position !== 'fixed' && s.position !== 'absolute'
            && s.position !== 'sticky') continue;
        if (e.matches(SHELL)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 60 || r.height < 30) continue;
        const bg = s.backgroundColor || '';
        const opaque = bg !== 'rgba(0, 0, 0, 0)'
                       && !bg.startsWith('rgba(0, 0, 0, 0)');
        const f = e.querySelectorAll('a[href],button,input,select,textarea,'
                                     + '[tabindex],[role=menuitem],[role=option]').length;
        if (!opaque && f === 0) continue;
        out.push({tag: e.tagName,
                  tid: e.getAttribute('data-testid') || '',
                  role: e.getAttribute('role') || '',
                  al: (e.getAttribute('aria-label') || '').slice(0, 44),
                  pos: s.position, z: s.zIndex, bg, opaque,
                  w: Math.round(r.width), h: Math.round(r.height),
                  x: Math.round(r.x), y: Math.round(r.y),
                  focusables: f,
                  ti: e.getAttribute('tabindex'),
                  cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 60)});
      }
      return out;
    }""", SHELL)


def focus_now():
    d = page.evaluate("""() => {
      const a = document.activeElement;
      if (!a || a === document.body) return {who: 'body'};
      const r = a.getBoundingClientRect();
      return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
                || a.getAttribute('aria-label') || a.tagName)),
              al: (a.getAttribute('aria-label') || '').trim().slice(0, 26),
              tid: a.getAttribute('data-testid') || '',
              tabindex: a.getAttribute('tabindex'),
              w: Math.round(r.width), h: Math.round(r.height)};
    }""")
    d["layers"] = [L["tid"] or L["role"] or L["al"] or L["cls"][:24]
                   for L in layers_now()]
    return d


def reset():
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    page.mouse.move(700, 500)
    page.wait_for_timeout(250)


def topbar_btn(al):
    """按 aria-label 找顶栏按钮，返回可点中心。"""
    return page.evaluate("""(al) => {
      const b = [...document.querySelectorAll('button,[role=button]')]
        .find(x => (x.getAttribute('aria-label') || '') === al);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) return null;
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
              w: Math.round(r.width), h: Math.round(r.height)};
    }""", al)


def rail_btn(al):
    return page.evaluate("""(al) => {
      const b = [...document.querySelectorAll('button,[role=button]')]
        .find(x => (x.getAttribute('aria-label') || '') === al);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) return null;
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
    }""", al)


def click_at(p):
    page.mouse.click(p["x"], p["y"])
    page.wait_for_timeout(1400)


# 顶栏有哪些按钮（先把源站顶栏的实名读出来，别猜）
print("== 源站顶栏按钮 ==")
topbar = page.evaluate("""() => {
  const h = document.querySelector('header[aria-label="Canvas top bar"]')
        || document.querySelector('header');
  if (!h) return null;
  return [...h.querySelectorAll('button,[role=button]')].map(b => {
    const r = b.getBoundingClientRect();
    return {al: b.getAttribute('aria-label') || '',
            tid: b.getAttribute('data-testid') || '',
            x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
            w: Math.round(r.width), h: Math.round(r.height)};
  }).filter(b => b.w > 0);
}""")
for b in topbar or []:
    print(f"  al={b['al']!r:<26} tid={b['tid']!r:<28} {b['w']}×{b['h']} @({b['x']},{b['y']})")

print("\n== 左栏按钮 ==")
rail = page.evaluate("""() => {
  const a = document.querySelector('aside[aria-label="Canvas left toolbar"]');
  if (!a) return null;
  return [...a.querySelectorAll('button,[role=button]')].map(b => {
    const r = b.getBoundingClientRect();
    return {al: b.getAttribute('aria-label') || '',
            x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
  }).filter(b => b.w > 0);
}""")
for b in rail or []:
    print(f"  al={b['al']!r}")

# 候选入口 → 复刻侧对应的浮层
OPENERS = [
    ("顶栏·更多菜单", "topbar-more-menu", lambda: topbar_btn("更多")),
    ("顶栏·账号菜单", "canvas-user-menu", None),   # 头像，另找
    ("顶栏·分享面板", "topbar-share-panel", lambda: topbar_btn("分享")),
    ("顶栏·生成历史", "topbar-history-menu", None),  # canvas-panel-launcher 第 2 个
    ("缩放菜单", "canvas-zoom-menu", lambda: rail_btn("Zoom options, 94%")),
]

out = {}
for name, clone_tid, opener in OPENERS:
    reset()
    if opener is None:
        out[name] = {"clone_tid": clone_tid,
                     "why": "这一轮的 opener 没写（留待下一轮按实名补）"}
        print(f"\n【{name}】SKIPPED: opener 没写")
        continue
    p = opener()
    if not p:
        out[name] = {"clone_tid": clone_tid,
                     "why": "源站上按实名找不到这个入口"}
        print(f"\n【{name}】SKIPPED: 源站上找不到入口")
        continue
    before = layers_now()
    click_at(p)
    after = layers_now()
    new = [L for L in after
           if L["tid"] not in {x["tid"] for x in before} or L["opaque"]]
    f = focus_now()
    print(f"\n【{name}】入口 @({p['x']},{p['y']})")
    print(f"   开层后焦点: {json.dumps(f, ensure_ascii=False)[:200]}")
    print(f"   开出来的层（fixed/absolute、≥60×30、非画布壳）:")
    for L in after:
        print("     ", json.dumps(L, ensure_ascii=False)[:200])
    out[name] = {"clone_tid": clone_tid, "entry": p,
                 "focus_at_open": f, "layers": after}

with open("/tmp/b847-discovery.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b847-discovery.json")
print("截图（发现轮没开付费流程，不留图）")
