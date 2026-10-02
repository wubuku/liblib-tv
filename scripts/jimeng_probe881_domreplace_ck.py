#!/usr/bin/env python3
"""batch 881（复刻侧）：**决定性**测量 —— Esc 前后音频节点 DOM 是不是被替换了。

## 已经排除掉的（别再重查）

探针 880 四项实测：

- ① 手工 replay 组件里那段逻辑：`closest` 命中工具条 ✓、nid 取到 ✓、
  按 `data-id` 找到节点 ✓、`focus()` **成功** ✓
- ③ 手工 focus 后**立刻**和 **300ms 后**，焦点都**稳在节点上** ✓
- ④ 但**真按 Esc**，从 +56ms 起一路 BODY 到 +1202ms
- 且清除**确实生效**（`Clear 还在=False`）⇒ 那个 `onKeyDown` **执行了**

⇒ 「focus 不可行」「焦点留不住」「代码没编译」全部排除。剩下的唯一解释：
**focus 成功之后、同一帧内**有什么东西把焦点又拿走了，或者**节点 DOM 被替换**
（DOM 一换，挂在上面的焦点就没了 ⇒ 浏览器落 body）。

## 这一跑就量这一个

在节点上打一个**标记属性** + 存一条全局引用，然后按 Esc，之后问三个问题：

1. **标记还在吗** —— `data-esc-probe` 还在 ⇒ DOM **没被替换**
2. **还是同一个元素吗** —— `document.querySelector(...) === window.__escNode`
3. **焦点有没有短暂落在节点上过** —— 这次用
   `MutationObserver` 监听 `blur`/`focusout`，**事件流**而不是 40ms 轮询
   （轮询的第一次采样就已经是 BODY 了，中间发生了什么全丢了）

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe881_domreplace_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b881-ck-domreplace.json")

# 打标记 + 存引用 + 装焦点事件监听（**改的是复刻的 DOM，不改产品代码**）
ARM_JS = """() => {
  const b = document.querySelector('[aria-label="Clear 性别 filter"]');
  const tb = b && b.closest('.react-flow__node-toolbar');
  const nid = tb ? tb.getAttribute('data-id') : null;
  if (!nid) return {no_toolbar: true};
  const all = [...document.querySelectorAll('.react-flow__node')];
  const el = all.find(n => n.getAttribute('data-id') === nid);
  if (!el) return {no_node: true};
  el.setAttribute('data-esc-probe', 'MARK');
  window.__escNode = el;
  window.__escNodeId = nid;
  window.__log = [];
  const t0 = performance.now();
  const push = (kind, e) => {
    const t = e && e.target;
    window.__log.push({dt: Math.round(performance.now() - t0), kind,
      tag: t ? t.tagName : '?',
      aria: t && t.getAttribute ? (t.getAttribute('aria-label') || '') : '',
      is_probe: t === el,
      is_node: !!(t && t.classList &&
                  t.classList.contains('react-flow__node'))});
  };
  document.addEventListener('focusin', (e) => push('focusin', e), true);
  document.addEventListener('focusout', (e) => push('focusout', e), true);
  document.addEventListener('blur', (e) => push('blur', e), true);
  // DOM 被替换 ⇒ MutationObserver 会报 childList 变化
  window.__mo = new MutationObserver((recs) => {
    for (const r of recs) {
      const gone = [...r.removedNodes].some(
        (n) => n === el || (n.contains && n.contains(el)));
      const added = [...r.addedNodes].some(
        (n) => n === el || (n.getAttribute &&
            n.getAttribute('data-id') === nid));
      if (gone || added) {
        window.__log.push({dt: Math.round(performance.now() - t0),
          kind: gone ? 'node_REMOVED' : 'node_ADDED',
          tag: 'DIV', aria: '', is_probe: true, is_node: true});
      }
    }
  });
  window.__mo.observe(document.body, {childList: true, subtree: true});
  // 把焦点放到 Clear 上（模拟 Esc 的起点）
  b.focus();
  return {armed: true, nid,
          focus_now: document.activeElement === b,
          focus_aria: document.activeElement.getAttribute('aria-label') || ''};
}"""

# Esc 之后的三个问题
CHECK_JS = """() => {
  const el = window.__escNode;
  const nid = window.__escNodeId;
  const now = [...document.querySelectorAll('.react-flow__node')]
    .find(n => n.getAttribute('data-id') === nid);
  const a = document.activeElement;
  return {
    probe_attr_still_there: el ? el.getAttribute('data-esc-probe') : null,
    /* DOM 被替换 ⇒ 旧元素 isConnected=false；没被替换 ⇒ 仍 true */
    old_elem_connected: el ? el.isConnected : null,
    old_elem_is_body_child: el ? el.parentElement === document.body : null,
    same_element_now: el ? (now === el) : null,
    new_elem_found: !!now,
    new_elem_has_probe: now ? now.getAttribute('data-esc-probe') : null,
    focus_tag: a === document.body ? 'BODY' : a.tagName,
    focus_aria: a.getAttribute ? (a.getAttribute('aria-label') || '') : '',
    focus_is_new_node: now ? a === now : false,
    log: window.__log,
  };
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
                return None
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

        w = prep()
        if w:
            res["verdict"] = f"前置态没成立：{w}"
            print("!! " + res["verdict"])
        else:
            arm = pg.evaluate(ARM_JS)
            res["arm"] = arm
            print(f"== 布防：{arm}")
            pg.keyboard.press("Escape")
            time.sleep(1.2)
            ck = pg.evaluate(CHECK_JS)
            res["check"] = ck
            print("\n== Esc 之后三个问题：")
            print(f"   ① 标记还在吗        {ck['probe_attr_still_there']!r}")
            print(f"   ② 旧元素 isConnected={ck['old_elem_connected']}  "
                  f"是同一个={ck['same_element_now']}  "
                  f"新元素带标记={ck['new_elem_has_probe']!r}")
            print(f"   ③ 最终焦点 {ck['focus_tag']}/{ck['focus_aria']!r}  "
                  f"在新节点上={ck['focus_is_new_node']}")
            print(f"\n== 焦点事件流（{len(ck['log'])} 条）：")
            for e in ck["log"][:24]:
                mk = ("  ←就是它" if e.get("is_probe") else
                      ("  [节点]" if e.get("is_node") else ""))
                print(f"   +{e['dt']:>5}ms {e['kind']:12s} "
                      f"{e['tag']}/{e['aria'][:20]!r}{mk}")
            replaced = (ck["old_elem_connected"] is False
                        or ck["same_element_now"] is False)
            res["dom_replaced"] = replaced
            landed = ck["focus_is_new_node"]
            res["focus_landed_on_node"] = landed
            # ⚠️⚠️ 判据**跟着事实一起改过**。第一版只看「DOM 有没有被替换」，
            #   于是修好之后它仍然打出「机制仍未查清」——
            #   **判据没跟上事实**，跟 876c 那个「把够不着写成没有」同族，
            #   只是方向相反（这次是**修好了还说没查清**）。
            #   现在改成两条**互斥**的判据：
            #     · 焦点最终落在节点上 ⇒ 这一条**对齐了**（哪怕抢焦点者没查明）
            #     · 没落上去 ⇒ 才需要继续查机制
            #   抢焦点那个动作的**身份**仍然**未查明**（见 why_still_unknown）。
            res["why_still_unknown"] = (
                "事件流里 +56ms 那个 blur 来自**哪个 handler 仍没查明**。"
                "现修法是在它**之后**补落（120ms setTimeout），属于**绕过**"
                "而不是**根修** —— 那个动作若改了时间或顺序，这里就失效。"
                "标为**未验证**，不许写成「已解决」。")
            if landed:
                res["verdict"] = (
                    "对齐了：焦点最终落在**该音频节点本体**（与源站同）。"
                    "但机制只查到「+56ms 有个延迟动作抢焦点」这一步，"
                    "**那个动作的身份未查明**；现修法是**补落**，不是根修。")
            elif replaced:
                res["verdict"] = (
                    "机制查清：Esc 之后**音频节点 DOM 被替换了** ⇒ "
                    "挂在上面的焦点随元素一起消失，浏览器把焦点落 body。"
                    "所以 `nodeEl.focus()` 同步执行**是对的、也不够** —— "
                    "必须在**重渲染之后**再落一次。")
            else:
                res["verdict"] = (
                    "**未对齐**：节点 DOM 没被替换，焦点却仍落 body。"
                    "说明有别的 handler 在同帧内把焦点拿走了 —— "
                    "**不许**据此改判据（§77），要先把那个 handler 找出来。")
            print(f"\n== {res['verdict']}")
            print(f"\n== ⚠️ 仍未查明：{res['why_still_unknown']}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
