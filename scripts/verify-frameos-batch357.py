#!/usr/bin/env python3

"""Verify Batch 357: 不允许存在「什么都没做、却声称成功」的 toast 谎报。

第三类交互谎言, 前两类的形状:
  - 静默丢弃输入 (Batch 350/355): 控件收下输入, 不绑定 onChange;
  - 假可点按钮 (Batch 344/356): 控件能点, 但压根没有 handler;
  - **本批**: 有 handler、点了确实出了东西 (一条绿色 ✓「已xxx」toast)、
    但底层状态一点没变。**最难发现** —— 因为它在每一层单看都是「正常的」。

判据是「**声称成功**」而不是「弹了 toast」: 一条 warning 说「暂不可用」是
诚实的、不是谎报。这条区分是被 batch170 打回一次之后才补上的 (见下)。

普查 (scripts/toast_lie_census.mjs, AST 版) 在 36 个 frameos 源文件里找到 6 条
只弹 toast 的处理器, 逐条人工核实后:

  | 位置                                | toast 文案            | 核实结论 |
  |-------------------------------------|-----------------------|----------|
  | page.tsx 设置为资产图                | 已设置为资产图 (mock)  | **谎报** |
  | FrameosGroupCanvas.tsx 复制分组       | 已复制分组 (mock)      | **谎报** |
  | FrameosGroupCanvas.tsx 创建分组副本   | 已创建分组副本 (mock)  | **谎报** |
  | FrameosGroupCanvas.tsx 批量连线       | 批量连线 (mock)        | **谎报** |
  | FrameosGroupToolbar.tsx 存为模板      | 已存为模板 (mock)      | **谎报** |
  | page.tsx ⌘S                         | 已保存当前画布         | **非谎报** |

逐条人工核实 (普查只列事实, 判定必须人做 —— Batch 355 的同一纪律):

1. **设置为资产图**: FrameosProjectAssetsPanel 的内容是**写死的空态**
   「暂无已生成的资产图」, 没有任何数据源, 结构上装不下东西。点完去看面板
   什么也没有。
2. **复制分组 / 创建分组副本**: store 里没有分组的复制 action, 也没有分组数据
   进剪贴板。更关键的是**语义未定义** —— 分组是由存活成员算出来的盒子
   (Batch 341 不变式「分组盒 == 存活成员包围盒 + padding」), 复制的是盒子还是
   成员? 成员副本归不归入新组? 两个组引用同一批成员合不合法? 源站未采样, 全是
   编造。(对照组: 节点级「创建副本」是真的, page.tsx 调 duplicateNode, Batch 170。)
3. **批量连线**: 多步交互的起点 (选起点 → 选终点 → 建边), 不是一条能就地补上
   的 action。
4. **存为模板**: 查了面板另一头 —— FrameosTemplatePanel 的卡片来自**硬编码常量**
   TEMPLATE_CARDS, store 里没有 template 字段。存进去的模板**永远不会**出现在
   面板里, 面板也不会多出一张卡。
5. **⌘S**: **不是谎报, 保持原样**。画布每次 nodes/groups/edges 变动都由 mount
   订阅自动写 localStorage (frameosStore.writePersistedCanvases), 所以「已保存
   当前画布」这句话在事实上为真 —— 它只是把功劳记在一次并不存在的动作上。绑死
   「必须改掉它」就是绑缺陷副作用, 不是绑真实性质。

## ⚠️ 修法改过一次: 被 batch170 打回, 而且它是对的

最初把 5 项统统改成 `disabled` + title。跑全量回归时 **batch170 红了**:
`node:item:设置为资产图:disabled=false`。按「我的改动撞上旧断言, 第一动作是找
一手源站证据」的纪律去查, 证据站在旧断言这边:

    docs/research/frameos/BEHAVIORS.md:33（2026-09-25 源站实测, Batch 226/228）
    内容图片 复制⌘C / 复制图片 / 创建副本⌘D / **设置为资产图** / 删除⌫(红)
    空图片 复制图片+重新生成均禁用

源站里「设置为资产图」是**启用**的, 禁用的只有空图片态那两行。改 enabled
是在改源站事实。

而且更重要的是: **缺陷本来就不在「这个菜单项能不能点」, 而在它谎称成功。**
把这四条一起推翻后, 统一改为:

    保持启用 (源站事实)  +  toast 从 success 改成 warning, 说清「暂不可用」

五个谎报**一个都没被藏起来** —— 用户照样点得到, 照样得到反馈, 只是那条反馈
终于说的是实话。判据也随之从「只弹 toast」收紧为「只弹 toast **且**声称成功」。

（另四项没有门禁钉住启用态, 但也没有任何证据说它们该是禁用的; 既然同一条
修法在有证据的那一项上被证伪, 就没有理由只对它网开一面。）

本验证器把普查变成**门禁**: 以后任何人新写一条「什么都没做却说已成功」的
处理, 这里会红。

断言:
1-4. 静态普查能跑通 / 只有 1 条声称成功 / 那条是已核实的 ⌘S / 5 条谎报文案已消失;
5-8. 分组右键菜单: 复制、创建副本**仍启用** (源站事实) 且弹 warning;
9.   分组批量连线圆点仍启用且弹 warning;
10.  工具条「存为模板」仍启用且弹 warning;
11.  节点右键「设置为资产图」**仍启用** (batch170 回归防护) 且弹 warning;
12.  五项弹出的 toast **都不是 success 变体**;
13.  「删除」仍然可用且真 ungroup (Batch 344 不回归);
14.  诊断零错误。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-frameos-batch357-2026-10-01" / "runtime-audit.json"
)
CENSUS = ROOT / "scripts" / "toast_lie_census.mjs"
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# 已人工核实为**非谎报**的唯一一条: 画布本就在自动持久化, 文案为真。
# 若日后画布不再自动保存, 这条应当改判为谎报并从这里移出 —— 别默默放过。
BENIGN_SUCCESS_CLAIM = "已保存当前画布"

# 本批修掉的 5 条谎报文案, 一条都不许再出现。
FIXED_LIES = [
    "已设置为资产图",
    "已复制分组",
    "已创建分组副本",
    "批量连线 (mock)",
    "已存为模板",
]

NODE_BIN = os.path.expanduser("~/.nvm/versions/node/v24.6.0/bin")


def run_census() -> dict[str, Any]:
    env = dict(os.environ)
    env["PATH"] = f"{NODE_BIN}:{env.get('PATH', '')}"
    proc = subprocess.run(
        ["node", str(CENSUS), "--json"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"普查失败 rc={proc.returncode}: {proc.stderr[-800:]}"
    return json.loads(proc.stdout)


SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [], selectedNodeId: null,
                selectedGroupId: null });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  window.__gid = gid;
  return { gid, groupCount: st.getState().groups.length };
}
"""

