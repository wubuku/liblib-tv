#!/usr/bin/env python3
"""batch 851b 源站探针：**音频生成面板**那 5 个下拉的键盘行为。

§68 的范围限制写「音频那 5 个下拉仍记 `kb_not_sampled`，下一批照 850 取」。
但那句话里还藏着一个**没验证过的前提**：`kb_not_sampled` 里那 5 条写的是
「没取过样」，而 §68 自己也没说清**为什么取不到**。851a 侦察给出了答案：
**源站这一版画布能插出音频节点**（点左栏 `button[aria-label="音频"]` →
新增 `rf__node-node_ay7f1jn45r`「音频 1」），选中后**真的有**下拉触发器：

    创作类型: 音频生成        80×32   → audio-gen-type-listbox
    选择模型: SeedAudio 1.0   135×32   → audio-voice-model-listbox
    音频生成: 全能配音        80×32   → audio-gen-mode-listbox
    音色: 音色库              68×32   → audio-all-voices-listbox

所以这 5 层**不是 BLOCKED_BY_FIXTURE**，是真能取样的。剩 2 个（音乐分支的
模型/时长）要先点「创作类型」切到**音乐生成**才出现。

量四项，口径与 850 **逐字同款**（判据从 `jimeng_kb_probe_lib` 共享库里来 ——
分档只按源站基线表走，两批口径不一致的话表就没法比）：
  ① 开层是否接管焦点（blur 之前读）
  ② 层内 Tab 会不会逃出（**并查层还在不在** —— 源站这些下拉失焦即关）
  ③ 方向键动不动（层内起手；refocus 失败就记**没测到**，不下结论）
  ④ Esc 关层后焦点回哪

⚠️ 计费边界：只点下拉触发器。付费护栏**按等值**拦（850 第一版
`startswith("生成")` 把「生成模式」这种**控件描述**也拦了，等于把
「测不到」印成「不许测」—— 护栏太宽也是缺陷）。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jimeng_kb_probe_lib import (  # noqa: E402
    ALIVE_JS, FOCUS_JS, SNAP_JS, UNMARK_JS, ensure_open, mark_layer,
)

MAX_TABS = 12
MAX_KEYS = 4

# 付费护栏：**等值**才拦。源站的付费按钮文案就是光秃秃两个字（「生成」/
# 「发送」），带 `: …` 后缀的一律是控件描述。
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即支付", "购买会员", "充值")


def guard(label: str) -> bool:
    t = (label or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT:
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    if any(t.startswith(b) for b in BILLED_PREFIX):
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    return False


def diff_layers(before, after):
    keys = {(b["x"], b["y"], b["w"], b["h"]) for b in before}
    return [a for a in after if (a["x"], a["y"], a["w"], a["h"]) not in keys]


def select_point(tid: str):
    return page.evaluate("""(tid) => {
      const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const CTRL = 'button,[role=button],a,input,select,textarea';
      for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                              [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
        const x = r.x + r.width*fx, y = r.y + r.height*fy;
        const t = document.elementFromPoint(x, y);
        if (t && n.contains(t) && !t.closest(CTRL))
          return [Math.round(x), Math.round(y)];
      }
      return null;
    }""", tid)


def reselect(tid: str) -> bool:
    pt = select_point(tid)
    if not pt:
        print("   !! 选不中节点 ⇒ 前置态没成立")
        return False
    page.mouse.click(pt[0], pt[1])
    page.wait_for_timeout(1300)
    ok = page.evaluate(
        "() => document.querySelectorAll('.react-flow__node.selected').length") == 1
    print(f"   （重新选中 {tid}: {ok}）")
    return ok


def probe(name, trig_aria, node_tid):
    print("=" * 74)
    print(f"【{name}】触发器 aria-label^={trig_aria!r}")
    rec = {"name": name, "trigger_aria": trig_aria}

    cands = page.evaluate("""(aria) => {
      const out = [];
      for (const l of document.querySelectorAll(`button[aria-label^="${aria}"]`)) {
        const s = getComputedStyle(l);
        const r = l.getBoundingClientRect();
        const x = r.x + r.width/2, y = r.y + r.height/2;
        const st = document.elementsFromPoint(x, y) || [];
        const top = st[0] || null;
        out.push({al: l.getAttribute('aria-label') || '',
                  visible: s.display !== 'none' && s.visibility !== 'hidden',
                  rect: [Math.round(r.x), Math.round(r.y),
                         Math.round(r.width), Math.round(r.height)],
                  in_view: r.width > 0 && r.height > 0 && x >= 0 && y >= 0
                        && x <= innerWidth && y <= innerHeight,
                  self_is_top: !!(top && (top === l || l.contains(top)))});
      }
      return out;
    }""", trig_aria)
    rec["candidates"] = cands
    print(f"   同名触发器 {len(cands)} 个")
    for i, c in enumerate(cands):
        print(f"     [{i}] visible={c['visible']} in_view={c['in_view']} "
              f"self_is_top={c['self_is_top']} rect={c['rect']} al={c['al'][:48]!r}")
    usable = [c for c in cands if c["visible"] and c["in_view"] and c["self_is_top"]]
    if not usable:
        rec["why"] = "没有可点的同名触发器（前置态没成立）"
        print("   ⚠ 没有可点的同名触发器 ⇒ **前置态没成立**，不硬点")
        return rec
    pt = usable[0]["rect"]
    if guard(usable[0]["al"]):
        rec["why"] = "付费护栏拦下"
        return rec

    before = page.evaluate(SNAP_JS)
    page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)
    page.wait_for_timeout(1000)

    new = diff_layers(before, page.evaluate(SNAP_JS))
    if not new:
        rec["why"] = "点了但没有新增层"
        print("   ⚠ 没有新增候选层 ⇒ **前置态没成立**")
        return rec
    layer = sorted(new, key=lambda x: -(x["w"] * x["h"]))[0]
    rec["layer"] = layer
    print(f"   层: {layer['w']}×{layer['h']} @[{layer['x']},{layer['y']}] "
          f"z={layer['z']} role={layer['role']!r} tid={layer['tid']!r}")

    marked = mark_layer(page, layer)
    rec["marked"] = marked
    if not marked.get("ok"):
        rec["why"] = "按 role=listbox/dialog 认不出层"
        print("   ⚠ 按 role 认不出层 ⇒ 前置态没成立")
        return rec
    lay = marked["rect"] + [layer["tid"]]

    # ① 开层焦点（blur 之前）
    at_open = page.evaluate(FOCUS_JS, lay)
    rec["focus_at_open"] = at_open
    print(f"   ① 开层焦点: {at_open.get('who')!r} al={at_open.get('al')!r} "
          f"in_layer={at_open.get('in_layer')}")

    # ② 冷启动只作参考（① 若接管焦点，这条用户路径就不存在）
    page.evaluate("() => { const a = document.activeElement;"
                  " if (a && a.blur) a.blur(); }")
    enter_at = None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        s = page.evaluate(FOCUS_JS, lay)
        if s.get("in_layer"):
            enter_at = i
            break
    rec["cold_enter_at_reference_only"] = enter_at
    print(f"   ② 参考（非判据）冷启动 Tab 第 {enter_at} 次进层")

    # 重开 → ② 真实口径。**不用「点两下」**：冷启动那 12 次 Tab 已经把层
    # 关掉了（失焦即关），盲点两下等于「开→关」，越弄越关。
    marked2 = ensure_open(page, layer,
                         (pt[0] + pt[2] // 2, pt[1] + pt[3] // 2),
                         note="重开")
    rec["remarked"] = marked2
    if not marked2.get("ok"):
        rec["why"] = "重开后认不出层"
        print("   ⚠ 重开后认不出层 ⇒ 前置态没成立")
        return rec
    lay2 = marked2["rect"] + [layer["tid"]]
    re_open = page.evaluate(FOCUS_JS, lay2)
    rec["focus_at_reopen"] = re_open
    print(f"   ② 重开后焦点: {re_open.get('who')!r} in_layer={re_open.get('in_layer')}")

    escaped_at, landed, closed_at = None, None, None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        s = page.evaluate(FOCUS_JS, lay2)
        if not page.evaluate(ALIVE_JS, lay2)["alive"]:
            closed_at = i
            break
        if not s.get("in_layer"):
            escaped_at, landed = i, s.get("who")
            break
    if closed_at is not None:
        rec["escape"] = {"trapped": False, "layer_closed_at": closed_at,
                         "ambiguous": True,
                         "why": f"第 {closed_at} 次 Tab 时层自己关了 ⇒ 测不了"}
        print(f"   ② 第 {closed_at} 次 Tab 时**层自己关了** ⇒ Tab 困不困**测不了**")
    elif escaped_at is None:
        rec["escape"] = {"trapped": True}
        print("   ② **困住**（12 次全在层内，层也一直在）")
    else:
        rec["escape"] = {"trapped": False, "escaped_at": escaped_at, "landed": landed}
        print(f"   ② 第 {escaped_at} 次逃出（层还在），落在 {landed!r}")

    # ③ 方向键： refocus 不成功就**记没测到**，绝不报结论
    ok_rf = page.evaluate("""() => {
      const L = document.querySelector('[data-probe850]');
      if (!L) return {ok: false, why: '标记不见了（层被关掉了？）'};
      const FOC = 'button:not([disabled]),[tabindex]:not([tabindex="-1"]),'
                + '[role=option],[role=menuitem],input:not([disabled])';
      const f = L.querySelector(FOC);
      if (!f) return {ok: false, why: '层里没有可聚焦项'};
      f.focus();
      return {ok: !!L.contains(document.activeElement)};
    }""")
    if not ok_rf.get("ok"):
        rec["arrow_down"] = {"measured": False,
                             "why": f"refocus 失败（{ok_rf.get('why')}）⇒ 没测到"}
        print(f"   ③ refocus 失败：{ok_rf.get('why')} ⇒ **本项没测到**")
    else:
        lay3 = page.evaluate("""() => {
          const L = document.querySelector('[data-probe850]');
          const r = L.getBoundingClientRect();
          return [Math.round(r.x), Math.round(r.y),
                  Math.round(r.width), Math.round(r.height)];
        }""")
        seq = []
        for _ in range(MAX_KEYS):
            page.keyboard.press("ArrowDown")
            s = page.evaluate(FOCUS_JS, lay3)
            seq.append({"who": s.get("who"), "in": s.get("in_layer")})
        uniq = len({x["who"] for x in seq})
        rec["arrow_down"] = {"measured": True, "moved": uniq > 1, "seq": seq}
        print(f"   ③ ArrowDown ×{MAX_KEYS}（层内起手）: moved={uniq > 1} "
              f"轨迹={[x['who'] for x in seq]}")

    # ④ Esc
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    after_esc = page.evaluate(FOCUS_JS, lay2)
    page.evaluate(UNMARK_JS)
    rec["esc"] = {"who": after_esc.get("who"), "al": after_esc.get("al"),
                  "in_layer": after_esc.get("in_layer")}
    print(f"   ④ Esc 后焦点: {after_esc.get('who')!r} al={after_esc.get('al')!r} "
          f"in_layer={after_esc.get('in_layer')}")
    return rec


# ══ 跑起来 ════════════════════════════════════════════════════════════
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
# 与 850 同口径：面板挂在节点下方，950 高的视口**点不到**触发器
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
print("== 视口 ==", page.evaluate("() => [innerWidth, innerHeight]"))

NODE_TIDS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || '')"""

