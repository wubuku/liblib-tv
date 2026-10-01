"""Jimeng clone batch 813-nodetitle verifier —— 节点标题的重命名按钮与左簇几何。

SOURCE_FACT batch 813 (2026-10-03 @1512×950 源站登录态，**两侧归到 100% 缩放**，
坐标一律相对卡片左上角、以 `.react-flow__viewport` 变换矩阵归一化后取整)：

## 1. 重命名入口是一个真按钮，不是裸文字
  选中态 `<button aria-label="Rename 视频 1">` **36×32 @ (20,-31)**、圆角 8、
  padding 0；盒内文字 span 36×24 @ (20,-31)（22 行高 + 上下各 1px）。
  **未选中时该按钮不渲染**（只剩 DIV + SPAN）。
  复刻此前只有裸 span：重命名行为在（batch 88），但缺这个按钮与它的实名。

## 2. 标题行左簇的三个数
  图标 16×16 @ (0,**-27**) —— 比行顶低 4px，与文字**中心**对齐（中心同为 -19）
  文字   @ (20,-31) —— 16(图标) + 4(gap)，所以左簇 gap 必须是 4
  行盒   32 高，顶在 -31
  推论：左簇必须 `items-start` 顶对齐，图标自己 `mt-1`。
  若用 `items-center`，图标会落到 -23（差 4px）；若 gap 不是 4，文字起点不是 20。

## 3. 保留复刻侧"点开输入框"的行为
  源站现状：连点该按钮 3 次都**不弹**内联输入框，只取焦（activeElement 停在按钮上）。
  复刻保留点开输入框 —— 照抄一个点不动的按钮等于主动删功能。
  差异记为 OPEN_QUESTION 813-a，本 verifier 反过来守住"别退化成死按钮"。

本 verifier 只跑复刻侧。宽度**不**断言 36 —— 源站那条是「视频 1」四个字，
复刻的标题是长文件名，宽由内容决定，断言绝对宽度会把 mock 文本变成脆依赖。
高度 / y / x / 圆角 / 实名 / 挂载条件才是结构性的，逐条断言。
"""

import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
SHOT = "docs/research/jimeng-canvas-batch813-2026-10-03"

fails: list[str] = []
checks = 0


