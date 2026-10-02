#!/usr/bin/env python3
"""batch 885 源站探针：**只做一件事** —— Esc 之后音频节点还在不在选中态。

## 为什么是全新的一份，而不是继续修 883

883 打了三轮补丁还是**前置态不成立**（阶段 B 点节点没选中），
而 884 已经证明「可靠地选中一个指定节点」**是做得到的**（5 策略 2/2）。
两个探针在同一件事上给出相反结果 ⇒ **883 的选中那段逻辑本身有问题**，
继续在它上面打补丁只会把「不可靠」越修越复杂。

所以 885 从零写，并且**把 884 的成果真正用起来**：

| 883 的做法 | 885 的做法 |
|---|---|
| 一个落点，点一次，旁证不成立就记账 | **五种落点依次试**，旁证不成立就**换下一个** |
| dump 按 `aria-label^="音频 node"` 找第一个 | 全部按 `data-testid`（884 查清这是 883 差分恒 0 的真因） |
| 打印旁证但继续往下跑 | 旁证**把关**，不成立就不产出数据 |

## 五种落点（884 实测 2/2 可靠的五个，逐一备胎）

center / quarter / corner / edge_mid / scan

## 测什么

选中节点 → 开音色库 → 给「性别」选一个值 → 焦点聚到 Clear → 按 Esc
然后问两个问题：

① 音频节点**还在不在选中态**？（旁证 = 音频生成工具条在不在）
② 焦点落在谁身上？（已知落在音频节点上，这儿是第 N 次复现）

## 为什么这条值得测

882 的根因是 `@xyflow/react` **取消选中时**把节点 blur 掉。
若源站 Esc **不取消选中** ⇒ 复刻「取消选中」才是**更根本的差异**，
882 的双 rAF 是在**治症状**；若源站也取消 ⇒ 复刻的库行为差异，治症状可接受。

## 计费边界

只点「音频」入口、点画布空白、点节点本体、开「音色」、点筛选钮、点选项、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe885_escselect2_src.py
"""

import json

OUT = "/tmp/b885-src-escselect2.json"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""

VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""

# 五种落点（884 实测 2/2 可靠的五个，逐一备胎）。**只算坐标，不点**。
STRATS_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const L = r.left, T = r.top, W = r.width, H = r.height;
  const at = (fx, fy) => [Math.round(L + W * fx), Math.round(T + H * fy)];
  const scan = [];
  for (let i = 1; i <= 19; i++) {
    const x = Math.round(L + W * i / 20), y = Math.round(T + H / 2);
    const t = document.elementFromPoint(x, y);
    if (t && n.contains(t)) { scan.push([x, y]); break; }
  }
  return {
    center:  at(0.5, 0.5),
    quarter: at(0.5, 0.25),
    corner:  at(0.15, 0.15),
    edge_mid:at(0.5, 0.04),
    scan:    scan[0] || null,
  };
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def click_blank():
    spot = ev("""() => {
      for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                            [1400, 840], [400, 1080]]) {
        const t = document.elementFromPoint(x, y);
        if (t && t.closest('.react-flow__pane')
            && !t.closest('.react-flow__node')) return [x, y];
      }
      return null;
    }""")
    if spot:
        page.mouse.click(spot[0], spot[1])
        page.wait_for_timeout(800)
    return spot


def select_node(tid, strats):
    """按策略**依次**试，旁证把关。返回命中的策略名，没成功就 None。
    ⚠️ 不是「点一次就记账」—— 884 已证五种都能中，
    这里做的是**备胎**，不是**硬试**。"""
    tried = []
    for name in ("center", "quarter", "corner", "edge_mid", "scan"):
        xy = strats.get(name)
        if not xy:
            tried.append({"strategy": name, "ok": False,
                          "why": "算不出落点"})
            continue
        click_blank()                       # 起点统一为「未选中」
        before = ev(TOOLBAR_JS)
        page.mouse.click(xy[0], xy[1])
        page.wait_for_timeout(1000)
        after = ev(TOOLBAR_JS)
        ok = (not before) and after
        tried.append({"strategy": name, "xy": xy,
                      "toolbar_before": before, "toolbar_after": after,
                      "ok": ok})
        print(f"   策略 {name:9s} 落点={xy} "
              f"工具条 {before}→{after} {'✅' if ok else '❌'}")
        if ok:
            return name, tried
    return None, tried