results = {}

# ── 插一个音频节点（按**集合差分**认新节点，不按序号 —— 843 的教训）─────
before = set(page.evaluate(NODE_TIDS))
page.locator('button[aria-label="音频"]').first.click(timeout=10000)
page.wait_for_timeout(2500)
new_nodes = [t for t in page.evaluate(NODE_TIDS) if t not in before]
print("== 新增节点 ==", new_nodes)
if not new_nodes:
    raise SystemExit("!! 插不出音频节点（前置态没成立）")
aud = new_nodes[0]
if not reselect(aud):
    raise SystemExit("!! 选不中音频节点（前置态没成立）")

# ── 音频生成分支：4 个 ─────────────────────────────────────────────────
for nm, aria in [("音色模型", "选择模型"),
                 ("音频生成模式", "音频生成"),
                 ("全音色", "音色")]:
    if not reselect(aud):
        results[nm] = {"name": nm, "why": "重新选中失败"}
        continue
    results[nm] = probe(nm, aria, aud)

# ── 音乐生成分支：先切「创作类型」，再量 2 个 ───────────────────────────
print("\n== 切到「音乐生成」分支 ==")
if reselect(aud):
    t = page.locator('button[aria-label^="创作类型"]')
    if t.count():
        t.first.click(timeout=8000)
        page.wait_for_timeout(900)
        opt = page.locator('[role=option]:text-is("音乐生成")')
        if opt.count():
            opt.first.click()
            page.wait_for_timeout(1200)
            print("   已切到音乐生成")
        else:
            print("   ⚠ 找不到「音乐生成」选项")
    else:
        print("   ⚠ 找不到「创作类型」触发器")