ITEM_STATE_JS = """
() => Array.from(document.querySelectorAll('[data-frameos-context-item]')).map((el) => ({
  label: el.getAttribute('data-frameos-context-item'),
  disabled: el.disabled === true,
  title: el.getAttribute('title') || '',
}))
"""

TOASTS_JS = """
() => Array.from(document.querySelectorAll('[data-frameos-toast]')).map((e) => ({
  text: e.textContent || '',
  variant: e.getAttribute('data-frameos-toast-variant') || '',
}))
"""


def toasts(page: Page) -> list[dict[str, str]]:
    return page.evaluate(TOASTS_JS)


def toast_multiset(page: Page) -> dict[str, int]:
    from collections import Counter

    return dict(Counter(f"{t['variant']}|{t['text']}" for t in toasts(page)))


def toasts_since(before: dict[str, int], page: Page) -> list[dict[str, str]]:
    """点击之后**新出现**的 toast。

    曾经试过 `document.querySelectorAll('[data-frameos-toast]').forEach(e => e.remove())`
    来「清场」, 结果把探针自己搞坏了: 那些节点是 React 管的, 手工摘掉之后 fiber 树
    与 DOM 对不上, 下一次重渲染把右键菜单一起拖没了(表现为
    `wait_for_selector('[data-frameos-context-item]')` 超时)。**探针不该改被测应用
    的 DOM** —— 改成前后取差集, 只读不写。
    """
    from collections import Counter

    after = Counter(f"{t['variant']}|{t['text']}" for t in toasts(page))
    fresh: Counter = Counter()
    for key, n in after.items():
        delta = n - before.get(key, 0)
        if delta > 0:
            fresh[key] = delta
    out: list[dict[str, str]] = []
    for key, n in fresh.items():
        variant, text = key.split("|", 1)
        out.extend({"variant": variant, "text": text} for _ in range(n))
    return out


