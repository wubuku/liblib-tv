#!/usr/bin/env python3
"""batch 848 源站探针：剩下 4 个「选中节点后才挂载」的浮层。

847 之后 `kb_not_sampled` 还剩 4 层（`video-toolbar-capture-menu` /
`video-toolbar-tools-menu` / `text-bg-palette` / `image-tools-menu`），
共同点是**都要先选中一个节点，浮层才存在**。847 的教训是**别猜标签** ——
按 `aria-label` 含「全屏编辑」去找，撞到的是另一个节点的入口。

所以这一轮：
  ① 逐个选中节点，把**全页**按钮全 dump（testid + aria-label + 位置 + 尺寸），
     从里面**读**出该节点工具条上到底有哪些入口，而不是猜「截取帧」「工具」
     这些中文名 —— 源站的文案可能完全不同（847 实测源站工具条按钮是英文的
     `Rename 视频 1` / `Add tags` / `Create connected node after …`）。
 ② 找得到入口的，开它、量焦点（口径与 846b/847d 一致：真按键盘读
     activeElement、开层瞬间焦点、层内 Tab、方向键）。
 ③ 找不到 / 开不出来的，如实记 **前置态没成立** 或 **BLOCKED_BY_FIXTURE**。

顺带一个已知风险：这一版画布上**没有图片节点**（节点是 视频 / 文本×3 / 时间线 /
导演台），所以 `image-tools-menu` 很可能压根取不到样 —— 那样就如实记
BLOCKED_BY_FIXTURE，**不是**「源站没问题」。

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


def all_buttons():
    return page.evaluate("""() => [...document.querySelectorAll('button,[role=button],[role=menuitem]')]
      .map(b => {
        const r = b.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return null;
        return {al: b.getAttribute('aria-label') || '',
                tid: b.getAttribute('data-testid') || '',
                role: b.getAttribute('role') || '',
                txt: (b.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 18),
                x: Math.round(r.x), y: Math.round(r.y),
                w: Math.round(r.width), h: Math.round(r.height)};
      }).filter(Boolean)""", )


def snap():
    return page.evaluate("""(SHELL) => {
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
              role: e.getAttribute('role') || '',
              al: (e.getAttribute('aria-label') || '').slice(0, 36),
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y), focusables: f, z: s.zIndex});
      }
      return out;
    }""", SHELL)


def focus_now(rect):
    d = page.evaluate("""(R) => {
      const a = document.activeElement;
      if (!a || a === document.body) return {who: 'body', in: false};
      const r = a.getBoundingClientRect();
      const inR = !!R && r.left >= R.x - 1 && r.top >= R.y - 1
                  && r.right <= R.x + R.w + 1 && r.bottom <= R.y + R.h + 1;
      return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
                || a.getAttribute('aria-label')
                || (a.innerText || '').trim().replace(/\\s+/g,' ').slice(0, 16)
                || a.tagName)),
              al: (a.getAttribute('aria-label') || '').trim().slice(0, 26),
              tid: a.getAttribute('data-testid') || '',
              tabindex: a.getAttribute('tabindex'),
              w: Math.round(r.width), h: Math.round(r.height), in: inR};
    }""", rect)
    return d


nodes = page.evaluate("""() => [...document.querySelectorAll('[data-id]')]
  .filter(n => { const r = n.getBoundingClientRect();
                 return r.width > 80 && r.height > 80; })
  .map(n => { const r = n.getBoundingClientRect();
    return {id: n.getAttribute('data-id'), al: n.getAttribute('aria-label') || '',
            x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
            w: Math.round(r.width), h: Math.round(r.height)}; })""")
print("== 画布上的节点（>80×80）==")
for n in nodes:
    print(f"  {n['id']:<32} al={n['al']!r} {n['w']}×{n['h']}")

# 逐个选中：把全页按钮 dump 出来，与未选中时做差 —— 差集就是该节点的工具条
baseline = {b["tid"] + "|" + b["al"] + "|" + str(b["x"]) + "," + str(b["y"])
            for b in all_buttons()}
print(f"\n未选中时全页按钮 {len(baseline)} 枚")

per_node = {}
for n in nodes:
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    page.mouse.move(700, 520)
    page.wait_for_timeout(200)
    page.mouse.click(n["x"], n["y"])
    page.wait_for_timeout(1600)
    now = all_buttons()
    fresh = [b for b in now
             if b["tid"] + "|" + b["al"] + "|" + str(b["x"]) + "," + str(b["y"])
             not in baseline]
    print("=" * 76)
    print(f"【{n['al']}】{n['id']} 选中后**新出现**的按钮 {len(fresh)} 枚")
    for b in fresh:
        print(f"    al={b['al']!r:<46} tid={b['tid']!r:<30} "
              f"{b['w']}×{b['h']} @({b['x']},{b['y']})")
    per_node[n["id"]] = {"al": n["al"], "fresh": fresh}
    baseline = {b["tid"] + "|" + b["al"] + "|" + str(b["x"]) + "," + str(b["y"])
                for b in now}

with open("/tmp/b848-toolbars.json", "w", encoding="utf-8") as f:
    json.dump(per_node, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b848-toolbars.json")
print("（本轮先只做发现：读出入口实名后再开层量焦点，别在没读到名字前就点）")
