#!/usr/bin/env python3
"""batch 857 复刻侧诊断：把「皮当不了栈顶」从**假设**变成**事实**。

§74 回退产品重写时留了个假设，但**没证伪**：

> 多半是**滚动容器**（`overflow-y-auto`）改变了层叠上下文，使「同层兄弟」的
> 假设不再成立 —— 皮插在行内、却落在滚动裁剪之外。

§74 只记了两个数（旧版 36/27、新版 52/0）和三个猜测。这一批**逐个证伪**。

⚠️⚠️ 本探针**自己起浏览器**（不能用 `jimeng_headless.py run` 注入 `page`
—— 那个是源站登录态；`sync_playwright` 在 asyncio loop 里会报错）。
跑法：/opt/miniconda3/bin/python3 scripts/jimeng_probe857_skinwhy.py

它**照抄审计的夹具与判据**（同一段 JS，逐字同款），并做三组对照：

  A. 面板**关**：基线（应当 ≈ §74 旧版的 36 控件 / 27 次）
  B. 面板**开**（旧版 242px）
  C. 面板**开**（新版 320px 四段）—— 用 `?skin=wide` 开关切换

每组报：控件数 / 皮数 / **皮当过栈顶几次** / 深探针层
`video-toolbar-capture-menu` 可达吗 / 面板挡住了谁。

**只诊断，不改产品。**
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"

# ⚠️ 与 jimeng_unclickable_audit.py 逐字同款（那一段是判据的核心，
#    抄错一行这次对照就白跑了）。
SKIN_JS = """() => {
  const SEL = 'a[href],button,input,select,textarea,[tabindex],'
            + '[role=menuitem],[role=option]';
  let n = 0;
  for (const c of document.querySelectorAll(SEL)) {
    const r = c.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (!c.parentNode) continue;
    const cs = getComputedStyle(c);
    let ox = 0, oy = 0;
    const op = c.offsetParent;
    if (op) {
      const orr = op.getBoundingClientRect();
      ox = orr.x + (op.clientLeft || 0);
      oy = orr.y + (op.clientTop || 0);
    }
    const d = document.createElement('div');
    d.setAttribute('data-kbskin-probe', '1');
    d.style.cssText = 'position:absolute;'
      + 'z-index:' + (cs.zIndex === 'auto' ? '0' : cs.zIndex) + ';'
      + 'left:' + (r.x - ox - 2) + 'px;'
      + 'top:' + (r.y - oy - 2) + 'px;'
      + 'width:' + (r.width + 4) + 'px;'
      + 'height:' + (r.height + 4) + 'px;'
      + 'background:transparent;';
    c.parentNode.insertBefore(d, c.nextSibling);
    n += 1;
  }
  return n;
}"""

# 皮插完之后，**为什么它不是栈顶**：把每个控件的边采样点与皮的几何一起交出来
# 批 858：把 §75 的推论变成事实 —— **Tab 游走到该层时**，皮当没当过栈顶。
# §75 猜「0 = Tab 没走进去 ⇒ 一个样本都没采到」。这一段照抄审计的采样口径：
# 反复按 Tab，每一步量「焦点所在控件的边采样点栈顶是谁」，累计 skin_top。
TABWALK_JS = """(layerTid) => {
  const L = document.querySelector(`[data-testid="${layerTid}"]`);
  if (!L) return {ok: false, why: '层没开'};
  const EDGE = (b) => [[b.left - 1, b.top + b.height / 2],
                       [b.right + 1, b.top + b.height / 2],
                       [b.x + b.width / 2, b.top - 1],
                       [b.x + b.width / 2, b.bottom + 1]];
  let steps = 0, in_layer = 0, skin_top = 0, samples = 0;
  const seen = [];
  for (let i = 0; i < 200; i++) {
    // 这一步的采样
    const a = document.activeElement;
    if (a && a !== document.body) {
      const b = a.getBoundingClientRect();
      if (b.width > 1 && b.height > 1) {
        if (L.contains(a)) in_layer += 1;
        for (const [ex, ey] of EDGE(b)) {
          const t = (document.elementsFromPoint(ex, ey) || [])[0];
          if (!t) continue;
          samples += 1;
          if (t.getAttribute && t.getAttribute('data-kbskin-probe')) skin_top += 1;
        }
        if (i < 60) seen.push((L.contains(a) ? '*' : ' ') + i + ':'
          + a.tagName + '/' + ((a.getAttribute('aria-label') || '')
            .slice(0, 18)));
      }
    }
    steps += 1;
    break;   // 只做一次采样；真正的 Tab 推进在 Python 侧
  }
  return {ok: true, steps, in_layer, skin_top, samples, seen};
}"""

WHY_JS = """(layerTid) => {
  const L = document.querySelector(`[data-testid="${layerTid}"]`);
  const out = {in_layer: !!L, rows: [], skins: 0, skins_in_layer: 0};
  const skins = document.querySelectorAll('[data-kbskin-probe]');
  out.skins = skins.length;
  for (const s of skins) {
    if (L && L.contains(s)) out.skins_in_layer += 1;
  }
  if (!L) return out;
  const lr = L.getBoundingClientRect();
  out.layer_rect = [Math.round(lr.x), Math.round(lr.y),
                     Math.round(lr.width), Math.round(lr.height)];
  // 层内每个可聚焦控件：皮在不在、边采样点的栈顶是谁
  const SEL = 'a[href],button,input,select,textarea,[tabindex],'
            + '[role=menuitem],[role=option]';
  for (const c of L.querySelectorAll(SEL)) {
    const b = c.getBoundingClientRect();
    if (b.width < 1 || b.height < 1) continue;
    const skin = c.nextElementSibling &&
                 c.nextElementSibling.hasAttribute('data-kbskin-probe')
                 ? c.nextElementSibling : null;
    const sb = skin ? skin.getBoundingClientRect() : null;
    const EDGE = [[b.left - 1, b.top + b.height / 2],
                  [b.right + 1, b.top + b.height / 2],
                  [b.x + b.width / 2, b.top - 1],
                  [b.x + b.width / 2, b.bottom + 1]];
    let skin_top = 0, tops = [];
    for (const [ex, ey] of EDGE) {
      const st = document.elementsFromPoint(ex, ey) || [];
      const t = st[0];
      if (!t) { tops.push('null'); continue; }
      const isSkin = !!(t.getAttribute && t.getAttribute('data-kbskin-probe'));
      if (isSkin) skin_top += 1;
      tops.push((isSkin ? 'SKIN:' : '') + t.tagName
                + (t.getAttribute && t.getAttribute('data-testid')
                   ? '#' + t.getAttribute('data-testid') : '')
                + (t.className && t.className.toString
                   ? '.' + t.className.toString().replace(/\\s+/g, ' ').slice(0, 26)
                   : ''));
    }
    out.rows.push({
      al: (c.getAttribute('aria-label') || '').slice(0, 22),
      tag: c.tagName,
      rect: [Math.round(b.x), Math.round(b.y),
             Math.round(b.width), Math.round(b.height)],
      has_skin: !!skin,
      skin_rect: sb ? [Math.round(sb.x), Math.round(sb.y),
                       Math.round(sb.width), Math.round(sb.height)] : null,
      skin_top_edges: skin_top,
      tops,
      in_view: b.y >= 0 && b.bottom <= innerHeight,
    });
  }
  return out;
}"""


def tabwalk(pg, layer_tid, max_tabs=200):
    """批 858：盖皮之后**按 Tab 游走**，每一步都采样（审计的同款口径）。"""
    pg.evaluate("""() => { const a = document.activeElement;
                    if (a && a.blur) a.blur(); return true; }""")
    w = {"ok": False, "steps": 0, "in_layer": 0, "skin_top": 0, "samples": 0,
         "trace": []}
    for i in range(max_tabs):
        pg.keyboard.press("Tab")
        step = pg.evaluate("""(tid) => {
          const L = document.querySelector(`[data-testid="${tid}"]`);
          const a = document.activeElement;
          if (!a || a === document.body)
            return {in: false, who: 'body', skin: 0, n: 0};
          const b = a.getBoundingClientRect();
          if (b.width < 1 || b.height < 1)
            return {in: false, who: a.tagName, skin: 0, n: 0};
          const EDGE = [[b.left - 1, b.top + b.height / 2],
                        [b.right + 1, b.top + b.height / 2],
                        [b.x + b.width / 2, b.top - 1],
                        [b.x + b.width / 2, b.bottom + 1]];
          let skin = 0, n = 0;
          for (const [ex, ey] of EDGE) {
            const t = (document.elementsFromPoint(ex, ey) || [])[0];
            if (!t) continue;
            n += 1;
            if (t.getAttribute && t.getAttribute('data-kbskin-probe')) skin += 1;
          }
          return {in: !!(L && L.contains(a)), skin, n,
                  who: a.tagName + '/' + (a.getAttribute('aria-label') || '')
                        .slice(0, 20)};
        }""", layer_tid)
        w["steps"] += 1
        w["in_layer"] += 1 if step.get("in") else 0
        w["skin_top"] += step.get("skin", 0)
        w["samples"] += step.get("n", 0)
        if len(w["trace"]) < 40:
            w["trace"].append(("*" if step.get("in") else " ")
                              + f"{i}:{step.get('who')}"
                              + f" skin={step.get('skin')}/{step.get('n')}")
        if w["in_layer"] >= 1 and i > 8:
            break
    return w


def snapshot(pg, label, layer_tid):
    """盖皮 → 问「皮当过几次栈顶 + 为什么」→ **按 Tab 游走再问一次** → 拆皮。"""
    n_skin = pg.evaluate(SKIN_JS)
    pg.wait_for_timeout(300)
    why = pg.evaluate(WHY_JS, layer_tid)
    walk = tabwalk(pg, layer_tid)
    pg.evaluate("""() => document.querySelectorAll('[data-kbskin-probe]')
        .forEach(e => e.remove())""")
    n_ctrl = why.get("rows")
    skin_top_total = sum(r.get("skin_top_edges", 0) for r in (n_ctrl or []))
    rec = {"label": label, "skins": n_skin,
           "layer_open": why.get("in_layer"),
           "layer_rect": why.get("layer_rect"),
           "skins_in_layer": why.get("skins_in_layer"),
           "rows_n": len(n_ctrl or []),
           "skin_top_edges_total": skin_top_total,
           "tabwalk": walk,
           "rows": (n_ctrl or [])[:26]}
    return rec


def run(pg, mode):
    """mode='old' | 'wide'：面板由**工作区当前文件**决定，跑两遍换版本。"""
    out = {"mode": mode}
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    pg.set_viewport_size({"width": 1512, "height": 1200})
    pg.wait_for_timeout(1500)

    LAYER = "jimeng-search-overlay"
    out["A_panel_closed"] = snapshot(pg, "A 面板关（基线）", LAYER)

    # 打开搜索面板（旧版 242px —— 当前工作区就是这个）
    trg = pg.locator('button[aria-label="搜索"]')
    if trg.count():
        try:
            trg.first.click(timeout=6000)
            pg.wait_for_timeout(900)
        except Exception as e:  # noqa: BLE001
            out["open_err"] = str(e)[:120]
    out["B_panel_open_old"] = snapshot(pg, "B 面板开（旧版 242px）", LAYER)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(600)

    # 重开一次页面（新版四段是同一份代码的另一种形态，跑第二遍时就是它）
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    pg.set_viewport_size({"width": 1512, "height": 1200})
    pg.wait_for_timeout(1500)
    trg2 = pg.locator('button[aria-label="搜索"]')
    opened2 = False
    if trg2.count():
        try:
            trg2.first.click(timeout=6000)
            pg.wait_for_timeout(900)
            opened2 = pg.locator(f'[data-testid="{LAYER}"]').count() > 0
        except Exception as e:  # noqa: BLE001
            out["open_err2"] = str(e)[:120]
    out["C_panel_open_second_run"] = snapshot(
        pg, f"C 第二遍面板开（mode={mode}）", LAYER)
    out["C_panel_open_second_run"]["opened"] = opened2
    return out


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1512, "height": 1200})
        pg = ctx.new_page()
        try:
            res = run(pg, sys.argv[1] if len(sys.argv) > 1 else "old")
        finally:
            b.close()
    with open("/tmp/b857-skinwhy.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    for k in ("A_panel_closed", "B_panel_open_old", "C_panel_open_second_run"):
        r = res.get(k) or {}
        print(f"\n===== {r.get('label', k)} =====")
        print(f"  面板开着={r.get('layer_open')} 层矩形={r.get('layer_rect')}")
        print(f"  皮 {r.get('skins')} 张（层内 {r.get('skins_in_layer')} 张）"
              f"｜层内控件 {r.get('rows_n')} 个")
        print(f"  ★ 静态量：皮当过栈顶的边采样点 = {r.get('skin_top_edges_total')}")
        w = r.get("tabwalk") or {}
        print(f"  ★ Tab 游走 {w.get('steps')} 步：进层 {w.get('in_layer')} 步"
              f"｜皮当栈顶 {w.get('skin_top')}/{w.get('samples')} 个采样点")
        for t in (w.get("trace") or [])[:12]:
            print(f"       {t}")
        for row in (r.get("rows") or [])[:8]:
            print(f"     {row['tag']:<7} al={row['al']!r:<24} "
                  f"rect={row['rect']} 皮={row['has_skin']} "
                  f"当栈顶 {row['skin_top_edges']}/4 tops={row['tops'][:2]}")
    print("\n== 已写 /tmp/b857-skinwhy.json ==")


if __name__ == "__main__":
    main()
