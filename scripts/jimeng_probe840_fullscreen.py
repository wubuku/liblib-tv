#!/usr/bin/env python3
"""batch 840 源站探针：视频「全屏预览」浮层在源站到底长什么样。

只观察，不点任何付费购买流程。探针用注入的全局 `page`，不自己 launch。
"""

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(9000)

nodes = page.evaluate("""() => [...document.querySelectorAll('.react-flow__node')]
    .map(e => ({tid: e.getAttribute('data-testid') || '',
                id: e.getAttribute('data-id') || '',
                cls: e.className.toString().slice(0, 60),
                r: (b => ({x: Math.round(b.x), y: Math.round(b.y),
                           w: Math.round(b.width), h: Math.round(b.height)}))
                   (e.getBoundingClientRect())}))""")
print("== 源站节点 ==")
for n in nodes:
    print(n)

# 找一个有媒体的视频节点：里面有播放键
target = None
for n in nodes:
    if "video" in n["cls"]:
        target = n
        break
print("\n== 目标节点 ==", target)

if target is None:
    print("!! 没找到视频节点，记 BLOCKED_BY_FIXTURE")
else:
    page.mouse.click(target["r"]["x"] + target["r"]["w"] // 2,
                     target["r"]["y"] + 16)
    page.wait_for_timeout(1500)
    # 找工具条上的全屏按钮
    cands = page.evaluate("""() => [...document.querySelectorAll('button,[role=menuitem]')]
        .filter(b => /全屏/.test((b.getAttribute('aria-label') || '')
                                  + (b.innerText || '')))
        .map(b => ({tag: b.tagName, al: b.getAttribute('aria-label') || '',
                    txt: (b.innerText || '').trim().slice(0, 20),
                    tid: b.getAttribute('data-testid') || '',
                    haspopup: b.getAttribute('aria-haspopup') || '',
                    r: (x => ({x: Math.round(x.x), y: Math.round(x.y),
                               w: Math.round(x.width), h: Math.round(x.height)}))
                       (b.getBoundingClientRect())}))""")
    print("\n== 全屏相关按钮 ==")
    for c in cands:
        print(c)

    if not cands:
        print("!! 源站这个节点上没有全屏入口，记 BLOCKED_BY_FIXTURE")
    else:
        b0 = cands[0]
        page.mouse.click(b0["r"]["x"] + b0["r"]["w"] // 2,
                         b0["r"]["y"] + b0["r"]["h"] // 2)
        page.wait_for_timeout(2000)
        layers = page.evaluate("""() => {
          const out = [];
          for (const e of document.querySelectorAll('body *')) {
            const s = getComputedStyle(e);
            if (!['absolute','fixed','sticky'].includes(s.position)) continue;
            const r = e.getBoundingClientRect();
            if (r.width < 200 || r.height < 100) continue;
            out.push({tid: e.getAttribute('data-testid') || '',
                      role: e.getAttribute('role') || '',
                      al: e.getAttribute('aria-label') || '',
                      z: s.zIndex, bg: s.backgroundColor,
                      w: Math.round(r.width), h: Math.round(r.height),
                      x: Math.round(r.x), y: Math.round(r.y),
                      cls: (e.className||'').toString().replace(/\\s+/g,' ')
                             .slice(0, 70)});
          }
          return out.sort((a,b) => b.w*b.h - a.w*a.h).slice(0, 12);
        }""")
        print("\n== 源站全屏层实测 ==")
        for l in layers:
            print(l)
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
