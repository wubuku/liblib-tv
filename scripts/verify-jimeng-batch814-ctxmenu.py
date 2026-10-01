"""Jimeng clone batch 814-ctxmenu verifier —— 画布右键菜单（项集 + 几何 + a11y）。

SOURCE_FACT batch 814 (2026-10-03 @1512×950 源站登录态，逐元素实测)：

  壳   200×292、padding 4、圆角 12、bg rgb(38,38,38)
  行   192×36 @x=4、padding 9px 12px、圆角 8
  文案 13px/22px 启用纯白、禁用 **rgba(255,255,255,0.2)**
  快捷 13px/22px rgba(255,255,255,0.6)，右缘 184
  7 项 + 1 分隔线：
      复制 ⌘C ｜复制副本 ⌘D ｜粘贴 ⌘V ｜——分隔线—— ｜下载 ｜重做 ⌘⇧Z ｜撤销 ⌘Z ｜删除 ⌫
  aria        = 文案本身
  title       = 启用时 `{文案} ({快捷键})`；禁用时**直接是禁用原因**
  禁用原因     = 另有一个 1×1 绝对定位隐藏 span，由 aria-describedby 指过去
  竖向账（与缩放菜单同款）：4 + 7×36 + 4 + 7×4 + 4 = 292 ✓

复刻此前：只有 4 项（新建节点/粘贴/重做/撤销）、192 宽、padding 8、行高 44，
且把「无需重做操作」当**正文**内联渲染 —— 把快捷键顶偏并溢出，是布局 bug。

本 verifier 的判据取舍：
- **不断言项数 == 7**。复刻侧刻意保留源站没有的「新建节点」子菜单
  （OPEN_QUESTION 814-a：删掉等于主动删 batch 25/221/808 建立的真插入通道）。
  改为断言**源站那 7 项按序全部存在**，允许克隆侧有额外项。
- **断言几何规则而非几何结果**：宽 200、pad 4、行高 36、行间隙 4、
  文案左内缩 12、快捷键右缘 184 —— 这些与项数无关，额外项不影响。
- 断言**分隔线只有一条且落在「粘贴」与「下载」之间**（源站语义位置）。
- 断言**禁用原因绝不进入 flex 流**：隐藏 span 必须是绝对定位且 1×1，
  否则快捷键会被顶偏（这正是旧实现的 bug）。
- 断言 `aria-describedby` 指向的隐藏 span 里确有原因文案（a11y 真的可达）。
"""

import re
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
SHOT = "docs/research/jimeng-canvas-batch814-2026-10-03"

# 源站 7 项：文案 + 快捷键（None = 源站该项无快捷键）
SOURCE_ITEMS = [
    ("复制", "⌘ C"),
    ("复制副本", "⌘ D"),
    ("粘贴", "⌘ V"),
    ("下载", None),
    ("重做", "⌘ ⇧ Z"),
    ("撤销", "⌘ Z"),
    ("删除", "⌫"),
]
DISABLED_REASONS = {
    "下载": "没有可用的就绪资源",
    "重做": "无需重做操作",
    "撤销": "无需撤销操作",
}

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


