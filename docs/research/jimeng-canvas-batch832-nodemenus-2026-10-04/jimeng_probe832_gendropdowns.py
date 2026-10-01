"""batch 832 取证（之二）：源站**生成表单里那些下拉**有没有 role。

上一支探针（noderoledropdowns）撞上前置态：源站示例画布上的视频节点全是
`暂无视频`，选中弹的是**生成表单**而不是工具条，所以「截取帧」「工具」
两个按钮根本没出现（`picked_label=None`）—— 那两个下拉在源站上**测不到**，
记 BLOCKED_BY_FIXTURE，不猜。

但生成表单**是可以打开的**，而它里面正好有一组下拉（模型 / 比例 / 模式 / 时长）。
这一支就问它们：**源站这些下拉带不带 role？** 复刻侧 13 处 listbox 全部带
`role="listbox"` + `aria-label`，如果源站也带，那 13 处补锚点就是「对齐」；
如果源站不带，那是复刻侧多给了 role，得记成 CLONE_DECISION 而不是默默留着。

只读：只点开下拉看结构，不选任何一项（不提交、不计费）。

跑法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe832_gendropdowns.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

ENUM = """() => {
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) return false;
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  const nameOf = (e) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const lb = e.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\\s+/).map(id => document.getElementById(id))
        .filter(Boolean).map(n => (n.getAttribute('aria-label') || n.innerText || '').trim())
        .join(' ').trim();
      if (t) return t;
    }
    return '';
  };
  const out = [];
  for (const el of document.querySelectorAll(
        '[role],[aria-haspopup],[class*="dropdown" i],[class*="popover" i],[class*="popup" i]')) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    const txt = (el.innerText || '').replace(/\\s+/g, ' ').trim();
    if (txt.length > 300) continue;
    out.push({
      tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || '',
      name: nameOf(el), tid: el.getAttribute('data-testid') || '',
      haspopup: el.getAttribute('aria-haspopup') || '',
      expanded: el.getAttribute('aria-expanded') || '',
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      bg: s.backgroundColor, radius: s.borderRadius,
      cls: (el.className || '').toString().replace(/\\s+/g, ' ').slice(0, 70),
      text: txt.slice(0, 80),
      options: el.querySelectorAll('[role=option],[role=menuitem],[role=radio]').length,
    });
  }
  return out;
}"""

page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

result = {"steps": []}

# ① 选一个**真能点到**的节点（源站节点互相叠压，见 noderoledropdowns 探针）
picked = page.evaluate(
    """() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.width < 20 || r.height < 20) continue;
    for (const [fx, fy] of [[0.5,0.5],[0.5,0.2],[0.2,0.5],[0.8,0.5],[0.5,0.8]]) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      const hit = document.elementFromPoint(x, y);
      if (hit && n.contains(hit)) {
        return {tid: n.getAttribute('data-testid') || '',
                aria: n.getAttribute('aria-label') || '', x: Math.round(x), y: Math.round(y)};
      }
    }
  }
  return null;
}"""
)
result["picked_node"] = picked
if picked is None:
    result["error"] = "no clickable node"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0)

page.mouse.click(picked["x"], picked["y"])
page.wait_for_timeout(2500)

# ② 生成表单里的下拉触发器，按**文案**认（模型名 / 尺寸 / 模式 / 时长）
TRIGGERS = ["即梦 Seedance", "16:9", "全能参考", "4s"]
for i, key in enumerate(TRIGGERS):
    # 每次重新点一下节点，保证表单还在（点空白会收起选中）
    page.mouse.click(picked["x"], picked["y"])
    page.wait_for_timeout(1200)
    label = page.evaluate(
        """(key) => {
      const scope = document.querySelector('[data-testid="video-generation-form"]')
                 || document.body;
      for (const b of scope.querySelectorAll('button,[role=button],[role=combobox]')) {
        const t = (b.innerText || '').replace(/\\s+/g, ' ').trim();
        if (t.includes(key) || (b.getAttribute('aria-label') || '').includes(key)) {
          b.click();
          return t || b.getAttribute('aria-label');
        }
      }
      return null;
    }""", key)
    page.wait_for_timeout(1500)
    result["steps"].append({
        "step": f"open:{key}", "clicked": label, "layers": page.evaluate(ENUM)
    })
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)

print(json.dumps(result, ensure_ascii=False, indent=2))
