"""batch 833 取证：源站生成表单里 4 个下拉**触发器**的 role / 可访问名。

832 已经量到源站**展开后**的浮层（`presentation` / `dialog` / `listbox` 混用，
还有英文名 `Duration options` / `Reference mode options`），但还没量**触发器
本身**的 role 与可访问名。没有触发器的对照，就说不清复刻侧的
`aria-label="视频尺寸选项: 16:9 · 720P · 1, Standard-only model"` 是照抄来的，
还是**从触发器文案拼的**（后者就是复刻自有）。

这一支只读：逐个记录触发器的 role / aria-label / aria-expanded / 几何，
点开再记浮层的 role / name / 几何。不选任何一项（不提交、不计费）。

跑法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe833_gentriggers.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

# 触发器认法：生成表单容器内，文本里含 key 的 button/combobox
TRIGGERS = ["即梦 Seedance", "16:9", "全能参考", "4s"]

READ = """(key) => {
  const form = document.querySelector('[data-testid="video-generation-form"]')
            || document.body;
  const t = (e) => (e.innerText || '').replace(/\\s+/g, ' ').trim();
  let hit = null;
  for (const b of form.querySelectorAll('button,[role=button],[role=combobox]')) {
    const txt = t(b);
    if (txt.includes(key) || (b.getAttribute('aria-label') || '').includes(key)) {
      hit = b; break;
    }
  }
  if (!hit) return {key, found: false};
  const r = hit.getBoundingClientRect();
  const cs = getComputedStyle(hit);
  const before = document.querySelectorAll('[role=dialog],[role=listbox],[role=menu]').length;
  hit.click();
  const after = document.querySelectorAll('[role=dialog],[role=listbox],[role=menu]').length;
  // 点开后新出现的浮层（按 role 层 + 几何猜：层级里最靠上的那块深色板）
  const layers = [...document.querySelectorAll('[role],[class*="dropdown" i],[class*="popover" i]')]
    .map(e => { const b = e.getBoundingClientRect();
      return {role: e.getAttribute('role') || '',
              name: e.getAttribute('aria-label') || '',
              tid: e.getAttribute('data-testid') || '',
              w: Math.round(b.width), h: Math.round(b.height),
              x: Math.round(b.x), y: Math.round(b.y),
              text: t(e).slice(0, 60),
              cls: (e.className || '').toString().replace(/\\s+/g,' ').slice(0, 60)};
    })
    .filter(l => l.w > 60 && l.h > 30 && l.text);
  return {
    key, found: true,
    trigger: {
      tag: hit.tagName.toLowerCase(), role: hit.getAttribute('role') || '',
      aria: hit.getAttribute('aria-label'), expanded: hit.getAttribute('aria-expanded'),
      haspopup: hit.getAttribute('aria-haspopup'),
      text: t(hit), w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      bg: cs.backgroundColor, radius: cs.borderRadius,
    },
    roleLayerDelta: after - before,
    layers,
  };
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
      const hit = document.elementFromPoint(x, y);
      if (hit && n.contains(hit)) {
        return {tid: n.getAttribute('data-testid') || '',
                aria: n.getAttribute('aria-label') || '',
                x: Math.round(x), y: Math.round(y)};
      }
    }
  }
  return null;
}"""
)
result = {"picked_node": picked, "triggers": []}
if picked is None:
    result["error"] = "no clickable node"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0)

for key in TRIGGERS:
    page.mouse.click(picked["x"], picked["y"])   # 点空白会收起选中，先点回节点
    page.wait_for_timeout(1400)
    result["triggers"].append(page.evaluate(READ, key))
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)

print(json.dumps(result, ensure_ascii=False, indent=2))