PROBE = """() => {
  const m = document.querySelector('[role="menu"]');
  if (!m) return { err: 'no menu' };
  const r = m.getBoundingClientRect();
  const cs = getComputedStyle(m);
  // 直接子节点顺序（含分隔线）
  const order = [...m.children].map(e => {
    if (e.getAttribute('role') === 'separator') return '__SEP__';
    const it = e.querySelector('[role="menuitem"]') || e;
    if (it.getAttribute('role') !== 'menuitem') return '__OTHER__';
    return (it.getAttribute('aria-label') || it.textContent || '').trim();
  });
  const items = [...m.querySelectorAll('[role="menuitem"]')].map(it => {
    const ir = it.getBoundingClientRect();
    const ics = getComputedStyle(it);
    const spans = [...it.querySelectorAll('span')].map(sp => {
      const sr = sp.getBoundingClientRect();
      const scs = getComputedStyle(sp);
      return { t: (sp.textContent || '').replace(/\\s+/g, ' ').trim(),
               x: Math.round(sr.left - r.left), w: Math.round(sr.width),
               h: Math.round(sr.height),
               color: scs.color, pos: scs.position, fs: scs.fontSize };
    });
    const db = it.getAttribute('aria-describedby');
    const hidden = db ? document.getElementById(db) : null;
    return {
      aria: it.getAttribute('aria-label') || '',
      title: it.getAttribute('title') || '',
      describedby: db || '',
      hiddenReason: hidden ? (hidden.textContent || '').trim() : '',
      hiddenBox: hidden
        ? (b => ({ w: Math.round(b.width), h: Math.round(b.height) }))(hidden.getBoundingClientRect())
        : null,
      disabled: it.disabled ? 1 : 0,
      x: Math.round(ir.left - r.left), y: Math.round(ir.top - r.top),
      w: Math.round(ir.width), h: Math.round(ir.height),
      radius: ics.borderRadius,
      labelColor: spans[0] ? spans[0].color : null,
      labelFS: spans[0] ? spans[0].fs : null,
      labelX: spans[0] ? spans[0].x : null,
      kbd: spans.length > 1 ? spans[1] : null,
      hiddenSpans: spans.filter(s => s.pos === 'absolute'),
      spans,
    };
  });
  const sep = m.querySelector('[role="separator"]');
  let sepInfo = null;
  if (sep) {
    const sr = sep.getBoundingClientRect();
    const line = sep.firstElementChild;
    const lr = line ? line.getBoundingClientRect() : null;
    sepInfo = { x: Math.round(sr.left - r.left), w: Math.round(sr.width),
                h: Math.round(sr.height),
                y: Math.round(sr.top - r.top),
                lineH: lr ? Math.round(lr.height) : -1,
                lineY: lr ? Math.round(lr.top - sr.top) : -1,
                lineW: lr ? Math.round(lr.width) : -1,
                lineBg: line ? getComputedStyle(line).backgroundColor : null };
  }
  return { w: Math.round(r.width), h: Math.round(r.height), pad: cs.padding,
           gap: cs.rowGap, radius: cs.borderRadius, bg: cs.backgroundColor,
           display: cs.display, order, items, sep: sepInfo,
           sepCount: m.querySelectorAll('[role="separator"]').length };
}"""


def open_menu(page):
    """在**保证空白**且**菜单能完整入屏**的角落右键，确认弹出的是**画布**菜单。

    两个坑都踩过：
    - 直接点画布中心 → 粘贴出来的节点可能正好落在中心，右键变成节点右键，
      弹出的也是 role=menu 但没有这些项，上一版就是这么超时的。
    - 点太靠下 → 菜单 292 高会溢出 950 视口，最后一项「删除」永远点不到。
    所以这里在一组候选点里依次试，取第一个能弹出画布菜单、且菜单底边在视口内的。
    """
    box = page.locator(".react-flow").first.bounding_box()
    vh = page.viewport_size["height"]
    cands = [(0.10, 0.12), (0.12, 0.30), (0.50, 0.10), (0.80, 0.12), (0.10, 0.55)]
    for fx, fy in cands:
        # 注意：**不要**先按 Escape 来"清场" —— Escape 会取消节点选中，
        # 于是 复制/复制副本/删除 全变灰，右键菜单也就测不到"选中后解禁"了。
        # 右键本身就会把上一个菜单换成新位置，无需清场。
        page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy, button="right")
        try:
            page.wait_for_selector('[role="menu"] [role="menuitem"][aria-label="复制副本"]', timeout=4000)
        except Exception:
            continue
        m = page.locator('[role="menu"]').first.bounding_box()
        if m and m["y"] + m["height"] <= vh - 4:
            page.wait_for_timeout(400)
            return
    raise AssertionError("找不到既能弹出画布菜单、菜单又完整入屏的空白点")


