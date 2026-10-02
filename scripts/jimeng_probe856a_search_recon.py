#!/usr/bin/env python3
"""batch 856a 源站侦察：搜索面板**到底长什么样**（复刻此前是**猜的**）。

`src/components/jimeng/JimengSearchOverlay.tsx` 的文件头自己写着：

    SOURCE_FACT: 源站顶栏 搜索 (canvas-search) 存在 (96 顶栏 dump)，但其
    覆盖层内容**从未被捕获**。
    CLONE_DECISION: 复刻为最小搜索面板 — 输入框 + 「暂无搜索结果」空态

⇒ 复刻这一层的**内容是个猜测**（CLONE_DECISION），几何 242px 也是照
「380px 与生成历史面板同族」随手写的。而 855a 顺带量到：源站点「搜索」
开出的是 **320×1084 `role=dialog` `canvas-feature-panel`** ——
**1084 高**，不是 242 宽的小下拉。

这一批就把真实内容抓出来：结构 / 文本 / 几何 / 交互元素。
**不点任何东西**，只 dump（搜索框里打字也算改动状态，所以**不打字**）。

⚠️ 计费边界：只点顶栏「搜索」一个按钮。
"""

import json
import sys

from jimeng_kb_probe_lib import SNAP_JS, UNMARK_JS  # noqa: E402

sys.path.insert(0, __file__.rsplit("/", 1)[0])

# 层内结构：文本节点 + 交互元素 + 几何，分开报
DUMP_JS = """(rect) => {
  const [x, y, w, h] = rect;
  // 先认层：testid
  let L = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!L) {
    // 兜底：找包含该矩形的最小 dialog
    let best = null, ba = Infinity;
    for (const e of document.querySelectorAll('[role=dialog],div,section,aside')) {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden') continue;
      const r = e.getBoundingClientRect();
      if (Math.abs(r.width - w) > 4 || Math.abs(r.height - h) > 4) continue;
      const a = r.width * r.height;
      if (a < ba) { ba = a; best = e; }
    }
    L = best;
  }
  if (!L) return {ok: false, why: '认不出层'};
  const texts = [];
  for (const e of L.querySelectorAll('h1,h2,h3,h4,div,span,p,li,label,button,a')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const own = [...e.childNodes].filter(n => n.nodeType === 3)
      .map(n => n.textContent.trim()).join(' ').trim();
    if (own && own.length <= 30)
      texts.push({tag: e.tagName, role: e.getAttribute('role') || '',
                  cls: (e.className || '').toString().replace(/\\s+/g, ' ')
                       .slice(0, 40),
                  txt: own, rect: [Math.round(r.x), Math.round(r.y),
                                   Math.round(r.width), Math.round(r.height)]});
  }
  const ctrls = [...L.querySelectorAll(
      'input,button,a,[role=button],[role=tab],[role=option],[tabindex],textarea')]
    .map(e => { const r = e.getBoundingClientRect();
      return {tag: e.tagName, role: e.getAttribute('role') || '',
              type: e.getAttribute('type') || '',
              al: e.getAttribute('aria-label') || '',
              ph: e.getAttribute('placeholder') || '',
              ti: e.getAttribute('tabindex'),
              txt: (e.innerText || '').trim().slice(0, 16),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]}; });
  const r = L.getBoundingClientRect();
  return {ok: true,
          layer: {tag: L.tagName, role: L.getAttribute('role') || '',
                  al: L.getAttribute('aria-label') || '',
                  tid: L.getAttribute('data-testid') || '',
                  cls: (L.className || '').toString().replace(/\\s+/g, ' ')
                       .slice(0, 60),
                  rect: [Math.round(r.x), Math.round(r.y),
                         Math.round(r.width), Math.round(r.height)],
                  scrollH: L.scrollHeight, clientH: L.clientHeight,
                  overflowY: getComputedStyle(L).overflowY},
          texts, ctrls};
}"""

out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
print(f"== URL {page.url[:60]}… ==")


def diff_layers(before, after):
    keys = {(b["x"], b["y"], b["w"], b["h"]) for b in before}
    return [a for a in after if (a["x"], a["y"], a["w"], a["h"]) not in keys]


def _hit_ok(cand, pg):
    """按钮中心的落点**在按钮矩形内**，且落点**不是另一个可交互元素**。

    ⚠️ 856a 记：旧判据 `top === l || l.contains(top)` 会把**按钮自己**判成
    不可点 —— 因为中心命中的是按钮里的 `svg` 图标，而图标到按钮的
    `contains` 关系在这套 DOM 上不成立（855a 实测同一按钮一点就开）。
    「矩形内 + 落点不是另一个可交互元素」才是对的。
    """
    x = cand["rect"][0] + cand["rect"][2] // 2
    y = cand["rect"][1] + cand["rect"][3] // 2
    return bool(pg.evaluate("""([x, y, r, al]) => {
      const t = document.elementFromPoint(x, y);
      if (!t) return false;
      if (x < r[0] || y < r[1] || x > r[0] + r[2] || y > r[1] + r[3]) return false;
      // ⚠️ 直接问「落点是不是这个按钮自己（或它的后代）」——
      //    `closest()` 一句话答完。**不要**沿祖先链自己判：那版在
      //    svg → button 这条链上走到 button（它自己有 aria-label）就判否，
      //    把按钮判成「被自己挡住」（856a 第二版栽在这）。
      const b = t.closest(`[aria-label="${al}"]`);
      return !!b;
    }""", [x, y, cand["rect"], cand.get("al", "搜索")]))


