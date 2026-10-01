"""Jimeng clone batch 812-nodechrome verifier —— 节点描边环 + 标题行 + 标签钮。

SOURCE_FACT batch 812 (2026-10-03 @1512×950 源站登录态，**两侧都归到 100% 缩放**
后逐元素量；见 docs/research/jimeng-canvas/README.md §21/§22)：

## 1. 描边环 —— 源站是 inset，复刻此前是 outset
源站在卡片外侧另有一层 `pointer-events-none absolute` 的交互/描边层
(577×328 @ 卡片 -4,-4)，环画在那里：
  - 未选中 `rgba(255,255,255,0.2) 0 0 0 1px inset`
  -   选中 `rgba(255,255,255,0.6) 0 0 0 1px inset,
          color(srgb 1 1 1 / 0.192) 0 2px 8px -2px`
复刻此前 7 处各写一份 `0 0 0 1.5px rgba(255,255,255,0.92)`（outset、1.5px、92%），
未选中态还有两种写法（`undefined` 与 `white/6 inset`，源站是 `white/20`）。

## 2. 标题行 —— 内容顶对齐在 -31，不是"在 32px 行里居中"
  源站行盒 56×32 @(0,-31)，但盒内没居中：
    图标 svg  16×16 @(0,-27)   ← 比行顶低 4
    文字 span 36×24 @(20,-31)  ← 顶着行顶，24 高 = 22 行高 + 上下各 1px
  复刻此前 `bottom-full h-8` + items-center + gap-1.5：
    行盒 @(0,-32)、文字 22 高 @(22,-27) —— 低 4px、左移多 2px、高少 2px。

## 3. 标签钮 —— 源站实名 `Add tags`
  源站 24×24、rounded-lg(8px)、padding 0 4px、右缘落在卡片右缘内侧 1px，
  外面套一层 `-inset-1`(32×32) 悬停命中区。
  复刻此前自造 aria「节点颜色标记」+ 16×16 无圆角。行为（五色选色盘）不变。

本 verifier 的两条**反向**断言：
- 环里必须出现 `inset`。若哪天写回 outset，源站的「环画在卡片内侧」就丢了。
- 7 个节点类型必须**共用** `nodeRingShadow()`，不能各写一份字面量
  （7 份字面量正是本批要消灭的东西，故用源码扫描守住）。

缩放归一化：本 verifier 先按 ⌘1 归到 100% 再量，并把量到的值除以
`.react-flow__viewport` 的缩放矩阵 a —— 忘了这一步会得出「手柄只有 26×26」
的假结论（36 × 0.73 ≈ 26），本批已踩过一次。
"""

import re
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
SHOT = "docs/research/jimeng-canvas-batch812-2026-10-03"

NODE_FILES = [
    "JimengVideoMediaCard.tsx",
    "JimengImageNode.tsx",
    "JimengAudioNode.tsx",
    "JimengTextNode.tsx",
    "JimengSubjectNode.tsx",
    "JimengDirectorNode.tsx",
    "JimengTimelineNode.tsx",
]

# 期望值写成**浏览器规范化后**的形式：getComputedStyle 会把
# `inset 0 0 0 1px rgba(...)` 重排成 `<color> 0px 0px 0px 1px inset`。
# （batch 811 的 verifier 就在这里脆断过一次：拿作者写下的顺序去比。）
RING_UNSELECTED = "rgba(255, 255, 255, 0.2) 0px 0px 0px 1px inset"
RING_SELECTED = (
    "rgba(255, 255, 255, 0.6) 0px 0px 0px 1px inset, "
    "rgba(255, 255, 255, 0.192) 0px 2px 8px -2px"
)

fails: list[str] = []
checks = 0


