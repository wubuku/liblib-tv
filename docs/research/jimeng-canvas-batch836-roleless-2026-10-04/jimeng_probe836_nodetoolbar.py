"""batch 836 取证：源站**节点工具条里的下拉**到底有没有 role？

## 为什么绕到文本节点

§47 记下一个盲区：复刻侧 `JimengNodeToolbar` 的两个下拉（截取帧 / 工具）是
**裸 div，一个 role 都没有** ⇒ 任何 `role ∈ dialog/menu/listbox/popover` 型
普查都看不见它们。

想去源站量，但源站示例画布上的视频节点全是 `暂无视频`，选中弹的是**生成
表单**而不是工具条 ⇒ 这两个按钮根本没出现（832 的
`jimeng_probe832_noderoledropdowns.py` 实测 `picked_label=None`），
记 BLOCKED_BY_FIXTURE。

**同一个问题有另一条可达路径**：源站画布上有**文本节点**，选中它会弹工具条。
如果源站的文本工具条下拉**带** role，说明"源站的节点工具条下拉带 role"这条
一般性结论成立，可以据此给复刻那两个补 role；如果**不带**，那复刻侧与源站
一致，是普查工具的盲区而不是产品的缺陷。

**这一支只做取证，不预设结论。** 两边都记，最后由数据说话。

只读：只点触发器展开下拉，不选任何一项（不提交、不计费）。

跑法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe836_nodetoolbar.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

# 枚举**任何**可能是工具条/浮层的块 —— 不预设 role，否则测的还是我的假设
ENUM = """() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    if (r.width < 24 || r.height < 16) return false;
    for (let p = e; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  const t = (e) => (e.innerText || '').replace(/\\s+/g, ' ').trim();
  const out = [];
  const seen = new Set();
  for (const e of document.querySelectorAll(
        '[role],[aria-haspopup],[class*="toolbar" i],[class*="dropdown" i],'
        + '[class*="popover" i],[class*="menu" i]')) {
    if (!vis(e)) continue;
    const txt = t(e);
    if (!txt || txt.length > 220) continue;
    const r = e.getBoundingClientRect();
    const key = (e.getAttribute('role') || '') + '|' + txt.slice(0, 24);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      role: e.getAttribute('role') || '',
      name: (e.getAttribute('aria-label') || '').slice(0, 40),
      tid: e.getAttribute('data-testid') || '',
      haspopup: e.getAttribute('aria-haspopup') || '',
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      items: e.querySelectorAll('button,[role=menuitem],[role=option],[role=radio]').length,
      text: txt.slice(0, 90),
      cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 60),
    });
  }
  return out;
}"""

page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

result = {"steps": []}

# ① 找一个**真能点到**的文本节点
picked = page.evaluate(
    """() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = (n.getAttribute('aria-label') || '');
    if (!t.includes('文本')) continue;
    const r = n.getBoundingClientRect();
    if (r.width < 20 || r.height < 20) continue;
    for (const [fx, fy] of [[0.5,0.5],[0.5,0.2],[0.2,0.5],[0.8,0.5],[0.5,0.8]]) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      const h = document.elementFromPoint(x, y);
      if (h && n.contains(h)) {
        return {tid: n.getAttribute('data-testid') || '', aria: t,
                x: Math.round(x), y: Math.round(y)};
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
result["steps"].append({"step": "text-node-selected", "layers": page.evaluate(ENUM)})

# ② 把当前工具条上**所有**按钮列出来（这是触发器清单，不能靠猜）
result["toolbar_buttons"] = page.evaluate(
    """() => [...document.querySelectorAll('button,[role=button]')]
      .map(b => { const r = b.getBoundingClientRect();
        return {label: (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 24),
                haspopup: b.getAttribute('aria-haspopup') || '',
                w: Math.round(r.width), h: Math.round(r.height),
                x: Math.round(r.x), y: Math.round(r.y)};
      })
      .filter(b => b.w > 4 && b.h > 4 && b.label)"""
)

# ③ 逐个点开「像是下拉」的按钮（带 aria-haspopup 的优先，其次带 ∨/chevron 的）
#    这里**不预设**哪些是下拉：点了之后看有没有**新的**块冒出来。
CAND = ["字体", "背景", "更多", "展开", "对齐", "列表", "样式"]
for key in CAND:
    page.mouse.click(picked["x"], picked["y"])
    page.wait_for_timeout(1200)
    hit = page.evaluate(
        """(key) => {
      for (const b of document.querySelectorAll('button,[role=button]')) {
        const t = (b.getAttribute('aria-label') || b.innerText || '').trim();
        if (t.includes(key)) { b.click(); return t; }
      }
      return null;
    }""", key)
    page.wait_for_timeout(1200)
    result["steps"].append({"step": f"open:{key}", "clicked": hit,
                             "layers": page.evaluate(ENUM)})
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)

print(json.dumps(result, ensure_ascii=False, indent=2))
