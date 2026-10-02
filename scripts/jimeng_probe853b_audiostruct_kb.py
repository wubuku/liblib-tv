#!/usr/bin/env python3
"""batch 853b 源站取样：把 §70 结尾那 3 层**真正取到样**（键盘四项）。

853a 侦察（登录态，视口 1512×1200）把 §69/§70 记的两种「测不到」各自拆开了，
这一批照着拆出来的真相去**正式取样**：

  A. **音乐模型 / 音乐时长** —— 之前判「前置态没成立」，理由是
     `[role=option]:text-is("音乐生成")` 计数 0。853a 查明：那个「计数 0」是
     **判据的错**，不是元素不存在 —— 「音乐生成」确实在，但它是一个
     **`<SPAN role="">`**（class `block min-w-canvas-zero truncate`），
     **根本不是 role=option**。⇒ 找它**不能按 role**，要按**文本**找到那个
     SPAN，再往上找**可点的祖先**去点它。切过去之后，音乐分支的
     `选择模型` / `选择时长` 两个触发器才会出现。

  B. **音色库层** —— 之前判「判据量错对象」，理由是矩形差分抓到 648×1932 整页
     容器。853a 查明它真正的身份：是一个**就地展开**的大面板，音色条目带稳定
     语义 class `min-w-canvas-audio-voice-shrinkable`。⇒ 改用
     `mark_by_class()`（取条目最近公共祖先）认层。**这不是放宽判据**：从「猜一个
     矩形」换成「按实测稳定 class 定位真身」，量的仍是同一个对象。

量四项，口径走共享库 `measure_kb()`（**852 修正版**：`moved` 含起点、
不 focus() 试探），与 850/851/852 逐字同款。

⚠️ 计费边界：只点下拉触发器 + 切分支的下拉项；**绝不**点生成/发送/购买/充值。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jimeng_kb_probe_lib import (  # noqa: E402
    FOCUS_JS, SNAP_JS, UNMARK_JS, ensure_open, mark_layer, mark_voice_panel,
    measure_kb,
)

# 计费护栏：**等值**才拦（850 教训：「生成模式」是控件描述，不是付费按钮）
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")


def guard(label):
    t = (label or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT or any(t.startswith(b) for b in BILLED_PREFIX):
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    return False


def diff_layers(before, after):
    keys = {(b["x"], b["y"], b["w"], b["h"]) for b in before}
    return [a for a in after if (a["x"], a["y"], a["w"], a["h"]) not in keys]


def select_audio_node():
    page.set_viewport_size({"width": 1512, "height": 1200})
    for _ in range(20):
        if page.evaluate("() => document.querySelectorAll('.react-flow__node').length"):
            break
        page.wait_for_timeout(700)
    page.wait_for_timeout(800)
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if loc.count():
            before = set(page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node')]"
                ".map(n => n.getAttribute('data-testid')||'')"))
            loc.first.click(timeout=10000)
            page.wait_for_timeout(2500)
            after = page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node')]"
                ".map(n => n.getAttribute('data-testid')||'')")
            new = [t for t in after if t and t not in before]
            if new:
                return new[0]
    return None


def click_node(tid):
    pt = page.evaluate("""(tid) => {
      const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const CTRL = 'button,[role=button],a,input,select,textarea';
      for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                              [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
        const x = r.x + r.width*fx, y = r.y + r.height*fy;
        const t = document.elementFromPoint(x, y);
        if (t && n.contains(t) && !t.closest(CTRL)) return [Math.round(x), Math.round(y)];
      }
      return null;
    }""", tid)
    if not pt:
        return False
    page.mouse.click(pt[0], pt[1])
    page.wait_for_timeout(1200)
    return page.evaluate(
        "() => document.querySelectorAll('.react-flow__node.selected').length") == 1


def probe_by_rect(name, trig_aria, node_tid):
    """按矩形差分认层的通用取样（音乐模型 / 音乐时长用这个）。"""
    print("=" * 74)
    print(f"【{name}】触发器 aria-label^={trig_aria!r}")
    rec = {"name": name, "trigger_aria": trig_aria}
    if not click_node(node_tid):
        rec["why"] = "选不中节点（前置态没成立）"
        return rec
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
    usable = [c for c in cands if c["visible"] and c["in_view"] and c["self_is_top"]]
    print(f"   同名触发器 {len(cands)} 个，可点 {len(usable)} 个")
    if not usable:
        rec["why"] = "没有可点的同名触发器（前置态没成立）"
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
        return rec
    layer = sorted(new, key=lambda x: -(x["w"] * x["h"]))[0]
    rec["layer"] = layer
    print(f"   层: {layer['w']}×{layer['h']} role={layer['role']!r}")
    marked = mark_layer(page, layer)
    rec["marked"] = marked
    if not marked.get("ok"):
        rec["why"] = "按 role=listbox/dialog 认不出层"
        return rec
    rec.update(measure_kb(page, marked, (pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)))
    return rec


results = {}
# ══ 跑起来 ════════════════════════════════════════════════════════════════
# ⚠️ 探针必须自己 goto 画布 URL（853 第一版栽过：漏了这行 ⇒ 停在首页/推广浮层，
#    左栏全是「打开画布/新建画布」，根本不是画布编辑器）。
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
print(f"== URL: {page.url[:70]}… ==")

tid = select_audio_node()
if not tid:
    print("!! 插不出音频节点 ⇒ A/B 都 BLOCKED_BY_FIXTURE")
    results["verdict"] = "no_audio_node"
else:
    results["audio_tid"] = tid
    print(f"== 音频节点 {tid} ==")

    # ── A. 切到「音乐生成」分支：按**文本**找 SPAN → 点它的**可点祖先** ──────
    print("\n== A. 切到「音乐生成」分支（按文本找 SPAN，851 按 role 找不到） ==")
    if click_node(tid):
        t = page.locator('button[aria-label^="创作类型"]')
        if t.count():
            t.first.click(timeout=8000)
            page.wait_for_timeout(900)
            # 按**文本**找「音乐生成」那个 SPAN（不限 role！），找它的可点祖先
            target = page.evaluate("""() => {
              let span = null;
              for (const e of document.querySelectorAll('span,div,p')) {
                if ((e.innerText||'').trim() === '音乐生成' && !e.querySelector('span,div,p')) {
                  span = e; break;
                }
              }
              if (!span) return {ok: false, why: '文本「音乐生成」的叶子元素都找不到'};
              // 往上找**可点的**祖先（cursor-pointer / button / role=button /
              // 带 onClick 痕迹的 div）
              let cand = span, best = null;
              while (cand && cand !== document.body) {
                const s = getComputedStyle(cand);
                const r = cand.getBoundingClientRect();
                const clickable = cand.tagName === 'BUTTON'
                  || cand.getAttribute('role') === 'button'
                  || s.cursor === 'pointer';
                if (clickable && r.width > 0 && r.height > 0) { best = cand; break; }
                cand = cand.parentElement;
              }
              if (!best) return {ok: false, why: '「音乐生成」没有可点的祖先'};
              const r = best.getBoundingClientRect();
              const cx = r.x + r.width/2, cy = r.y + r.height/2;
              const top = document.elementFromPoint(cx, cy);
              return {ok: true,
                      tag: best.tagName, cursor: getComputedStyle(best).cursor,
                      rect: [Math.round(r.x), Math.round(r.y),
                             Math.round(r.width), Math.round(r.height)],
                      self_is_top: !!(top && (top === best || best.contains(top)))};
            }""")
            print(f"   「音乐生成」可点祖先: {target}")
            if target.get("ok") and target.get("self_is_top") and not guard("音乐生成"):
                r = target["rect"]
                page.mouse.click(r[0] + r[2] // 2, r[1] + r[3] // 2)
                page.wait_for_timeout(1200)
                page.keyboard.press("Escape")  # 关掉「创作类型」层
                page.wait_for_timeout(500)
                # ⚠️ 切完之后**立刻**查触发器会数到 0（面板还没刷新完），
                #    但 `probe_by_rect` 里**重新选中一次**就出现了 ⇒ 这是
                #    **刷新时序**，不是「切不过去」。这里也照做：重新选中再查，
                #    否则会把「时序」误读成「前置态没成立」（853b 第一版就栽了）。
                if click_node(tid):
                    page.wait_for_timeout(1200)
                dur = page.locator('button[aria-label^="选择时长"]')
                mdl = page.locator('button[aria-label^="选择模型"]')
                mdl_al = mdl.first.get_attribute("aria-label") if mdl.count() else ""
                print(f"   切后(重新选中): 选择时长 {dur.count()} 个, "
                      f"选择模型 {mdl.count()} 个 {mdl_al!r}")
                results["A_switched"] = {"n_duration": dur.count(),
                                         "n_model": mdl.count(),
                                         "model_aria": mdl_al}
            else:
                print(f"   ⚠ 切分支失败: {target}")
                results["A_switched"] = {"failed": target}
        else:
            print("   ⚠ 找不到「创作类型」触发器")
    else:
        print("   ⚠ 选不中音频节点")

    # ── 正式取样 A：音乐模型 / 音乐时长（切过去之后才存在） ────────────────
    for nm, aria in [("音乐模型", "选择模型"), ("音乐时长", "选择时长")]:
        results[nm] = probe_by_rect(nm, aria, tid)

    # ── B. 音色库层：按 class `min-w-canvas-audio-voice-shrinkable` 认层 ────
    # ⚠️⚠️ **前置态**：A 段把面板切到了**音乐生成**分支，而「音色: 音色库」只在
    #    **音频生成**分支下有（853b 第一版忘了切回来 ⇒「音色」触发器 0 个，
    #    被当成「触发器不存在」—— 其实是**在错误的分支上问**）。
    #    「测不到」和「在错的分支上问」是两回事（§66 记过同款）。
    print("\n" + "=" * 74)
    print("【音色库】先切回「音频生成」分支，再按 class 认层")
    rec = {"name": "音色库", "trigger_aria": "音色"}
    if click_node(tid):
        t2 = page.locator('button[aria-label^="创作类型"]')
        cur_al = t2.first.get_attribute("aria-label") if t2.count() else ""
        print(f"   当前创作类型: {cur_al!r}")
        if t2.count() and "音乐" in (cur_al or ""):
            t2.first.click(timeout=8000)
            page.wait_for_timeout(900)
            back = page.evaluate("""() => {
              for (const e of document.querySelectorAll('span,div,p')) {
                if ((e.innerText||'').trim() === '音频生成'
                    && !e.querySelector('span,div,p')) {
                  let c = e, best = null;
                  while (c && c !== document.body) {
                    const s = getComputedStyle(c);
                    const r = c.getBoundingClientRect();
                    if ((c.tagName==='BUTTON' || c.getAttribute('role')==='button'
                         || s.cursor==='pointer') && r.width>0 && r.height>0) { best=c; break; }
                    c = c.parentElement;
                  }
                  if (!best) return {ok:false, why:'没有可点的祖先'};
                  const r = best.getBoundingClientRect();
                  return {ok:true, rect:[Math.round(r.x),Math.round(r.y),
                         Math.round(r.width),Math.round(r.height)]};
                }
              }
              return {ok:false, why:'找不到「音频生成」叶子元素'};
            }""")
            if back.get("ok"):
                r = back["rect"]
                page.mouse.click(r[0] + r[2] // 2, r[1] + r[3] // 2)
                page.wait_for_timeout(1200)
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                if click_node(tid):
                    page.wait_for_timeout(1000)
                now_al = (page.locator('button[aria-label^="创作类型"]')
                          .first.get_attribute("aria-label")
                          if page.locator('button[aria-label^="创作类型"]').count() else "")
                print(f"   切回后创作类型: {now_al!r}")
                rec["branch_restored"] = now_al
            else:
                print(f"   ⚠ 切回音频生成失败: {back}")
                rec["branch_restore_failed"] = back
        vt = page.locator('button[aria-label^="音色"]')
        print(f"   「音色」触发器 {vt.count()} 个")
        if vt.count() and not guard(vt.first.get_attribute("aria-label") or ""):
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
                          in_view: r.width>0 && r.height>0 && x>=0 && y>=0
                                && x<=innerWidth && y<=innerHeight,
                          self_is_top: !!(top && (top===l || l.contains(top)))});
              }
              return out;
            }""", "音色")
            usable = [c for c in cands if c["visible"] and c["in_view"] and c["self_is_top"]]
            if usable:
                pt = usable[0]["rect"]
                page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)
                page.wait_for_timeout(1000)
                marked = mark_voice_panel(page)
                rec["marked"] = marked
                if marked.get("ok"):
                    rec["layer"] = {"rect": marked["rect"], "role": "voice-library"}
                    rec.update(measure_kb(page, marked,
                                          (pt[0] + pt[2] // 2, pt[1] + pt[3] // 2),
                                          note="（音色库）"))
                else:
                    rec["why"] = f"按 class 认不出层：{marked.get('why')}"
            else:
                rec["why"] = "没有可点的音色触发器"
        else:
            rec["why"] = "音色触发器不存在或被护栏拦下"
    else:
        rec["why"] = "选不中音频节点"
    results["音色库"] = rec

with open("/tmp/b853b-source-audiostruct.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n== 汇总 ==")
for nm, r in results.items():
    if nm in ("audio_tid", "verdict", "A_switched"):
        continue
    if r.get("why"):
        print(f"  {nm:<10} ⚠ {r['why']}")
        continue
    fo = r.get("focus_at_open") or {}
    esc = r.get("escape") or {}
    arr = r.get("arrow_down") or {}
    # ⚠️ `layer` 的形状不统一（矩形差分走 dict，class 认层走 `{"rect": [...]}`），
    #    汇总这行第一版就栽在 `r['layer']['rect']` 的 KeyError 上 —— 打印代码
    #    自己崩了会把**已经量好的结果一起带走**（探针退出码 1，JSON 写了但
    #    没人看汇总）。取值一律 `.get` 兜底。
    lay = (r.get("layer") or {}).get("rect")
    print(f"  {nm:<10} 层={lay} "
          f"｜①接管={fo.get('in_layer')} "
          f"｜②{'困' if esc.get('trapped') else ('逃@'+str(esc.get('escaped_at')) if esc.get('escaped_at') else '?')} "
          f"｜③{('动' if arr.get('moved') else '不动') if arr.get('measured') else '没测到'}"
          + (f" (why={arr.get('why')})" if arr.get("why") else ""))
print("\n== 已写 /tmp/b853b-source-audiostruct.json ==")