def check(cond: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    print(f"  {'✓' if cond else '✗'} {label}" + ("" if cond else f"  {detail}"))
    if not cond:
        fails.append(f"{label}  {detail}")


def wait_server() -> None:
    """共享 dev server 会被并行 session 反复重启 —— 连续 3 次 200 才开跑。"""
    ok = 0
    for _ in range(15):
        try:
            with urllib.request.urlopen(URL, timeout=5) as r:
                ok = ok + 1 if r.status == 200 else 0
                if ok >= 3:
                    return
        except Exception:
            ok = 0
        time.sleep(2)
    print("!! dev server 连续 3 次 200 未达成，跳过本轮验收")
    sys.exit(2)


PROBE = """() => {
  const vp = document.querySelector('.react-flow__viewport');
  const z = vp ? new DOMMatrixReadOnly(getComputedStyle(vp).transform).a : 1;
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    const rec = { id: n.getAttribute('data-id'),
                  selected: n.classList.contains('selected'),
                  w: Math.round(r.width / z), h: Math.round(r.height / z),
                  ring: null, row: null, icon: null, text: null, tag: null };
    // 描边环：取本节点内第一个非 none 的 boxShadow
    for (const e of n.querySelectorAll('*')) {
      const cs = getComputedStyle(e);
      if (cs.boxShadow && cs.boxShadow !== 'none') { rec.ring = cs.boxShadow; break; }
    }
    // 标题行容器：认它真的带着 top-[-31px] 这个类。
    // 不用「卡片上方的叶子元素」去找 —— 那样会挑中 13×13 的图标 <path>。
    const rowEl = n.querySelector('div[class*="top-[-31px]"]');
    if (rowEl) {
      const b = rowEl.getBoundingClientRect();
      rec.row = { y: Math.round((b.top - r.top) / z), h: Math.round(b.height / z),
                  w: Math.round(b.width / z), x: Math.round((b.left - r.left) / z) };
    }
    const t = n.querySelector('[data-testid="node-title-text"]');
    if (t) {
      const b = t.getBoundingClientRect(); const cs = getComputedStyle(t);
      rec.text = { x: Math.round((b.left - r.left) / z), y: Math.round((b.top - r.top) / z),
                   w: Math.round(b.width / z), h: Math.round(b.height / z),
                   pad: cs.padding, fs: cs.fontSize, lh: cs.lineHeight,
                   color: cs.color, txt: (t.textContent||'').trim().slice(0,16) };
      const ic = t.previousElementSibling;
      if (ic && ic.tagName.toLowerCase() === 'svg') {
        const ib = ic.getBoundingClientRect();
        rec.icon = { x: Math.round((ib.left - r.left) / z), y: Math.round((ib.top - r.top) / z),
                     w: Math.round(ib.width / z), h: Math.round(ib.height / z) };
      }
    }
    const tg = n.querySelector('button[aria-label="Add tags"]');
    if (tg) {
      const b = tg.getBoundingClientRect(); const cs = getComputedStyle(tg);
      rec.tag = { x: Math.round((b.left - r.left) / z), y: Math.round((b.top - r.top) / z),
                  w: Math.round(b.width / z), h: Math.round(b.height / z),
                  right: Math.round((b.right - r.left) / z), radius: cs.borderRadius,
                  pad: cs.padding, cardW: Math.round(r.width / z) };
    }
    out.push(rec);
  }
  return { zoom: Math.round(z * 1000) / 100, nodes: out };
}"""


def main() -> None:
    wait_server()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1512, "height": 950})
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector(".react-flow__node", timeout=45000)
        page.wait_for_timeout(2500)

        # —— 缩放归一化：先归到 100%
        page.locator('[data-testid="dock-zoom"]').first.focus()
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(1200)

        print("\n[0] 缩放已归一化")
        z = page.evaluate(
            """() => { const v=document.querySelector('.react-flow__viewport');
                       return Math.round(new DOMMatrixReadOnly(getComputedStyle(v).transform).a*1000)/10; }"""
        )
        check(z == 100, f"当前缩放 = 100%（实得 {z}）")

        def snapshot() -> dict:
            return page.evaluate(PROBE)

        # —— 未选中态
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)
        un = snapshot()
        check(
            all(not n["selected"] for n in un["nodes"]),
            "Escape 后无节点选中",
        )

        print("\n[1] 描边环 · 未选中态")
        rings_u = [n["ring"] for n in un["nodes"] if n["ring"]]
        check(len(rings_u) == len(un["nodes"]), "每个节点都有描边环", f"{len(rings_u)}/{len(un['nodes'])}")
        for i, rg in enumerate(rings_u):
            check(rg == RING_UNSELECTED, f"节点{i+1} 未选中环 = inset 1px white/20", f"实得 {rg!r}")
            check("inset" in rg, f"节点{i+1} 环是 inset（画在卡片内侧）", f"实得 {rg!r}")
            check("1.5px" not in rg, f"节点{i+1} 环不是 1.5px", f"实得 {rg!r}")

        # —— 选中态
        nb = page.locator(".react-flow__node").first.bounding_box()
        page.mouse.click(nb["x"] + min(200, nb["width"] / 2), nb["y"] + 20)
        page.wait_for_timeout(900)
        sel = snapshot()
        picked = [n for n in sel["nodes"] if n["selected"]]
        check(len(picked) == 1, f"恰好一个节点被选中（{len(picked)}）")
        if picked:
            rg = picked[0]["ring"]
            check(rg == RING_SELECTED, f"选中环 = inset 1px white/60 + 投影", f"实得 {rg!r}")
            check("inset" in rg, "选中环是 inset", f"实得 {rg!r}")
            check(
                "0px 2px 8px -2px" in rg,
                "选中环带 0 2px 8px -2px 投影",
                f"实得 {rg!r}",
            )
            check("0.92" not in rg, "不再用旧的 white/92", f"实得 {rg!r}")

        print("\n[2] 标题行几何（相对卡片，100% 缩放下）")
        n0 = picked[0] if picked else sel["nodes"][0]
        row = n0["row"]
        check(row is not None, "存在标题行元素")
        if row:
            check(row["y"] == -31, f"标题行顶 = -31（实得 {row['y']}）")
            check(row["h"] == 32, f"标题行高 32（保留 32px 命中区，实得 {row['h']}）")
        ic = n0["icon"]
        check(ic is not None, "标题左侧有 16×16 图标")
        if ic:
            check(ic["w"] == 16 and ic["h"] == 16, f"图标 16×16（实得 {ic['w']}×{ic['h']}）")
            check(ic["x"] == 0, f"图标左缘 x=0（实得 {ic['x']}）")
            check(ic["y"] == -27, f"图标顶 = -27（行顶下 4px，实得 {ic['y']}）")
        tx = n0["text"]
        check(tx is not None, "存在标题文字 span")
        if tx:
            check(tx["y"] == -31, f"文字顶 = -31（顶对齐，非居中；实得 {tx['y']}）")
            check(tx["h"] == 24, f"文字高 24（22 行高 + 上下各 1px；实得 {tx['h']}）")
            check(tx["x"] == 20, f"文字左缘 x=20（16 图标 + gap 4；实得 {tx['x']}）")
            check(tx["pad"].replace(" ", "") == "1px0px", f"文字 padding 1px 0（实得 {tx['pad']}）")
            check(tx["fs"] == "13px", f"字号 13px（实得 {tx['fs']}）")
            check(tx["lh"] == "22px", f"行高 22px（实得 {tx['lh']}）")
            # 图标与文字互为中心对齐（中心都在 -19）
            if ic:
                check(
                    abs((ic["y"] + ic["h"] / 2) - (tx["y"] + tx["h"] / 2)) <= 0.6,
                    f"图标与文字中心对齐（{ic['y']+ic['h']/2} vs {tx['y']+tx['h']/2}）",
                )

        print("\n[3] 标签钮 `Add tags`")
        tag = n0["tag"]
        check(tag is not None, "存在 aria=Add tags 的标签钮")
        if tag:
            check(tag["w"] == 24 and tag["h"] == 24, f"标签钮 24×24（实得 {tag['w']}×{tag['h']}）")
            check(tag["y"] == -31, f"标签钮顶 = -31（实得 {tag['y']}）")
            check(tag["radius"] == "8px", f"圆角 8px（实得 {tag['radius']}）")
            check(tag["pad"].replace(" ", "") == "0px4px", f"padding 0 4px（实得 {tag['pad']}）")
            check(
                tag["cardW"] - tag["right"] == 1,
                f"右缘落在卡片右缘内侧 1px（卡片 {tag['cardW']} / 右缘 {tag['right']}）",
            )
        # 行为未回退：点开仍是五色选色盘
        if tag is not None:
            page.locator('.react-flow__node button[aria-label="Add tags"]').first.click()
            page.wait_for_timeout(600)
            n_colors = page.locator('.react-flow__node button[aria-label^="颜色标记"]').count()
            check(n_colors == 5, f"五色选色盘仍可打开（{n_colors} 个色钮）")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)

        page.screenshot(path=f"{SHOT}/clone-nodechrome.png")
        browser.close()

    print("\n[4] 源码一致性：7 个节点类型必须共用 nodeRingShadow()")
    for fn in NODE_FILES:
        p = REPO / "src/components/jimeng/nodes" / fn
        if not p.exists():
            check(False, f"{fn} 存在")
            continue
        s = p.read_text()
        uses = "nodeRingShadow(" in s
        literal = bool(re.search(r"0 0 0 1\.5px rgba\(255,255,255,0\.92\)", s))
        check(uses and not literal, f"{fn} 走 nodeRingShadow() 且无旧字面量",
              f"uses={uses} literal={literal}")

    p = REPO / "src/components/jimeng/nodeChrome.ts"
    check(p.exists(), "nodeChrome.ts 存在")
    if p.exists():
        s = p.read_text()
        check(
            'inset 0 0 0 1px rgba(255,255,255,0.2)' in s,
            "nodeChrome.ts 里未选中环是 white/20（不是旧的 0.06）",
        )
        check("0.2" in s and "0.06" not in s, "旧的 white/0.06 已从常量里消失")

    print(f"\n{'=' * 52}")
    if fails:
        print(f"FAIL —— {len(fails)}/{checks} 项不通过:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"PASS —— {checks}/{checks} 项全部通过")


if __name__ == "__main__":
    main()
