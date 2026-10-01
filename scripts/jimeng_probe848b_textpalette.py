#!/usr/bin/env python3
"""batch 848 源站探针（第二轮）：测能取到的层，并修上一轮的差分基准 bug。

第一轮（`jimeng_probe848_toolbars.py`）读到的事实：

  · **视频节点**选中后是**生成面板**：`选择模型: 即梦 Seedance 2.0 VIP` /
    `视频尺寸选项: 16:9 · 720P · 1` / `生成模式: 全能参考` /
    `选择视频生成时长: 4s` + `添加参考` / `引用参考` / `展开视频生成器` / `生成`。
    **没有「截取帧」「工具」下拉** —— 这一版画布上的视频是**生成结果**，
    不是挂在时间线上的可编辑片段。
  · **文本节点**选中后是 8 个 `Resize text from …` 手柄 + `Rename` +
    一枚**没有 aria-label 的 75×32 钮**（位置在标题行，疑似背景色调色板）
    + `全屏` + `下载`。
  · **画布上没有图片节点**（节点只有 视频 / 文本×3 / 时间线 / 导演台）
    ⇒ `image-tools-menu` 确认 **BLOCKED_BY_FIXTURE**。

第一轮自己的 bug：差分基准 `baseline` 在循环里被**累加**了，所以第二个节点起
「相对未选中态的新按钮」就变成 0 —— 文本 2/文本 3/导演台各报 0 枚是假的。
这一轮固定成「始终对未选中态求差集」。

⚠️ **计费边界**：这一轮会点视频生成面板的**下拉触发器**（模型/尺寸/模式/时长），
它们只是开菜单，安全；**绝不点 `生成`**（那会消耗积分）。代码里显式排掉它。

量法与 846b / 847d 一致：真按键盘读 `activeElement`、层身份用**矩形**（源站这几层
未必有 testid）、每个测量从重开的层起手。

只观察，不点任何付费购买流程。
"""

import json

MAX_TABS = 12
MAX_KEYS = 4

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)

SHELL = (".react-flow__renderer, .react-flow__pane, .react-flow__viewport, "
         ".react-flow__nodes, [id*=react-flow], [class*=canvas-main-region], "
         "header[aria-label='Canvas top bar'], main, section")

# 计费护栏：这些文案绝不能点
BILLED = ("生成", "立即生成", "确认生成", "发送", "局部重拍", "购买", "充值")


def sig(b):
    return f"{b['tid']}|{b['al']}|{b['x']},{b['y']}"


def all_buttons():
    return page.evaluate("""() => [...document.querySelectorAll('button,[role=button],[role=menuitem]')]
      .map(b => {
        const r = b.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return null;
        return {al: b.getAttribute('aria-label') || '',
                tid: b.getAttribute('data-testid') || '',
                txt: (b.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
                x: Math.round(r.x), y: Math.round(r.y),
                w: Math.round(r.width), h: Math.round(r.height),
                cx: Math.round(r.x + r.width/2), cy: Math.round(r.y + r.height/2)};
      }).filter(Boolean)""", )


def snap():
    return page.evaluate("""(SHELL) => {
      const out = [];
      for (const e of document.querySelectorAll('body *')) {
        const s = getComputedStyle(e);
        if (s.position !== 'fixed' && s.position !== 'sticky') continue;
        if (e.matches(SHELL)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 60 || r.height < 30) continue;
        const bg = s.backgroundColor || '';
        const opaque = bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
        const f = e.querySelectorAll('a[href],button,input,select,textarea,'
          + '[tabindex],[role=menuitem],[role=option]').length;
        if (!opaque && f === 0) continue;
        out.push({sig: e.tagName + '|' + s.position + '|' + s.zIndex + '|'
                   + Math.round(r.width) + 'x' + Math.round(r.height) + '|'
                   + Math.round(r.x) + ',' + Math.round(r.y),
              tid: e.getAttribute('data-testid') || '',
              role: e.getAttribute('role') || '',
              al: (e.getAttribute('aria-label') || '').slice(0, 36),
              w: Math.round(r.width), h: Math.round(r.height),
              x: Math.round(r.x), y: Math.round(r.y), focusables: f, z: s.zIndex});
      }
      return out;
    }""", SHELL)


def focus_now(rect):
    return page.evaluate("""(R) => {
      const a = document.activeElement;
      if (!a || a === document.body) return {who: 'body', in: false};
      const r = a.getBoundingClientRect();
      const inR = !!R && r.left >= R.x - 1 && r.top >= R.y - 1
                  && r.right <= R.x + R.w + 1 && r.bottom <= R.y + R.h + 1;
      return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
                || a.getAttribute('aria-label')
                || (a.innerText || '').trim().replace(/\\s+/g,' ').slice(0, 16)
                || a.tagName)),
              al: (a.getAttribute('aria-label') || '').trim().slice(0, 30),
              tid: a.getAttribute('data-testid') || '',
              tabindex: a.getAttribute('tabindex'),
              w: Math.round(r.width), h: Math.round(r.height), in: inR};
    }""", rect)


