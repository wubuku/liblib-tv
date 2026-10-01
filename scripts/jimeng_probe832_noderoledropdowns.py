"""batch 832 取证：源站视频节点工具条里的下拉**到底有没有 role**。

背景：复刻侧 `JimengNodeToolbar.tsx` 的两个下拉（截取帧 / 工具）是**裸 div**，
`role=` 一个都没有 ⇒ 任何按 `role ∈ dialog/menu/listbox/popover` 的普查都看不见它们。
在写进 README 之前必须先问源站：**源站那两个下拉有 role 吗**？

  · 有  → 复刻侧漏了，是真缺口（但补 role 属「复刻自有」还是「对齐」要看结论）
  · 没有 → 复刻侧与源站一致，普查看不见是**源站同款**，不是缺口
  · 测不到 → 如实记 BLOCKED_BY_FIXTURE，不猜

只读：只点「截取帧」这一个纯展示下拉，不选任何帧（不产出节点、不计费），
点完立即 Escape 收起。

跑法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe832_noderoledropdowns.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

# 枚举「**任何**看起来像浮层的东西」，不预设它有 role —— 否则测的还是我的假设
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
  // 候选 = 有 role 的 ＋ 视觉上像浮层的（深色圆角板 + 阴影）
  const SEL = '[role],[aria-haspopup],[class*="dropdown" i],[class*="popover" i],'
            + '[class*="menu" i],[class*="panel" i],[class*="popup" i]';
  const out = [];
  for (const el of document.querySelectorAll(SEL)) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    const txt = (el.innerText || '').replace(/\\s+/g, ' ').trim();
    if (txt.length > 300) continue;
    out.push({
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      name: nameOf(el),
      tid: el.getAttribute('data-testid') || '',
      haspopup: el.getAttribute('aria-haspopup') || '',
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      bg: s.backgroundColor, radius: s.borderRadius, z: s.zIndex,
      cls: (el.className || '').toString().replace(/\\s+/g, ' ').slice(0, 80),
      text: txt.slice(0, 90),
      items: el.querySelectorAll('button,[role=menuitem],[role=option]').length,
    });
  }
  return out;
}"""

page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

result = {"steps": []}

# ① 基线：什么浮层都没打开时
result["steps"].append({"step": "baseline", "layers": page.evaluate(ENUM)})

# ② 选一个**真能点到**的视频节点。
#    ⚠️ 踩过的坑：源站画布上的文本节点互相叠压，直接 node.click() 会超时 ——
#    日志里是「…from <div data-testid="rf__node-node_xxx"> subtree intercepts
#    pointer events」。`force=True` 在这里**没用**：真实鼠标事件仍落到最上层那个
#    元素上。唯一可靠的办法是先用 `elementFromPoint` 问**事实**：
#    谁的中心点最上层就是谁，我才去点谁。
picked_node = page.evaluate(
    """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  for (const n of nodes) {
    const r = n.getBoundingClientRect();
    if (r.width < 20 || r.height < 20) continue;
    // 采样 5 个点，只要有一个的最上层元素落在本节点内，就认为点得到
    const pts = [[0.5, 0.5], [0.5, 0.2], [0.2, 0.5], [0.8, 0.5], [0.5, 0.8]];
    for (const [fx, fy] of pts) {
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
result["picked_node"] = picked_node
if picked_node is None:
    result["error"] = "no clickable node (all overlapped)"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0)

page.mouse.click(picked_node["x"], picked_node["y"])
page.wait_for_timeout(2500)
result["steps"].append({"step": "node-selected", "layers": page.evaluate(ENUM)})

# ③ 找「截取帧」按钮并点开（只展开下拉，不选任何一帧）
picked = None
# 用 JS 直接 .click()，绕开命中测试 —— 源站节点互相叠压，坐标点击会打到别人身上。
# 这是一次**只读**探索（只展开下拉、不选任何一帧），不触发任何计费动作。
picked = page.evaluate(
    """() => {
  for (const b of document.querySelectorAll('button,[role=button]')) {
    const t = (b.innerText || '').replace(/\\s+/g, ' ').trim();
    if (t.includes('截取帧')) { b.click(); return t; }
  }
  return null;
}"""
)
result["picked_label"] = picked
page.wait_for_timeout(1500)
result["steps"].append({"step": "capture-dropdown-open", "layers": page.evaluate(ENUM)})

# ④ 同理点「工具」下拉
page.keyboard.press("Escape")
page.wait_for_timeout(800)
picked2 = page.evaluate(
    """() => {
  for (const b of document.querySelectorAll('button,[role=button]')) {
    const t = (b.innerText || '').replace(/\\s+/g, ' ').trim();
    if (t.startsWith('工具')) { b.click(); return t; }
  }
  return null;
}"""
)
result["picked_label_2"] = picked2
page.wait_for_timeout(1500)
result["steps"].append({"step": "tools-dropdown-open", "layers": page.evaluate(ENUM)})

print(json.dumps(result, ensure_ascii=False, indent=2))
