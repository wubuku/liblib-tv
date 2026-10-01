#!/usr/bin/env python3
"""batch 841 源站探针：AI 抽屉里那四层的 testid / role / 几何。

复刻侧 role 层普查报出 4 处「有 role 无锚点」：
  会话列表 / 搜索技能 / 添加来源(menu) / 添加参考
本探针去源站问同一个问题：**源站这几层自己带不带 data-testid**。
带了 → 逐字照抄；没带 → 记 SOURCE_FACT，复刻侧再用我方约定命名，并写明。
只观察，不点任何付费购买流程。
"""

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(9000)


def census(tag):
    d = page.evaluate("""() => {
      const out = [];
      for (const e of document.querySelectorAll('body *')) {
        const r = e.getAttribute('role');
        if (!['dialog','menu','listbox','popover'].includes(r || '')) continue;
        const b = e.getBoundingClientRect();
        if (b.width < 40 || b.height < 20) continue;
        const al = (e.getAttribute('aria-label') || '').trim();
        const txt = (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 30);
        out.push({role: r, tid: e.getAttribute('data-testid') || '',
                  al: al || '(无 aria-label)', txt: txt || '(无文本)',
                  w: Math.round(b.width), h: Math.round(b.height),
                  x: Math.round(b.x), y: Math.round(b.y)});
      }
      return out;
    }""")
    print(f"\n== {tag}：{len(d)} 处 role 浮层 ==")
    for x in d:
        print("  ", x)
    return d


census("初始")

# 打开 AI 抽屉（Agent sidecar）
cands = page.evaluate("""() => {
  const out = [];
  for (const b of document.querySelectorAll('button,[role=button]')) {
    const s = ((b.getAttribute('aria-label')||'') + ' ' + (b.innerText||'')).trim();
    if (/AI|对话|Agent|智能/i.test(s)) {
      const r = b.getBoundingClientRect();
      if (r.width > 8 && r.height > 8)
        out.push({tag: b.tagName, s: s.slice(0, 30),
                  tid: b.getAttribute('data-testid') || '',
                  r: [Math.round(r.x), Math.round(r.y),
                      Math.round(r.width), Math.round(r.height)]});
    }
  }
  return out;
}""")
print("\n== 能打开 AI 抽屉的候选 ==")
for c in cands:
    print("  ", c)

if not cands:
    print("!! 找不到 AI 抽屉入口，记 BLOCKED_BY_FIXTURE")
else:
    page.mouse.click(cands[0]["r"][0] + cands[0]["r"][2] // 2,
                     cands[0]["r"][1] + cands[0]["r"][3] // 2)
    page.wait_for_timeout(2500)
    census("点开 AI 抽屉后")

    # 逐个找那四层的入口（会话 / 技能 / 来源 / 参考）
    for kw in ("会话", "技能", "来源", "参考"):
        b = page.evaluate("""(kw) => {
          for (const e of document.querySelectorAll('button,[role=button],[role=menuitem]')) {
            const s = ((e.getAttribute('aria-label')||'') + ' ' + (e.innerText||''));
            if (!s.includes(kw)) continue;
            const r = e.getBoundingClientRect();
            if (r.width < 8 || r.height < 8) continue;
            return {s: s.trim().slice(0, 30), tid: e.getAttribute('data-testid')||'',
                    r: [Math.round(r.x), Math.round(r.y),
                        Math.round(r.width), Math.round(r.height)]};
          }
          return null;
        }""", kw)
        print(f"\n-- 含「{kw}」的按钮 =", b)
        if not b:
            continue
        try:
            page.mouse.click(b["r"][0] + b["r"][2] // 2,
                             b["r"][1] + b["r"][3] // 2)
        except Exception as e:
            print("   点击失败", e)
            continue
        page.wait_for_timeout(1800)
        got = census(f"点了「{kw}」之后")
        for g in got:
            if not g["tid"] or kw in g["al"] or kw in g["txt"]:
                print(f"   ★ 与「{kw}」相关：{g}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(900)

page.screenshot(path="/tmp/b841-source.png")
print("\n截图 /tmp/b841-source.png")
