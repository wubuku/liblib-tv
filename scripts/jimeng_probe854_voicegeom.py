#!/usr/bin/env python3
"""batch 854 源站探针：全音色层**高度到底多少**（680×96 还是 680×328？）。

§71 自己记了一条范围限制：认层时量到 **680×96**（9 个 chip 横向一行），
而 `ensure_open` 重开后量到 **680×328**。两者差 3 倍多。这个差**必须查清**：

  · 若 **96 才是稳定态**（328 是动画/展开的中间帧）⇒ 基线表按 96 记，
    并把「328 是什么」写进 why —— 半年后有人量到 328 会以为判据坏了；
  · 若这一层**会随交互变形**（比如横向排不下就换行成网格）⇒ 基线表的
    几何**不该写死**，只记 role/认法，几何随内容变。

⚠️ 这一批**只量几何**，不重测四项键盘行为（853b 已经测过且入表了）。
⚠️ 视口 1512×1200，与 850/851/852/853 同口径。

⚠️ 计费边界：只点「音色: 音色库」触发器与切分支，**绝不**点生成/发送/购买。
"""

import json
import sys

MAX_WATCH = 8   # 打开后连续采样多少次

# 面板几何 + 内部布局，一次采全
GEOM_JS = """() => {
  const hdr = [...document.querySelectorAll('h1,h2,h3,div,span,p')]
      .find(e => (e.innerText||'').trim() === '全音色'
                 && !e.querySelector('h1,h2,h3,div,span,p'));
  if (!hdr) return {ok: false, why: '找不到「全音色」标题'};
  let cur = hdr.parentElement, best = null;
  while (cur && cur !== document.body && cur !== document.documentElement) {
    const r = cur.getBoundingClientRect();
    const n = [...document.querySelectorAll(
        '[class*="min-w-canvas-audio-voice-shrinkable"]')]
      .filter(c => cur.contains(c) && c.getBoundingClientRect().width > 4).length;
    if (n >= 8 && r.width * r.height < innerWidth * innerHeight * 0.5) {
      best = cur; break;
    }
    cur = cur.parentElement;
  }
  if (!best) return {ok: false, why: '找不到满足条件的祖先'};
  const r = best.getBoundingClientRect();
  const chips = [...best.querySelectorAll(
      '[class*="min-w-canvas-audio-voice-shrinkable"]')]
    .map(c => { const cr = c.getBoundingClientRect();
      return [Math.round(cr.x), Math.round(cr.y),
              Math.round(cr.width), Math.round(cr.height)]; });
  // 芯片按 y 聚类 ⇒ 看它们是「一行」还是「多行」
  const ys = [...new Set(chips.map(c => c[1]))].sort((a,b)=>a-b);
  return {ok: true,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          n_chips: chips.length,
          n_rows: ys.length,
          chip_rects: chips,
          scrollH: best.scrollHeight, clientH: best.clientHeight,
          overflowY: getComputedStyle(best).overflowY};
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

tid = None
for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
    loc = page.locator(cand)
    if loc.count():
        before = set(page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')"))
        loc.first.click(timeout=10000)
        page.wait_for_timeout(2500)
        after = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        if new:
            tid = new[0]
            break

if not tid:
    print("!! 插不出音频节点 ⇒ BLOCKED_BY_FIXTURE")
    out["verdict"] = "no_audio_node"
else:
    print(f"== 音频节点 {tid} ==")
    pt = page.evaluate("""(tid) => {
      const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const CTRL = 'button,[role=button],a,input,select,textarea';
      for (const [fx,fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],[0.5,0.75]]) {
        const x = r.x + r.width*fx, y = r.y + r.height*fy;
        const t = document.elementFromPoint(x, y);
        if (t && n.contains(t) && !t.closest(CTRL)) return [Math.round(x), Math.round(y)];
      }
      return null;
    }""", tid)
    if pt:
        page.mouse.click(pt[0], pt[1])
        page.wait_for_timeout(1200)

    vt = page.locator('button[aria-label^="音色"]')
    print(f"== 「音色」触发器 {vt.count()} 个 ==")
    if vt.count():
        cands = page.evaluate("""(aria) => {
          const out = [];
          for (const l of document.querySelectorAll(`button[aria-label^="${aria}"]`)) {
            const s = getComputedStyle(l);
            const r = l.getBoundingClientRect();
            const x = r.x + r.width/2, y = r.y + r.height/2;
            const st = document.elementsFromPoint(x, y) || [];
            const top = st[0] || null;
            out.push({rect:[Math.round(r.x),Math.round(r.y),
                           Math.round(r.width),Math.round(r.height)],
                      visible: s.display!=='none' && s.visibility!=='hidden',
                      self_is_top: !!(top && (top===l || l.contains(top)))});
          }
          return out;
        }""", "音色")
        use = [c for c in cands if c["visible"] and c["self_is_top"]]
        if use:
            p = use[0]["rect"]
            page.mouse.click(p[0] + p[2] // 2, p[1] + p[3] // 2)
            print("\n== 打开后连续采样（看是不是动画中间帧）==")
            samples = []
            for i in range(MAX_WATCH):
                page.wait_for_timeout(400)
                g = page.evaluate(GEOM_JS)
                if g.get("ok"):
                    print(f"   [{i}] rect={g['rect']} chips={g['n_chips']} "
                          f"rows={g['n_rows']} scrollH={g['scrollH']} "
                          f"clientH={g['clientH']} overflowY={g['overflowY']}")
                    samples.append({"i": i, "rect": g["rect"],
                                    "n_chips": g["n_chips"],
                                    "n_rows": g["n_rows"],
                                    "scrollH": g["scrollH"],
                                    "clientH": g["clientH"]})
                else:
                    print(f"   [{i}] {g.get('why')}")
                    samples.append({"i": i, "why": g.get("why")})
            out["samples"] = samples
            hs = [s["rect"][3] for s in samples if "rect" in s]
            if hs:
                out["heights"] = hs
                out["stable_h"] = hs[-1]
                print(f"\n== 高度序列 {hs} ⇒ 稳定值 {hs[-1]} ==")
        else:
            out["verdict"] = "no_clickable_trigger"
    else:
        out["verdict"] = "no_voice_trigger"

with open("/tmp/b854-voicegeom.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n== 已写 /tmp/b854-voicegeom.json ==")
if "heights" in out:
    print(f"== 结论：稳定高度 {out['stable_h']}，"
          f"整个序列 {out['heights']} ==")
