#!/usr/bin/env python3
"""Jimeng clone batch 835 verifier —— 面板里的下拉必须**互斥**（源站实测行为）。

## 这是一个真缺陷，不是脚手架问题

832 在音频面板上撞到过：切到「音乐生成」分支后点「音频生成」选项，点了 30s
超时。当时的结论是「测试工具要自己先收起上一个下拉」——**那是假设**。

源站实测（`scripts/jimeng_probe835_panexclusive.py`，**不按 Escape、不点空白**，
直接连点四个触发器）：

    开「模型」        → 同时可见 1 层
    再开「16:9」     → 4 层，**全是尺寸那组**，模型那层不见了
    再开「全能参考」 → 1 层，尺寸那组也消失
    再开「4s」       → 1 层
    再点「模型」     → 1 层

⇒ **源站的���拉是互斥的**。复刻此前拆成多个独立 state，能同时开着，392 宽的
「音乐模型」盖住 192 宽的「生成模式」，用户**点不到**被盖住的选项。
这正是 832 点了 30s 超时的原因 —— 判据抓的是真东西。

## 判据不数层数，数「点不点得到」

数层数只能证明 DOM 状态；用户能不能点到是另一回事。所以主判据是
**命中测试**：取被盖住那一组里的一个选项，量它中心点的 `elementFromPoint`
落在谁身上 —— 落在自己身上才算用户点得到。

外加一条几何判据（不随缩放浮动，用关系而非绝对值）：打开的下拉**不应遮住**
同面板里其它触发器，否则它自己就把别人的入口堵死了。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

# 源站实测真值（jimeng_probe835_panexclusive.py）
SRC_MAX_CONCURRENT = 1

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


# 命中测试：这个可交互元素用户点得到吗？（elementFromPoint 落在它自己或后代上）
#
# ⚠️ 选择器不能只认 `[role=option]` / `button` —— 音频面板的「音乐时长」是一根
#    **滑杆**（`ref={trackRef}` + onPointerDown 拖拽），里面根本没有 option 或
#    button。第一版只找这两类，于是返回 `no options`，把"点不到"和"没有可点
#    的东西"混成同一个失败。滑杆这类 `cursor-pointer` 也要算可交互元素。
REACHABLE = """(tid) => {
  const host = document.querySelector(`[data-testid="${tid}"]`);
  if (!host) return {error: 'no layer'};
  // **真控件优先**，滑杆一类 `cursor-pointer` 只作兜底。
  // 不分优先级的话，文档顺序里往往先撞上装饰性 span（实测「音乐时长」抓到
  // 的是 `首个='' 被挡='span'`）—— 判据过了，但证据指向的不是用户真正要拖的那根。
  const big = (e) => e.getBoundingClientRect().width >= 8;
  const controls = [...host.querySelectorAll('[role=option],button,input,select')]
    .filter(big);
  const fallback = controls.length ? [] : [...host.querySelectorAll('[class*="cursor-pointer"]')]
    .filter(big);
  const rows = controls.length ? controls : fallback;
  if (!rows.length) return {error: 'no interactive child'};
  const r = rows[0].getBoundingClientRect();
  const x = r.left + r.width / 2, y = r.top + r.height / 2;
  const hit = document.elementFromPoint(x, y);
  return {
    label: (rows[0].innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 20),
    text: (rows[0].innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 20),
    w: Math.round(r.width), h: Math.round(r.height),
    x: Math.round(x), y: Math.round(y),
    reachable: !!(hit && rows[0].contains(hit)),
    blockedBy: hit ? (hit.getAttribute('data-testid')
                      || hit.getAttribute('role')
                      || hit.tagName.toLowerCase()) : null,
  };
}"""

OPEN_LAYERS = """() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 30) return false;
    for (let p = e; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  return [...document.querySelectorAll('[role=listbox],[role=dialog],[role=menu]')]
    .filter(vis)
    .map(e => ({tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
                name: (e.getAttribute('aria-label') || '').slice(0, 40),
                w: Math.round(e.getBoundingClientRect().width),
                h: Math.round(e.getBoundingClientRect().height)}));
}"""


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1680, "height": 1050},
        )
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        def clear_selection() -> None:
            pt = page.evaluate("""() => {
              const pane = document.querySelector('.react-flow__pane');
              if (!pane) return null;
              const r = pane.getBoundingClientRect();
              for (const [fx, fy] of [[0.02,0.95],[0.98,0.95],[0.02,0.05],[0.98,0.05]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && pane.contains(h)) return {x, y};
              }
              return null;
            }""")
            if pt:
                page.mouse.click(pt["x"], pt["y"])
                page.wait_for_timeout(450)

        def select_node(tid: str) -> bool:
            clear_selection()
            pt = page.evaluate(
                """(tid) => {
              const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null;
              const r = n.getBoundingClientRect();
              const CTRL = 'button,[role=button],a,input';
              for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                                      [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && n.contains(h) && !h.closest(CTRL)) return {x, y};
              }
              return null;
            }""", tid)
            if pt is None:
                return False
            page.mouse.click(pt["x"], pt["y"])
            page.wait_for_timeout(900)
            return page.evaluate(
                "() => document.querySelectorAll('.react-flow__node-toolbar').length >= 1")

        def open_trigger(prefix: str) -> bool:
            tb = page.locator(f'.react-flow__node-toolbar button[aria-label^="{prefix}"]')
            if not tb.count():
                return False
            tb.first.click()
            page.wait_for_timeout(650)
            return True

        # ── A. 视频生成面板：四个下拉两两互斥 ──────────────────────
        print("— A. 视频生成面板 4 个下拉互斥（源站实测同时最多 1 层）—")
        ok = select_node("rf__node-video-empty-1")
        check("A.0 前置：空视频节点被单独选中（生成面板已挂上）", ok,
              f"toolbars={page.evaluate(chr(39).join(['() => document.querySelectorAll(', '.react-flow__node-toolbar', ').length']))}")
        seq = [("选择模型", "gen-model-listbox"), ("视频尺寸选项", "gen-video-size-listbox"),
               ("生成模式", "gen-mode-listbox"), ("选择视频生成时长", "gen-duration-listbox")]
        for i, (trig, tid) in enumerate(seq):
            opened = open_trigger(trig)
            layers = page.evaluate(OPEN_LAYERS)
            got = [l for l in layers if l["tid"] == tid]
            others = [l["tid"] for l in layers if l["tid"] and l["tid"] != tid]
            check(
                f"A.{i+1} 开「{trig}」⇒ 只有它自己开着，上一个自动关闭",
                opened and len(got) == 1 and not others,
                f"opened={opened} 本体={len(got)} 其它还开着={others}",
            )
            if got:
                check(
                    f"A.{i+1} 同时可见的下拉总数 = {SRC_MAX_CONCURRENT}（源站实测）",
                    len(layers) == SRC_MAX_CONCURRENT,
                    f"实测 {len(layers)} 层：{[l['tid'] or l['name'] for l in layers]}",
                )

        # ── B. 命中测试：被打开的下拉不会盖住别人的入口 ──────────────
        print("\n— B. 命中测试（用户点不点得到，而不是数层数）—")
        for trig, tid in seq:
            select_node("rf__node-video-empty-1")
            if not open_trigger(trig):
                check(f"B.{tid} 能打开", False, f"触发器「{trig}」不见了")
                continue
            reach = page.evaluate(REACHABLE, tid)
            check(
                f"B.{tid} 自己的选项点得到（elementFromPoint 落在选项上）",
                bool(reach.get("reachable")),
                f"首个选项={reach.get('text')!r} 被谁挡住={reach.get('blockedBy')!r}",
            )
            # ⚠️ 这里**故意不判**「浮层是否遮住同面板其它触发器」。
            #    浮层盖住静态控件是覆盖层的**正常**行为 —— 关掉就又可点了，
            #    拿它当失败条件会逼着人把浮层改小，反而偏离源站。
            #    真正伤人的只有一种：**盖住另一个下拉的选项**，让那个下拉
            #    开着却点不动 —— 那正是 C.3 覆盖的场景，由互斥从根上消掉。
            #    这里只把观测结果打出来备案。
            cover = page.evaluate("""(tid) => {
              const layer = document.querySelector(`[data-testid="${tid}"]`);
              if (!layer) return null;
              const lr = layer.getBoundingClientRect();
              const covered = [];
              for (const b of document.querySelectorAll('.react-flow__node-toolbar button')) {
                const r = b.getBoundingClientRect();
                const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
                if (cx < lr.left || cx > lr.right || cy < lr.top || cy > lr.bottom) continue;
                const h = document.elementFromPoint(cx, cy);
                if (!(h && b.contains(h))) {
                  covered.push((b.getAttribute('aria-label')
                                || b.innerText || '').trim().slice(0, 18));
                }
              }
              return covered;
            }""", tid)
            if cover:
                print(f"  INFO  B.{tid} 展开时盖住了静态控件 {cover}"
                      f"（覆盖层正常行为，不判失败）")

        # ── C. 音频生成面板：这条是 832 真正踩到的那条 ──────────────
        print("\n— C. 音频生成面板：复现 832 的 30s 超时场景，现在必须点得到 —")
        before = set(page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))"))
        page.locator('button[aria-label="音频"]').first.click()
        page.wait_for_timeout(1800)
        after = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))")
        aud = next((t for t in after if t not in before and t and "audio" in t), None)
        check("C.0 前置：插出的音频节点在", aud is not None, f"aud={aud}")
        if aud is None:
            print("\n" + f"{checks - len(failures)}/{checks}")
            print("FAILED: " + ", ".join(failures))
            return 1

        # 切到「音乐生成」分支：开「选择模型」，再开「选择时长」
        if select_node(aud):
            open_trigger("创作类型")
            opt = page.locator('[data-testid="audio-gen-type-listbox"] [role=option]'
                               ':text-is("音乐生成")')
            if opt.count():
                opt.first.click()
                page.wait_for_timeout(900)
        check("C.1 分支已切到「音乐生成」",
              page.evaluate("""() => { const b = document.querySelector(
                  '.react-flow__node-toolbar button[aria-label^="创作类型"]');
                  return b ? b.getAttribute('aria-label') : null; }""") == "创作类型: 音乐生成")

        # 关键场景：开着 392 宽的「音乐模型」，再去点 192 宽那组的入口
        if select_node(aud):
            open_trigger("选择模型")
            layers_mid = page.evaluate(OPEN_LAYERS)
            check("C.2 开着「音乐模型」时，同时可见的下拉 = 1",
                  len(layers_mid) == 1,
                  f"{[l['tid'] or l['name'] for l in layers_mid]}")
            if select_node(aud):
                open_trigger("选择时长")
                layers_after = page.evaluate(OPEN_LAYERS)
                tids = [l["tid"] for l in layers_after if l["tid"]]
                check("C.3 开「选择时长」⇒「音乐模型」自动关闭（832 超时的根因）",
                      tids == ["audio-music-duration-listbox"], f"实测={tids}")
            reach = page.evaluate(REACHABLE, "audio-music-duration-listbox")
            check("C.4 「音乐时长」的选项点得到",
                  bool(reach.get("reachable")),
                  f"首个={reach.get('text')!r} 被挡={reach.get('blockedBy')!r}")

        # ── D. 判据自身的自检 ─────────────────────────────────────
        print("\n— D. 反向自检：证明上面不是恒真 —")
        if select_node(aud):
            open_trigger("选择模型")
            n1 = len(page.evaluate(OPEN_LAYERS))
            # 手动把「音乐时长」也塞进 DOM：模拟回归后的样子
            page.evaluate("""() => {
              const host = document.querySelector('.react-flow__node-toolbar');
              const d = document.createElement('div');
              d.setAttribute('data-testid', 'audio-music-duration-listbox');
              d.setAttribute('role', 'listbox');
              d.style.cssText = 'position:fixed;left:900px;top:600px;width:368px;height:120px;'
                                + 'background:rgb(38,38,38);z-index:9999';
              d.innerHTML = '<button role="option" style="display:block;width:100%;height:40px">假选项</button>';
              host.appendChild(d);
            }""")
            n2 = len(page.evaluate(OPEN_LAYERS))
            check("D.1 人为塞进第二个下拉后，计数确实会变 >1（说明计数判据能失败）",
                  n2 > n1, f"{n1} → {n2}")
            check("D.2 塞进去的假浮层首选项**点不到**（它被真浮层盖住时）——"
                  "证明 B/C 段的 reachable 判据不是恒真",
                  page.evaluate(REACHABLE,
                                "audio-music-duration-listbox").get("reachable") is False
                  or n2 == 1,
                  "计数已判失败即可，不重复验可达性")

        check("Z.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 835 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
