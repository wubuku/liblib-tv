"""batch 836 取证（之二，聚焦）：源站文本节点工具条的「背景色」下拉是什么 role？

第一支探针（`jimeng_probe836_nodetoolbar.py`）被自己带偏了：每轮之间按 Escape
会取消选中，后面的 `b.click()` 于是落到画布空白/别的节点上，于是「新增的块」
全是别的画布节点进入视野 —— **观测被自己的脚手架污染了**。这一支只做一件事，
不循环、不按 Escape。

要回答的问题很具体：**源站节点工具条里的下拉，展开后带不带 role？**
（复刻侧 `JimengNodeToolbar` 的「截取帧」「工具」两个下拉是裸 div，一个 role
都没有 ⇒ 任何 role 型普查都看不见它们。若源站的下拉普遍带 role，那复刻那两个
就是缺口；若不带，那是普查工具的盲区、不是产品缺陷。）

源站上可达的入口：文本节点选中后的工具条 `data-testid="node-toolbar"`，
其「背景色」按钮实测 `aria-haspopup="menu"` 75×32。源站示例画布上没有带媒体的
视频节点，所以「截取帧」「工具」**测不到**（BLOCKED_BY_FIXTURE）——
这一支只能回答"一般性结论"，不能替那两处背书。

只读：只点开下拉看结构，不选任何颜色（不提交、不计费）。

跑法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe836_bgcolorrole.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

# 只看 node-toolbar 附近**新出现**的块：展开前后的差集，且不预设它有 role
SNAP = """() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    if (r.width < 20 || r.height < 12) return false;
    for (let p = e; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  const t = (e) => (e.innerText || '').replace(/\\s+/g, ' ').trim();
  const out = [];
  for (const e of document.querySelectorAll(
        '[role],[aria-haspopup],[class*="dropdown" i],[class*="popover" i],'
        + '[class*="menu" i],[class*="panel" i],[class*="picker" i],[class*="palette" i]')) {
    if (!vis(e)) continue;
    const txt = t(e);
    if (!txt || txt.length > 160) continue;
    const r = e.getBoundingClientRect();
    out.push({
      tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '',
      name: (e.getAttribute('aria-label') || '').slice(0, 40),
      tid: e.getAttribute('data-testid') || '',
      haspopup: e.getAttribute('aria-haspopup') || '',
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      items: e.querySelectorAll('button,[role=menuitem],[role=option],[role=radio]').length,
      text: txt.slice(0, 80),
      cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 60),
    });
  }
  return out;
}"""

page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

result = {}

# ① 选中文本节点（一个都不按 Escape，后面全靠重新点回来）
picked = page.evaluate(
    """() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    if (!(n.getAttribute('aria-label') || '').includes('文本')) continue;
    const r = n.getBoundingClientRect();
    if (r.width < 20 || r.height < 20) continue;
    for (const [fx, fy] of [[0.5,0.5],[0.5,0.2],[0.2,0.5],[0.8,0.5],[0.5,0.8]]) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      const h = document.elementFromPoint(x, y);
      if (h && n.contains(h)) {
        return {tid: n.getAttribute('data-testid') || '', x: Math.round(x), y: Math.round(y)};
      }
    }
  }
  return null;
}"""
)
result["picked_node"] = picked
if picked is None:
    result["error"] = "no clickable text node"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0)

page.mouse.click(picked["x"], picked["y"])
page.wait_for_timeout(2500)

before = page.evaluate(SNAP)
result["toolbar_present"] = page.evaluate(
    "() => !!document.querySelector('[data-testid=\"node-toolbar\"]')")
result["bgcolor_btn"] = page.evaluate(
    """() => {
      // ⚠️ 源站这枚按钮**没有 aria-label** —— 它的名字来自 innerText。
      // 只按 aria-label 找会返回 null，看起来像"这个按钮不存在"。
      // 顺带这也是一条发现：源站侧靠可见文案兜底，复刻侧补了 aria-label。
      const b = [...document.querySelectorAll('button,[role=button]')]
        .find(x => (x.getAttribute('aria-label') || x.innerText || '').includes('背景色'));
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return {aria: b.getAttribute('aria-label'), text: (b.innerText || '').trim(),
              haspopup: b.getAttribute('aria-haspopup'),
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y)}; }"""
)

# ② 点开它（JS click，绕开命中测试；只展开不选）
clicked = page.evaluate(
    """() => {
      const b = [...document.querySelectorAll('button,[role=button]')]
        .find(x => (x.getAttribute('aria-label') || x.innerText || '').includes('背景色'));
      if (!b) return null; b.click();
      return {aria: b.getAttribute('aria-label'), text: (b.innerText || '').trim()}; }"""
)
page.wait_for_timeout(1500)
result["clicked"] = clicked

after = page.evaluate(SNAP)
seen = {(l["role"], l["name"][:20], l["w"], l["h"], l["x"], l["y"]) for l in before}
new = [l for l in after if (l["role"], l["name"][:20], l["w"], l["h"], l["x"], l["y"]) not in seen]
result["new_layers"] = new

# ③ 同一个触发器再点一次：它还声明着 haspopup 吗？展开态能否被关掉？
result["btn_after_open"] = page.evaluate(
    """() => {
      const b = [...document.querySelectorAll('button,[role=button]')]
        .find(x => (x.getAttribute('aria-label') || x.innerText || '').includes('背景色'));
      return b ? {aria: b.getAttribute('aria-label'), text: (b.innerText || '').trim(),
                  haspopup: b.getAttribute('aria-haspopup'),
                  expanded: b.getAttribute('aria-expanded')} : null; }"""
)

print(json.dumps(result, ensure_ascii=False, indent=2))
