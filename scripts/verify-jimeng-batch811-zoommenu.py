"""Jimeng clone batch 811-zoommenu verifier —— 底部 dock 缩放菜单。

SOURCE_FACT batch 811 (2026-10-03 @1512×950 源站登录态实测，扁平化菜单子树逐元素量得):

  菜单壳   200×292、padding 4、radius 12、bg rgb(38,38,38)
  7 项     放大视图 ⌘+ ｜缩小视图 ⌘- ｜适配画布 ⇧1 ｜缩放至选中项 ⇧2
           ｜separator｜缩放至50% ｜缩放至100% ⌘1 ｜缩放至200%
  竖向     8(边距) + 7×36(行高) + 4(分隔线) + 7×4(flex gap-1) = 292
  行       padding 9px 12px、圆角 8、x=4 w=192、文案左内缩 12
  文字     文案 13px/20px 纯白；快捷键 13px/20px white/60、右缘 x=180
  悬停     white/8
  分隔线   1px、左右 margin 12 → 宽 168、白色 4%（实测 rgb(47,47,47) @ rgb(38,38,38)）
  禁用     无选中时「缩放至选中项」disabled，title 文案「请先选择至少一个画布元素」

本 verifier 只跑复刻侧。断言以**相对量**为主（总高由行高/间隙/边距推出、行间
等距、分隔线宽度由左右内缩推出），少写死绝对 x，避免脆断。

另含一条**功能**断言：⌘+ / ⌘- 两枚新项必须真的接上 xyflow（步长 1.2，
与源站实测 50 → 83.3 → 100 一致），不接受只画不接的空壳。
"""

import math
import re
import sys

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"

EXPECTED_ROWS = [
    ("放大视图", "⌘ +"),
    ("缩小视图", "⌘ -"),
    ("适配画布", "⇧ 1"),
    ("缩放至选中项", "⇧ 2"),
    ("缩放至50%", None),
    ("缩放至100%", "⌘ 1"),
    ("缩放至200%", None),
]

DISABLED_TITLE = "请先选择至少一个画布元素"

fails: list[str] = []
checks = 0


# --- 颜色归一化 -----------------------------------------------------------
# 源站发 `rgba(255,255,255,0.6)`，而复刻侧 Tailwind v4 发
# `oklab(0.999994 ... / 0.6)` —— 两者是同一个颜色，只是记法不同。
# 直接字符串比对会误判，故一律归一到 sRGB + alpha 再比。
def _srgb_from_oklab(L: float, a: float, b: float) -> tuple[int, int, int]:
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    bb = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_

    def enc(c: float) -> int:
        c = 0.0 if c < 0 else (1.0 if c > 1 else c)
        return round((c ** (1 / 2.4) if c > 0.0031308 else c * 12.92) * 255)

    return enc(r), enc(g), enc(bb)


_NUM = r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"


