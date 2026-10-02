#!/usr/bin/env python3
"""batch 879：Clear 上 Esc 的焦点落点修复**没生效** —— 先量能不能够着节点。

## 上一版（878 修复）为什么没生效

我写了 `closest(".react-flow__node")?.focus()`，跑出来焦点**仍然落 body**。

原因没查就写了：React Flow 的 `NodeToolbar` 内部是 **portal**，
渲染到渲染器容器上、**不在** `.react-flow__node` 里面
（`JimengAudioNode.tsx:129` 把 `<JimengAudioGenPanel>` 当子元素传下去，
但面板里那个 `<NodeToolbar>` 自己会搬到别处）⇒ `closest()` 返回 null。

⚠️ 这是**又一次「没量就写」**（876 的 Clear 焦点、876c 的判据、
这次连着三回）。所以本探针**只量两件事**，不碰产品：

① Clear 的**完整祖先链**（到底能不能 closest 到节点）
② 复刻节点元素**带哪些属性**（`data-id` / `data-testid` / …）——
   要用属性选择器定位，就得先知道属性叫什么

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe879_reachnode_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b879-ck-reachnode.json")

CHAIN_JS = """() => {
  const b = document.querySelector('[aria-label="Clear 性别 filter"]');
  if (!b) return {no_clear: true};
  const chain = [];
  let n = b;
  while (n && chain.length < 12) {
    chain.push({tag: n.tagName,
                cls: ((n.className || '') + '').slice(0, 70),
                data_id: n.getAttribute('data-id'),
                data_testid: n.getAttribute('data-testid'),
                is_node: !!(n.classList &&
                            n.classList.contains('react-flow__node')),
                is_toolbar: !!(n.classList &&
                               n.classList.contains('react-flow__node-toolbar'))});
    if (n === document.body) break;
    n = n.parentElement;
  }
  return {chain,
          can_closest_node: !!b.closest('.react-flow__node'),
          can_closest_toolbar: !!b.closest('.react-flow__node-toolbar')};
}"""

NODE_ATTRS_JS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => {
    const attrs = {};
    for (const a of n.attributes) attrs[a.name] = (a.value || '').slice(0, 40);
    return {attrs,
            tabindex: n.getAttribute('tabindex'),
            role: n.getAttribute('role'),
            aria: n.getAttribute('aria-label') || ''};
  })"""

# 各种候选定位方式，逐个**验**能不能选中那个音频节点
REACH_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const audio = nodes.find(n => /audio/i.test(
    (n.getAttribute('data-testid') || '') + (n.getAttribute('data-id') || '')
    + (n.innerHTML || '').slice(0, 400)));
  const tries = {
    'data-testid^=rf__node-audio':
      'div[data-testid^="rf__node-audio"]',
    'data-id 含 audio': '[data-id*="audio"]',
    'data-id 含 rf__node-audio': '[data-id^="rf__node-audio"]',
  };
  const out = {};
  for (const [k, sel] of Object.entries(tries)) {
    const el = document.querySelector(sel);
    out[k] = {found: !!el,
              n: document.querySelectorAll(sel).length,
              same_as_audio: el ? el === audio : null,
              tabindex: el ? el.getAttribute('tabindex') : null};
  }
  return {out,
          audio_found: !!audio,
          audio_testid: audio ? audio.getAttribute('data-testid') : null,
          audio_data_id: audio ? audio.getAttribute('data-id') : null,
          audio_aria: audio ? audio.getAttribute('aria-label') : null};
}"""


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        t = pg.locator('button[aria-label="音频"]')
        if t.count():
            t.first.click(timeout=8000)
            time.sleep(2.0)
        nid = [x for x in pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))") if x and "audio" in x]
        res["audio_testid"] = nid[0] if nid else None
        if nid:
            pt = pg.evaluate("""(tid) => {
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
            }""", nid[0])
            if pt:
                pg.mouse.click(pt[0], pt[1])
                time.sleep(1.2)

        # 开音色库 + 选一个值，让 Clear 出现
        if not pg.locator('[data-testid="audio-all-voices-listbox"]').count():
            vt = pg.locator('button[aria-label^="音色"]')
            if vt.count():
                vt.first.click(timeout=8000)
                time.sleep(1.5)
        res["voices_open"] = bool(
            pg.locator('[data-testid="audio-all-voices-listbox"]').count())
        if res["voices_open"]:
            c = pg.evaluate("""() => {
              for (const b of document.querySelectorAll('button[aria-expanded]')) {
                const a = b.getAttribute('aria-label') || '';
                if (a.startsWith('性别:')) {
                  const r = b.getBoundingClientRect();
                  return [r.x + r.width/2, r.y + r.height/2];
                }
              }
              return null;
            }""")
            if c:
                pg.mouse.click(c[0], c[1])
                time.sleep(0.8)
                o = pg.get_by_text("男", exact=True).first
                if o.count():
                    o.click(timeout=8000)
                    time.sleep(0.9)

        chain = pg.evaluate(CHAIN_JS)
        res["chain"] = chain
        print("== Clear 的祖先链 ==")
        if chain.get("no_clear"):
            print("  !! Clear 不存在 ⇒ 前置态没成立")
        else:
            for i, c in enumerate(chain["chain"]):
                mk = (" ←节点" if c["is_node"] else
                      (" ←工具条" if c["is_toolbar"] else ""))
                print(f"   {'  '*i}{c['tag']} data-id={c['data_id']!r} "
                      f"testid={c['data_testid']!r}{mk}")
                print(f"   {'  '*i}   cls={c['cls']!r}")
            print(f"   can_closest_node={chain['can_closest_node']}  "
                  f"can_closest_toolbar={chain['can_closest_toolbar']}")

        res["node_attrs"] = pg.evaluate(NODE_ATTRS_JS)
        print("\n== 节点元素属性 ==")
        for n in res["node_attrs"]:
            print(f"   data-id={n['attrs'].get('data-id')!r} "
                  f"testid={n['attrs'].get('data-testid')!r} "
                  f"tabindex={n['tabindex']!r} role={n['role']!r} "
                  f"aria={n['aria'][:20]!r}")

        reach = pg.evaluate(REACH_JS)
        res["reach"] = reach
        print("\n== 候选定位方式 ==")
        for k, v in reach["out"].items():
            print(f"   {k:32s} found={v['found']} n={v['n']} "
                  f"是音频节点={v['same_as_audio']} tabindex={v['tabindex']!r}")
        print(f"   音频节点：testid={reach['audio_testid']!r} "
              f"data-id={reach['audio_data_id']!r} "
              f"aria={reach['audio_aria']!r}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
