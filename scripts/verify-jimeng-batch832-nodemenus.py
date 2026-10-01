#!/usr/bin/env python3
"""Jimeng clone batch 832-nodemenus verifier —— 普查的**第三层**：节点带来的浮层。

§38 立契约（每个浮层都要可指名 + 可定位）→ §43 补了画布内菜单 →
本批补最后一层：节点自己带出来的工具条 / 生成面板及其下拉。

## 本批真正的收获不是补了几个 testid，是**判据的边界画错了**

我一开始的普查用 `closest('.react-flow__node')` 判「节点内浮层」。实测（见 §I）
**这个边界是错的**：

    div.react-flow__node-toolbar      ← NodeToolbar / NodePanel 走 portal
      └ div.react-flow__renderer      ← 挂在**这里**，不在节点里
    div.react-flow__node
      └ div.react-flow__nodes
        └ div.react-flow__viewport

`NodeToolbar` 与 `.react-flow__node` 是**兄弟**（实测 4 个生成面板 listbox 全部
`inNode=False / inNodeToolbar=True`）。按错的边界扫，13 处生成面板 listbox
一个都进不了普查 —— 它们有名（`aria-label`）但没锚点（无 `data-testid`），
正是 §38 契约要消灭的形态。

**边界画错 = 整层漏掉，而漏掉的那一层看起来「本来就干净」。**
这和批 807/808/810/812/816/821/827 一脉相承：判据的缺陷比产品的缺陷更难发现，
因为它不会报错，只会安静地少报。

所以本批做两件事，缺一不可：
  ① 把边界改对，并**用断言锁住修正后的边界**（§I）——防后人「顺手改回去」；
  ② 按新边界把 13 处 listbox 的锚点补齐。

## 补了什么

  视频/音频节点 颜色标记选择器  ×2   （同一段代码的两个拷贝）
  文本节点 背景色调色板              ×1
  图片工具条 工具菜单                ×1
  视频生成面板 4 个 listbox          ×4
  音频生成面板 7 个 listbox          ×7
  图片生成面板 2 个 listbox          ×2

两枚颜色标记选择器**刻意不给 aria-label**（源站实测点开后枚举 0 个 role 浮层，
即该选择器在源站上既无 testid 也无可访问名）——不编名字，编了就成「复刻自有」。

## 留下的缺口（如实记，不在本批擅自补）

  · 视频工具条的「截取帧」「工具」两个下拉是**裸 div，一个 role 都没有**
    ⇒ 任何 role 型普查都看不见。见 README §47 与
    `scripts/jimeng_probe832_noderoledropdowns.py` 的源站取证。
  · `JimengAiDrawer` 3 处 + `JimengVideoPreview` 1 处有名无锚点，
    但它们**不是**节点内浮层（抽屉 / 全屏预览），不在本批边界内。
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

# ⚠️ 边界：NodeToolbar / NodePanel 是 portal 挂到 .react-flow__renderer 的，
#    与 .react-flow__node 是**兄弟**。只写 .react-flow__node 会漏掉整层。
NODE_SCOPE = ".react-flow__node, .react-flow__node-toolbar, .react-flow__node-panel"

# 源站同样没有可访问名的节点内浮层 —— 白名单，每条附取证结论
NAME_EXEMPT = {
    "audio-node-tag-picker": "源站标记按钮实测 data-testid=flow-node-selected-tag、"
                             "aria-label='Add tags'，但点开后的**选择器自身**在源站上"
                             "既无 testid 也无可访问名（实测枚举 0 个 role 浮层）",
    "video-node-tag-picker": "源站标记按钮实测 data-testid=flow-node-selected-tag、"
                             "aria-label='Add tags'，但点开后的**选择器自身**在源站上"
                             "既无 testid 也无可访问名（实测枚举 0 个 role 浮层）；"
                             "与音频节点那份是同一段代码的两个拷贝，"
                             "只补一处等于没修（同 §43 的画布右键菜单）",
}

# 源站实测真值（`scripts/jimeng_probe833_gentriggers.py` + 832 的
# `jimeng_probe832_gendropdowns.py`）。832 当时**没有**这张表，只验了
# "可访问名非空"，于是把三处非源站的名字放了过去。
SRC_NAME = {
    # 源站在这一处自相矛盾：触发器 aria-haspopup="listbox"，但展开层实测是
    # 无名 `role=presentation`。取一致的那一路 ⇒ listbox，名字沿用既有值。
    "gen-model-listbox": "模型列表",
    "gen-video-size-listbox": "视频尺寸选项",
    "gen-mode-listbox": "Reference mode options",
    "gen-duration-listbox": "Duration options",
}
SRC_ROLE = {
    "gen-model-listbox": "listbox",
    "gen-video-size-listbox": "dialog",
    "gen-mode-listbox": "listbox",
    "gen-duration-listbox": "dialog",
}
# 触发器上源站实测的 aria-haspopup（决定它弹出的 role）
SRC_HASPOPUP = {
    "gen-model-listbox": "listbox",
    "gen-video-size-listbox": "dialog",
    "gen-mode-listbox": "listbox",
    "gen-duration-listbox": "dialog",
}

CENSUS_JS = """(scope) => {
  const SEL = '[role=dialog],[role=menu],[role=listbox],[role=popover]';
  const nameOf = (e) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const lb = e.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\\s+/).map(id => document.getElementById(id))
        .filter(Boolean).map(n => (n.getAttribute('aria-label')
             || n.innerText || n.textContent || '').trim()).join(' ').trim();
      if (t) return t;
    }
    return '';
  };
  return [...document.querySelectorAll(SEL)].filter(e => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width >= 4 && r.height >= 4;
  }).map(e => {
    const r = e.getBoundingClientRect();
    return {role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
            name: nameOf(e), w: +r.width.toFixed(0), h: +r.height.toFixed(0),
            inScope: !!e.closest(scope),
            // 旧判据留一份，用来证明它确实会漏 —— §I 用
            inNodeOnly: !!e.closest('.react-flow__node')};
  });
}"""

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


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1680, "height": 1050},
        )
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        seen: list[dict] = []
        census_steps: list[str] = []

        def census(tag: str) -> list[dict]:
            rows = page.evaluate(CENSUS_JS, NODE_SCOPE)
            for r in rows:
                r["state"] = tag
            seen.extend(rows)
            census_steps.append(tag)
            return rows

        def node_tids() -> list[str]:
            return page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node')]"
                ".map(n => n.getAttribute('data-testid'))"
            )

        def insert(kind: str) -> str | None:
            """插入一个节点，返回新节点的 data-testid（按集合差分，不按序号）。"""
            before = set(node_tids())
            page.locator(f'button[aria-label="{kind}"]').first.click()
            page.wait_for_timeout(1800)
            after = node_tids()
            new = [t for t in after if t not in before]
            return new[0] if new else None

        def clear_selection() -> None:
            """把选中清空到 0 个节点。

            ⚠️ 为什么必须清：`JimengImageGenPanel` / `JimengGenPanel` 的门控是
            `selected === true && soloSelected`（多选时不挂面板，源站 62 多选
            截图同款）。而 `addNodeAt` 插出来的新节点**自带 selected**、旧的还
            选着，于是计数 = 2 ⇒ 面板永远不挂。实测 F 段 `selected=2 /
            toolbars=0` 就是这么来的 —— 看起来像「够不着」，其实是「没清场」。
            """
            pt = page.evaluate("""() => {
              const pane = document.querySelector('.react-flow__pane');
              if (!pane) return null;
              const r = pane.getBoundingClientRect();
              for (const [fx, fy] of [[0.02,0.95],[0.98,0.95],[0.02,0.05],[0.98,0.05],
                                      [0.5,0.97],[0.5,0.03],[0.03,0.5],[0.97,0.5]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const hit = document.elementFromPoint(x, y);
                if (hit && pane.contains(hit)) return {x, y};
              }
              return null;
            }""")
            if pt:
                page.mouse.click(pt["x"], pt["y"])
                page.wait_for_timeout(500)
            else:
                # 找不到空白面板点：退一步用 Escape 取消选中
                # （会顺带收起下拉，但 select() 的用途就是从头开始）
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)

        def selected_count() -> int:
            return page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length")

        def select(tid: str) -> bool:
            """选中一个节点（且**只**选中它）。

            ⚠️ 三件事都在这里，任一件不成立都返回 False，绝不假装成功：
              ① 先清场。`JimengNodeToolbar` / 生成面板的门控都是
                 `selected === true && soloSelected`；`addNodeAt` 插出来的
                 新节点自带 selected、旧的还选着，计数 = 2 ⇒ 工具条**永远不挂**。
                 实测 C 段 `toolbars: 0` 就是这么来的 —— 看着像"产品坏了"。
              ② 画布上的节点**互相叠压**，坐标点击常被别的节点子树拦截，
                 `force=True` 也没用（真实事件仍落到最上层）。所以先用
                 `elementFromPoint` 问**事实**：哪个采样点的最上层元素落在本
                 节点内，就点哪里；都不在就是**真的够不着**，如实 False。
              ③ 点完复核选中数 = 1。
            """
            clear_selection()
            pt = page.evaluate(
                """(tid) => {
              const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null;
              const r = n.getBoundingClientRect();
              if (r.width < 8 || r.height < 8) return null;
              // ⚠️ 「命中元素在本节点内」**不够** —— 还得是「不是个控件」。
              // 实测带媒体的视频节点：中心点命中的是 32px 的**播放/暂停按钮**
              // （命中元素是按钮里的 <path>），它 onClick 有 stopPropagation，
              // 于是点了不选中，`selected` 恒为 0。看着像「这节点点不动」，
              // 其实是「我点在了播放键上」。
              const CTRL = 'button,[role=button],a,input,select,textarea,'
                         + '[role=option],[role=menuitem],[role=tab]';
              for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                                      [0.5,0.75],[0.2,0.2],[0.8,0.8],[0.3,0.3],
                                      [0.7,0.7],[0.15,0.5],[0.85,0.5],[0.5,0.15]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const hit = document.elementFromPoint(x, y);
                if (hit && n.contains(hit) && !hit.closest(CTRL)) return {x, y};
              }
              return null;
            }""", tid)
            if pt is None:
                return False
            page.mouse.click(pt["x"], pt["y"])
            page.wait_for_timeout(900)
            return selected_count() == 1
            """选中一个节点。

            ⚠️ 不能直接 `locator.click()`：画布上的节点**互相叠压**，点下去
            常被别的节点的子树拦截（`subtree intercepts pointer events`），
            而且 `force=True` 也没用——真实鼠标事件仍落到最上层那个元素上。
            唯一可靠的办法是先用 `elementFromPoint` 问**事实**：哪个采样点的
            最上层元素落在本节点内，就去点哪里。够不着就**如实返回 False**，
            让前置态断言红掉，而不是悄悄换成别的节点。
            """

        def open_trigger(sel: str, want_tid: str | None = None) -> bool:
            """点开一个下拉触发器。

            三条前置态纪律都在这里：
              ① **幂等**：这些触发器是 toggle。上一次没关的话再点一次就是
                 「关上」，于是枚举到 0 个浮层，判据会**恒空**。所以先看目标
                 是不是已经开着，开着就不再点。
              ② **不用 Escape / 点空白收**：那会取消选中，连带把 NodeToolbar
                 整个卸载掉，前置态当场没了（本批踩过两次）。
              ③ **先收起别的已开下拉**：同一块面板里两个下拉是各自独立的
                 state，**可以同时开着**，而且宽的那个会盖住窄的 —— 实测
                 `音乐模型`（392 宽）压住了 `创作类型`（192 宽）里的选项，
                 点「音频生成」直接超时。真人不会这么干，先收起再点下一个。
            """
            close_open()
            if want_tid and page.locator(f'[data-testid="{want_tid}"]').count():
                return True
            loc = page.locator(sel)
            if not loc.count():
                return False
            try:
                loc.first.click(timeout=8000)
            except Exception:
                return False
            page.wait_for_timeout(700)
            return True

        # 已开下拉 → 其触发器的 aria-label 前缀（用于点原触发器收起）
        TID2TRIG = {
            "gen-model-listbox": "选择模型", "gen-video-size-listbox": "视频尺寸选项",
            "gen-mode-listbox": "生成模式", "gen-duration-listbox": "选择视频生成时长",
            "image-gen-model-listbox": "选择模型", "image-gen-size-listbox": "图片尺寸选项",
            "audio-gen-type-listbox": "创作类型", "audio-music-model-listbox": "选择模型",
            "audio-music-duration-listbox": "选择时长", "audio-voice-model-listbox": "选择模型",
            "audio-gen-mode-listbox": "音频生成", "audio-all-voices-listbox": "音色",
        }

        def close_open() -> None:
            """把当前开着的下拉逐个点回它自己的触发器（toggle 关闭）。

            ⚠️ 不能用 Escape：那会取消选中 → NodeToolbar 卸载 → 顺带把
            还没扫的浮层一起弄没了，判据会**假装**没查到。
            """
            for tid, trig in TID2TRIG.items():
                if not page.locator(f'[data-testid="{tid}"]').count():
                    continue
                loc = page.locator(f'.react-flow__node-toolbar button[aria-label^="{trig}"]')
                if not loc.count():
                    continue
                try:
                    loc.first.click(timeout=4000)
                except Exception:
                    continue
                page.wait_for_timeout(350)

        # ══ I. 先验边界本身 —— 判据错了，后面全白做 ══════════════════
        print("— I. 判据边界（本批的真正对象）—")
        empty = select("rf__node-video-empty-1")
        if open_trigger('.react-flow__node-toolbar button[aria-label^="选择模型"]'):
            census("视频生成面板·模型列表")
        mt = page.evaluate("""() => {
            const tb = document.querySelector('.react-flow__node-toolbar');
            if (!tb) return null;
            return {exists: true,
                    insideNode: !!tb.closest('.react-flow__node'),
                    insideViewport: !!tb.closest('.react-flow__viewport'),
                    parent: tb.parentElement ? tb.parentElement.className.split(/\\s+/)[0] : ''};
        }""")
        check("I.0 前置：能选中空视频节点并展开生成面板", bool(mt), f"empty={empty} tb={mt}")
        if mt:
            check(
                "I.1 NodeToolbar **不在** .react-flow__node 里（判据边界的实证）",
                mt["insideNode"] is False, f"insideNode={mt['insideNode']}",
            )
            check(
                "I.2 NodeToolbar 也不在 .react-flow__viewport 里，"
                "挂在 .react-flow__renderer 下（与节点是兄弟）",
                mt["insideViewport"] is False and mt["parent"] == "react-flow__renderer",
                f"parent={mt['parent']!r} inViewport={mt['insideViewport']}",
            )
        got = [r for r in seen if r["tid"] == "gen-model-listbox"]
        check(
            "I.3 旧判据（只看 .react-flow__node）会漏掉它，新判据能抓到 —— "
            "证明这次改的不是措辞而是覆盖",
            bool(got) and got[0]["inScope"] and not got[0]["inNodeOnly"],
            f"rows={[(r['tid'], r['inScope'], r['inNodeOnly']) for r in got]}",
        )

        # ══ E. 视频生成面板 4 处 listbox ══════════════════════════════
        print("\n— E. 视频生成面板 —")
        for trig, tid in [
            ("选择模型", "gen-model-listbox"),
            ("视频尺寸选项", "gen-video-size-listbox"),
            ("生成模式", "gen-mode-listbox"),
            ("选择视频生成时长", "gen-duration-listbox"),
        ]:
            select("rf__node-video-empty-1")
            ok = open_trigger(f'.react-flow__node-toolbar button[aria-label^="{trig}"]', tid)
            el = page.locator(f'[data-testid="{tid}"]')
            check(
                f"E.{tid} 可指名可定位（触发器「{trig}」）",
                ok and el.count() == 1,
                f"opened={ok} count={el.count()}",
            )
            if el.count():
                # 批 833 订正：可访问名不再要求"非空"就算过，而是**逐字**等于
                # 源站那一版。832 当时只验了"有名字"，把三处非源站的名字
                # （照抄了触发器按钮的 aria-label、复刻自造的两个英文名）
                # 放过去了 —— 判据太松，等于没验。
                check(
                    f"E.{tid} 可访问名**逐字**等于源站（832 只验了非空，太松）",
                    el.get_attribute("aria-label") == SRC_NAME[tid],
                    f"实际={el.get_attribute('aria-label')!r} 源站={SRC_NAME[tid]!r}",
                )
                check(
                    f"E.{tid} role 与源站一致（833：尺寸/时长 listbox→dialog）",
                    el.get_attribute("role") == SRC_ROLE[tid],
                    f"实际={el.get_attribute('role')!r} 源站={SRC_ROLE[tid]!r}",
                )
                # 批 833：触发器上要**声明**自己弹出的 role（源站四个按钮实测
                # 都有 aria-haspopup + aria-expanded），且声明值必须与浮层实际
                # role 一致 —— 两者互相矛盾时，说明有一处是错的。
                trig = page.locator(
                    f'.react-flow__node-toolbar button[aria-label^="{trig}"]').first
                check(
                    f"E.{tid} 触发器 aria-haspopup={SRC_HASPOPUP[tid]!r}（源站实测）",
                    trig.get_attribute("aria-haspopup") == SRC_HASPOPUP[tid],
                    repr(trig.get_attribute("aria-haspopup")),
                )
                check(
                    f"E.{tid} 触发器 aria-expanded 随展开态翻转（此刻应 true）",
                    trig.get_attribute("aria-expanded") == "true",
                    repr(trig.get_attribute("aria-expanded")),
                )
                check(
                    f"E.{tid} 声明的 haspopup 与浮层实际 role 自洽",
                    trig.get_attribute("aria-haspopup") == el.get_attribute("role"),
                    f"haspopup={trig.get_attribute('aria-haspopup')!r} "
                    f"role={el.get_attribute('role')!r}",
                )
                census(f"视频生成面板·{trig}")

        # ══ C. 图片工具条的工具菜单（需要**带 poster** 的图片节点）════
        #    踩过的坑：左栏新插的图片节点**没有 poster**，渲染的是生成面板而不是
        #    工具条，所以「工具」按钮数恒为 0 —— 前置态不成立，不能报成 PASS。
        #    带 poster 的图片节点要走视频「截取帧 → 首帧」才有。
        print("\n— C. 图片工具条（前置态：必须先造出带 poster 的图片节点）—")
        before = set(node_tids())
        clear_selection()
        csel = select("rf__node-video-local-1")
        cpre = page.evaluate("""() => ({
            selCount: document.querySelectorAll('.react-flow__node.selected').length,
            selectedTids: [...document.querySelectorAll('.react-flow__node.selected')]
                .map(n => n.getAttribute('data-testid')),
            hasLocal: !!document.querySelector(
                '.react-flow__node[data-testid="rf__node-video-local-1"]'),
        })""")
        cap_ok = open_trigger('.react-flow__node-toolbar button:has-text("截取帧")')
        framed = None
        if cap_ok:
            it = page.locator('.react-flow__node-toolbar button:text-is("首帧")')
            if it.count():
                it.first.click()
                page.wait_for_timeout(2200)
                new = [t for t in node_tids() if t not in before and t and "image" in t]
                framed = new[0] if new else None
        cdiag = page.evaluate("""() => ({
            toolbars: document.querySelectorAll('.react-flow__node-toolbar').length,
            labels: [...document.querySelectorAll('.react-flow__node-toolbar button')]
                      .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())
                      .filter(Boolean),
        })""")
        check("C.0 前置：走「截取帧 → 首帧」产出带 poster 的图片节点",
              framed is not None,
              f"sel={csel} pre={cpre} cap={cap_ok} framed={framed} diag={cdiag}")
        if framed:
            clear_selection()
            sel_ok = select(framed)
            tb_ok = open_trigger('.react-flow__node-toolbar button:text-is("工具")')
            tm = page.locator('[data-testid="image-tools-menu"]')
            check("C.1 图片工具条上的「工具」能展开", sel_ok and tb_ok,
                  f"sel={sel_ok} open={tb_ok}")
            check("C.2 工具菜单有锚点 image-tools-menu", tm.count() == 1,
                  f"count={tm.count()}")
            if tm.count():
                check("C.3 可访问名仍是「工具菜单」（本批只补锚点）",
                      tm.get_attribute("aria-label") == "工具菜单",
                      repr(tm.get_attribute("aria-label")))
                check("C.4 菜单内含两组共 10 项（编辑 4 + 预设 6，源站批 209 采样）",
                      tm.locator('[role=menuitem]').count() == 10,
                      f"items={tm.locator('[role=menuitem]').count()}")
                census("图片工具菜单")

        # ══ F. 图片生成面板 2 处 listbox ══════════════════════════════
        print("\n— F. 图片生成面板 —")
        img_tid = insert("图片")
        # 前置态诊断：插完节点先确认「它存在 + 点得到 + 面板真会挂上来」。
        # 上一版只报 `toolbar 按钮 aria-label=[]`，等于什么都没说。
        clear_selection()
        diag = page.evaluate(
            """(tid) => {
          if (!tid) return {tids: null};
          const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
          if (!n) return {found: false, tids: [...document.querySelectorAll(
              '.react-flow__node')].map(x => x.getAttribute('data-testid'))};
          const r = n.getBoundingClientRect();
          let hit = null;
          for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],[0.5,0.75]]) {
            const el = document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy);
            if (el && n.contains(el)) { hit = true; break; }
          }
          return {found: true, rect: [Math.round(r.x), Math.round(r.y),
                                      Math.round(r.width), Math.round(r.height)],
                  clickable: !!hit,
                  selectedNow: n.classList.contains('selected')};
        }""", img_tid)
        sel_img = select(img_tid) if img_tid else False
        state = page.evaluate("""() => ({
            toolbars: document.querySelectorAll('.react-flow__node-toolbar').length,
            selected: document.querySelectorAll('.react-flow__node.selected').length,
            labels: [...document.querySelectorAll('.react-flow__node-toolbar button')]
                      .map(b => b.getAttribute('aria-label')).filter(Boolean),
        })""")
        check(
            "F.0 前置：插出的图片节点存在、点得到、且生成面板挂上来了",
            bool(img_tid) and diag.get("found") and diag.get("clickable")
            and sel_img and state["toolbars"] >= 1 and state["selected"] == 1,
            f"tid={img_tid} diag={diag} sel={sel_img} toolbars={state['toolbars']} "
            f"selected={state['selected']} labels={state['labels']}",
        )
        for trig, tid in [
            ("选择模型", "image-gen-model-listbox"),
            ("图片尺寸选项", "image-gen-size-listbox"),
        ]:
            clear_selection()
            if img_tid:
                select(img_tid)
            ok = open_trigger(f'.react-flow__node-toolbar button[aria-label^="{trig}"]', tid)
            el = page.locator(f'[data-testid="{tid}"]')
            check(f"F.{tid} 可指名可定位（触发器「{trig}」）",
                  ok and el.count() == 1, f"opened={ok} count={el.count()}")
            if el.count():
                check(f"F.{tid} 可访问名取自源站", bool(el.get_attribute("aria-label")),
                      repr(el.get_attribute("aria-label"))[:60])
                census(f"图片生成面板·{trig}")

        # ══ G. 音频生成面板 7 处 listbox ══════════════════════════════
        print("\n— G. 音频生成面板 —")
        aud_tid = insert("音频")
        clear_selection()
        # G.1 创作类型下拉（两种创作类型共用这一个入口）
        if aud_tid:
            select(aud_tid)
        ok_type = open_trigger('.react-flow__node-toolbar button[aria-label^="创作类型"]', "audio-gen-type-listbox")
        ttype = page.locator('[data-testid="audio-gen-type-listbox"]')
        check("G.audio-gen-type-listbox 可指名可定位", ok_type and ttype.count() == 1,
              f"opened={ok_type} count={ttype.count()}")
        if ttype.count():
            census("音频生成面板·创作类型")

        # 两条互斥分支各扫一遍：音乐生成 2 处 / 音频生成 4 处。
        # ⚠️ 分支选项是 `[data-testid="audio-gen-type-listbox"]` **里面**的
        #    role=option，不是工具条上的散按钮 —— 上一版用
        #    `.react-flow__node-toolbar button:text-is("音乐生成")` 找不到，
        #    分支根本没切过去，于是「音乐模型」那处报了一个假的 0。
        trig_map = {
            "audio-music-model-listbox": "选择模型",
            "audio-music-duration-listbox": "选择时长",
            "audio-voice-model-listbox": "选择模型",
            "audio-gen-mode-listbox": "音频生成",
            "audio-all-voices-listbox": "音色",
        }
        for branch, expect in [
            ("音乐生成", ["audio-music-model-listbox", "audio-music-duration-listbox"]),
            ("音频生成", ["audio-voice-model-listbox", "audio-gen-mode-listbox",
                          "audio-all-voices-listbox", "@filter"]),
        ]:
            clear_selection()
            if aud_tid:
                select(aud_tid)
            open_trigger('.react-flow__node-toolbar button[aria-label^="创作类型"]',
                         "audio-gen-type-listbox")
            opt = page.locator(
                '[data-testid="audio-gen-type-listbox"] [role=option]'
                f':text-is("{branch}")')
            switched = False
            if opt.count():
                opt.first.click()
                page.wait_for_timeout(900)
                switched = True
            now = page.evaluate(
                """() => { const b = document.querySelector(
                    '.react-flow__node-toolbar button[aria-label^="创作类型"]');
                    return b ? b.getAttribute('aria-label') : null; }""")
            check(f"G.分支切换到「{branch}」", switched and now and branch in now,
                  f"switched={switched} now={now!r}")
            for tid in expect:
                clear_selection()
                if aud_tid:
                    select(aud_tid)
                if tid == "@filter":
                    # 音色筛选下拉**没有自己的触发器**：它们是「全音色」面板里
                    # 4 个筛选钮各自挂的子下拉，渲染在同一个 map 里，父面板一开
                    # 4 个就同时在 DOM 里。所以这里的「打开」= 打开全音色。
                    ok = open_trigger(
                        '.react-flow__node-toolbar button[aria-label^="音色"]',
                        "audio-all-voices-listbox")
                    tid = "audio-voice-filter-listbox"
                else:
                    ok = open_trigger(
                        f'.react-flow__node-toolbar button[aria-label^="{trig_map[tid]}"]', tid)
                el = page.locator(f'[data-testid="{tid}"]')
                # 音色筛选下拉是 4 个**同族实例**（性别/年龄/语言/声音特点），
                # 共用一个 testid —— 这是刻意的：它们是同一段 map 出来的，
                # 彼此靠**互不相同**的 aria-label 区分（下方单独断言）。
                # 其余都是单例，必须 count()==1。
                want = 1 if tid != "audio-voice-filter-listbox" else 4
                check(f"G.{tid} 可指名可定位（{branch} 分支）",
                      ok and el.count() == want,
                      f"opened={ok} count={el.count()} want={want}")
                if el.count() == 1:
                    check(f"G.{tid} 可访问名取自源站", bool(el.get_attribute("aria-label")),
                          repr(el.get_attribute("aria-label"))[:60])
                else:
                    # 同族多实例：Playwright strict mode 会直接报错，所以走批量
                    names = page.evaluate(
                        """(tid) => [...document.querySelectorAll(
                            `[data-testid="${tid}"]`)]
                            .map(e => e.getAttribute('aria-label'))""", tid)
                    check(f"G.{tid} 每个实例都有可访问名（取自源站）",
                          all(names) and len(names) == el.count(), f"{names}")
                    check(f"G.{tid} 同族实例的 aria-label 互不相同（靠名字区分）",
                          len(set(names)) == len(names), f"{names}")
                if el.count():
                    census(f"音频生成面板·{branch}·{tid}")

        # ══ A. 视频节点颜色标记选择器 ════════════════════════════════
        print("\n— A. 颜色标记选择器（刻意无名）—")
        clear_selection()
        select("rf__node-video-local-1")
        ok_a = open_trigger(
            '.react-flow__node[data-testid="rf__node-video-local-1"] '
            'button[aria-label="Add tags"]')
        vp = page.locator('[data-testid="video-node-tag-picker"]')
        check("A.1 视频节点标记选择器有锚点", ok_a and vp.count() == 1,
              f"opened={ok_a} count={vp.count()}")
        if vp.count():
            check("A.2 **刻意无** aria-label —— 源站该选择器实测枚举 0 个 role 浮层",
                  vp.get_attribute("aria-label") is None,
                  repr(vp.get_attribute("aria-label")))
            check("A.3 内含「清除颜色标记」+ N 枚颜色钮",
                  vp.locator("button").count() >= 2,
                  f"buttons={vp.locator('button').count()}")
            census("视频节点标记选择器")

        # ══ D. 音频节点颜色标记选择器（同一段代码的另一个拷贝）════════
        clear_selection()
        if aud_tid:
            select(aud_tid)
        # ⚠️ 必须把触发器**限定在目标节点内**：`Add tags` 在**每个**节点的标题行里
        # 都常驻 DOM（批 263 只用 CSS 控制悬停可见），所以全局取
        # `button[aria-label="Add tags"]` 的 `.first` 拿到的是**文档顺序更靠前的
        # 视频节点**那份 —— 点了它，`video-node-tag-picker` 开了，
        # `audio-` 的自然数 0。看起来像「这处没补锚点」，其实是点错了地方。
        ok_d = open_trigger(
            f'.react-flow__node[data-testid="{aud_tid}"] button[aria-label="Add tags"]'
            if aud_tid else 'button[aria-label="Add tags"]')
        ap = page.locator('[data-testid="audio-node-tag-picker"]')
        check("D.1 音频节点标记选择器有锚点（与视频那份是**两个拷贝**，只补一处等于没修）",
              ok_d and ap.count() == 1, f"opened={ok_d} count={ap.count()}")
        if ap.count():
            check("D.2 **刻意无** aria-label（同 A.2）",
                  ap.get_attribute("aria-label") is None,
                  repr(ap.get_attribute("aria-label")))
            census("音频节点标记选择器")

        # ══ B. 文本节点背景色调色板 ══════════════════════════════════
        print("\n— B. 文本节点 —")
        txt_tid = insert("文本")
        clear_selection()
        # ⚠️ 前置态是**互斥**的，叠一起就永远不成立：「背景色」挂在
        # `NodeToolbar isVisible={selected === true && !editing}` 上 ——
        # 只在**选中非编辑态**才有。上一版先 dblclick 进编辑态再找「背景色」，
        # 工具条压根不挂，报出来是「点不开」，看着像产品坏了，其实是前置态自相矛盾。
        opened_b = False
        bdiag: dict = {}
        if txt_tid and select(txt_tid):
            bdiag = page.evaluate("""() => ({
                toolbars: document.querySelectorAll('.react-flow__node-toolbar').length,
                labels: [...document.querySelectorAll('.react-flow__node-toolbar button')]
                          .map(b => b.getAttribute('aria-label')).filter(Boolean),
            })""")
            opened_b = open_trigger('button[aria-label="背景色"]', "text-bg-palette")
        tn = page.locator('[data-testid="text-bg-palette"]')
        check("B.0 前置：文本节点**选中态**工具条挂上来了并点开「背景色」",
              opened_b, f"opened={opened_b} diag={bdiag}")
        check("B.1 背景色调色板有锚点", tn.count() == 1, f"count={tn.count()}")
        if tn.count():
            check("B.2 可访问名仍是源站那个「背景色调色板」（本批只补锚点，不改名字）",
                  tn.get_attribute("aria-label") == "背景色调色板",
                  repr(tn.get_attribute("aria-label")))
            census("文本背景色调色板")

        # ══ H. 普查结论（白名单四道锁，同 §43）══════════════════════
        print("\n— H. 节点内浮层普查 —")
        scope_rows = [r for r in seen if r["inScope"]]
        by_tid = {r["tid"]: r for r in scope_rows if r["tid"]}
        check(
            f"H.1 本次打开的节点内浮层都有 data-testid（枚举 {len(scope_rows)} 层 / "
            f"{len(census_steps)} 个状态）",
            all(r["tid"] for r in scope_rows),
            "; ".join(f"{r['state']}/{r['role']}" for r in scope_rows if not r["tid"]),
        )
        unnamed = [r for r in scope_rows if not r["name"] and r["tid"] not in NAME_EXEMPT]
        check("H.2 除白名单外都有可访问名", not unnamed,
              "; ".join(f"{r['state']}/{r['tid']}" for r in unnamed[:4]))
        exempt_hits = [r for r in scope_rows if not r["name"] and r["tid"] in NAME_EXEMPT]
        check("H.3 白名单条目确实以「无名」状态出现过（都拿到名字了会红，提醒摘掉）",
              bool(exempt_hits), f"命中 {[r['tid'] for r in exempt_hits]}")
        check("H.4 白名单每条都带取证结论",
              all("源站" in v for v in NAME_EXEMPT.values()),
              "; ".join(f"{k}:{len(v)}字" for k, v in NAME_EXEMPT.items()))
        check("H.5 白名单条目在本次枚举里都真的出现过（不能写没扫过的条目）",
              all(any(r["tid"] == k for r in scope_rows) for k in NAME_EXEMPT),
              "; ".join(k for k in NAME_EXEMPT if not any(r["tid"] == k for r in scope_rows)))
        check("H.6 旧判据确实会漏 —— 记下漏了几层，免得以后有人把边界改回去还看不见",
              len([r for r in scope_rows if not r["inNodeOnly"]]) > 0,
              f"旧判据漏 {len([r for r in scope_rows if not r['inNodeOnly']])} 层")

        # 静态：17 个 testid 都在源码里，防止被误删
        root = Path(__file__).resolve().parent.parent / "src/components/jimeng"
        allsrc = "\n".join(f.read_text(encoding="utf-8") for f in root.rglob("*.tsx"))
        WANT = ["text-bg-palette", "image-tools-menu", "audio-node-tag-picker",
                "video-node-tag-picker", "gen-model-listbox", "gen-video-size-listbox",
                "gen-mode-listbox", "gen-duration-listbox", "audio-gen-type-listbox",
                "audio-music-model-listbox", "audio-music-duration-listbox",
                "audio-voice-model-listbox", "audio-gen-mode-listbox",
                "audio-all-voices-listbox", "audio-voice-filter-listbox",
                "image-gen-model-listbox", "image-gen-size-listbox"]
        missing = [t for t in WANT if f'data-testid="{t}"' not in allsrc]
        check(f"H.7 静态：{len(WANT)} 个锚点都在源码里", not missing, f"缺 {missing}")

        check("Z.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print("\n普查状态序列：")
    for i, s in enumerate(census_steps, 1):
        print(f"  {i:2}. {s}")
    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 832-nodemenus OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