trig = page.locator('button[aria-label="搜索"]')
print(f"== 「搜索」按钮 {trig.count()} 个 ==")
if not trig.count():
    out["verdict"] = "no_search_button"
    print("!! 找不到「搜索」按钮")
else:
    cands = page.evaluate("""(aria) => {
      const out = [];
      for (const l of document.querySelectorAll(`button[aria-label="${aria}"]`)) {
        const s = getComputedStyle(l);
        const r = l.getBoundingClientRect();
        const x = r.x + r.width/2, y = r.y + r.height/2;
        const st = document.elementFromPoint(x, y) || [];
        const top = st[0] || null;
        out.push({al: l.getAttribute('aria-label') || '',
                  rect:[Math.round(r.x),Math.round(r.y),
                        Math.round(r.width),Math.round(r.height)],
                  visible: s.display!=='none' && s.visibility!=='hidden',
                  self_is_top: !!(top && (top===l || l.contains(top)))});
      }
      return out;
    }""", "搜索")
    # ⚠️⚠️ 855a/856a 第二版栽在 `self_is_top` 上。诊断（见上面打印的落点）：
    #    按钮中心 `elementFromPoint` 命中的是按钮里那个 **`svg` 图标**，
    #    而 `top === l || l.contains(top)` 判 False ⇒ 按钮被自己的图标判成
    #    「不可点」。**但 855a 实测同一个按钮一点就开**（开出 320×1084）。
    #    ⇒ 判据错了，不是产品不可点。
    #    正确判据：落点**在按钮矩形内**就算数（图标、span、伪元素都在里面），
    #    再叠一条「落点不是另一个**可交互元素**」。
    use = [c for c in cands
           if c["visible"] and _hit_ok(c, page)]
    for c in cands:
        cxx = c["rect"][0] + c["rect"][2] // 2
        cyy = c["rect"][1] + c["rect"][3] // 2
        top = page.evaluate("""([x,y]) => {
          const t = document.elementFromPoint(x,y);
          if (!t) return 'null';
          return t.tagName + '|role=' + (t.getAttribute('role')||'') +
                 '|al=' + (t.getAttribute('aria-label')||'').slice(0,30) +
                 '|cls=' + (t.className||'').toString().replace(/\\s+/g,' ').slice(0,40);
        }""", [cxx, cyy])
        print(f"   候选 rect={c['rect']} visible={c['visible']} "
              f"落点={top}")
        c["hit_detail"] = top
    out["candidates"] = cands
    if not use:
        out["verdict"] = "no_clickable_search"
    else:
        p = use[0]["rect"]
        cx, cy = p[0] + p[2] // 2, p[1] + p[3] // 2
        # ⚠️ 点之前先验落点（843/855a 同款）
        hit = page.evaluate("""([x,y]) => {
          const t = document.elementFromPoint(x,y);
          return t ? t.tagName + '/' + (t.getAttribute('aria-label')||'') : 'null';
        }""", [cx, cy])
        before = page.evaluate(SNAP_JS)
        page.mouse.click(cx, cy)
        page.wait_for_timeout(1500)
        new = diff_layers(before, page.evaluate(SNAP_JS))
        print(f"== 落点 {hit}；新增候选层 {len(new)} 个 ==")
        if not new:
            out["verdict"] = "no_new_layer"
        else:
            layer = sorted(new, key=lambda z: -(z["w"] * z["h"]))[0]
            print(f"   层: {layer['w']}×{layer['h']} @[{layer['x']},{layer['y']}] "
                  f"role={layer['role']!r} tid={layer['tid']!r}")
            d = page.evaluate(DUMP_JS,
                              [layer["x"], layer["y"], layer["w"], layer["h"]])
            if not d.get("ok"):
                out["verdict"] = "dump_failed"
                print(f"   ⚠ dump 失败: {d.get('why')}")
            else:
                out["layer"] = d["layer"]
                out["texts"] = d["texts"]
                out["ctrls"] = d["ctrls"]
                print(f"\n== 层本身 ==\n   {d['layer']}")
                print(f"\n== 交互元素 {len(d['ctrls'])} 个 ==")
                for c in d["ctrls"][:24]:
                    print(f"   <{c['tag']} role={c['role']!r} type={c['type']!r} "
                          f"ti={c['ti']} rect={c['rect']} "
                          f"al={c['al'][:24]!r} ph={c['ph'][:20]!r} "
                          f"txt={c['txt']!r}")
                print(f"\n== 文本节点 {len(d['texts'])} 个 ==")
                for t in d["texts"][:30]:
                    print(f"   <{t['tag']} role={t['role']!r}> rect={t['rect']} "
                          f"{t['txt']!r}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        page.evaluate(UNMARK_JS)

with open("/tmp/b856a-search-recon.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n== 已写 /tmp/b856a-search-recon.json ==")
if "layer" in out:
    print(f"== 源站搜索面板: {out['layer']['rect']} "
          f"role={out['layer']['role']!r} tid={out['layer']['tid']!r} "
          f"scrollH={out['layer']['scrollH']} ==")
