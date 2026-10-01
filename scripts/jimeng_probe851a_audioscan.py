#!/usr/bin/env python3
"""batch 851a 源站侦察：**能不能插出音频节点**、插了之后有没有那 5 个下拉。

§68 的范围限制写着一句没验证过的话：音频生成面板那 5 个下拉「没取过样」。
但**没说清为什么**。848 只 dump 了这一版画布**已有**的节点（视频 / 文本×3 /
时间线 / 导演台），**从没试过往画布里插音频**。而复刻侧 849 探针里
`insert("音频")` 是**能**插出来的（kb_rows 里有 5 个 audio-* 层）。

两条路，处置完全相反：
  (a) 源站能插 → 5 层可以取样（照 850 的路子）
  (b) 源站插不出 / 插了没有那 5 个下拉 → 5 层是 **BLOCKED_BY_FIXTURE**
      （夹具不具备），和 `image-tools-menu` 同性质

所以这一轮**只做侦察，不下结论**：能不能插、插出来长什么样。

⚠️ 计费边界：只点「音频」插入按钮和下拉触发器，**绝不点生成/发送/购买**。
⚠️ 用**集合差分**认新节点（不按序号 —— 批 843 的教训）。
"""

import json

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})   # 与 850 同口径
page.wait_for_timeout(2500)

NODE_TIDS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || n.getAttribute('data-id') || '')"""

LEFT_RAIL = """() => {
  const out = [];
  for (const b of document.querySelectorAll(
        '.react-flow__pane button, [class*="left"] button, aside button')) {
    const r = b.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    out.push({al: b.getAttribute('aria-label') || '',
              txt: (b.innerText || '').trim().slice(0, 12)});
  }
  return out;
}"""

out = {}
print("== 已有节点 ==", page.evaluate(NODE_TIDS))
out["nodes_before"] = page.evaluate(NODE_TIDS)

rail = page.evaluate(LEFT_RAIL)
labels = sorted({c["al"] or c["txt"] for c in rail if (c["al"] or c["txt"])})
print(f"== 左栏按钮 {len(labels)} 个 ==", labels)
out["rail"] = labels

audio_btn = None
for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
    loc = page.locator(cand)
    if loc.count():
        audio_btn = loc.first
        print(f"== 找到音频插入按钮: {cand} ==")
        out["audio_button"] = cand
        break
if audio_btn is None:
    print("!! 左栏**没有**音频插入按钮 ⇒ 夹具不具备（BLOCKED_BY_FIXTURE）")
    out["verdict"] = "no_audio_button"
else:
    before = set(page.evaluate(NODE_TIDS))
    audio_btn.click(timeout=10000)
    page.wait_for_timeout(2500)
    after = page.evaluate(NODE_TIDS)
    new = [t for t in after if t not in before]
    print(f"== 插入后新增节点 ==", new)
    out["nodes_after"] = after
    out["new_nodes"] = new
    if not new:
        print("!! 点了「音频」但**没有新节点** ⇒ 插不出音频")
        out["verdict"] = "no_new_node"
    else:
        # 选中新节点，把它的所有可点入口 dump 出来
        tid = new[0]
        pt = page.evaluate("""(tid) => {
          const n = document.querySelector(
            `.react-flow__node[data-testid="${tid}"]`)
            || [...document.querySelectorAll('.react-flow__node')]
                 .find(e => (e.getAttribute('data-id')||'') === tid);
          if (!n) return null;
          const r = n.getBoundingClientRect();
          const CTRL = 'button,[role=button],a,input,select,textarea';
          for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                                  [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
            const x = r.x + r.width*fx, y = r.y + r.height*fy;
            const t = document.elementFromPoint(x, y);
            if (t && n.contains(t) && !t.closest(CTRL)) return [Math.round(x), Math.round(y)];
          }
          return null;
        }""", tid)
        print("== 选点 ==", pt)
        if not pt:
            print("!! 选不中音频节点")
            out["verdict"] = "cannot_select"
        else:
            page.mouse.click(pt[0], pt[1])
            page.wait_for_timeout(2000)
            sel = page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node.selected')]"
                ".map(n => n.getAttribute('data-testid')||n.getAttribute('data-id'))")
            print("== 选中态 ==", sel)
            # 差分出**新增**的可点入口（选中后浮出来的那批）
            entries = page.evaluate("""() => {
              const out = [];
              for (const b of document.querySelectorAll('button,[role=button]')) {
                const r = b.getBoundingClientRect();
                if (r.width < 1 || r.height < 1) continue;
                const s = getComputedStyle(b);
                if (s.display === 'none' || s.visibility === 'hidden') continue;
                out.push({al: b.getAttribute('aria-label') || '',
                          txt: (b.innerText || '').trim().slice(0, 20),
                          w: Math.round(r.width), h: Math.round(r.height),
                          x: Math.round(r.x), y: Math.round(r.y)});
              }
              return out;
            }""")
            print(f"== 选中后页面上的可点入口 {len(entries)} 个 ==")
            keys = ('选择模型', '音乐', '时长', '创作类型', '音频', '音色', '模型')
            hits = [e for e in entries
                    if any(k in (e["al"] or e["txt"] or "") for k in keys)]
            print(f"== 与「音频/音乐/音色/模型/时长」相关的 {len(hits)} 条 ==")
            for e in hits:
                print(f"   al={e['al'][:56]!r} txt={e['txt']!r} {e['w']}×{e['h']} @[{e['x']},{e['y']}]")
            out["entries"] = entries
            out["relevant"] = hits
            out["verdict"] = ("has_relevant_entries" if hits
                              else "node_but_no_5_dropdowns")

with open("/tmp/b851a-audioscan.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b851a-audioscan.json")
