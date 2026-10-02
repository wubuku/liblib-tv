#!/usr/bin/env python3
"""batch 882（复刻侧）：找出那个在 **+46ms** 把焦点抢走的 handler。

## 为什么找它

881 查到的机制链停在半路：

```
+  6ms  focusin  DIV ← 节点   ← 组件里同步 focus()，**成功**
+ 46ms  blur     DIV ← 节点   ← **被抢走**
```

而且 881 同时排除了「节点 DOM 被替换」。所以抢焦点的是**某个代码在跑**，
不是 DOM 换了。组件里那个 `onKeyDown` 只做了三件事：落焦点、两次
`setState`。它**不可能**在 46ms 后自己把自己的焦点抢走。

**而这是关键**：组件里**还有别的 Esc 响应者**。Esc 会**继续冒泡**到祖先，
祖先上的 handler 也会跑。谁在 46ms 后动了焦点，只有量才知道。

## 三条查法（互相独立，交叉印证）

① **给焦点变化打时间戳**：`focusin`/`focusout` 全部记录，看 46ms 那个
   `blur` 的 `event.target` 是谁、`relatedTarget` 是 null 还是别的元素
   （`relatedTarget` 为 null 通常意味着焦点被**显式移走**、或元素被移除）
② **劫持 `HTMLElement.prototype.focus` / `HTMLElement.prototype.blur`**：
   把每次调用的**调用栈**抓下来 —— 这是找「哪个 handler」最直接的证据
③ **对比「按 Esc」与「不按 Esc」**：同前置态下，不按 Esc 时焦点在 46ms
   会不会自己掉？（若不会 ⇒ 确实是 Esc 触发的某个 handler）

⚠️ ② 是**诊断动作**（劫持 prototype），必须在**测完之后恢复**，而且
**只在这一页里**。本探针每段测完自己 reload，不留痕。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe882_who stealsfocus_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b882-ck-whosteals.json")

# 劫持 focus/blur + 记录调用栈 + 记录焦点事件（含 relatedTarget）
HOOK_JS = """() => {
  window.__focusLog = [];
  window.__blurs = [];
  const t0 = performance.now();
  const dt = () => Math.round(performance.now() - t0);

  // ① 焦点事件（带 relatedTarget —— 区分「显式移走」与「元素被移除」）
  for (const k of ['focusin', 'focusout']) {
    document.addEventListener(k, (e) => {
      window.__focusLog.push({dt: dt(), kind: k,
        tag: e.target ? e.target.tagName : '?',
        cls: e.target ? ((e.target.className || '') + '').slice(0, 60) : '',
        aria: e.target && e.target.getAttribute
          ? (e.target.getAttribute('aria-label') || '') : '',
        related: e.relatedTarget
          ? (e.relatedTarget.tagName + '/'
             + ((e.relatedTarget.getAttribute
                 && e.relatedTarget.getAttribute('aria-label')) || ''))
          : null,
        related_connected: e.relatedTarget
          ? e.relatedTarget.isConnected : null});
    }, true);
  }

  // ② 劫持 focus() / blur()，抓调用栈
  const of = HTMLElement.prototype.focus;
  const ob = HTMLElement.prototype.blur;
  HTMLElement.prototype.focus = function (...a) {
    const st = (new Error()).stack || '';
    const frames = st.split('\\n').slice(1, 9).map(x =>
      x.trim().replace(/^at\\s+/, '').slice(0, 130));
    window.__focusLog.push({dt: dt(), kind: 'focus() call',
      tag: this.tagName,
      cls: ((this.className || '') + '').slice(0, 60),
      aria: this.getAttribute ? (this.getAttribute('aria-label') || '') : '',
      stack: frames});
    return of.apply(this, a);
  };
  HTMLElement.prototype.blur = function (...a) {
    const st = (new Error()).stack || '';
    const frames = st.split('\\n').slice(1, 9).map(x =>
      x.trim().replace(/^at\\s+/, '').slice(0, 130));
    window.__blurs.push({dt: dt(), tag: this.tagName,
      cls: ((this.className || '') + '').slice(0, 60),
      aria: this.getAttribute ? (this.getAttribute('aria-label') || '') : '',
      stack: frames});
    return ob.apply(this, a);
  };
  return {hooked: true};
}"""

READ_JS = """() => {
  const a = document.activeElement;
  return {focus_log: window.__focusLog || [],
          blur_calls: window.__blurs || [],
          final_focus: a === document.body ? 'BODY' : a.tagName,
          final_aria: a.getAttribute ? (a.getAttribute('aria-label') || '') : ''};
}"""

UNHOOK_JS = """() => { location.reload(); return true; }"""


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1680, "height": 1050})
        pg = ctx.new_page()

        def prep_and_run(press_esc: bool, tag: str):
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3.5)
            t = pg.locator('button[aria-label="音频"]')
            if t.count():
                t.first.click(timeout=8000)
                time.sleep(2.0)
            nid = [x for x in pg.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node')]"
                ".map(n => n.getAttribute('data-testid'))")
                if x and "audio" in x]
            if not nid:
                return {"verdict": "插不进音频节点"}
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
            if not pg.locator(
                    '[data-testid="audio-all-voices-listbox"]').count():
                vt = pg.locator('button[aria-label^="音色"]')
                if vt.count():
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
                return {"verdict": "认不出性别芯片"}
            if not pg.locator('[aria-label="Clear 性别 filter"]').count():
                pg.mouse.click(c[0], c[1])
                time.sleep(0.8)
                o = pg.get_by_text("男", exact=True).first
                if o.count():
                    o.click(timeout=8000)
                    time.sleep(0.9)
            if not pg.locator('[aria-label="Clear 性别 filter"]').count():
                return {"verdict": "Clear 没出现"}

            pg.evaluate(HOOK_JS)
            pg.evaluate("""() => {
              const b = document.querySelector(
                '[aria-label="Clear 性别 filter"]');
              if (b) b.focus();
            }""")
            time.sleep(0.3)
            if press_esc:
                pg.keyboard.press("Escape")
            time.sleep(1.2)
            out = pg.evaluate(READ_JS)
            # 诊断动作**必须**恢复 —— 重新加载，把 prototype 还回去
            pg.evaluate(UNHOOK_JS)
            time.sleep(1.0)
            out["tag"] = tag
            return out

        res["with_esc"] = prep_and_run(True, "按了 Esc")
        r1 = res["with_esc"]
        print("== ① 按 Esc ==")
        if r1.get("verdict"):
            print("  !! " + r1["verdict"])
        else:
            print(f"   最终焦点 {r1['final_focus']}/{r1['final_aria']!r}")
            print(f"   焦点事件 {len(r1['focus_log'])} 条：")
            for e in r1["focus_log"][:20]:
                st = ""
                if e.get("stack"):
                    st = "  ← " + " | ".join(e["stack"][:3])
                print(f"     +{e['dt']:>4}ms {e['kind']:12s} "
                      f"{e['tag']}/{e['aria'][:18]!r} "
                      f"related={e.get('related')!r}{st}")
            if r1["blur_calls"]:
                print(f"   显式 blur() 调用 {len(r1['blur_calls'])} 次：")
                for e in r1["blur_calls"][:8]:
                    print(f"     +{e['dt']:>4}ms {e['tag']}/{e['aria'][:18]!r}")
                    for f in e["stack"][:5]:
                        print(f"        {f}")
            else:
                print("   **没有任何显式 blur() 调用** ⇒ "
                      "焦点不是被代码 `blur()` 走的")

        res["no_esc"] = prep_and_run(False, "没按 Esc（对照）")
        r2 = res["no_esc"]
        print(f"\n== ② 对照组（不按 Esc）：最终焦点 "
              f"{r2.get('final_focus')}/{r2.get('final_aria')!r}")
        print(f"   焦点事件 {len(r2.get('focus_log', []))} 条（应只有布防那次）")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
