#!/usr/bin/env python3
"""batch 880（复刻侧）：Clear 上 Esc 的焦点**到底丢在哪一步**。

## 前两版修复都「没生效」

- 878 修法：`closest(".react-flow__node")?.focus()`
  → 探针 879 查明 `can_closest_node=False`（NodeToolbar 是 portal）
- 879 修法：`closest(".react-flow__node-toolbar")` → 读 `data-id`
  → 按属性相等找节点 → `focus()`
  → **重跑仍然落 body**，且**重启 dev server 后仍然**落 body

⇒ 不是热更新。清除生效证明 `onKeyDown` **执行了**，所以问题在 focus 那一段。

## 本探针只量四件事（**不碰产品**）

① 此刻（Esc 之前）我那段逻辑**手工跑一遍**能不能聚焦成功
   —— 把「focus 本身不可行」和「Esc 之后被抢走」分成两栏
② `closest(".react-flow__node-toolbar")` 此刻的 `data-id` 到底是什么
③ 聚焦成功后**立刻**读 `activeElement`（同步，还没按 Esc）
④ 按 Esc 之后读 `activeElement` —— 跟 ③ 比，差值就是「谁抢走的」

⚠️ ①③④ 必须**各自**跑，中途不复用状态（否则又是「诊断动作改了被诊断状态」）。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe880_escfocus_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b880-ck-escfocus.json")

FOCUS_JS = """() => { const a = document.activeElement;
  if (!a) return {tag: '(null)'};
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          data_id: a.getAttribute('data-id'),
          is_node: !!(a.classList &&
                      a.classList.contains('react-flow__node')),
          in_toolbar: !!(a.closest &&
                         a.closest('.react-flow__node-toolbar'))}; }"""

# ① 手工跑一遍组件里那段逻辑，逐步记录
REPLAY_JS = """() => {
  const b = document.querySelector('[aria-label="Clear 性别 filter"]');
  if (!b) return {no_clear: true};
  const tb = b.closest('.react-flow__node-toolbar');
  const nid = tb ? tb.getAttribute('data-id') : null;
  const out = {tb_found: !!tb, nid,
               n_nodes: document.querySelectorAll('.react-flow__node').length,
               n_toolbars: document.querySelectorAll(
                 '.react-flow__node-toolbar').length};
  if (!nid) { out.reason = 'closest 没命中工具条'; return out; }
  const all = [...document.querySelectorAll('.react-flow__node')];
  out.all_data_ids = all.map(n => n.getAttribute('data-id'));
  const nodeEl = all.find(n => n.getAttribute('data-id') === nid);
  out.node_found = !!nodeEl;
  if (!nodeEl) { out.reason = 'data-id 对不上，节点没找到'; return out; }
  out.node_tabindex = nodeEl.getAttribute('tabindex');
  const before = document.activeElement;
  out.before = before.getAttribute
    ? (before.getAttribute('aria-label') || before.tagName) : '?';
  nodeEl.focus();
  const a = document.activeElement;
  out.focus_ok = a === nodeEl;
  out.after = a.getAttribute ? (a.getAttribute('aria-label') || a.tagName) : '?';
  out.after_is_node = !!(a.classList &&
                         a.classList.contains('react-flow__node'));
  return out;
}"""

# 聚焦后**同步**再读一次（隔 0ms 与 300ms，看有没有被异步换掉）
SETTLE_JS = """(tid) => {
  const all = [...document.querySelectorAll('.react-flow__node')];
  const el = all.find(n => n.getAttribute('data-id') === tid);
  if (!el) return {gone: true};
  el.focus();
  const a = document.activeElement;
  const sync = a === el ? 'node' : (a === document.body ? 'body' : 'other');
  return {sync_focus: sync, tabindex: el.getAttribute('tabindex')};
}"""


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        t = pg.locator('button[aria-label="音频"]')
        if t.count():
            t.first.click(timeout=8000)
            time.sleep(2.0)
        nid = [x for x in pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))") if x and "audio" in x]
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

        def prep():
            if not pg.locator(
                    '[data-testid="audio-all-voices-listbox"]').count():
                vt = pg.locator('button[aria-label^="音色"]')
                if not vt.count():
                    return "音色钮不在"
                vt.first.click(timeout=8000)
                time.sleep(1.5)
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
            if not c:
                return "认不出性别芯片"
            if pg.locator('[aria-label="Clear 性别 filter"]').count():
                return None                      # 已经有值了
            pg.mouse.click(c[0], c[1])
            time.sleep(0.8)
            o = pg.get_by_text("男", exact=True).first
            if not o.count():
                return "选项「男」不在层里"
            o.click(timeout=8000)
            time.sleep(0.9)
            if not pg.locator('[aria-label="Clear 性别 filter"]').count():
                return "选完 Clear 没出现"
            return None

        # ── ① 手 replay 一遍组件里那段逻辑 ─────────────────────
        w = prep()
        if w:
            res["replay"] = {"verdict": f"前置态没成立：{w}"}
        else:
            rp = pg.evaluate(REPLAY_JS)
            res["replay"] = rp
            print("== ① 手工 replay 组件里那段逻辑 ==")
            if rp.get("no_clear"):
                print("  !! Clear 不存在")
            else:
                print(f"   closest 命中工具条 = {rp['tb_found']}  "
                      f"nid = {rp['nid']!r}")
                print(f"   画布节点 {rp['n_nodes']} 个：{rp.get('all_data_ids')}")
                print(f"   工具条 {rp['n_toolbars']} 个")
                print(f"   按 data-id 找到节点 = {rp.get('node_found')}  "
                      f"tabindex={rp.get('node_tabindex')!r}")
                print(f"   focus 前焦点 = {rp.get('before')!r}  "
                      f"focus 后 = {rp.get('after')!r}  "
                      f"成功={rp.get('focus_ok')}  "
                      f"是节点={rp.get('after_is_node')}")
                if rp.get("reason"):
                    print(f"   !! 原因：{rp['reason']}")

        # ── ③ focus 成功后**立刻**读（同步 + 300ms 后）─────────
        nid_attr = None
        if not w:
            nid_attr = pg.evaluate("""() => {
              const b = document.querySelector(
                '[aria-label="Clear 性别 filter"]');
              const tb = b && b.closest('.react-flow__node-toolbar');
              return tb ? tb.getAttribute('data-id') : null;
            }""")
            st = pg.evaluate(SETTLE_JS, nid_attr)
            res["settle_sync"] = st
            focus_now = pg.evaluate(FOCUS_JS)
            res["settle_focus_now"] = focus_now
            time.sleep(0.3)
            focus_later = pg.evaluate(FOCUS_JS)
            res["settle_focus_300ms"] = focus_later
            print(f"\n== ③ 手工 focus 后立刻读：{focus_now}")
            print(f"   300ms 后再读：{focus_later}")
            print(f"   同步结果：{st}")

        # ── ④ 真按 Esc，看焦点去哪 ────────────────────────────
        w2 = prep()
        if w2:
            res["esc"] = {"verdict": f"前置态没成立：{w2}"}
        else:
            pg.evaluate("""() => {
              const b = document.querySelector(
                '[aria-label="Clear 性别 filter"]');
              if (b) b.focus();
            }""")
            rec = {"focus_before": pg.evaluate(FOCUS_JS)}
            # 监听 Esc 之后 0ms / 50ms / 300ms / 900ms 的焦点
            seq = []
            pg.evaluate("""() => { window.__escProbe = [];
              const t0 = performance.now();
              const id = setInterval(() => {
                const a = document.activeElement;
                window.__escProbe.push({
                  dt: Math.round(performance.now() - t0),
                  tag: a === document.body ? 'BODY' : a.tagName,
                  aria: a.getAttribute
                    ? (a.getAttribute('aria-label') || '') : '',
                  is_node: !!(a.classList &&
                              a.classList.contains('react-flow__node'))});
                if (performance.now() - t0 > 1200) clearInterval(id);
              }, 40);
            }""")
            pg.keyboard.press("Escape")
            time.sleep(1.4)
            seq = pg.evaluate("() => window.__escProbe")
            rec["seq"] = seq
            rec["focus_after"] = pg.evaluate(FOCUS_JS)
            rec["voices_open"] = bool(
                pg.locator('[data-testid="audio-all-voices-listbox"]').count())
            rec["clear_still"] = bool(
                pg.locator('[aria-label="Clear 性别 filter"]').count())
            res["esc"] = rec
            print(f"\n== ④ 真按 Esc ==")
            print(f"   按之前焦点：{rec['focus_before']}")
            print(f"   焦点时间线：")
            for s in seq:
                if s["dt"] % 200 < 60 or s["dt"] < 130:
                    print(f"     +{s['dt']:>5}ms {s['tag']}/{s['aria']!r} "
                          f"节点={s['is_node']}")
            print(f"   最终焦点：{rec['focus_after']}")
            print(f"   面板还开={rec['voices_open']}  "
                  f"Clear 还在={rec['clear_still']}")

        res["page_errors"] = errors[:8]
        if errors:
            print(f"\n== 页面报错 {len(errors)} 条（前 8）：")
            for e in errors[:8]:
                print(f"   {e[:150]}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