for nm, aria in [("音乐模型", "选择模型"), ("音乐时长", "选择时长")]:
    if not reselect(aud):
        results[nm] = {"name": nm, "why": "重新选中失败"}
        continue
    results[nm] = probe(nm, aria, aud)

with open("/tmp/b851b-source-audiopanel.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n== 汇总 ==")
for nm, r in results.items():
    if r.get("why"):
        print(f"  {nm:<14} ⚠ {r['why']}")
        continue
    fo = r.get("focus_at_open") or {}
    esc = r.get("escape") or {}
    arr = r.get("arrow_down") or {}
    print(f"  {nm:<14} 层={r['layer']['w']}×{r['layer']['h']} "
          f"role={r['layer']['role']!r}｜①接管={fo.get('in_layer')} "
          f"｜②{'困' if esc.get('trapped') else ('逃@'+str(esc.get('escaped_at')) if esc.get('escaped_at') else ('层自关@'+str(esc.get('layer_closed_at')) if esc.get('layer_closed_at') else '?'))} "
          f"｜③{('动' if arr.get('moved') else '不动') if arr.get('measured') else '没测到'} "
          f"｜④Esc后焦点={((r.get('esc') or {}).get('al') or (r.get('esc') or {}).get('who'))!r}")
print("\n明细 /tmp/b851b-source-audiopanel.json")
