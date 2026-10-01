"""batch 840 取证：源站 composer 底行那枚「+」到底打开什么？

复刻现状（**未取证**，来自批 809 的推断）：点它弹一个 `role=menu` 的三项内联
菜单 —— 上传 / 从资产库添加 / 从画布添加，点任一项弹一句 toast、菜单关闭。
这三项**从哪来的没写过来源**，也没量过源站长什么样。

本探针只做**观察**，不点浮层里的任何一项：
  · 「上传」会拉起**原生文件选择框** —— headless 下会挂住或直接吞掉后续脚本；
  · 其余项可能进资产库/触发上传流程，有消耗积分的可能。
按 830 的规矩：不点消耗积分的控件。要知道后果，等哪天拿到一条明确的、
确定不消耗的路径再说 —— 「量不到」不等于「可以编」。

量到的写进 `docs/research/jimeng-canvas-batch840-2026-10-04/`。

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_840_addsource.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("docs/research/jimeng-canvas-batch840-2026-10-04")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# 浮层枚举：认 role，也认「底色深 + 圆角 + 内含若干可点行」的几何特征。
# 为什么不只认 role：批 837 记过源站有些浮层不带任何 role，
# 只认 role 会得到「点了没反应」的错误结论（批 836 同一个坑）。
OVERLAY_JS = """() => {
  const sel = '[role="menu"],[role="listbox"],[role="dialog"],[role="menu"],[data-radix-popper-content-wrapper]';
  const out = [];
  const seen = new Set();
  const push = (el, how) => {
    const b = el.getBoundingClientRect();
    if (b.width < 40 || b.height < 20) return;
    const key = [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)].join(',');
    if (seen.has(key)) return;
    seen.add(key);
    const cs = getComputedStyle(el);
    const rows = [...el.querySelectorAll('li,button,[role="menuitem"],[role="option"],[role="listitem"]')]
      .map((n) => { const nb = n.getBoundingClientRect();
        return { text: (n.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 30),
                 rect: [Math.round(nb.x), Math.round(nb.y), Math.round(nb.width), Math.round(nb.height)],
                 aria: n.getAttribute('aria-label') || '', tid: n.getAttribute('data-testid') || '',
                 role: n.getAttribute('role') || '', tag: n.tagName.toLowerCase() }; })
      .filter((r) => r.text);
    out.push({ how, role: el.getAttribute('role') || '', aria: el.getAttribute('aria-label') || '',
               bg: cs.backgroundColor, radius: cs.borderRadius,
               rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
               rows });
  };
  for (const el of document.querySelectorAll(sel)) push(el, 'role');
  // 几何兜底：靠右下、宽 120~420、圆角 ≥8 的深色块
  for (const el of document.querySelectorAll('div')) {
    const b = el.getBoundingClientRect();
    if (b.width < 120 || b.width > 420) continue;
    if (b.y < innerHeight * 0.2) continue;
    if (b.x < innerWidth - 560) continue;
    const cs = getComputedStyle(el);
    const r = parseFloat(cs.borderRadius) || 0;
    if (r < 8) continue;
    const m = cs.backgroundColor.match(/rgba?\\((\\d+), (\\d+), (\\d+)/);
    if (!m) continue;
    if (+m[1] > 90 || +m[2] > 90 || +m[3] > 90) continue;   // 深色
    push(el, 'geom');
  }
  return out;
}"""

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(24):
        if not page.evaluate("() => document.body.innerText.includes('Loading canvas')"):
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(2500)
    page.click('[data-testid="canvas-sidecar-launcher"]')
    page.wait_for_timeout(1500)

    report: dict = {"viewport": page.viewport_size, "steps": []}

    btn = page.locator('[data-testid="canvas-agent-composer-add"]')
    report["button"] = {
        "rect": btn.bounding_box(),
        "aria_label": btn.get_attribute("aria-label"),
        "aria_expanded": btn.get_attribute("aria-expanded"),
        "outer": (btn.evaluate("e => e.outerHTML") or "")[:400],
    }
    page.screenshot(path=str(OUT_DIR / "source-add-closed.png"))

    # 打开。⚠ 先把「打开前」的元素集合留在页面里，才能算出**新增了谁**。
    page.evaluate("""() => { window.__before = new Set(document.querySelectorAll('*')); }""")
    btn.click()
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT_DIR / "source-add-open.png"))

    report["overlays"] = page.evaluate(OVERLAY_JS)
    report["added_elements"] = page.evaluate(
        """() => {
          const added = [];
          for (const el of document.querySelectorAll('*')) {
            if (window.__before.has(el)) continue;
            const b = el.getBoundingClientRect();
            if (b.width < 8 || b.height < 8) continue;
            const t = (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 40);
            if (!t) continue;
            added.push({ tid: el.getAttribute('data-testid') || '', text: t,
                         rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] });
          }
          return added.slice(0, 60);
        }"""
    )
    report["body_tail"] = page.evaluate(
        "() => document.body.innerText.replace(/\\s+/g, ' ').slice(-600)"
    )
    # 打开态下整页所有 testid（看看新浮层到底带不带 testid —— 836 的教训）
    report["testids_visible"] = page.evaluate(
        """() => [...new Set([...document.querySelectorAll('[data-testid]')]
             .map((e) => e.getAttribute('data-testid'))
             .filter((t) => t && !/^rf__/.test(t)))].sort()"""
    )

    (OUT_DIR / "source-addsource-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
