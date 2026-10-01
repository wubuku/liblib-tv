"""batch 838 取证：源站「添加参考」浮层是**两级**的（categories 列表 + 挂在它**左边**
的第二块面板），而复刻是 tab 式单层面板。

⚠ 第一轮我把它当成了「就地展开」—— 错在**取样窗口**：行计数用的 x 过滤是
`innerWidth - 620`（=892），而二级浮层在 x≈760，被自己的取样条件挡在门外，
于是只看见一级行数从 5 变 7（那两行是二级面板的文字被算进了 DOM 子树）。
截图揭穿的。**取样条件本身也是判据的一部分** —— 它会决定你能看见什么。

836 把占位符里那枚 @ 接成了真按钮，复用的是复刻底行「引用参考」那个
`agent-mention-panel`（810 验过：5 个分类 **tab** + 确认按钮 + 切 tab 改按钮
文案）。而源站点开后的浮层是**一列带 `›` 的行**（主体/图片/视频/音频/文本），
**一个 testid 都没有** —— 于是 836 只能靠截图看清它存在，看不清它是什么结构。

本探针要回答四件事（**只打开、不确认**，不插入任何引用、不消耗积分）：
1. 浮层的 role / 几何（相对 composer 出现在哪）
2. 每一行点下去会不会出**第二级**？第二级里有什么？在哪？
3. 底行那枚 `canvas-agent-composer-mention` 是不是**同一个**浮层
4. 「+」那枚 `canvas-agent-composer-add` 打开的是不是另一个东西

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_838_refpopover_probe.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("docs/research/jimeng-canvas-batch838-2026-10-04")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# 面板里除已知 chrome 之外**新出现**的东西：靠 aria/role + 尺寸捞，
# 因为它没有 testid（836 已实测）。
DUMP_JS = """() => {
  const r = (el) => { const b = el.getBoundingClientRect();
    return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const panel = [...document.querySelectorAll('div')].find((el) => {
    const b = el.getBoundingClientRect();
    return Math.abs(b.width - 398) < 10 && b.x > innerWidth - 460 && b.height > 800; });
  if (!panel) return { error: '没找到面板' };
  const known = new Set(['canvas-agent-session-menu-trigger','canvas-agent-session-title',
    'canvas-agent-session-create','canvas-agent-session-collapse','canvas-agent-session-heading',
    'canvas-agent-session-modes','canvas-agent-mode-action','canvas-agent-session-composer',
    'prompt-composer','canvas-agent-composer-placeholder-mention','canvas-agent-composer-action-row',
    'canvas-agent-composer-add','canvas-agent-skill-trigger','canvas-agent-composer-mention',
    'canvas-agent-send']);
  // 已知 chrome 之外、且不在这 6 枚已知 testid 里的浮层候选：
  // 特征 = 出现在 composer 附近、尺寸像个菜单、role 是 menu/listbox 或带行文字
  const cands = [];
  for (const el of document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],div')) {
    const b = el.getBoundingClientRect();
    if (b.width < 90 || b.width > 420 || b.height < 60 || b.height > 700) continue;
    if (b.x < innerWidth - 900) continue;               // 必须在右缘附近（含挂在左边的二级浮层）
    if (b.y < 380) continue;                            // 在 composer 上方
    if (panel.contains(el) && el !== panel) {
      // 面板内部的：只认没有 testid 且不是那 19 枚已知 chrome
      if (el.getAttribute('data-testid') || known.has(el.getAttribute('data-testid'))) continue;
    }
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const rows = [...el.querySelectorAll('[role="menuitem"],[role="option"],li,button')].map((n) => {
      const nb = n.getBoundingClientRect();
      const ncs = getComputedStyle(n);
      return { tag: n.tagName, role: n.getAttribute('role') || '',
               text: (n.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 20),
               al: n.getAttribute('aria-label') || '',
               rect: [Math.round(nb.x), Math.round(nb.y), Math.round(nb.width), Math.round(nb.height)],
               color: ncs.color, fontSize: ncs.fontSize, cursor: ncs.cursor };
    });
    if (!rows.length) continue;
    cands.push({ tag: el.tagName, role: el.getAttribute('role') || '',
                 rect: r(el), background: cs.backgroundColor, borderRadius: cs.borderRadius,
                 padding: cs.padding, shadow: cs.boxShadow.slice(0, 60), rowCount: rows.length, rows });
  }
  return { candidates: cands, bodyTail: (document.body.innerText || '').replace(/\\s+/g, ' ').slice(-260) };
}"""


def snap(page, label: str) -> dict:
    return {"label": label, **page.evaluate(DUMP_JS)}


def main() -> int:
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(24):
        if not page.evaluate("() => document.body.innerText.includes('Loading canvas')"):
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(2500)
    page.click('[data-testid="canvas-sidecar-launcher"]')
    page.wait_for_timeout(1500)

    report: dict = {"viewport": page.viewport_size, "steps": [snap(page, "① 面板刚打开（基线）")]}

    # ② 点底行「引用参考」（不用占位符那枚，避免往 composer 插裸 @）
    page.click('[data-testid="canvas-agent-composer-mention"]')
    page.wait_for_timeout(1000)
    report["steps"].append(snap(page, "② 点底行「引用参考」"))
    page.screenshot(path=str(OUT_DIR / "source-refpopover-level1.png"))

    # ③ 点第一级里的一行（用文字定位，不靠 testid —— 它没有 testid）
    rows = page.evaluate("""() => {
      const out = [];
      for (const el of document.querySelectorAll('[role="menuitem"],[role="option"],li,button')) {
        const b = el.getBoundingClientRect();
        if (b.x < innerWidth - 900 || b.y < 380 || b.y > 900) continue;
        const t = (el.innerText || '').replace(/\\s+/g, ' ').trim();
        if (['主体','图片','视频','音频','文本'].includes(t)) out.push({ text: t, rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] });
      }
      return out;
    }""")
    report["level1_rows"] = rows
    if rows:
        r = rows[0]
        page.mouse.click(r["rect"][0] + r["rect"][2] / 2, r["rect"][1] + r["rect"][3] / 2)
        page.wait_for_timeout(1200)
        report["clicked_row"] = r["text"]
        report["steps"].append(snap(page, f"③ 点第一级「{r['text']}」之后"))
        page.screenshot(path=str(OUT_DIR / "source-refpopover-level2.png"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "source-refpopover-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for s in report["steps"]:
        print("===", s["label"])
        if s.get("error"):
            print("   ", s["error"])
            continue
        for c in s["candidates"]:
            print(f"    <{c['tag']}> role={c['role']!r} {c['rect']} bg={c['background']} 行数={c['rowCount']}")
            for row in c["rows"][:8]:
                print(f"        {row['text']!r} {row['rect']} cursor={row['cursor']} al={row['al']!r}")
    print("第一级行:", json.dumps(rows, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
