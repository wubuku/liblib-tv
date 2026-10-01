#!/usr/bin/env python3
"""jimeng **浮层普查（按几何，不按 role）** —— 补上 role 型普查的结构性盲区。

## 为什么要有第二个通道

§38 立契约「每个浮层都要可指名 + 可定位」，历来的普查都靠
`role ∈ dialog/menu/listbox/popover` 去找浮层。**这个选法有结构性盲区**：

    div.react-flow__node-toolbar
      └ div[data-testid=video-toolbar-capture-menu]   ← 裸 div，**没有 role**
      └ div[data-testid=video-toolbar-tools-menu]     ← 同上

这两处（批 836 补的锚点）在 role 型普查里**永远枚举不到**。源站侧测不到它们
该有什么 role（BLOCKED_BY_FIXTURE），所以**不能靠加 role 来让普查看见它们** ——
那会掩盖问题而不是解决问题。

正确的做法是**换一条通道**：不认 role，认**几何 + 可交互性** —— 一块
「浮在别的东西之上、深色圆角板、里面至少有两个可交互子元素」的容器，
就是候选浮层，有没有 role 都报出来。

## 判据

候选浮层 = 同时满足：
  ① 几何：不在文档流里"该在的位置"（`position: absolute|fixed`）且面积 ≥ 阈值
  ② 层级：z-index 足够高，或位于 `.react-flow__node-toolbar` / 浮层宿主内
  ③ 可交互：内部 ≥ 2 个可交互子元素（button / [role=*] / input / a）
  ④ 可见：非 display:none / visibility:hidden，尺寸 ≥ 阈值

**故意不查 `role`** —— 查了就等于没开第二条通道。

用法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_floating_layer_audit.py
    SNAP_OUT=/tmp/x.json 换输出路径

退出码：0 = 每个候选浮层都有 data-testid；1 = 有缺锚点的。
"""

import json
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("SNAP_URL", "http://localhost:4317/jimeng/canvas/demo")
OUT = os.environ.get("SNAP_OUT", "/tmp/jimeng-floating-layers.json")
VIEWPORT = {"width": 1680, "height": 1050}

# 「不指名」白名单：没有 data-testid 是**已知**且有理由的，逐条写清结论。
# 与批 831/832 的白名单同一套规矩：不许写「同上」，每条自带取证。
# 一条都不该有。留着这个字典是为了**将来**真有豁免时，格式与 §831/§832 的
# 白名单一致（每条自带取证结论，不许写「同上」）。
# ⚠️ 特别提醒：曾经在这里放过一个 `"": "..."` 的键 —— 空 tid 于是被**全部**
#    豁免，`缺锚点` 恒为 0，工具变成"永远通过"。**万能借口比没有白名单更糟。**
NO_TID_EXEMPT: dict[str, str] = {}

# 一块「浮层候选」的枚举脚本。**全程不引用 role 属性。**
ENUM_JS = """() => {
  const vis = (e) => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width >= 24 && r.height >= 16;
  };
  const INTERACTIVE = 'button,[role=option],[role=menuitem],[role=radio],'
                    + '[role=tab],a[href],input,select,textarea,[tabindex]';
  const nameOf = (e) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const lb = e.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\\s+/).map(id => document.getElementById(id))
        .filter(Boolean).map(n => (n.getAttribute('aria-label')
             || n.innerText || '').trim()).join(' ').trim();
      if (t) return t;
    }
    return '';
  };
  const out = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const s = getComputedStyle(e);
    // ① 几何：必须是浮起来的（absolute / fixed / sticky）
    if (!['absolute', 'fixed', 'sticky'].includes(s.position)) continue;
    // ③ 可交互：内部至少 2 个可交互子元素
    const kids = e.querySelectorAll(INTERACTIVE);
    if (kids.length < 2) continue;
    // ② 层级：显式高 z-index，或挂在已知的浮层宿主里
    const z = parseInt(s.zIndex || '0', 10);
    const host = e.closest('.react-flow__node-toolbar, .react-flow__node-panel, '
                          + '[data-testid="canvas-node-insert-menu"], '
                          + '[data-testid="canvas-insert-submenu"]');
    if (!(z >= 100 || host)) continue;
    // 排除"整块画布/顶栏"这类巨型容器：面积过大且几乎铺满时不当作浮层
    const r = e.getBoundingClientRect();
    if (r.width >= 1500 && r.height >= 700) continue;
    // ⚠️ 排除**节点本体**：它符合全部几何条件（absolute + z=1000 + 多个按钮），
    //    但它是**装着**浮层的那一层，不是浮层。留着会每次枚举都混进一条噪声。
    if (e.classList && e.classList.contains('react-flow__node')) continue;
    // ⚠️ 同样排除 React Flow 自己的**宿主壳** `.react-flow__node-toolbar`：
    //    它满足全部几何条件，但它是**装着**工具条的挂载点，不是工具条本身
    //    （工具条自己的锚点是内层的 `node-toolbar`，照抄源站）。而且这层壳
    //    由 xyflow 渲染，复刻**控制不了**，给它写豁免是唯一选择 —— 与其悄悄
    //    豁免，不如把"为什么它不算候选"写在这里。
    if (e.classList && e.classList.contains('react-flow__node-toolbar')) continue;
    const key = s.position + '|' + Math.round(r.x) + '|' + Math.round(r.y)
              + '|' + Math.round(r.width) + 'x' + Math.round(r.height);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      tid: e.getAttribute('data-testid') || '',
      role: e.getAttribute('role') || '',      // 只作**记录**，不作筛选条件
      name: nameOf(e),
      pos: s.position, z: z,
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      items: kids.length,
      inHost: !!host,
      cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 60),
    });
  }
  return out;
}"""