def open_group_menu(page: Page) -> list[dict[str, Any]]:
    """打开分组右键菜单, 读出菜单项状态。**幂等**。

    菜单开着的时候不能直接右键: FrameosContextMenu 有一层
    `position:fixed; inset:0; zIndex:5000` 的遮罩, 它的 onContextMenu 只是
    `closeContextMenu()` —— 于是右键被遮罩吃掉, 菜单反而关掉了, 表现为
    `wait_for_selector('[data-frameos-context-item]')` 超时。
    (实测: 第 1 次右键 items=3, 点完项菜单关闭, 第 2 次右键 items=3,
     第 3 次右键直接 items=0 —— 正是「菜单还开着就又右键」。)
    所以每次都先 Esc 收场, 再右键。
    """
    if page.locator("[data-frameos-context-item]").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)
    box = page.locator(".frameos-canvas-group").first.bounding_box()
    assert box, "找不到分组盒 —— 态没进去"
    page.mouse.click(
        box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, button="right"
    )
    page.wait_for_selector("[data-frameos-context-item]", timeout=8000)
    page.wait_for_timeout(300)
    return page.evaluate(ITEM_STATE_JS)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch357 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    # ══ 静态普查: 把「谎称成功」变成门禁 ══
    census = run_census()
    sites = [s for f in census["findings"] for s in f["sites"]]
    lies = [s for s in sites if s["isSuccessClaim"]]
    result["census"] = {
        "scanned": census["scanned"],
        "handlers": len(census["findings"]),
        "toastSites": len(sites),
        "toastOnly": [s["text"] for s in sites if s["isToastOnly"]],
        "successClaims": [s["text"] for s in lies],
    }
    # 防假绿: 普查必须真的扫到东西
    check("census:scanned-enough", census["scanned"] >= 30,
          f"只扫到 {census['scanned']} 个文件 —— 普查可能整体失效(假绿)")
    check("census:toast-sites-found", len(sites) >= 8,
          f"只找到 {len(sites)} 条 toast —— 扫描范围可能不对(假绿)")

    check("census:exactly-one-success-claim", len(lies) == 1,
          f"期望只剩 1 条声称成功(已核实的 ⌘S), 实际 {len(lies)} 条: "
          f"{[s['text'] for s in lies]}")
    check("census:remaining-is-benign",
          bool(lies) and lies[0]["text"] == BENIGN_SUCCESS_CLAIM,
          f"剩下那条不是已核实的 {BENIGN_SUCCESS_CLAIM!r}: "
          f"{[s['text'] for s in lies]}")

    all_texts = " || ".join(s["text"] for s in sites)
    for lie in FIXED_LIES:
        check(f"lie-removed:{lie}", lie not in all_texts,
              f"谎报文案 {lie!r} 又出现了 —— 该 handler 回到了只弹成功 toast 的状态")

    # 5 处「暂不可用」必须在场, 且都不是 success 变体
    unavailable = [s for s in sites if "暂不可用" in s["text"]]
    check("census:five-unavailable-toasts", len(unavailable) == 5,
          f"期望 5 条「暂不可用」, 实际 {len(unavailable)}: "
          f"{[s['text'] for s in unavailable]}")
    check("census:unavailable-not-success",
          all(s["variant"] != "success" for s in unavailable),
          f"「暂不可用」不该用 success 变体: "
          f"{[(s['text'], s['variant']) for s in unavailable]}")

    # ══ 运行时: 源站的启用形态没被动过, 提示改成了实话 ══
    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 分组右键菜单 ──
    setup = page.evaluate(SETUP_JS)
    result["setup"] = setup
    page.wait_for_timeout(600)
    items = open_group_menu(page)
    by_label = {i["label"]: i for i in items}
    result["group_menu"] = items

    # 源站事实: 这几项在源站菜单里是存在的、可点的。禁用它们才是改源站。
    for label in ("复制", "创建副本"):
        check(f"group-menu:{label}:present", label in by_label,
              f"菜单项缺失, 现有: {[i['label'] for i in items]}")
        check(f"group-menu:{label}:still-enabled", not by_label[label]["disabled"],
              f"{label} 被禁用了 —— batch170 的教训: 没有源站证据说它该是禁用的")
        check(f"group-menu:{label}:explains-why", bool(by_label[label]["title"]),
              f"{label} 应当用 title 说明为什么暂不可用")

    for label, expect_word in (("复制", "复制分组"), ("创建副本", "创建分组副本")):
        # 菜单项被点后 FrameosContextMenu 会 closeContextMenu, 所以每次点击前
        # 都要**重新右键打开** —— 否则第二次点会一直等不到元素。
        open_group_menu(page)
        before = toast_multiset(page)
        page.locator(f'[data-frameos-context-item="{label}"]').click()
        page.wait_for_timeout(500)
        got = toasts_since(before, page)
        result.setdefault("toasts", {})[label] = got
        check(f"group-menu:{label}:warns-not-claims-success",
              bool(got) and all(t["variant"] != "success" for t in got),
              f"{label} 弹出的不是 warning 而是 success: {got}")
        check(f"group-menu:{label}:says-unavailable",
              any(expect_word in t["text"] and "暂不可用" in t["text"] for t in got),
              f"{label} 的提示没说清是 {expect_word}: {got}")

    # 删除必须仍然可用且真接线 —— Batch 344 的修复不许被这批顺手带走
    check("group-menu:删除:still-enabled", by_label.get("删除", {}).get("disabled") is False,
          f"删除被误禁: {by_label.get('删除')}")
    # 菜单此刻仍是关着的(上一轮点击已关闭它), 重新打开再点删除
    open_group_menu(page)
    before = toast_multiset(page)
    page.locator('[data-frameos-context-item="删除"]').click()
    page.wait_for_timeout(500)
    has_group = page.evaluate(
        "() => window.__frameos_store.getState().groups.some(g => g.id === window.__gid)"
    )
    check("group-menu:删除:actually-ungroups", not has_group,
          "点了删除但分组还在 —— Batch 344 的真接线被回归了")
    check("group-menu:删除:no-mock-toast",
          not any("已删除分组" in t["text"] for t in toasts_since(before, page)),
          f"又弹出了 mock toast: {toasts_since(before, page)}")

    # ── 分组批量连线圆点 (需重新建组, 因为上面把组解了) ──
    page.evaluate(SETUP_JS)
    page.wait_for_timeout(500)
    page.evaluate("() => window.__frameos_store.getState().selectGroup(window.__gid)")
    page.wait_for_timeout(400)
    port = page.locator(".frameos-group-batch-connect-port")
    check("port:present", port.count() == 1, f"count={port.count()}")
    check("port:still-enabled", not port.evaluate("el => el.disabled === true"),
          "批量连线圆点被禁用了 —— 源站未采样不等于源站禁用它")
    check("port:explains-why", bool(port.get_attribute("title")),
          "批量连线圆点应当用 title 说明为什么暂不可用")
    before = toast_multiset(page)
    port.click()
    page.wait_for_timeout(500)
    got = toasts_since(before, page)
    result.setdefault("toasts", {})["批量连线"] = got
    check("port:warns-not-claims-success",
          bool(got) and all(t["variant"] != "success" for t in got),
          f"批量连线弹出的不是 warning 而是 success: {got}")
    check("port:says-unavailable",
          any("暂不可用" in t["text"] for t in got), f"提示没说清: {got}")

    # ── 工具条「存为模板」 ──
    tpl = page.locator('[data-frameos-group-action="save-template"]')
    check("save-template:present", tpl.count() == 1, f"count={tpl.count()}")
    check("save-template:still-enabled", not tpl.evaluate("el => el.disabled === true"),
          "存为模板被禁用了 —— 与批量连线同一条修法, 不该只对它网开一面")
    check("save-template:explains-why", bool(tpl.get_attribute("title")),
          "存为模板应当用 title 说明为什么暂不可用")
    before = toast_multiset(page)
    tpl.click()
    page.wait_for_timeout(500)
    got = toasts_since(before, page)
    result.setdefault("toasts", {})["存为模板"] = got
    check("save-template:warns-not-claims-success",
          bool(got) and all(t["variant"] != "success" for t in got),
          f"存为模板弹出的不是 warning 而是 success: {got}")
    check("save-template:says-unavailable",
          any("暂不可用" in t["text"] for t in got), f"提示没说清: {got}")

    # ── 节点右键「设置为资产图」: batch170 回归防护 ──
    page.evaluate(
        "() => { const s = window.__frameos_store.getState();"
        " if (s.selectedGroupId) s.ungroup(window.__gid); s.selectNode(null); }"
    )
    page.wait_for_timeout(400)
    node = page.locator('.react-flow__node[data-id="image-1"]')
    node.click()
    page.wait_for_timeout(400)
    nbox = node.bounding_box()
    assert nbox, "找不到 image-1 节点"
    page.mouse.click(nbox["x"] + nbox["width"] / 2, nbox["y"] + nbox["height"] / 2, button="right")
    page.wait_for_selector("[data-frameos-context-item]", timeout=8000)
    page.wait_for_timeout(300)
    node_items = page.evaluate(ITEM_STATE_JS)
    by_node = {i["label"]: i for i in node_items}
    result["node_menu"] = node_items
    check("node-menu:设为资产图:present", "设置为资产图" in by_node,
          f"菜单项缺失, 现有: {[i['label'] for i in node_items]}")
    # 源站实测(BEHAVIORS.md:33): 内容图片态的「设置为资产图」是**启用**的
    check("node-menu:设为资产图:still-enabled", not by_node["设置为资产图"]["disabled"],
          "「设置为资产图」被禁用了 —— BEHAVIORS.md:33 的源站实测记着它是启用���, "
          "禁用的只有空图片态的复制图片/重新生成")
    check("node-menu:设为资产图:explains-why", bool(by_node["设置为资产图"]["title"]),
          "应当用 title 说明为什么暂不可用")
    before = toast_multiset(page)
    page.locator('[data-frameos-context-item="设置为资产图"]').click()
    page.wait_for_timeout(500)
    got = toasts_since(before, page)
    result.setdefault("toasts", {})["设置为资产图"] = got
    check("node-menu:设为资产图:warns-not-claims-success",
          bool(got) and all(t["variant"] != "success" for t in got),
          f"设为资产图弹出的不是 warning 而是 success: {got}")
    check("node-menu:设为资产图:says-unavailable",
          any("暂不可用" in t["text"] for t in got), f"提示没说清: {got}")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 357,
        "defect": "第三类交互谎言: 有 handler、点了弹绿色「已xxx」成功提示、但底层状态"
                  "一点没变。普查在 36 个 frameos 源文件里找到 6 条只弹 toast 的处理器, "
                  "人工核实 5 条为谎报(设置为资产图/复制分组/创建分组副本/批量连线/"
                  "存为模板), 1 条(⌘S)为真——画布本就在自动持久化。",
        "fix": "5 条谎报**保持启用**、只把 toast 从 success 改成 warning 并加 title 说明; "
               "⌘S 保持原样。禁用方案被 batch170 打回——BEHAVIORS.md:33 的源站实测记着"
               "「设置为资产图」是启用的, 缺陷在谎称成功而不在控件能不能点。",
        "role": "把「谎称成功」普查变成门禁, 并给上下文菜单加 title 支持",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run_desktop(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 357 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "No frameos handler claims success via a toast while leaving state untouched "
        "any more: the five verified lies now say plainly that they are unavailable "
        "(still clickable, as in the source), and the census is enforced as a gate."
    )


if __name__ == "__main__":
    main()