def select_node(al_like):
    n = page.evaluate("""(k) => {
      for (const x of document.querySelectorAll('[data-id]')) {
        if ((x.getAttribute('aria-label') || '').includes(k)) {
          const r = x.getBoundingClientRect();
          if (r.width < 80 || r.height < 80) continue;
          return {id: x.getAttribute('data-id'),
                  x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }
      }
      return null;
    }""", al_like)
    if not n:
        return None
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    page.mouse.move(700, 520)
    page.wait_for_timeout(200)
    page.mouse.click(n["x"], n["y"])
    page.wait_for_timeout(1600)
    return n


# ── 固定的「未选中态」基准（第一轮把它在循环里累加了，是 bug）─────────────
page.keyboard.press("Escape")
page.wait_for_timeout(800)
UNSELECTED = {sig(b) for b in all_buttons()}
print(f"未选中态全页按钮 {len(UNSELECTED)} 枚（固定基准）")

targets = []
for n in page.evaluate("""() => [...document.querySelectorAll('[data-id]')]
  .filter(n => { const r = n.getBoundingClientRect();
                 return r.width > 80 && r.height > 80; })
  .map(n => ({id: n.getAttribute('data-id'),
              al: n.getAttribute('aria-label') || ''}))"""):
    sel = select_node(n["al"])
    if not sel:
        continue
    fresh = [b for b in all_buttons() if sig(b) not in UNSELECTED]
    real = [b for b in fresh
            if not any(word in (b["al"] or b["txt"]) for word in BILLED)]
    print("=" * 76)
    print(f"【{n['al']}】对未选中态的新按钮 {len(fresh)} 枚（其中计费护栏外 {len(real)} 枚）")
    for b in fresh:
        flag = " ⚠计费" if any(w in (b["al"] or b["txt"]) for w in BILLED) else ""
        print(f"    al={b['al']!r:<50} txt={b['txt']!r:<14} "
              f"{b['w']}×{b['h']} @({b['x']},{b['y']}){flag}")
    targets.append({"node": n["al"], "fresh": real})

with open("/tmp/b848b-toolbars.json", "w", encoding="utf-8") as f:
    json.dump(targets, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b848b-toolbars.json")

# ── 文本节点那枚**无 aria-label 的 75×32 钮**：开它，看是什么层 ────────────
print("\n" + "=" * 76)
print("【文本工具条里那枚无名钮】")
sel = select_node("文本 node: 文本 1")
if sel:
    fresh = [b for b in all_buttons() if sig(b) not in UNSELECTED]
    unnamed = [b for b in fresh if not b["al"] and not b["tid"] and 40 < b["w"] < 120]
    print("  无名钮候选:", json.dumps(unnamed, ensure_ascii=False))
    if unnamed:
        t = unnamed[0]
        before = {L["sig"] for L in snap()}
        page.mouse.click(t["cx"], t["cy"])
        page.wait_for_timeout(1500)
        after = snap()
        fresh_layers = [L for L in after if L["sig"] not in before]
        print("  点开后新出现的 fixed/sticky 层:")
        for L in fresh_layers:
            print("    ", json.dumps(L, ensure_ascii=False)[:200])
        if fresh_layers:
            R = max(fresh_layers, key=lambda L: L["focusables"])
            rect = {"x": R["x"], "y": R["y"], "w": R["w"], "h": R["h"]}
            at_open = focus_now(rect)
            print("  开层那一瞬间焦点:", json.dumps(at_open, ensure_ascii=False)[:210])
            # 层内 Tab / 方向键（每个测量从重开的层起手）
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            page.mouse.click(t["cx"], t["cy"])
            page.wait_for_timeout(1200)
            esc_at = None
            for i in range(1, MAX_TABS + 1):
                page.keyboard.press("Tab")
                f = focus_now(rect)
                if not f.get("in"):
                    esc_at = i
                    print(f"  层内 Tab 第 {i} 次逃出 → al={f.get('al')!r} "
                          f"tid={f.get('tid')!r}")
                    break
            if esc_at is None:
                print(f"  层内 Tab：{MAX_TABS} 次全在层内（困住）")
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            page.mouse.click(t["cx"], t["cy"])
            page.wait_for_timeout(1200)
            seq = []
            for _ in range(MAX_KEYS):
                page.keyboard.press("ArrowDown")
                seq.append(focus_now(rect).get("who"))
            print("  方向键 ArrowDown ×4:", " → ".join(str(s) for s in seq),
                  "| moved=", len(set(seq)) > 1)
        else:
            print("  ⚠ 点开后**没有新层** —— 可能是就地控件不是浮层，如实记账")