def parse_color(v: str) -> tuple[int, int, int, float] | None:
    """把 rgb()/rgba()/oklab() 归一成 (r,g,b,a)；解析不了返回 None。"""
    v = (v or "").strip()
    if not v or v == "rgba(0, 0, 0, 0)" and False:
        return None
    m = re.match(rf"rgba?\(\s*({_NUM})[,\s]+({_NUM})[,\s]+({_NUM})(?:[,/\s]+({_NUM}))?\s*\)", v)
    if m:
        r, g, b = (round(float(m.group(i))) for i in (1, 2, 3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return (r, g, b, round(a, 3))
    m = re.match(
        rf"oklab\(\s*({_NUM})\s+({_NUM})\s+({_NUM})\s*(?:/\s*({_NUM}))?\s*\)", v
    )
    if m:
        r, g, b = _srgb_from_oklab(
            float(m.group(1)), float(m.group(2)), float(m.group(3))
        )
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return (r, g, b, round(a, 3))
    return None


def color_eq(got: str, want: tuple[int, int, int, float], tol: int = 2) -> bool:
    p = parse_color(got)
    if p is None:
        return False
    return (
        all(abs(p[i] - want[i]) <= tol for i in range(3))
        and abs(p[3] - want[3]) <= 0.02
    )


WHITE_60 = (255, 255, 255, 0.60)
WHITE_04 = (255, 255, 255, 0.04)
WHITE_08 = (255, 255, 255, 0.08)
WHITE_20 = (255, 255, 255, 0.20)
WHITE = (255, 255, 255, 1.0)
MENU_BG = (38, 38, 38, 1.0)


def check(cond: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if cond:
        print(f"  ✓ {label}")
    else:
        print(f"  ✗ {label}  {detail}")
        fails.append(f"{label}  {detail}")


def wait_server(pw, tries: int = 12) -> "Page":  # type: ignore[name-defined]
    """共享 dev server 会被并行 session 反复重启 —— 连续 3 次 200 才开跑。"""
    import time
    import urllib.request

    ok = 0
    for _ in range(tries):
        try:
            with urllib.request.urlopen(URL, timeout=5) as r:
                if r.status == 200:
                    ok += 1
                    if ok >= 3:
                        break
                else:
                    ok = 0
        except Exception:
            ok = 0
        time.sleep(2)
    if ok < 3:
        print("!! dev server 连续 3 次 200 未达成，跳过本轮验收")
        sys.exit(2)

    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1512, "height": 950})
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector('[data-testid="dock-zoom"]', timeout=45000)
    page.wait_for_timeout(2500)
    return page


def open_menu(page) -> None:
    page.locator('[data-testid="dock-zoom"]').first.click()
    page.wait_for_selector('[role="menu"]', timeout=10000)
    page.wait_for_timeout(500)


def close_menu(page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    if page.locator('[role="menu"]').count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(350)


def zoom_of(page) -> float:
    return page.evaluate(
        """() => {
          const vp = document.querySelector('.react-flow__viewport');
          if (!vp) return -1;
          const m = new DOMMatrixReadOnly(getComputedStyle(vp).transform);
          return Math.round(m.a * 1000) / 10;
        }"""
    )


def main() -> None:
    with sync_playwright() as pw:
        page = wait_server(pw)

        print("\n[1] 菜单项内容与顺序")
        open_menu(page)
        items = page.locator('[role="menu"] [role="menuitem"]')
        n = items.count()
        check(n == 7, f"共 7 项（实得 {n}）", f"期望 7，实得 {n}")
        if n == 7:
            for i, (label, shortcut) in enumerate(EXPECTED_ROWS):
                el = items.nth(i)
                got_label = el.locator("span").first.inner_text().strip()
                spans = el.locator("span")
                got_sc = spans.nth(1).inner_text().strip() if spans.count() > 1 else ""
                check(
                    got_label == label,
                    f"第 {i+1} 项文案 = {label}",
                    f"实得 {got_label!r}",
                )
                check(
                    got_sc == (shortcut or ""),
                    f"第 {i+1} 项快捷键 = {shortcut or '(无)'}",
                    f"实得 {got_sc!r}",
                )

        print("\n[2] 菜单壳几何")
        geo = page.evaluate(
            """() => {
              const m = document.querySelector('[role="menu"]');
              const r = m.getBoundingClientRect();
              const cs = getComputedStyle(m);
              const rows = [...m.querySelectorAll('[role="menuitem"]')].map(e => {
                const rr = e.getBoundingClientRect();
                const rc = getComputedStyle(e);
                const sp = e.querySelector('span');
                const sr = sp ? sp.getBoundingClientRect() : null;
                const scs = sp ? getComputedStyle(sp) : null;
                const kbd = e.querySelectorAll('span')[1];
                const kcs = kbd ? getComputedStyle(kbd) : null;
                return { h: rr.height, w: rr.width, x: rr.left - r.left, pad: rc.padding,
                         radius: rc.borderRadius,
                         label: sp ? scs.color : null, labelFS: sp ? scs.fontSize : null,
                         labelX: sr ? sr.left - rr.left : null, labelLH: sp ? scs.lineHeight : null,
                         kbdColor: kcs ? kcs.color : null, kbdFS: kcs ? kcs.fontSize : null,
                         kbdRight: kbd ? Math.round(kbd.getBoundingClientRect().right - r.left) : null,
                         disabled: e.disabled };
              });
              const sepEl = m.querySelector('[role="separator"]');
              let sep = null;
              if (sepEl) {
                const s = sepEl.getBoundingClientRect();
                // 源站：4px 盒 + top:2px 的 1px 伪元素线（线色从像素采样 = rgb(47,47,47) = white/4）
                const line = sepEl.firstElementChild;
                const lr = line ? line.getBoundingClientRect() : null;
                sep = { x: Math.round(s.left - r.left), w: Math.round(s.width), h: Math.round(s.height),
                        bg: getComputedStyle(sepEl).backgroundColor,
                        lineH: lr ? Math.round(lr.height) : -1,
                        lineY: lr ? Math.round(lr.top - s.top) : -1,
                        lineW: lr ? Math.round(lr.width) : -1,
                        lineBg: line ? getComputedStyle(line).backgroundColor : null };
              }
              return { w: Math.round(r.width), h: Math.round(r.height), pad: cs.padding,
                       radius: cs.borderRadius, bg: cs.backgroundColor,
                       display: cs.display, rowGap: cs.rowGap, rows, sep,
                       sepIdx: sepEl ? [...m.children].indexOf(sepEl) : -1,
                       kids: [...m.children].length };
            }"""
        )
        check(geo["w"] == 200, f"菜单宽 200（实得 {geo['w']}）")
        check(geo["radius"] == "12px", f"圆角 12px（实得 {geo['radius']}）")
        check(
            color_eq(geo["bg"], MENU_BG),
            f"底色 rgb(38,38,38)（实得 {geo['bg']}）",
        )
        check(geo["pad"].startswith("4px"), f"内边距 4px（实得 {geo['pad']}）")
        check(geo["rowGap"] == "4px", f"行间隙 gap-1 = 4px（实得 {geo['rowGap']}）")

        rows = geo["rows"]
        if len(rows) == 7:
            heights = {r["h"] for r in rows}
            check(heights == {36}, f"七项行高全为 36（实得 {sorted(heights)}）")
            check(
                all(r["w"] == 192 for r in rows),
                "七项行宽全为 192（= 200 − 左右各 4）",
                str([r["w"] for r in rows]),
            )
            check(
                all(r["x"] == 4 for r in rows),
                "七项左缘统一 x=4",
                str([r["x"] for r in rows]),
            )
            check(
                all(r["labelX"] == 12 for r in rows),
                "文案左内缩统一 12px",
                str([r["labelX"] for r in rows]),
            )
            check(
                all(r["radius"] == "8px" for r in rows),
                "行圆角 8px",
                str(sorted({r["radius"] for r in rows})),
            )
            enabled = [r for r in rows if not r["disabled"]]
            check(
                all(color_eq(r["label"], WHITE) for r in enabled),
                "可用项文案纯白",
                str(sorted({r["label"] for r in enabled})),
            )
            check(
                all(r["labelFS"] == "13px" for r in rows if r["labelFS"]),
                "文案 13px",
                str(sorted({r["labelFS"] for r in rows if r["labelFS"]})),
            )
            with_kbd = [r for r in rows if r["kbdFS"]]
            check(
                all(r["kbdFS"] == "13px" for r in with_kbd),
                "快捷键同为 13px（源站非 12px）",
                str(sorted({r["kbdFS"] for r in with_kbd})),
            )
            check(
                all(color_eq(r["kbdColor"], WHITE_60) for r in with_kbd),
                "快捷键 white/60",
                str(sorted({r["kbdColor"] for r in with_kbd})),
            )
            check(
                all(r["kbdRight"] == 184 for r in with_kbd),
                "快捷键右缘统一 184（= 192 行宽 − 8）",
                str(sorted({r["kbdRight"] for r in with_kbd})),
            )
            dis_rows = [r for r in rows if r["disabled"]]
            # 订正（batch 814）：本文件此前断言禁用文案是 white/30，但那个值是从
            # **复刻侧自己的代码**抄来的，从没在源站量过。batch 814 在源站右键菜单
            # 上实测到禁用项（下载/重做/撤销）文案是 `rgba(255,255,255,0.2)`，
            # 而两处菜单是同一套设计系统（200/pad 4/行高 36/gap 4/快捷键 white/60
            # 全部同款），故以实测值 white/20 为准。
            check(
                all(color_eq(r["label"], WHITE_20) for r in dis_rows),
                "禁用项文案 white/20（源站右键菜单实测值；此前误用未实测的 0.3）",
                str(sorted({r["label"] for r in dis_rows})),
            )

        print("\n[3] 分隔线（唯一一条，落在「缩放至选中项」与「缩放至50%」之间）")
        sep = geo["sep"]
        check(sep is not None, "存在 role=separator", "未找到分隔线")
        if sep:
            check(sep["x"] == 16, f"分隔线左缘 x=16（内缩 12）（实得 {sep['x']}）")
            check(sep["w"] == 168, f"分隔线宽 168（200 − 左右各 12 + 4）（实得 {sep['w']}）")
            check(sep["h"] == 4, f"分隔线盒高 4px（实得 {sep['h']}）")
            check(sep["lineH"] == 1, f"盒内线 1px（实得 {sep['lineH']}）")
            check(
                sep["lineY"] == 2,
                f"线落在盒顶 +2px（与源站 ::before top:2px 一致，实得 {sep['lineY']}）",
            )
            check(
                sep["lineW"] == sep["w"],
                f"线宽撑满盒宽（{sep['lineW']} vs {sep['w']}）",
            )
            check(
                color_eq(sep["lineBg"], WHITE_04),
                f"线色 white/4（源站像素实测 rgb(47,47,47)，实得 {sep['lineBg']}）",
            )
        check(
            geo["kids"] == 8,
            f"菜单直接子节点 8 个（7 项 + 1 分隔线，实得 {geo['kids']}）",
        )
        # 分隔线必须紧跟在第 4 项（缩放至选中项）之后 —— 用可见顺序校验
        order_ok = page.evaluate(
            """() => {
              const kids = [...document.querySelector('[role="menu"]').children];
              const idx = kids.findIndex(e => e.getAttribute('role') === 'separator');
              const before = kids.slice(0, idx).map(e => (e.textContent||'').trim());
              return { idx, before, prev: (kids[idx-1]?.textContent||'').trim() };
            }"""
        )
        check(
            order_ok["prev"].startswith("缩放至选中项"),
            f"分隔线紧随「缩放至选中项」之后（实得 {order_ok['prev']!r}）",
        )

        print("\n[4] 总高 292 由「边距 + 行高 + 分隔线 + 间隙」推出")
        if len(rows) == 7 and sep:
            derived = 8 + 7 * 36 + sep["h"] + 7 * 4
            check(
                geo["h"] == derived == 292,
                f"总高 = 8 + 7×36 + {sep['h']} + 7×4 = {derived}（实得 {geo['h']}）",
            )
        else:
            check(False, "总高可推算", "缺行/分隔线数据")

        print("\n[4b] 悬停态底色 white/8")
        page.locator('[role="menu"] [role="menuitem"]').first.hover()
        page.wait_for_timeout(450)
        hbg = page.evaluate(
            """() => getComputedStyle(
                 document.querySelector('[role="menu"] [role="menuitem"]')
               ).backgroundColor"""
        )
        check(color_eq(hbg, WHITE_08), f"悬停底色 white/8（实得 {hbg}）")

        print("\n[5] 禁用态：未选中节点时「缩放至选中项」应禁用且带提示文案")
        d = rows[3] if len(rows) > 3 else None
        check(d is not None and d["disabled"], "第 4 项 disabled", str(d))
        if d:
            title = page.locator('[role="menu"] [role="menuitem"]').nth(3).get_attribute("title")
            check(title == DISABLED_TITLE, f"title = {DISABLED_TITLE}", f"实得 {title!r}")

        print("\n[6] 功能：新补的两枚必须真接 xyflow（1.2 步长），非空壳")
        close_menu(page)
        page.evaluate(
            """() => { const b=document.querySelector('[data-testid="dock-zoom"]');
                       b.focus(); }"""
        )
        z0 = zoom_of(page)
        page.keyboard.press("Meta+=")
        page.wait_for_timeout(900)
        z1 = zoom_of(page)
        page.keyboard.press("Meta+-")
        page.wait_for_timeout(900)
        z2 = zoom_of(page)
        check(
            math.isclose(z1, z0 * 1.2, rel_tol=0.02),
            f"⌘+ 放大 ×1.2（{z0} → {z1}）",
        )
        check(
            math.isclose(z2, z1 / 1.2, rel_tol=0.02),
            f"⌘- 缩小 ÷1.2（{z1} → {z2}）",
        )

        print("\n[7] 菜单项点击后确实生效：缩放至50%")
        open_menu(page)
        page.locator('[role="menu"] [role="menuitem"]', has_text="缩放至50%").first.click()
        page.wait_for_timeout(1000)
        z50 = zoom_of(page)
        check(math.isclose(z50, 50, abs_tol=0.6), f"点「缩放至50%」→ {z50}%")
        dock = page.locator('[data-testid="dock-zoom"]').first.inner_text().strip()
        check(dock.startswith("50%"), f"dock 读数同步为 50%（实得 {dock!r}）")

        print("\n[8] 选中节点后「缩放至选中项」解禁")
        close_menu(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        node = page.locator(".react-flow__node").first
        if node.count() > 0:
            # 不能点节点正中 —— 那里常是播放/媒体控件，会吞掉选中。
            # batch 8 的既有做法是点 (200, 100) 这类正文偏移位。
            nb = node.bounding_box()
            if nb and nb["width"] > 60 and nb["height"] > 40:
                page.mouse.click(nb["x"] + min(200, nb["width"] / 2), nb["y"] + 20)
            else:
                page.mouse.click(nb["x"] + nb["width"] / 2, nb["y"] + nb["height"] / 2)
            page.wait_for_timeout(800)
            sel = page.evaluate(
                """() => {
                  const e = document.querySelector('.react-flow__node.selected');
                  return e ? e.getAttribute('data-id') : null;
                }"""
            )
            check(sel is not None, "节点确实进入 selected 态", "selected 态未出现")
            if sel is not None:
                open_menu(page)
                dis = page.locator('[role="menu"] [role="menuitem"]').nth(3).is_disabled()
                check(not dis, "选中节点后第 4 项解禁")
        else:
            check(False, "画布上存在节点可供选中", "未找到 .react-flow__node")

        page.screenshot(path="docs/research/jimeng-canvas-batch811-2026-10-03/clone-zoommenu.png")
        print(f"\n截图: docs/research/jimeng-canvas-batch811-2026-10-03/clone-zoommenu.png")

    print(f"\n{'='*52}")
    if fails:
        print(f"FAIL —— {len(fails)}/{checks} 项不通过:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"PASS —— {checks}/{checks} 项全部通过")


if __name__ == "__main__":
    from playwright.sync_api import Page  # noqa: F401  (类型注解用)

    main()
