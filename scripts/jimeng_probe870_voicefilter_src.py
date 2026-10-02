#!/usr/bin/env python3
"""batch 870 源站探针：音色库里的**筛选面板**在源站长什么样、落在哪？

## 为什么要取这个样

复刻侧量到（探针 870，`/tmp/b870-voicefilter.json`）：打开「全音色」时
性别/年龄/语言/声音特点**四个筛选面板同时渲染**，且几何 y = -56 / -92 /
-164 / -164 ⇒ **整个跑到视口外**，点不到也关不掉。

批 870 修了「无条件常驻 + 关不掉」（渲染条件补开合判据、onClick 改成切换），
修完 0 → 1 → 0。但**打开之后仍然落在 y = -56**（视口外）。
那一半本批**没修**，理由是：**源站这个面板长什么样、落在哪，没取样** ⇒
不许照着想象改版式（847 明令：源站没做的/没取样的，不许在复刻里假称可用）。

所以本探针只回答一个问题：**源站的音色库里有没有筛选钮？点开之后面板落在哪？**

三种结果都算完成：
  · 源站**没有**筛选钮 ⇒ 复刻这几个筛选是「复刻自有」，要么删、要么标成待定；
  · 源站**有**且展开位置合理 ⇒ 复刻照抄那个位置；
  · 取不到（登录态没了 / 路径变了）⇒ 如实记 `BLOCKED_BY_FIXTURE`，
    **不许**用「大概就是这样」把复刻那一半糊过去。

## 计费边界

只点「音频」入口、选中节点、开「音色」筛选钮。**绝不**点生成/发送/购买/充值。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe870_voicefilter_src.py
"""

import json

OUT = "/tmp/b870-src-voicefilter.json"

# 打开音色库后，把「像筛选钮的东西」连同它们祖先的文本一起倒出来。
# ⚠️ 不预设类名：源站的 class 名跟复刻无关（853a 吃过一次亏 —— 按类名找
#   抓到的是整页容器）。这里只按**可见文本**找，这也是 853b 认出音色面板
#   时用的那套思路。
FILTER_SCAN_JS = """() => {
  const KEYS = ['性别', '年龄', '语言', '声音特点', '筛选', '语速', '情感'];
  const vis = (e) => { const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return r.width > 1 && r.height > 1 && cs.display !== 'none'
        && cs.visibility !== 'hidden'; };
  const out = [];
  for (const e of document.querySelectorAll('button,[role=button],[role=option],span,div')) {
    const own = (e.innerText || '').trim();
    if (!own || own.length > 12) continue;
    if (!KEYS.some(k => own.includes(k))) continue;
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect();
    out.push({tag: e.tagName, own, role: e.getAttribute('role') || '',
              aria: e.getAttribute('aria-label') || '',
              expanded: e.getAttribute('aria-expanded'),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)],
              parent_text: (e.parentElement?.innerText || '')
                              .trim().slice(0, 60)});
  }
  return out;
}"""

# 音色库面板的认法沿用 854（标题「全音色」往上找「装 ≥8 个音色 chip 且
# 面积 < 半视口」的最小祖先）—— 与基线表**同款**，不另发明一套。
PANEL_JS = """() => {
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
  return {ok: true,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          n_voice_chips: best.querySelectorAll(
              '[class*="min-w-canvas-audio-voice-shrinkable"]').length,
          text_head: (best.innerText || '').trim().slice(0, 120)};
}"""

# 点开某个筛选之后：**新出现了什么**、落在哪、有没有跑到视口外
#
# ⚠️⚠️ 第一版把「点之前的所有元素」当参数传进 evaluate，想在 JS 里
# `before.has(e)` 比对 —— **行不通**：Playwright 不能把 DOM 元素当参数
# 传（会被序列化成空对象），于是 `before.has is not a function` 当场崩，
# 而且崩在**已经量完**之后 —— 前面量到的东西一起丢。
# 改成审计那边同款的**打标记**：点之前给所有元素盖一个 `data-b870-prev`，
# 点之后查「**没有**这个标记的」，全程不跨边界传元素。
MARK_JS = """() => {
  document.querySelectorAll('[data-b870-prev]').forEach(
    e => e.removeAttribute('data-b870-prev'));
  document.querySelectorAll('*').forEach(
    e => e.setAttribute('data-b870-prev', '1'));
  return document.querySelectorAll('*').length;
}"""