def main() -> None:
    wait_server()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1512, "height": 950})
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector(".react-flow__node", timeout=45000)
        page.wait_for_timeout(2500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        print("\n[1] 菜单壳几何（与缩放菜单同一套）")
        open_menu(page)
        g = page.evaluate(PROBE)
        if g.get("err"):
            check(False, "右键能弹出菜单", g["err"])
            browser.close()
            sys.exit(1)
        check(g["w"] == 200, f"菜单宽 200（实得 {g['w']}）")
        check(g["pad"].startswith("4px"), f"内边距 4px（实得 {g['pad']}）")
        check(g["radius"] == "12px", f"圆角 12px（实得 {g['radius']}）")
        check(g["bg"] == "rgb(38, 38, 38)", f"底色 rgb(38,38,38)（实得 {g['bg']}）")
        check(g["gap"] == "4px", f"行间隙 4px（实得 {g['gap']}）")

        print("\n[2] 源站 7 项按序全部存在（允许克隆侧有额外项）")
        by_aria = {}
        for it in g["items"]:
            by_aria.setdefault(it["aria"], []).append(it)
        present = [lbl for lbl, _ in SOURCE_ITEMS if lbl in by_aria]
        missing = [lbl for lbl, _ in SOURCE_ITEMS if lbl not in by_aria]
        check(not missing, "源站 7 项全部在列", f"缺 {missing}")
        # 按序：每项在 order 里的下标必须单调递增
        idx = []
        for lbl, _ in SOURCE_ITEMS:
            hits = [i for i, v in enumerate(g["order"]) if v == lbl]
            idx.append(hits[0] if hits else -1)
        check(
            all(v >= 0 for v in idx) and idx == sorted(idx),
            f"7 项相对顺序与源站一致（源站序：复制→复制副本→粘贴→下载→重做→撤销→删除）",
            f"下标 {idx}",
        )

        print("\n[3] 每项几何：192×36 @x=4、圆角 8、文案 13px 左内缩 12")
        for lbl, sc in SOURCE_ITEMS:
            if lbl not in by_aria:
                continue
            it = by_aria[lbl][0]
            check(it["h"] == 36, f"{lbl} 行高 36（实得 {it['h']}）")
            check(it["w"] == 192, f"{lbl} 行宽 192（实得 {it['w']}）")
            check(it["x"] == 4, f"{lbl} 行左缘 x=4（实得 {it['x']}）")
            check(it["radius"] == "8px", f"{lbl} 圆角 8px（实得 {it['radius']}）")
            check(it["labelFS"] == "13px", f"{lbl} 文案 13px（实得 {it['labelFS']}）")
            # 文案 span 的 x 是**相对菜单**量的：4(菜单内边距) + 12(行内边距) = 16
            # （batch 811 的缩放菜单 verifier 用的是相对**行盒**的 12，两处都对，别混）
            check(it["labelX"] == 16, f"{lbl} 文案左缘 x=16（菜单基准；实得 {it['labelX']}）")
            if sc:
                kbd = it["kbd"]
                check(
                    kbd is not None and kbd["t"] == sc,
                    f"{lbl} 快捷键 = {sc!r}（实得 {None if not kbd else kbd['t']!r}）",
                )
                # 源站实测快捷键 span 右缘 = 184（= 192 行宽 − 8）
                check(
                    kbd is not None and kbd["x"] + kbd["w"] == 184,
                    f"{lbl} 快捷键右缘 184（实得 {None if not kbd else kbd['x']+kbd['w']}）",
                )

        print("\n[4] 禁用态契约：white/20 + title 是原因 + aria-describedby 指向 1×1 隐藏 span")
        # 源站 fixture 里 下载/重做/撤销 都禁用，但那是**内容态**造成的
        # （源站画布上没有可用资源、也没有历史）。复刻 demo 有带媒体节点，
        # 所以「下载」在这里应当是**启用**的 —— 不能照抄源站的启用态，
        # 要断言的是「禁用时这套契约成立」，门控本身在 [6] 单独验。
        for lbl, reason in DISABLED_REASONS.items():
            if lbl not in by_aria:
                check(False, f"{lbl} 在列")
                continue
            it = by_aria[lbl][0]
            if it["disabled"] != 1:
                print(f"  · {lbl} 当前启用（内容态使然），跳过其禁用契约")
                continue
            check(
                it["labelColor"] and "0.2" in it["labelColor"],
                f"{lbl} 文案 white/20（实得 {it['labelColor']}）",
            )
            check(it["title"] == reason, f"{lbl} title = {reason!r}（实得 {it['title']!r}）")
            check(bool(it["describedby"]), f"{lbl} 带 aria-describedby")
            check(
                it["hiddenReason"] == reason,
                f"{lbl} 隐藏 span 里确有原因文案（实得 {it['hiddenReason']!r}）",
            )
            check(
                it["hiddenBox"] is not None
                and it["hiddenBox"]["w"] <= 1
                and it["hiddenBox"]["h"] <= 1,
                f"{lbl} 原因 span 是 1×1（实得 {it['hiddenBox']}）",
            )
            # 关键：隐藏 span 必须绝对定位，否则会进 flex 流把快捷键顶偏
            check(
                bool(it["hiddenSpans"]),
                f"{lbl} 原因 span 是 absolute（不进 flex 流）",
                f"实得 pos={[s['pos'] for s in it['spans']]}",
            )
            # 禁用项的快捷键右缘不能被"内联原因"顶偏
            if it["kbd"] and it["kbd"]["t"]:
                check(
                    it["kbd"]["x"] + it["kbd"]["w"] == 184,
                    f"{lbl} 快捷键未被内联原因顶偏（右缘 184，实得 {it['kbd']['x']+it['kbd']['w']}）",
                )

        print("\n[5] 分隔线：恰好一条，落在「粘贴」与「下载」之间")
        check(g["sepCount"] == 1, f"分隔线恰好 1 条（实得 {g['sepCount']}）")
        sep = g["sep"]
        check(sep is not None, "分隔线元素存在")
        if sep:
            check(sep["w"] == 168, f"分隔线宽 168（左右各内缩 12；实得 {sep['w']}）")
            check(sep["h"] == 4, f"分隔线盒高 4（实得 {sep['h']}）")
            check(sep["lineH"] == 1, f"盒内线 1px（实得 {sep['lineH']}）")
            check(sep["lineY"] == 2, f"线在盒顶 +2（实得 {sep['lineY']}）")
            check(sep["lineW"] == 168, f"线宽撑满（实得 {sep['lineW']}）")
        seps = [i for i, v in enumerate(g["order"]) if v == "__SEP__"]
        if seps:
            prev_label = g["order"][seps[0] - 1] if seps[0] > 0 else None
            next_label = g["order"][seps[0] + 1] if seps[0] + 1 < len(g["order"]) else None
            check(
                next_label == "下载",
                f"分隔线之后是「下载」（实得 {next_label!r}；克隆侧首项为额外的「新建节点」）",
            )
            check(
                prev_label == "粘贴",
                f"分隔线之前是「粘贴」（实得 {prev_label!r}）",
            )

        page.screenshot(path=f"{SHOT}/clone-ctxmenu.png")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        print("\n[6] 行为：新补的四项必须真接上（不接受画完不接的空壳）")
        def n_nodes() -> int:
            return page.locator(".react-flow__node").count()

        def select_first_node() -> int:
            nb = page.locator(".react-flow__node").first.bounding_box()
            page.mouse.click(nb["x"] + min(200, nb["width"] / 2), nb["y"] + 20)
            page.wait_for_timeout(800)
            return page.locator(".react-flow__node.selected").count()

        # 选中一个节点 → 复制/复制副本/删除 解禁
        sel_n = select_first_node()
        check(sel_n >= 1, f"已选中 {sel_n} 个节点")
        open_menu(page)
        g2 = page.evaluate(PROBE)
        by2 = {it["aria"]: it for it in g2["items"]}
        for lbl in ("复制", "复制副本", "删除"):
            check(
                lbl in by2 and by2[lbl]["disabled"] == 0,
                f"选中后「{lbl}」解禁",
                f"实得 {by2.get(lbl, {}).get('disabled')}",
            )

        # 「复制」：只写剪贴板，节点数不变 —— 且它是后续「粘贴」的前置
        n0 = n_nodes()
        page.locator('[role="menu"] [role="menuitem"][aria-label="复制"]').first.click()
        page.wait_for_timeout(900)
        check(n_nodes() == n0, f"「复制」不改节点数（{n0} → {n_nodes()}）")

        # 「粘贴」：此时剪贴板非空
        open_menu(page)
        g3 = page.evaluate(PROBE)
        paste_item = next((i for i in g3["items"] if i["aria"] == "粘贴"), None)
        check(
            paste_item is not None and paste_item["disabled"] == 0,
            "复制之后「粘贴」解禁",
            f"实得 {None if not paste_item else paste_item['disabled']}",
        )
        n1 = n_nodes()
        page.locator('[role="menu"] [role="menuitem"][aria-label="粘贴"]').first.click()
        page.wait_for_timeout(900)
        check(n_nodes() == n1 + 1, f"「粘贴」加了 1 个节点（{n1} → {n_nodes()}）")

        # 「复制副本」：直接加节点
        select_first_node()
        n2 = n_nodes()
        open_menu(page)
        page.locator('[role="menu"] [role="menuitem"][aria-label="复制副本"]').first.click()
        page.wait_for_timeout(900)
        check(n_nodes() == n2 + 1, f"「复制副本」加了 1 个节点（{n2} → {n_nodes()}）")

        # 「删除」：删掉选中的
        sel_before = select_first_node()
        n3 = n_nodes()
        open_menu(page)
        page.locator('[role="menu"] [role="menuitem"][aria-label="删除"]').first.click()
        page.wait_for_timeout(900)
        check(
            n_nodes() == n3 - sel_before,
            f"「删除」删掉了 {sel_before} 个选中节点（{n3} → {n_nodes()}）",
        )
        # 复原到初始 2 节点
        for _ in range(10):
            if page.locator(".react-flow__node").count() <= 2:
                break
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(500)
        final_n = page.locator(".react-flow__node").count()
        check(final_n == 2, f"已撤销回初始 2 节点（实得 {final_n}）")

        print("\n[6b] 「下载」的门控：画布上没有任何带媒体节点时应禁用并给出原因")
        # 源站把「下载」禁用的原因写得很直白：「没有可用的就绪资源」。
        # 复刻的门控取其字面意思：没有带媒体的节点 → 禁用。
        # 这里把节点全删掉来真验一次门控，再 ⌘Z 复原。
        page.keyboard.press("Meta+a")
        page.wait_for_timeout(700)
        sel_all = page.locator(".react-flow__node.selected").count()
        check(sel_all >= 1, f"⌘A 全选了 {sel_all} 个节点")
        n_before = n_nodes()
        # 走菜单自己的删除通道（已验过），不用键盘 —— 复刻的删除键不认 Backspace
        open_menu(page)
        page.locator('[role="menu"] [role="menuitem"][aria-label="删除"]').first.click()
        page.wait_for_timeout(1000)
        n_empty = n_nodes()
        check(n_empty < n_before, f"已清空画布（{n_before} → {n_empty}）")
        open_menu(page)
        g4 = page.evaluate(PROBE)
        dl = next((i for i in g4["items"] if i["aria"] == "下载"), None)
        check(
            dl is not None and dl["disabled"] == 1,
            "无带媒体节点时「下载」禁用",
            f"实得 {None if not dl else dl['disabled']}",
        )
        if dl and dl["disabled"] == 1:
            check(
                dl["title"] == "没有可用的就绪资源",
                f"「下载」title = 源站原因文案（实得 {dl['title']!r}）",
            )
            check(dl["hiddenReason"] == "没有可用的就绪资源", "「下载」原因进了隐藏 span + aria-describedby")
            check(
                dl["labelColor"] and "0.2" in dl["labelColor"],
                f"「下载」禁用文案 white/20（实得 {dl['labelColor']}）",
            )
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        for _ in range(10):
            if page.locator(".react-flow__node").count() >= 2:
                break
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(500)
        back_n = page.locator(".react-flow__node").count()
        check(back_n == 2, f"已 ⌘Z 复原回 2 节点（实得 {back_n}）")

        browser.close()

    print("\n[7] 源码一致性：两处菜单必须共用 jimengMenuChrome")
    def code_only(path: Path) -> str:
        """只看代码行：注释里出现的旧值（如「此前是 w-48 p-2」）不算残留。"""
        lines = []
        for ln in path.read_text().split("\n"):
            s = ln.strip()
            if s.startswith("*") or s.startswith("//") or s.startswith("/*"):
                continue
            lines.append(ln.split("//")[0] if "//" in ln and "http" not in ln else ln)
        return "\n".join(lines)

    ctx = code_only(REPO / "src/components/jimeng/JimengPaneContextMenu.tsx")
    zoom = code_only(REPO / "src/components/jimeng/JimengZoomMenu.tsx")
    for name, src in (("右键菜单", ctx), ("缩放菜单", zoom)):
        check("jimengMenuChrome" in src, f"{name} 引用 jimengMenuChrome")
        check("MENU_PANEL_CLASS" in src, f"{name} 用共享面板类")
        check("MenuItem" in src, f"{name} 用共享 MenuItem")
        check(
            "w-48" not in src and "p-2" not in src,
            f"{name} 不再自带 192 宽 / padding 8 的旧壳",
        )
        check("h-11" not in src, f"{name} 不再残留 44px 旧行高")
    check(
        (REPO / "src/components/jimeng/jimengMenuChrome.tsx").exists(),
        "jimengMenuChrome.tsx 存在",
    )
    zoom_src = (REPO / "src/components/jimeng/JimengZoomMenu.tsx").read_text()
    check(
        "无法重做操作" not in zoom_src,
        "旧的行内禁用原因文案已不在缩放菜单里",
    )

    print(f"\n{'=' * 52}")
    if fails:
        print(f"FAIL —— {len(fails)}/{checks} 项不通过:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"PASS —— {checks}/{checks} 项全部通过")


if __name__ == "__main__":
    main()
