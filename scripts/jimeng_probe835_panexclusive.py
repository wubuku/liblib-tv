"""batch 835 取证：源站生成表单里，几个下拉**是不是互斥**的？

832/833 两批都撞到同一件事：复刻侧同一块面板里的几个下拉**各自独立 state，
可以同时开着**，而且宽的那个会盖住窄的 —— 实测 `音乐模型`（392 宽）压住了
`生成模式`（192 宽）里的选项，点「音频生成」直接超时。

832 当时把它当成「测试工具要自己先收起」的脚手架问题。但那是**假设**：
源站会不会也这样？**没测过。** 两种可能，结论完全相反：

  · 源站也同时开着     → 复刻与源站一致，不是缺陷，只需把"要自己收起"写进工具
  · 源站开一个关一个   → 复刻是真缺陷（用户点不动被盖住的那一项），该修产品

取证方法：**不按 Escape、不点空白**（那会收起整个面板），直接点第二个触发器，
然后数"同时可见的下拉有几个"。

只读：只点触发器展开下拉，不选任何一项（不提交、不计费）。

跑法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe835_panexclusive.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

# 只认**可见且够大**的下拉块；按 role 抓，抓不到再按几何兜底
COUNT = """() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 30) return false;
    for (let p = e; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  const out = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('[role=listbox],[role=dialog],[role=menu],[role=presentation]')) {
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect();
    const t = (e.innerText || '').replace(/\\s+/g, ' ').trim();
    if (!t || t.length > 200) continue;
    // 内层容器（几何被外层完全包含）不重复计
    const key = t.slice(0, 30);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({role: e.getAttribute('role') || '', name: e.getAttribute('aria-label') || '',
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y), text: t.slice(0, 60)});
  }
  return out;
}"""

CLICK = """(key) => {
  const form = document.querySelector('[data-testid="video-generation-form"]')
            || document.querySelector('.react-flow__node-toolbar') || document.body;
  for (const b of form.querySelectorAll('button,[role=button],[role=combobox]')) {
    const t = (b.innerText || '').replace(/\\s+/g, ' ').trim();
    if (t.includes(key) || (b.getAttribute('aria-label') || '').includes(key)) {
      b.click();
      return t || b.getAttribute('aria-label');
    }
  }
  return null;
}"""

page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

picked = page.evaluate(
    """() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.width < 20 || r.height < 20) continue;
    for (const [fx, fy] of [[0.5,0.5],[0.5,0.2],[0.2,0.5],[0.8,0.5],[0.5,0.8]]) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      const h = document.elementFromPoint(x, y);
      if (h && n.contains(h)) return {tid: n.getAttribute('data-testid') || '',
                                      x: Math.round(x), y: Math.round(y)};
    }
  }
  return null;
}"""
)
result = {"picked_node": picked, "sequence": []}
if picked is None:
    result["error"] = "no clickable node"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0)

# 依次点开三个下拉，**中间不按 Escape、不点空白**
for key in ["即梦 Seedance", "16:9", "全能参考", "4s"]:
    page.mouse.click(picked["x"], picked["y"]) if not result["sequence"] else None
    page.wait_for_timeout(600)
    clicked = page.evaluate(CLICK, key)
    page.wait_for_timeout(1200)
    result["sequence"].append({
        "clicked": clicked,
        "open": page.evaluate(COUNT),
    })

# 再点一次第一个，看它是"再关掉"还是"仍然开着"
result["reclick_first"] = page.evaluate(CLICK, "即梦 Seedance")
page.wait_for_timeout(1200)
result["after_reclick_first"] = page.evaluate(COUNT)

print(json.dumps(result, ensure_ascii=False, indent=2))