AFTER_JS = """() => {
  const added = [];
  for (const e of document.querySelectorAll('*')) {
    if (e.hasAttribute('data-b870-prev')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 20) continue;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const own = (e.innerText || '').trim();
    added.push({tag: e.tagName, role: e.getAttribute('role') || '',
                aria: e.getAttribute('aria-label') || '',
                rect: [Math.round(r.x), Math.round(r.y),
                       Math.round(r.width), Math.round(r.height)],
                offscreen_top: r.y < 0,
                own_text: own.slice(0, 80),
                n_options: e.querySelectorAll('[role=option],li').length});
  }
  added.sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]));
  document.querySelectorAll('[data-b870-prev]').forEach(
    e => e.removeAttribute('data-b870-prev'));
  return {added: added.slice(0, 12), n_added: added.length};
}"""

out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["url"] = page.url
# ⚠️ 先验**登录态还在不在**：掉到登录页就当场收工，别把「登录没了」写成
#   「源站没有筛选钮」—— 那正是本项目反复在治的病。
out["logged_in"] = "/login" not in page.url and page.locator(
    'button[aria-label="音频"]').count() > 0
print(f"== URL {page.url[:70]}… ==")
print(f"== 登录态/画布在不在：{out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了或画布结构变了 —— "\
                     "**不是**「源站没有筛选钮」）"
    print("!! " + out["verdict"])
else:
    # 插音频节点（集合差分）
    tid = None
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if not loc.count():
            continue
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
    out["audio_node"] = tid
    print(f"== 音频节点 {tid} ==")
    if not tid:
        out["verdict"] = "BLOCKED_BY_FIXTURE（画布上插不出音频节点）"
    else:
        pt = page.evaluate("""(tid) => {
          const n = document.querySelector(
            `.react-flow__node[data-testid="${tid}"]`);
          if (!n) return null;
          const r = n.getBoundingClientRect();
          const CTRL = 'button,[role=button],a,input,select,textarea';
          for (const [fx,fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
            const x = r.x + r.width*fx, y = r.y + r.height*fy;
            const t = document.elementFromPoint(x, y);
            if (t && n.contains(t) && !t.closest(CTRL)) return [x, y];
          }
          return null;
        }""", tid)
        if pt:
            page.mouse.click(pt[0], pt[1])
            page.wait_for_timeout(1200)

        vt = page.locator('button[aria-label^="音色"]')
        out["voice_trigger_n"] = vt.count()
        print(f"== 「音色」触发器 {vt.count()} 个 ==")
        if not vt.count():
            out["verdict"] = "no_voice_trigger（这一版画布上没有「音色」入口）"
        else:
            vt.first.click(timeout=8000)
            page.wait_for_timeout(1200)
            out["panel"] = page.evaluate(PANEL_JS)
            print(f"== 音色库面板 {out['panel']} ==")
            out["filter_candidates"] = page.evaluate(FILTER_SCAN_JS)
            print(f"== 像筛选钮的元素 {len(out['filter_candidates'])} 个 ==")
            for c in out["filter_candidates"][:10]:
                print(f"   <{c['tag']} role={c['role']!r} expanded={c['expanded']!r}>"
                      f" {c['rect']} 文本={c['own']!r}")
            # 点第一个候选，量「点开之后多出来的那块在哪」
            chip = None
            for c in out["filter_candidates"]:
                if c["tag"] == "BUTTON" or c["role"] in ("button", "option"):
                    chip = c
                    break
            if chip:
                out["n_marked"] = page.evaluate(MARK_JS)
                loc = page.get_by_text(chip["own"], exact=True).first
                loc.click(timeout=8000)
                page.wait_for_timeout(1000)
                out["after_click"] = page.evaluate(AFTER_JS)
                print(f"== 点 {chip['own']!r} 之后：新增 "
                      f"{out['after_click']['n_added']} 块候选 ==")
                for a in out["after_click"]["added"][:6]:
                    print(f"   <{a['tag']} role={a['role']!r}> {a['rect']} "
                          f"跑到视口外={a['offscreen_top']} "
                          f"选项={a['n_options']} 文本={a['own_text'][:40]!r}")
                out["verdict"] = "sampled"
            else:
                out["verdict"] = "no_filter_chip_found（音色库里**没有**筛选钮）"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
print(f"== 结论：{out.get('verdict')} ==")
