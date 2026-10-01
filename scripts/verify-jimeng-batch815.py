#!/usr/bin/env python3
"""Jimeng clone batch 815 verifier — 快捷键面板的承诺审计。

这一批的出发点是一个自相矛盾的现场：面板上写着的键，要么按了没反应，要么名字
和源站对不上，而面板还漏了整整两段分区。逐条审计后能落地的动作只有四类：

  1. **文案逐字对齐**（源站 evidence 抓取，见 README §22）
     - 「全屏 F」→ 源站写的是「**预览视图 F**」
     - 补「**宫格视图 G**」（复刻整行缺失）
     - 补源站有的整段「**时间线**」（分割片段/向左裁剪/向右裁剪/缩放时间线）
     - 补源站有的整段「**文本编辑**」（加粗…有序列表，10 行，复刻完全没有）
     - 两键行（还原 / 适配画布）从字面 "A | B" 改成**两个 chip + 竖分隔线**
  2. **几何对齐**：242 → 240 宽，行距 36 → 40（行高 36 + 4 gap），分区标题 12px/0.35
  3. **接上真缺口 ⌘/**：面板承诺「打开/关闭 Agent ⌘ /」，复刻此前根本没这个分支
     —— 依赖数组里躺着 aiDrawerOpen/setAiDrawerOpen 两个**孤儿依赖**，没有任何分支
     读它们。源站实测 ⌘/ 首次按下新增 17 个 canvas-agent-* testid（含
     canvas-agent-panel），再按一次**精确回到基线**。
  4. **V / F / G 判为展示项**：对源站逐项做状态指纹比对（画布背景、光标、testid
     集合、视口 transform），按 G / F / V 指纹**全部零变化** —— 源站自己就测不到可见
     响应。不擅自实现源站测不到的行为。

判据纪律（沿用 807/808/810/812 的教训）：**断言状态变化，不断言元素存在**。
本文件里凡是"应该生效"的项，都读一个前后对比的量（面板宽度、行距、testid 集合、
编组状态、缩放读数、撤销栈深度），而不是 `element is visible`。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def open_shortcuts(page) -> None:
    page.locator('button[aria-label="用户菜单"]').click()
    page.wait_for_timeout(500)
    page.locator('[role="menuitem"]', has_text="快捷键").click()
    page.wait_for_selector('div[aria-label="快捷键"]', timeout=8000)
    page.wait_for_timeout(400)


def rail_click(page, label: str) -> None:
    """按坐标点左栏按钮。

    判据纪律：这里**不用** `locator.click()`。它在左栏上会间歇性空点 ——
    连续三次 locator.click() 实测 2→3→3→3，而同样的坐标 mouse.click 连点是
    2→3→4 正常递增。差点据此判成「左栏只能插一次」的产品缺陷，实际是测试工装
    的问题。坐标点击绕开 actionability/命中校验的抖动。
    """
    box = page.locator(f'button[aria-label="{label}"]').first.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(1300)


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state=str(STATE) if STATE.exists() else None,
                            viewport={"width": 1680, "height": 1050})
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)

        # ── 1. 面板文案：四个分区 + 源站全部 30 行 ──────────────────────────
        open_shortcuts(page)
        panel = page.evaluate(
            """() => {
                const d = document.querySelector('div[aria-label="快捷键"]');
                if (!d) return null;
                const spans = [...d.querySelectorAll('span')].map(s => s.textContent.trim());
                const r = d.getBoundingClientRect();
                const txt = d.innerText;
                // 行几何：取所有「标签 + 键位」的行容器
                const rowTops = [...new Set([...d.querySelectorAll('div')]
                    .filter(e => e.getBoundingClientRect().height === 36
                              && (e.innerText||'').trim())
                    .map(e => Math.round(e.getBoundingClientRect().top)))].sort((a,b)=>a-b);
                return {
                  w: Math.round(r.width), h: Math.round(r.height),
                  sections: ['通用操作','视图','时间线','文本编辑'].filter(s => txt.includes(s)),
                  spans,
                  // 源站逐字文案
                  rows: ['打开/关闭 Agent','撤销','还原','移动工具','预览视图','宫格视图',
                         '创建编组','取消编组','放大视图','缩小视图','适配画布','缩放至 100%',
                         '缩放至选中项','缩放画布','分割片段','向左裁剪','向右裁剪','缩放时间线',
                         '加粗','倾斜','下划线','删除线','一级标题','二级标题','三级标题',
                         '普通文本','无序列表','有序列表'].filter(s => txt.includes(s)),
                  hasFullScreenLabel: txt.includes('全屏'),
                  keyChips: ['⌘ /','⌘ Z','⌘ ⇧ Z','⌘ Y','V','F','G','⌘ G','⌘ ⇧ G','⌘ +','⌘ -',
                             '⇧ 1','⌘ 0','⌘ 1','⇧ 2','⌘ scroll','⌘ B','Q','W','⌘ I','⌘ U',
                             '⌘ ⇧ X','⌘ ⌥ 1','⌘ ⌥ 2','⌘ ⌥ 3','⌘ ⌥ 0','⌘ ⇧ 8','⌘ ⇧ 7']
                            .filter(k => spans.includes(k)),
                  rowTops,
                  hasLiteralPipe: spans.some(s => s.includes('|')),
                  // 段内行距：直接量首行(打开/关闭 Agent)到末行(取消编组)的跨度，
                  // 按 8 行折算。不用「找分区容器」—— 初稿用 innerText 前缀找容器，
                  // 结果抓到的是整块滚动区，把跨分区的 72 也算了进来（判据过宽）。
                  secPitch: (() => {
                    const topOf = (label) => {
                      const l = [...d.querySelectorAll('span')].find(
                        s => s.textContent.trim() === label);
                      if (!l) return null;
                      let n = l.parentElement, k = 0;
                      while (n && k < 3) {
                        if (n.getBoundingClientRect().height === 36) {
                          return Math.round(n.getBoundingClientRect().top);
                        }
                        n = n.parentElement; k++;
                      }
                      return null;
                    };
                    const a = topOf('打开/关闭 Agent'), b = topOf('取消编组');
                    return (a !== null && b !== null) ? (b - a) / 7 : null;
                  })(),
                };
            }"""
        )
        if not panel:
            print("FAIL: panel did not open")
            return 1

        check("1.1 四个分区齐全", panel["sections"] == ["通用操作", "视图", "时间线", "文本编辑"],
              str(panel["sections"]))
        # 源站行数 = 通用 8 + 视图 6 + 时间线 4 + 文本编辑 10 = **28**。
        # （初稿这里写成 30，是我自己的算术错误，不是源站/复刻的差异。）
        check("1.2 源站 28 行全覆盖", len(panel["rows"]) == 28, f"{len(panel['rows'])}/28")
        check("1.3 文案订正：不再是「全屏」而是「预览视图」",
              not panel["hasFullScreenLabel"] and "预览视图" in panel["rows"])
        check("1.4 补上「宫格视图 G」",
              "宫格视图" in panel["rows"] and "G" in panel["keyChips"])
        check("1.5 补上「时间线」整段（分割/向左裁剪/向右裁剪/缩放时间线）",
              all(x in panel["rows"] for x in ["分割片段", "向左裁剪", "向右裁剪", "缩放时间线"]))
        check("1.6 补上「文本编辑」整段（10 行）",
              all(x in panel["rows"] for x in ["加粗", "倾斜", "下划线", "删除线", "一级标题",
                                              "二级标题", "三级标题", "普通文本", "无序列表", "有序列表"]))
        # 键位 chip 去重后共 28 个（还原 2 个、适配画布 2 个，其余各 1）。
        # （初稿写 27 也是我自己的算术错误。）
        check("1.7 源站 28 个键位 chip 全在", len(panel["keyChips"]) == 28,
              f"{len(panel['keyChips'])}/28")
        check("1.8 两键行不再是字面 \"|\"", not panel["hasLiteralPipe"])
        # 还原 / 适配画布 的两个 chip 必须同属一行（源站形态）
        chips = page.evaluate(
            """() => {
                const d = document.querySelector('div[aria-label="快捷键"]');
                const rowOf = (label) => {
                  const l = [...d.querySelectorAll('span')].find(s => s.textContent.trim() === label);
                  if (!l) return null;
                  let n = l.parentElement, depth = 0;
                  while (n && depth < 3) {
                    const t = (n.innerText||'').trim();
                    if (t.startsWith(label) && n.getBoundingClientRect().height === 36) return n;
                    n = n.parentElement; depth++;
                  }
                  return n;
                };
                const out = {};
                for (const lab of ['还原','适配画布']) {
                  const r = rowOf(lab);
                  out[lab] = r ? r.innerText.split('\\n').map(s=>s.trim()) : null;
                }
                return out;
            }"""
        )
        check("1.9 「还原」= ⌘⇧Z + ⌘Y 两个 chip",
              chips["还原"] is not None and chips["还原"][:3] == ["还原", "⌘ ⇧ Z", "⌘ Y"],
              str(chips["还原"]))
        check("1.10 「适配画布」= ⇧1 + ⌘0 两个 chip",
              chips["适配画布"] is not None and chips["适配画布"][:3] == ["适配画布", "⇧ 1", "⌘ 0"],
              str(chips["适配画布"]))

        # ── 2. 几何：240 宽 / 行距 40 ────────────────────────────────────────
        check("2.1 面板宽 240（源站值，此前 242）", panel["w"] == 240, f"w={panel['w']}")
        check("2.2 段内行距恒为 40（行高 36 + 4 gap）", panel["secPitch"] == 40,
              f"pitch={panel['secPitch']}")
        check("2.3 面板可滚动（四段 28 行装不下）", panel["h"] < 1050 - 56,
              f"h={panel['h']}")

        # ── 3. ⌘/ 打开/关闭 Agent（真缺口，本批接上）─────────────────────────
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        tid = """() => [...document.querySelectorAll('[data-testid]')].map(e => e.getAttribute('data-testid'))"""
        agent_open = """() => !!document.querySelector('[aria-label="Agent"]')"""
        check("3.0 前置：Agent 面板未打开", page.evaluate(agent_open) is False)

        base_tids = set(page.evaluate(tid))
        page.locator("body").click(position={"x": 800, "y": 900})
        page.keyboard.press("Meta+Slash")
        page.wait_for_timeout(900)
        opened = page.evaluate(agent_open)
        open_tids = set(page.evaluate(tid))
        check("3.1 ⌘/ 打开 Agent 面板（读 aria-label=Agent 真出现）", opened is True)
        check("3.2 ⌘/ 新增了 canvas-agent-* testid",
              len([t for t in open_tids - base_tids if t and "agent" in t]) > 0,
              f"新增 {sorted(t for t in open_tids - base_tids if t and 'agent' in t)[:4]}")

        page.keyboard.press("Meta+Slash")
        page.wait_for_timeout(900)
        closed = page.evaluate(agent_open)
        close_tids = set(page.evaluate(tid))
        check("3.3 ⌘/ 再按关闭（真开关，不是单向开）", closed is False)
        check("3.4 关闭后 testid 集合精确回到基线", close_tids == base_tids,
              f"差异 {sorted(close_tids ^ base_tids)[:4]}")

        # 反向断言：面板开着时，在 composer 里打 "/" 不得触发全局快捷键。
        # 先用 ⌘/ 重新打开（3.4 之后是关着的）。
        # 注意 composer 是 <input> 且**没有 type 属性** —— 用 input[type="text"]
        # 选不中（初稿因此把这步静默跳过了，而"跳过"被报成 PASS，正是
        # 「我没检测到 ≠ 事实如此」的老坑）。这里显式排除 hidden/button。
        page.locator("body").click(position={"x": 800, "y": 900})
        page.keyboard.press("Meta+Slash")
        page.wait_for_timeout(900)
        comp = page.locator('[aria-label="Agent"] input:not([type="hidden"]):not([type="button"])').first
        if comp.count() == 0:
            check("3.5 反向：composer 里打 \"/\" 不会误关 Agent（inField 早退）", False,
                  "找不到 composer input —— 判据够不着，如实报错而非跳过")
        else:
            comp.click()
            comp.type("a/b")
            page.wait_for_timeout(600)
            typed = comp.input_value()
            check("3.5 反向：composer 里打 \"/\" 不会误关 Agent（inField 早退）",
                  page.evaluate(agent_open) is True and typed == "a/b",
                  f"agent_open={page.evaluate(agent_open)} value={typed!r}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        # ── 4. V / F / G 判为展示项：不伪称可用 ─────────────────────────────
        # 本批不实现 G（源站实测零变化）。此处断言"面板仍逐字照抄源站文案"，
        # 也就是：不因为复刻没实现就把行删掉或改名。
        open_shortcuts(page)
        g_listed = page.evaluate(
            """() => {
                const d = document.querySelector('div[aria-label="快捷键"]');
                const t = d.innerText;
                return ['移动工具','预览视图','宫格视图'].every(x => t.includes(x));
            }"""
        )
        check("4.1 V/F/G 三项在面板上仍按源站逐字列出（不因复刻未实现而删改）", g_listed)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        # ── 5. 编组 ⌘G / ⌘⇧G 兑现（复核 batch 39，顺带纠正早先的误判）──────────
        # 关键：**必须先选中 ≥2 个节点**，否则 ⌘G 静默不生效。
        # batch 815 复盘：早先曾把这三项误判为失效，根因是测试前置条件错误。
        page.evaluate("""() => {
            const r = document.querySelector('.react-flow__viewport');
            if (r) r.style.transform = 'translate(0px,0px) scale(1)';
        }""")
        page.wait_for_timeout(300)
        # 通过左栏插入两个节点（坐标点击，见 rail_click 的说明）
        for _ in range(2):
            rail_click(page, "主体")
        node_count = page.evaluate("""() => document.querySelectorAll('.react-flow__node').length""")
        check("5.0 前置：画布上至少 2 个节点", node_count >= 2, f"nodes={node_count}")

        group_state = """() => {
            const el = document.querySelector('.jimeng-canvas');
            return el ? el.textContent.includes('编组 1') : false;
        }"""
        # 全选 → ⌘G
        page.locator("body").click(position={"x": 800, "y": 900})
        page.keyboard.press("Meta+a")
        page.wait_for_timeout(400)
        page.keyboard.press("Meta+g")
        page.wait_for_timeout(700)
        grouped = page.evaluate(group_state)
        check("5.1 ⌘G 兑现：画布出现「编组 1」", grouped is True)

        page.keyboard.press("Meta+Shift+g")
        page.wait_for_timeout(700)
        ungrouped = page.evaluate(group_state)
        check("5.2 ⌘⇧G 兑现：「编组 1」消失（编组可逆）", ungrouped is False)

        # ── 6. ⌘Z / ⌘⇧Z 兑现 ───────────────────────────────────────────────
        # 判据踩坑记录：初稿拿「缩放读数」当撤销的可观测量，结果 ⌘0 → ⌘Z 后读数
        # 73% → 114% 判失败。查 store 才发现 `past: { nodes, edges }` —— **视口
        # 根本不在撤销域里**，撤销缩放从来就不是本产品承诺的行为，是判据越界。
        # 改为测真在撤销域内的量：节点数。
        nodes_js = """() => document.querySelectorAll('.react-flow__node').length"""
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        n0 = page.evaluate(nodes_js)
        rail_click(page, "主体")
        n1 = page.evaluate(nodes_js)
        check("6.0 前置：左栏插入后节点数 +1", n1 == n0 + 1, f"{n0} -> {n1}")

        page.keyboard.press("Meta+z")
        page.wait_for_timeout(700)
        n2 = page.evaluate(nodes_js)
        check("6.1 ⌘Z 撤销插入（节点数回到插入前）", n2 == n0, f"{n1} -> {n2}")

        page.keyboard.press("Meta+Shift+z")
        page.wait_for_timeout(700)
        n3 = page.evaluate(nodes_js)
        check("6.2 ⌘⇧Z 还原插入（节点数回到 +1）", n3 == n1, f"{n2} -> {n3}")

        check("7.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))

        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 815 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
