#!/usr/bin/env python3
"""batch 735 验收（收官）：全仓 data-inert 的运行时实例普查

## 起点

729–734 把 46 个写点收口成「42 已逐处打开 + 4 条件门控」。
本批不再追新写点，而是回答一个前面五批都没问过的问题：
**这 46 个写点在浏览器里到底渲染成多少枚按钮？**

## 三个口径必须分清（这是本批的主要修正）

前面普查脚本报的「峰值并存 25 / 去重身份 78 / 累计实例 87」三个数
分属三种不同的问题，混着报会高估用户能遇到的控件量：

| 口径 | 问的是 | 本批读数 |
|---|---|---|
| 去重身份 | 有几种**不同**的按钮 | 78 |
| 名义累计 | 驱动一遍累计渲染多少枚 | 117 |
| 可见可点峰值 | 同一时刻**看得见也点得到**最多几枚 | **22** |

25 那个「峰值」是特效库面板：25 枚里 24 枚 `opacity: 0` + `pointer-events: none`，
可见的只有 1 枚筛选按钮。真峰值是**视频卡标记选择 12 + 生成历史 10 = 22 枚，全可见**。

## 判据

C1  静态 46 写点（掩码扫描，16 文件）
C2  片段重拍的入口选择器真相：`button[title=片段重拍]` 命中 0
C3  片段重拍面板打开后 6 → 9 枚（SegmentReshootPanel 6 枚换掉生成面板 3 枚）
C4  16 状态逐状态枚数表
C5  叠加：标记选择 + 生成历史 = 22 全可见；底部坞三面板互斥（10→4→4 而非 10+4+4）
C6  40 枚不可见 = 风格库 16 + 特效库 24，40 个互不相同的可及名
C7  自然 Tab 260 步：特效库状态 77 次停靠 / 27 种名（25 自身 + 2 顶栏）
C8  全部实例 role=button（AX 通道）+ 程序化 focus() 成功（DOM 通道）
C9  除显式 addNode 的状态外，store 的 nodes/edges 计数零变化
C10 4 个条件门控写点仍不出现（回归确认 733/734）
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch735-2026-10-01"
BASE = "http://localhost:4317"
W, H = 1280, 1150
TAB_STEPS = 260

# 每个状态都存在的顶栏两枚，普查时扣掉（730 已确认它们是 TopNavBar.tsx:183/:200）
TOPNAV = {"开通会员 限时 45 折", "积分余额"}

# 四个条件门控写点（733/734 已带源码 + DOM 双证），普查里应始终不出现
GATED = ["故事脚本生成", "分镜脚本", "上传视频后开始", "生成故事脚本"]


# ---------------------------------------------------------------- 静态扫描
def mask_comments(src: str) -> str:
    """抹掉行注释与块注释，保持字节偏移不变。

    730 已证：朴素 `<button\\b[^>]*>` 会在注释里那个 `<button>` 的 `>` 上截断，
    把 TopNavBar 的积分余额连同 data-inert 一起漏掉（45 而非 46）。
    """
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'`":
            q = c
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == q:
                    i += 1
                    break
                if q == "'" and src[i] == "\n":
                    break
                i += 1
            continue
        if src.startswith("//", i):
            while i < n and src[i] != "\n":
                out[i] = " "
                i += 1
            continue
        if src.startswith("/*", i):
            while i < n and not src.startswith("*/", i):
                if src[i] != "\n":
                    out[i] = " "
                i += 1
            for k in range(i, min(i + 2, n)):
                out[k] = " "
            i += 2
            continue
        i += 1
    return "".join(out)


# 729/730 的扫描范围：显式排除另两个 App 的原型目录。
# 本批第一版写成 src/**/*.tsx，把 FrameOS 的 FrameosGroupToolbar.tsx:257 一并数了进来
# （47 处 / 17 文件），差点被误读成「有人新加了写点」—— 范围必须与前批逐字一致。
EXCLUDED_PREFIXES = ("src/app/frameos", "src/components/frameos", "src/components/jimeng")


def in_scope(rel: str) -> bool:
    return not any(rel == x or rel.startswith(x + "/") for x in EXCLUDED_PREFIXES)


def static_sites():
    """返回 data-inert 写点 [(文件, 行号, 开标签属性串)]，只认落在 <button> 开标签上的。"""
    sites = []
    for path in sorted(ROOT.glob("src/**/*.tsx")):
        rel = str(path.relative_to(ROOT))
        if not in_scope(rel):
            continue
        src = path.read_text(encoding="utf-8")
        masked = mask_comments(src)
        for m in re.finditer(r"<button\b[^>]*>", masked, re.S):
            tag = m.group(0)
            if "data-inert" not in tag:
                continue
            line = masked[: m.start()].count("\n") + 1
            sites.append((rel, line, " ".join(tag.split())))
    return sites


def out_of_scope_sites():
    """范围外的 data-inert 写点，只记数不评判 —— 本批不覆盖 FrameOS / jimeng。"""
    found = []
    for path in sorted(ROOT.glob("src/**/*.tsx")):
        rel = str(path.relative_to(ROOT))
        if in_scope(rel):
            continue
        masked = mask_comments(path.read_text(encoding="utf-8"))
        for m in re.finditer(r"<button\b[^>]*>", masked, re.S):
            if "data-inert" in m.group(0):
                found.append((rel, masked[: m.start()].count("\n") + 1))
    return found


# ---------------------------------------------------------------- 运行时工具
ENUM = """() => [...document.querySelectorAll('button[data-inert]')].map(el => {
  const cs = getComputedStyle(el);
  el.focus();
  return {aria: el.getAttribute('aria-label') || '',
          title: el.getAttribute('title') || '',
          text: (el.textContent || '').trim().slice(0, 16),
          opacity: cs.opacity,
          pe: cs.pointerEvents,
          focusable: document.activeElement === el};
})"""


def snap(page):
    rows = page.evaluate(ENUM)
    return [r for r in rows if r["aria"] not in TOPNAV]


def visible(rows):
    return [r for r in rows if r["opacity"] != "0" and r["pe"] != "none"]


def name_of(row):
    return row["aria"] or row["title"] or row["text"]


def goto(page, tag):
    page.goto(f"{BASE}/?batch735={tag}", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_300)


def select_node(page, node_id):
    # 不能用 boxModel 中心真实点击：图片卡中心被封面图遮挡（723）
    page.evaluate("""(id) => { const n = document.querySelector(
      '.react-flow__node[data-id="' + CSS.escape(id) + '"]');
      if (n) { n.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:0, clientY:0}));
               n.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:0, clientY:0}));
               n.click(); } }""", node_id)
    page.wait_for_timeout(800)


def add_entry(page, entry, sub=None):
    page.evaluate("""() => { const b=document.querySelector('[aria-label="添加节点"]'); if (b) b.click(); }""")
    page.wait_for_timeout(400)
    if sub:
        page.evaluate("""(e)=>{const b=document.querySelector('[data-add-node-entry="'+e+'"]'); if(b)b.click();}""", entry)
        page.wait_for_timeout(350)
        page.evaluate("""(e)=>{const b=document.querySelector('[data-add-node-entry="'+e+'"]'); if(b)b.click();}""", sub)
    else:
        page.evaluate("""(e)=>{const b=document.querySelector('[data-add-node-entry="'+e+'"]'); if(b)b.click();}""", entry)
    page.wait_for_timeout(800)


def newest_id(page, node_type):
    return page.evaluate("""(t) => { const g = window.__libtv_store.getState().getActiveCanvas();
      const ns = g.nodes.filter(x => x.type === t);
      return ns.length ? ns[ns.length-1].id : null; }""", node_type)


def click_dock(page, label):
    page.evaluate("""(l)=>{const b=document.querySelector('[aria-label="'+l+'"]'); if(b)b.click();}""", label)
    page.wait_for_timeout(700)


def click_text(page, frag):
    return page.evaluate("""(f)=>{const b=[...document.querySelectorAll('button')]
      .find(x=>(x.textContent||'').includes(f));
      if(!b) return 'NO_BTN'; b.click(); return 'clicked';}""", frag)


def click_selector(page, selector):
    return page.evaluate("""(s)=>{const b=document.querySelector(s); if(!b) return 'NO_BTN';
      b.click(); return 'clicked';}""", selector)


def store_shape(page):
    return page.evaluate("""() => { const g = window.__libtv_store.getState().getActiveCanvas();
      return {nodes: g.nodes.length, edges: g.edges.length}; }""")


def ax_roles(cdp, page):
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    ids = cdp.send("DOM.querySelectorAll", {"nodeId": root, "selector": "button[data-inert]"})["nodeIds"]
    out = []
    for nid in ids:
        try:
            backend = cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
            tree = cdp.send("Accessibility.getPartialAXTree", {"backendNodeId": backend, "fetchRelatives": False})
        except Exception:
            out.append(None)
            continue
        own = next((n for n in tree.get("nodes", []) if n.get("role")), None)
        out.append((own or {}).get("role", {}).get("value"))
    return out


def tab_walk(page, steps):
    """自然 Tab 序列：只按 Tab 键，记录每一步 activeElement 是不是 button[data-inert]。"""
    page.evaluate("() => { window.__tabHits = []; }")
    page.evaluate("""() => {
      window.__onKey = (e) => {
        if (e.key !== 'Tab') return;
        setTimeout(() => {
          const a = document.activeElement;
          if (!a) return;
          const hit = (a.matches && a.matches('button[data-inert]'))
            ? ((a.getAttribute('aria-label') || a.getAttribute('title') || a.textContent || '').trim().slice(0, 24))
            : null;
          window.__tabHits.push(hit);
        }, 0);
      };
      document.addEventListener('keydown', window.__onKey, true);
    }""")
    for _ in range(steps):
        page.keyboard.press("Tab")
    hits = page.evaluate("() => window.__tabHits")
    page.evaluate("() => document.removeEventListener('keydown', window.__onKey, true)")
    inert = [h for h in hits if h is not None]
    counts = Counter(inert)
    return {"steps": steps, "stops": len(inert), "distinct": len(counts),
            "top": sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))}


# ---------------------------------------------------------------- 主流程
def run_census(page, cdp):
    states = {}
    store_log = {}

    def record(name, tag_allows_new_node=False):
        before = store_shape(page)
        rows = snap(page)
        roles = ax_roles(cdp, page)
        own = [r for r in rows if r["aria"] not in TOPNAV]
        own_roles = [ro for r, ro in zip(rows, roles) if r["aria"] not in TOPNAV]
        after = store_shape(page)
        states[name] = {
            "own": len(own),
            "visible": len(visible(own)),
            "rows": own,
            "axRoles": own_roles,
            "focusableAll": all(r["focusable"] for r in own),
        }
        store_log[name] = {"before": before, "after": after, "allowsNewNode": tag_allows_new_node}
        print(f"  {name:22s} 自身 {len(own):3d}  可见 {len(visible(own)):3d}  "
              f"非button {sum(1 for x in own_roles if x != 'button')}")
        return own

    # ---- 1 底部坞三面板
    goto(page, "dock")
    record("裸画布")
    for label, name in (("打开工具箱", "工具箱"), ("生成历史", "生成历史"), ("教程", "教程")):
        click_dock(page, label)
        record(name)

    # ---- 2 Agent 抽屉
    page.evaluate("""() => { const b=[...document.querySelectorAll('button')]
      .find(x=>(x.textContent||'').trim()==='Agent'); if(b)b.click(); }""")
    page.wait_for_timeout(700)
    record("Agent 抽屉")

    # ---- 3 图片卡：编辑面板 → 全景派生 → 全景面板
    goto(page, "img")
    img_id = page.evaluate("""() => { const g=window.__libtv_store.getState().getActiveCanvas();
      const n=g.nodes.find(x=>x.type==='image'); return n?n.id:null; }""")
    select_node(page, img_id)
    record("图片卡·编辑面板")
    click_selector(page, '[data-testid="image-toolbar-panorama-slash"]')
    page.wait_for_timeout(900)
    pano_id = page.evaluate("""() => { const g=window.__libtv_store.getState().getActiveCanvas();
      const n=[...g.nodes].reverse().find(x=>x.type==='image'&&x.data&&x.data.editorVariant==='panorama');
      return n?n.id:null; }""")
    if pano_id:
        select_node(page, pano_id)
    record("图片卡·全景面板", tag_allows_new_node=True)

    # ---- 4 新视频卡：生成面板 → 特效菜单 → 标记选择 → 片段重拍
    goto(page, "vid")
    add_entry(page, "video")
    video_id = newest_id(page, "video")
    select_node(page, video_id)
    record("新视频卡·生成面板", tag_allows_new_node=True)

    # C2：入口选择器真相 —— ToolbarButton 只传 label，不传 title（VideoProcessingToolbar.tsx:256-257）
    by_title = page.evaluate("""() => document.querySelectorAll('button[title="片段重拍"]').length""")
    by_text_hit = click_text(page, "片段重拍")
    selector_truth = {"byTitle": by_title, "byText": by_text_hit}
    print(f"  [C2] button[title=片段重拍] 命中 {by_title}；按可见文本 {by_text_hit}")

    # 特效菜单（先于片段重拍，保证 4 段各自独立驱动）
    goto(page, "effects")
    add_entry(page, "video")
    video_id = newest_id(page, "video")
    select_node(page, video_id)
    click_text(page, "特效")
    page.wait_for_timeout(800)
    record("视频卡·特效菜单", tag_allows_new_node=True)

    goto(page, "mark")
    add_entry(page, "video")
    video_id = newest_id(page, "video")
    select_node(page, video_id)
    click_text(page, "特效")
    page.wait_for_timeout(800)
    click_selector(page, "[data-mark-select-trigger]")
    page.wait_for_timeout(800)
    record("视频卡·标记选择", tag_allows_new_node=True)

    # 片段重拍：必须从干净的特效菜单之外驱动，且按可见文本点（见 C2）
    goto(page, "reshoot")
    add_entry(page, "video")
    video_id = newest_id(page, "video")
    select_node(page, video_id)
    reshoot_before = len(snap(page))
    click_text(page, "片段重拍")
    page.wait_for_timeout(1_000)
    record("视频卡·片段重拍", tag_allows_new_node=True)
    reshoot = {"before": reshoot_before, "after": states["视频卡·片段重拍"]["own"]}

    # ---- 5 添加节点三族
    goto(page, "audio")
    add_entry(page, "audio")
    audio_id = newest_id(page, "audio")
    if audio_id:
        select_node(page, audio_id)
    record("音频卡", tag_allows_new_node=True)

    goto(page, "clip")
    add_entry(page, "video-clip")
    clip_id = newest_id(page, "video-clip")
    if clip_id:
        select_node(page, clip_id)
    record("智能剪辑卡", tag_allows_new_node=True)

    goto(page, "script")
    add_entry(page, "script", sub="script-new")
    script_id = newest_id(page, "script-generator")
    if script_id:
        select_node(page, script_id)
    record("脚本生成器卡", tag_allows_new_node=True)

    # ---- 6 素材库两面板
    for label, name in (("风格库", "风格库"), ("特效库", "特效库")):
        goto(page, name)
        click_dock(page, "素材库")
        page.wait_for_timeout(300)
        click_text(page, label)
        page.wait_for_timeout(700)
        record(name)

    return states, store_log, selector_truth, reshoot


def run_stack(page):
    """C5：面板能不能叠加，以及叠加后的可见峰值。"""
    out = {}

    # 标记选择 + 生成历史
    goto(page, "stack-mark")
    add_entry(page, "video")
    video_id = newest_id(page, "video")
    select_node(page, video_id)
    click_text(page, "特效")
    page.wait_for_timeout(800)
    click_selector(page, "[data-mark-select-trigger]")
    page.wait_for_timeout(800)
    mark = snap(page)
    click_dock(page, "生成历史")
    stacked = snap(page)
    out["markPlusHistory"] = {"mark": len(mark), "stacked": len(stacked), "stackedVisible": len(visible(stacked))}
    print(f"  [C5] 标记选择 {len(mark)} + 生成历史 → {len(stacked)}（可见 {len(visible(stacked))}）")

    # 底部坞三面板是否互斥
    goto(page, "stack-dock")
    click_dock(page, "生成历史")
    only_history = len(snap(page))
    click_dock(page, "教程")
    plus_tutorial = len(snap(page))
    click_dock(page, "工具箱")
    plus_toolbox = len(snap(page))
    out["docks"] = {"history": only_history, "plusTutorial": plus_tutorial, "plusToolbox": plus_toolbox}
    print(f"  [C5] 坞面板：历史 {only_history} → +教程 {plus_tutorial} → +工具箱 {plus_toolbox}")

    return out


def run_tab_walks(page):
    out = {}

    goto(page, "tab-effects")
    click_dock(page, "素材库")
    page.wait_for_timeout(300)
    click_text(page, "特效库")
    page.wait_for_timeout(700)
    mounted = snap(page)
    walk = tab_walk(page, TAB_STEPS)
    out["effects"] = {"mounted": len(mounted), "mountedVisible": len(visible(mounted)), **walk}
    print(f"  [C7] 特效库 {len(mounted)} 枚（可见 {len(visible(mounted))}）："
          f"Tab {TAB_STEPS} 步停靠 {walk['stops']} 次 / {walk['distinct']} 种名")

    goto(page, "tab-mark")
    add_entry(page, "video")
    video_id = newest_id(page, "video")
    select_node(page, video_id)
    click_text(page, "特效")
    page.wait_for_timeout(800)
    click_selector(page, "[data-mark-select-trigger]")
    page.wait_for_timeout(800)
    mounted2 = snap(page)
    walk2 = tab_walk(page, TAB_STEPS)
    out["mark"] = {"mounted": len(mounted2), "mountedVisible": len(visible(mounted2)), **walk2}
    print(f"  [C7] 标记选择 {len(mounted2)} 枚：Tab {TAB_STEPS} 步停靠 {walk2['stops']} 次 / {walk2['distinct']} 种名")

    return out


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== 静态扫描 ===")
    sites = static_sites()
    files = sorted({s[0] for s in sites})
    outside = out_of_scope_sites()
    print(f"  data-inert 写点 {len(sites)} 处 / {len(files)} 文件"
          f"（范围外另有 {len(outside)} 处，不在本批范围：{outside}）")

    print("\n=== 16 状态普查 ===")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        cdp = page.context.new_cdp_session(page)
        cdp.send("Accessibility.enable")
        states, store_log, selector_truth, reshoot = run_census(page, cdp)
        print("\n=== 叠加 ===")
        stack = run_stack(page)
        print("\n=== 自然 Tab ===")
        walks = run_tab_walks(page)
        page.close()
        browser.close()

    # ---- 汇总三个口径
    identities = {}
    nominal_total = 0
    for name, st in states.items():
        nominal_total += st["own"]
        for row in st["rows"]:
            key = name_of(row)
            ident = identities.setdefault(key, {"instances": 0, "opacity": row["opacity"], "pe": row["pe"]})
            ident["instances"] += 1

    invisible = {k: v for k, v in identities.items() if v["opacity"] == "0" or v["pe"] == "none"}
    visible_peak = stack["markPlusHistory"]["stackedVisible"]
    nominal_peak_name = max(states, key=lambda k: states[k]["own"])
    nominal_peak = states[nominal_peak_name]["own"]
    nominal_peak_visible = states[nominal_peak_name]["visible"]

    all_roles = [role for st in states.values() for role in st["axRoles"]]
    all_focusable = all(st["focusableAll"] for st in states.values())
    gated_hits = sorted({name_of(r) for st in states.values() for r in st["rows"] if name_of(r) in GATED})
    style_inv = sum(1 for r in states["风格库"]["rows"] if r["opacity"] == "0" or r["pe"] == "none")
    effects_inv = sum(1 for r in states["特效库"]["rows"] if r["opacity"] == "0" or r["pe"] == "none")

    summary = {
        "staticSites": len(sites),
        "staticFiles": len(files),
        "outOfScopeSites": len(outside),
        "states": len(states),
        "identities": len(identities),
        "nominalTotal": nominal_total,
        "nominalPeakName": nominal_peak_name,
        "nominalPeak": nominal_peak,
        "nominalPeakVisible": nominal_peak_visible,
        "visiblePeak": visible_peak,
        "invisibleIdentities": len(invisible),
        "invisibleInstances": sum(v["instances"] for v in invisible.values()),
        "styleLibraryInvisible": style_inv,
        "effectsLibraryInvisible": effects_inv,
        "nonButtonRoles": sum(1 for x in all_roles if x != "button"),
        "allFocusable": all_focusable,
        "gatedHits": gated_hits,
    }
    print("\n=== 汇总 ===")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    checks = [
        ("C1 静态写点数/文件数", summary["staticSites"] == 46 and summary["staticFiles"] == 16,
         f"{summary['staticSites']} 处 / {summary['staticFiles']} 文件"),
        ("C2 片段重拍入口：title 选择器命中 0", selector_truth["byTitle"] == 0 and selector_truth["byText"] == "clicked",
         str(selector_truth)),
        ("C3 片段重拍 6→9 枚", reshoot["before"] == 6 and reshoot["after"] == 9, str(reshoot)),
        ("C4 状态数 16", summary["states"] == 16, str(summary["states"])),
        ("C5 叠加 12+10=22 全可见；坞面板互斥",
         stack["markPlusHistory"] == {"mark": 12, "stacked": 22, "stackedVisible": 22}
         and stack["docks"] == {"history": 10, "plusTutorial": 4, "plusToolbox": 4},
         json.dumps(stack, ensure_ascii=False)),
        ("C6 40 枚不可见（16+24）且可及名互不相同",
         summary["invisibleInstances"] == 40 and summary["invisibleIdentities"] == 40
         and style_inv == 16 and effects_inv == 24,
         f"{summary['invisibleIdentities']} 身份 / {summary['invisibleInstances']} 枚；风格库 {style_inv} 特效库 {effects_inv}"),
        ("C7 特效库 Tab 260 步 77 停靠 / 27 名",
         walks["effects"]["stops"] == 77 and walks["effects"]["distinct"] == 27,
         f"stops={walks['effects']['stops']} distinct={walks['effects']['distinct']}"),
        ("C8 全实例 role=button 且 focus() 成功",
         summary["nonButtonRoles"] == 0 and summary["allFocusable"],
         f"非button {summary['nonButtonRoles']} / focusable 全成功 {summary['allFocusable']}"),
        ("C9 除 addNode 状态外 store 零写入",
         all(log["before"] == log["after"] for log in store_log.values() if not log["allowsNewNode"]),
         str({k: v for k, v in store_log.items() if not v["allowsNewNode"] and v["before"] != v["after"]})),
        ("C10 4 个门控写点仍不出现", gated_hits == [], str(gated_hits)),
    ]

    print("\n=== 判据 ===")
    failures = []
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ⟵ {detail}")
        if not ok:
            failures.append(name)

    payload = {
        "static": {"sites": [{"file": f, "line": ln, "tag": tag} for f, ln, tag in sites],
                   "files": files, "outOfScope": [{"file": f, "line": ln} for f, ln in outside]},
        "run": {"states": states, "storeLog": store_log, "selectorTruth": selector_truth,
                "reshoot": reshoot, "stack": stack, "walks": walks},
        "summary": summary,
        "failures": failures,
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"\n{len(checks) - len(failures)}/{len(checks)} 判据通过；写入 {AUDIT_DIR / 'runtime-audit.json'}")
    try:
        subprocess.run(["git", "status", "--porcelain", "src"], cwd=ROOT, check=True)
    except Exception:
        pass
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