out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    tid = None
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if not loc.count():
            continue
        before = set(ev("() => [...document.querySelectorAll('.react-flow__node')]"
                        ".map(n => n.getAttribute('data-testid')||'')"))
        loc.first.click(timeout=10000)
        page.wait_for_timeout(2500)
        after = ev("() => [...document.querySelectorAll('.react-flow__node')]"
                   ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        if new:
            tid = new[0]
            break
    out["audio_node"] = tid
    print(f"== 音频节点 {tid} ==")

    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    else:
        strats = ev(STRATS_JS, tid)
        out["strats"] = strats
        print(f"\n== 五种落点：{strats}")
        print("\n== 选节点（旁证把关，策略备胎）==")
        hit, tried = select_node(tid, strats)
        out["select_tries"] = tried
        out["select_strategy"] = hit
        if not hit:
            out["verdict"] = (
                "前置态没成立：**五种落点全试了**，旁证（工具条在不在）"
                "一次都没成立 ⇒ 「在源站可靠地选中一个指定节点」这个"
                "**前置问题本身仍未解决**（884 的 2/2 不能外推："
                "那是**另一个节点实例**、另一个时机的结果）。"
                "**不是**「节点选不中」—— 可能是这次插入的节点位置"
                "恰好被别的浮层盖住了。**要查的是浮层，不是落点。**")
            print("  !! " + out["verdict"])
        else:
            rec = {"selected_by": hit}
            # 开音色库
            for _ in range(3):
                if ev(VOICES_JS):
                    break
                vt = page.locator('button[aria-label^="音色"]')
                if vt.count():
                    vt.first.click(timeout=8000)
                    page.wait_for_timeout(1800)
            rec["voices_open"] = ev(VOICES_JS)
            # 选一个值，让 Clear 冒出来
            if rec["voices_open"]:
                c = ev("""() => {
                  for (const b of document.querySelectorAll('button[aria-expanded]')) {
                    const a = b.getAttribute('aria-label') || '';
                    if (a.startsWith('性别:')) {
                      const r = b.getBoundingClientRect();
                      return [Math.round(r.x + r.width/2),
                              Math.round(r.y + r.height/2)];
                    }
                  }
                  return null;
                }""")
                if c:
                    page.mouse.click(c[0], c[1])
                    page.wait_for_timeout(800)
                    o = page.get_by_text("男", exact=True).first
                    if o.count():
                        o.click(timeout=8000)
                        page.wait_for_timeout(900)
            rec["clear_shown"] = bool(ev(
                """() => !!document.querySelector(
                     '[aria-label="Clear 性别 filter"]')"""))
            rec["toolbar_before_esc"] = ev(TOOLBAR_JS)
            if rec["clear_shown"]:
                ev("""() => {
                  const b = document.querySelector(
                    '[aria-label="Clear 性别 filter"]');
                  if (b) b.focus();
                }""")
                rec["focus_before"] = ev(FOCUS_JS)
                page.keyboard.press("Escape")
                page.wait_for_timeout(1100)
            rec["focus_after"] = ev(FOCUS_JS)
            # ⚠️ **旁证就是判据**：工具条在 = 节点仍选中
            rec["toolbar_after_esc"] = ev(TOOLBAR_JS)
            rec["node_still_selected"] = rec["toolbar_after_esc"]
            print(f"\n== 关键读数 ==")
            print(f"   Clear 出现={rec['clear_shown']}  "
                  f"Esc 前工具条={rec['toolbar_before_esc']}")
            print(f"   Esc 后：工具条={rec['toolbar_after_esc']}  "
                  f"焦点={rec['focus_after']['aria']!r}")
            if rec["clear_shown"]:
                if rec["node_still_selected"]:
                    rec["verdict"] = (
                        "**源站 Esc 之后节点仍处于选中态**（工具条还在）"
                        "⇒ ① 号解释成立：复刻「Esc 取消选中」才是"
                        "**更根本的差异**，882 的双 rAF 是在**治症状**。")
                else:
                    rec["verdict"] = (
                        "源站 Esc 之后节点**也取消了选中**（工具条没了），"
                        "但焦点仍落在它身上 ⇒ ③ 号解释：源站有"
                        "「blur 之后把焦点抢回来」的东西，复刻缺的是它；"
                        "**复刻 882 的双 rAF 方向是对的**（补的是同一件事）。")
                print(f"\n== {rec['verdict']}")
            else:
                rec["verdict"] = ("前置态没成立：Clear 没出现 ⇒ 本轮不测")
                print(f"  !! {rec['verdict']}")
            out["result"] = rec
        if not out.get("verdict"):
            out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
