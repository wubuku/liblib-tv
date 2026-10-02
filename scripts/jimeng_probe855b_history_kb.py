#!/usr/bin/env python3
"""batch 855b 源站取样：**生成历史**层的四项键盘行为。

855a 侦察推翻了 §70/§71 一直记着的那条前提。原文写「点第 2 个
`canvas-panel-launcher` 开出的是『积分明细』⇒ 前置态没成立」——
但那是**按位置猜**的：源站顶栏一排 launcher 里「位置」和「功能」没有
对应关系，847 猜错了。855a **按 aria-label 找名字**：
`button[aria-label="生成历史"]` 就在那儿（1175,16 28×28），
点开是 **320×211 `role=dialog` `canvas-feature-panel`**，
内容写着「生成历史 / **暂无生成历史**」。

⇒ 这一层**不是 `BLOCKED_BY_FIXTURE`，也不是「前置态没成立」**，
是**探针按位置猜名字猜错了**。量四项，口径走共享库 `measure_kb()`。

⚠️ 注意内容是「**暂无生成历史**」—— 这一版画布**没有生成过任何东西**，
所以层里**没有条目**。那 ③ 方向键**必然**交出「没测到」（层里没有可聚焦项），
这是**内容决定的**，不是判据坏了。记 `None` 并写清 why。

⚠️ 计费边界：只点顶栏「生成历史」这一个按钮。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jimeng_kb_probe_lib import (  # noqa: E402
    SNAP_JS, UNMARK_JS, mark_layer, measure_kb,
)

MAX_TABS = 12
MAX_KEYS = 4
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")


def guard(label):
    t = (label or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT:
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    return False


def diff_layers(before, after):
    keys = {(b["x"], b["y"], b["w"], b["h"]) for b in before}
    return [a for a in after if (a["x"], a["y"], a["w"], a["h"]) not in keys]


results = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
print(f"== URL {page.url[:60]}… ==")

trig = page.locator('button[aria-label="生成历史"]')
print(f"== 「生成历史」按钮 {trig.count()} 个 ==")
rec = {"name": "生成历史", "trigger_aria": "生成历史"}
if not trig.count():
    rec["why"] = "这一版画布**没有**「生成历史」按钮"
    print("   ⚠ 找不到「生成历史」按钮 ⇒ BLOCKED_BY_FIXTURE")
    results["生成历史"] = rec
else:
    cands = page.evaluate("""(aria) => {
      const out = [];
      for (const l of document.querySelectorAll(`button[aria-label="${aria}"]`)) {
        const s = getComputedStyle(l);
        const r = l.getBoundingClientRect();
        const x = r.x + r.width/2, y = r.y + r.height/2;
        const st = document.elementsFromPoint(x, y) || [];
        const top = st[0] || null;
        out.push({al: l.getAttribute('aria-label') || '',
                  visible: s.display!=='none' && s.visibility!=='hidden',
                  rect: [Math.round(r.x), Math.round(r.y),
                         Math.round(r.width), Math.round(r.height)],
                  in_view: r.width>0 && r.height>0 && x>=0 && y>=0
                        && x<=innerWidth && y<=innerHeight,
                  self_is_top: !!(top && (top===l || l.contains(top)))});
      }
      return out;
    }""", "生成历史")
    usable = [c for c in cands if c["visible"] and c["in_view"] and c["self_is_top"]]
    rec["candidates"] = cands
    print(f"   可点 {len(usable)} 个")
    if not usable or guard(usable[0]["al"]):
        rec["why"] = "没有可点的按钮 / 被护栏拦下"
        results["生成历史"] = rec
    else:
        pt = usable[0]["rect"]
        cx, cy = pt[0] + pt[2] // 2, pt[1] + pt[3] // 2
        before = page.evaluate(SNAP_JS)
        page.mouse.click(cx, cy)
        page.wait_for_timeout(1200)
        new = diff_layers(before, page.evaluate(SNAP_JS))
        print(f"   新增候选层 {len(new)} 个")
        if not new:
            rec["why"] = "点了但没有新增层"
        else:
            layer = sorted(new, key=lambda z: -(z["w"] * z["h"]))[0]
            rec["layer"] = layer
            print(f"   层: {layer['w']}×{layer['h']} role={layer['role']!r} "
                  f"tid={layer['tid']!r}")
            marked = mark_layer(page, layer)
            rec["marked"] = marked
            if not marked.get("ok"):
                rec["why"] = "按 role=listbox/dialog 认不出层"
            else:
                # 层里到底有什么（决定 ③ 能不能测）
                inside = page.evaluate("""() => {
                  const L = document.querySelector('[data-probe850]');
                  if (!L) return null;
                  return [...L.querySelectorAll('h1,h2,h3,div,span,p,li,button')]
                    .map(e => (e.innerText||'').trim())
                    .filter(t => t && t.length <= 24)
                    .slice(0, 12);
                }""")
                rec["inside"] = inside
                print(f"   层内文本: {inside}")
                rec.update(measure_kb(page, marked, (cx, cy), max_tabs=MAX_TABS,
                                      max_keys=MAX_KEYS))
        results["生成历史"] = rec

with open("/tmp/b855b-source-history.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n== 汇总 ==")
r = results["生成历史"]
if r.get("why"):
    print(f"  生成历史 ⚠ {r['why']}")
else:
    fo = r.get("focus_at_open") or {}
    esc = r.get("escape") or {}
    arr = r.get("arrow_down") or {}
    e = r.get("esc") or {}
    # ⚠️ 853b 同一个坑第二次：探针自己**打印代码**崩了会带走已量好的结果
    #    （JSON 写了，退出码 1，没人看汇总）。取值一律 `.get` 兜底。
    lay = (r.get("layer") or {}).get("rect")
    tidv = (r.get("layer") or {}).get("tid")
    print(f"  生成历史 层={lay} tid={tidv!r} "
          f"｜①接管={fo.get('in_layer')} "
          f"｜②{'困' if esc.get('trapped') else ('逃@'+str(esc.get('escaped_at')) if esc.get('escaped_at') else ('自关@'+str(esc.get('layer_closed_at')) if esc.get('layer_closed_at') else '?'))} "
          f"｜③{('动' if arr.get('moved') else '不动') if arr.get('measured') else '没测到'}"
          + (f" (why={arr.get('why')})" if arr.get("why") else "") +
          f" ｜④Esc后={e.get('who')!r}")
print("\n== 已写 /tmp/b855b-source-history.json ==")