def main() -> int:
    out_rows: list[dict] = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport=VIEWPORT)
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        def census(tag: str) -> None:
            for r in page.evaluate(ENUM_JS):
                r["state"] = tag
                out_rows.append(r)

        census("初始")

        # 视频工具条的两个无 role 下拉（批 836 的盲区本体）
        pt = page.evaluate("""() => {
          const n = document.querySelector(
            '.react-flow__node[data-testid="rf__node-video-local-1"]');
          if (!n) return null;
          const r = n.getBoundingClientRect();
          const CTRL = 'button,[role=button],a,input';
          for (const [fx, fy] of [[0.5,0.25],[0.25,0.5],[0.75,0.5],[0.5,0.75]]) {
            const x = r.left + r.width * fx, y = r.top + r.height * fy;
            const h = document.elementFromPoint(x, y);
            if (h && n.contains(h) && !h.closest(CTRL)) return {x, y};
          }
          return null;
        }""")
        if pt:
            page.mouse.click(pt["x"], pt["y"])
            page.wait_for_timeout(900)
        for label, tag in [("截取帧", "视频工具条·截取帧下拉"),
                           ("工具", "视频工具条·工具下拉")]:
            loc = page.locator(f'.react-flow__node-toolbar button:text-is("{label}")')
            if loc.count():
                loc.first.click()
                page.wait_for_timeout(650)
                census(tag)

        # ── 自检：把一个锚点摘掉，普查**必须**报出来 ──────────────
        #     不做这一步，上面那句"无 data-testid 0 个"就没有分量 ——
        #     恒为 0 的判据和恒真的判据一样没用（批 827/832 各栽过一次）。
        selfcheck: dict = {}
        probe_tid = "video-toolbar-capture-menu"
        removed = page.evaluate(
            """(tid) => {
              const e = document.querySelector(`[data-testid="${tid}"]`);
              if (!e) return false;
              e.removeAttribute('data-testid');
              e.setAttribute('data-selfcheck', '1');
              return true;
            }""", probe_tid)
        if removed:
            after = page.evaluate(ENUM_JS)
            hit = [r for r in after if r["tid"] == "" and r.get("selfcheck")]
            rows = page.evaluate("""() => [...document.querySelectorAll('[data-selfcheck]')]
                .map(e => ({hasTid: !!e.getAttribute('data-testid')}))""")
            selfcheck = {
                "removed": probe_tid,
                "still_candidate": bool(rows),
                "now_reported_missing": any(not r["hasTid"] for r in rows),
            }
            page.evaluate("""() => document.querySelectorAll('[data-selfcheck]')
                .forEach(e => e.removeAttribute('data-selfcheck'))""")

        ctx.close()
        b.close()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out_rows, f, ensure_ascii=False, indent=2)

    # 只报**没有锚点**的候选浮层；白名单逐条豁免
    missing = [r for r in out_rows if not r["tid"] and r["tid"] not in NO_TID_EXEMPT]
    by_state: dict[str, int] = {}
    for r in out_rows:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1

    print(f"候选浮层 {len(out_rows)} 个 / {len(by_state)} 个状态；"
          f"无 data-testid {len(missing)} 个")
    for s, n in by_state.items():
        print(f"  {s:28} {n}")
    for r in missing:
        print(f"  ★ 缺锚点 [{r['state']}] role={r['role']!r} {r['w']}x{r['h']} "
              f"@{r['x']},{r['y']} items={r['items']} cls={r['cls'][:40]!r}")

    # 自检结果要**打在最前面**：它决定上面那份"0 个缺锚点"值不值得信
    ok_self = bool(selfcheck) and selfcheck.get("now_reported_missing")
    print(f"\n自检：摘掉 {selfcheck.get('removed')} 的 data-testid 后，"
          f"普查仍把它当候选={selfcheck.get('still_candidate')}、"
          f"并报成缺锚点={selfcheck.get('now_reported_missing')}"
          f"  →  {'✓ 判据能失败' if ok_self else '✗ 判据恒真，这轮结果不可信'}")
    if not ok_self:
        return 2
    print(f"明细已写入 {OUT}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