def check(cond: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    print(f"  {'✓' if cond else '✗'} {label}" + ("" if cond else f"  {detail}"))
    if not cond:
        fails.append(f"{label}  {detail}")


def wait_server() -> None:
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


PROBE = """(idx) => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const n = nodes[idx];
  if (!n) return { err: 'no node' };
  const r = n.getBoundingClientRect();
  const vp = document.querySelector('.react-flow__viewport');
  const z = vp ? new DOMMatrixReadOnly(getComputedStyle(vp).transform).a : 1;
  const box = (e) => { if (!e) return null; const b = e.getBoundingClientRect();
    return { x: Math.round((b.left - r.left) / z), y: Math.round((b.top - r.top) / z),
             w: Math.round(b.width / z), h: Math.round(b.height / z) }; };
  const btn = n.querySelector('button[aria-label^="Rename"]');
  const span = n.querySelector('[data-testid="node-title-text"]');
  const row = n.querySelector('div[class*="top-[-31px]"]');
  // 左簇 = 标题行的那个 flex 子盒（视频/音频节点里它与行容器不是同一个元素，
  // 所以不能拿 row 的 gap 当左簇的 gap —— 踩过一次）
  const cluster = row ? (row.querySelector('div[class*="items-start"]') || row) : null;
  // 图标 = 左簇里的第一个 <svg>（不能靠 span.previousElementSibling：
  // 选中态时 span 藏在 button 里，previousElementSibling 是 null）
  const ic = cluster ? cluster.querySelector('svg') : null;
  const tags = n.querySelector('button[aria-label="Add tags"]');
  return {
    selected: n.classList.contains('selected'),
    zoom: Math.round(z * 100) / 100,
    title: (span ? span.textContent : '') || '',
    btn: btn ? { ...box(btn), aria: btn.getAttribute('aria-label'),
                 radius: getComputedStyle(btn).borderRadius,
                 pad: getComputedStyle(btn).padding,
                 tag: btn.tagName } : null,
    span: span ? box(span) : null,
    spanPad: span ? getComputedStyle(span).padding : null,
    icon: ic ? box(ic) : null,
    row: row ? { ...box(row), align: getComputedStyle(row).alignItems } : null,
    cluster: cluster && cluster !== row
      ? { ...box(cluster), gap: getComputedStyle(cluster).gap,
          align: getComputedStyle(cluster).alignItems } : null,
    tagBtn: tags ? box(tags) : null,
  };
}"""


def main() -> None:
    wait_server()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1512, "height": 950})
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector(".react-flow__node", timeout=45000)
        page.wait_for_timeout(2500)
        page.locator('[data-testid="canvas-zoom-percent"]').first.focus()
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(1200)

        print("\n[0] 缩放归一化")
        z = page.evaluate(
            """() => { const v=document.querySelector('.react-flow__viewport');
                       return Math.round(new DOMMatrixReadOnly(getComputedStyle(v).transform).a*1000)/10; }"""
        )
        check(z == 100, f"当前缩放 = 100%（实得 {z}）")
        n_nodes = page.locator(".react-flow__node").count()
        check(n_nodes >= 2, f"画布上至少 2 个节点（{n_nodes}）")

        # ---------- 未选中 ----------
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)
        print("\n[1] 未选中态：重命名按钮必须**不渲染**")
        for i in range(n_nodes):
            d = page.evaluate(PROBE, i)
            if d.get("err"):
                continue
            check(not d["selected"], f"节点{i+1} 未选中")
            check(d["btn"] is None, f"节点{i+1} 无 Rename 按钮", f"实得 {d['btn']}")
            check(d["span"] is not None, f"节点{i+1} 仍有标题文字")
            if d["span"]:
                check(d["span"]["y"] == -31, f"节点{i+1} 文字顶 = -31（实得 {d['span']['y']}）")
                check(d["span"]["h"] == 24, f"节点{i+1} 文字高 24（实得 {d['span']['h']}）")
                check(d["span"]["x"] == 20, f"节点{i+1} 文字左缘 x=20（实得 {d['span']['x']}）")
                check(
                    (d["spanPad"] or "").replace(" ", "") == "1px0px",
                    f"节点{i+1} 文字 padding 1px 0（实得 {d['spanPad']}）",
                )

        print("\n[2] 标题行左簇几何（未选中即可量）")
        d0 = page.evaluate(PROBE, 0)
        check(d0["row"] is not None, "存在标题行容器")
        if d0["row"]:
            check(d0["row"]["y"] == -31, f"行盒顶 = -31（实得 {d0['row']['y']}）")
            check(d0["row"]["h"] == 32, f"行盒高 32（实得 {d0['row']['h']}）")
            check(
                d0["row"]["align"] == "flex-start",
                f"行盒 items-start（顶对齐，实得 {d0['row']['align']}）",
            )
        cl = d0["cluster"]
        check(cl is not None, "标题行里有独立的左簇盒（gap 挂在这里，不是行盒上）")
        if cl:
            check(
                cl["gap"].replace(" ", "") == "4px",
                f"左簇 gap = 4px（文字起点 x=20 的来源；实得 {cl['gap']!r}）",
            )
            check(
                cl["align"] == "flex-start",
                f"左簇 items-start（顶对齐到行顶；实得 {cl['align']}）",
            )
        ic = d0["icon"]
        check(ic is not None, "标题左侧有 16×16 图标")
        if ic:
            check(ic["w"] == 16 and ic["h"] == 16, f"图标 16×16（实得 {ic['w']}×{ic['h']}）")
            check(ic["x"] == 0, f"图标左缘 x=0（实得 {ic['x']}）")
            check(ic["y"] == -27, f"图标顶 = -27（行顶下 4px，实得 {ic['y']}）")
            if d0["span"]:
                check(
                    abs((ic["y"] + ic["h"] / 2) - (d0["span"]["y"] + d0["span"]["h"] / 2)) <= 0.6,
                    f"图标与文字中心对齐（{ic['y']+ic['h']/2} vs {d0['span']['y']+d0['span']['h']/2}）",
                )

        # ---------- 选中 ----------
        nb = page.locator(".react-flow__node").first.bounding_box()
        page.mouse.click(nb["x"] + min(200, nb["width"] / 2), nb["y"] + 20)
        page.wait_for_timeout(900)
        print("\n[3] 选中态：必须渲染 `<button aria-label=\"Rename {标题}\">`")
        d1 = page.evaluate(PROBE, 0)
        check(d1["selected"], "节点已选中")
        b = d1["btn"]
        check(b is not None, "存在 Rename 按钮", "未找到")
        if b:
            check(b["tag"] == "BUTTON", f"是 <button> 而非 span（实得 {b['tag']}）")
            check(
                b["aria"] == f"Rename {d1['title']}",
                f"实名 = Rename {d1['title']!r}（实得 {b['aria']!r}）",
            )
            check(b["h"] == 32, f"按钮高 32（实得 {b['h']}）")
            check(b["y"] == -31, f"按钮顶 = -31（实得 {b['y']}）")
            check(b["x"] == 20, f"按钮左缘 x=20（与文字同左，实得 {b['x']}）")
            check(b["radius"] == "8px", f"圆角 8px（实得 {b['radius']}）")
            check(b["pad"].replace(" ", "") == "0px", f"padding 0（实得 {b['pad']}）")
            # 按钮盒内的文字仍顶对齐、高 24
            if d1["span"]:
                check(
                    d1["span"]["y"] == b["y"],
                    f"盒内文字与按钮同顶（文字 {d1['span']['y']} vs 按钮 {b['y']}）",
                )
                check(d1["span"]["h"] == 24, f"盒内文字高仍 24（实得 {d1['span']['h']}）")
        # 未选中的兄弟节点不该有按钮
        if n_nodes >= 2:
            d2 = page.evaluate(PROBE, 1)
            check(d2["btn"] is None, "未选中的兄弟节点无 Rename 按钮（多选判定按节点）")

        print("\n[4] 行为不退回：点按钮应打开内联输入框，Enter 提交")
        old_title = d1["title"]
        page.locator('.react-flow__node button[aria-label^="Rename"]').first.click()
        page.wait_for_timeout(600)
        has_input = page.evaluate(
            """() => {
              const n = document.querySelector('.react-flow__node.selected');
              const i = n && n.querySelector('input[data-testid="node-rename-input"]');
              return !!i;
            }"""
        )
        check(has_input, "点 Rename 打开内联输入框（不是死按钮）")
        if has_input:
            focused = page.evaluate("() => document.activeElement.tagName")
            check(focused == "INPUT", f"输入框自动聚焦（实得 {focused}）")
            page.keyboard.press("Meta+a")
            page.keyboard.type("视频 改名验收")
            page.keyboard.press("Enter")
            page.wait_for_timeout(800)
            now = page.evaluate(PROBE, 0)
            check(now["title"] == "视频 改名验收", f"Enter 提交改名（实得 {now['title']!r}）")
            check(
                now["btn"] is not None and now["btn"]["aria"] == "Rename 视频 改名验收",
                f"实名随标题更新（实得 {None if not now['btn'] else now['btn']['aria']!r}）",
            )
            # 复原
            page.locator('.react-flow__node button[aria-label^="Rename"]').first.click()
            page.wait_for_timeout(500)
            if page.evaluate("() => document.activeElement.tagName") == "INPUT":
                page.keyboard.press("Meta+a")
                page.keyboard.type(old_title)
                page.keyboard.press("Enter")
                page.wait_for_timeout(700)
            back = page.evaluate(PROBE, 0)
            check(back["title"] == old_title, f"已复原标题（实得 {back['title']!r}）")

        page.screenshot(path=f"{SHOT}/clone-nodetitle.png")
        browser.close()

    print(f"\n{'=' * 52}")
    if fails:
        print(f"FAIL —— {len(fails)}/{checks} 项不通过:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"PASS —— {checks}/{checks} 项全部通过")


if __name__ == "__main__":
    main()
